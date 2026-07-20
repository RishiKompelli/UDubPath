#!/usr/bin/env python3
"""Download public UW course-description pages into one local JSON catalog.

Uses only Python's standard library. The scraper covers Seattle, Bothell, and
Tacoma catalog indexes. It is intentionally conservative: a small worker pool,
request timeout, retries, and a descriptive user agent.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "catalog-live.json"
CATALOGS = {
    "Seattle": "https://www.washington.edu/students/crscat/",
    "Bothell": "https://www.washington.edu/students/crscatb/",
    "Tacoma": "https://www.washington.edu/students/crscatt/",
}
USER_AGENT = "UW-Degree-Mapper/1.0 (personal academic planning; public catalog sync)"
PREFIX_NORMALIZATION = {"M E": "ME", "A A": "AA", "E E": "EE"}
COURSE_HEADER = re.compile(
    r"^([A-Z][A-Z0-9 &/.'-]*?)\s+(\d{3}[A-Z]?)\s+(.+?)\s+\(([^)]*)\)\s*(.*)$"
)
CODE_RE = re.compile(r"\b([A-Z][A-Z0-9 &/.'-]{0,12}?)\s+(\d{3}[A-Z]?)\b")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


class ParagraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.buffer: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "p":
            self.depth += 1
            if self.depth == 1:
                self.buffer = []
        elif self.depth and tag in {"br", "li"}:
            self.buffer.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "p" and self.depth:
            self.depth -= 1
            if self.depth == 0:
                text = clean_text("".join(self.buffer))
                if text:
                    self.paragraphs.append(text)

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.buffer.append(data)


@dataclass(frozen=True)
class DepartmentPage:
    campus: str
    url: str


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def normalize_prefix(prefix: str) -> str:
    prefix = clean_text(prefix).upper()
    return PREFIX_NORMALIZATION.get(prefix, prefix)


def normalize_code(prefix: str, number: str) -> str:
    return f"{normalize_prefix(prefix)} {number.upper()}"


def fetch(url: str, retries: int = 2, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except Exception as exc:  # Network errors vary by platform.
            last_error = exc
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"Could not download {url}: {last_error}")


def discover_pages(campus: str, base_url: str) -> list[DepartmentPage]:
    parser = LinkParser()
    parser.feed(fetch(base_url))
    base_path = urllib.parse.urlparse(base_url).path
    pages: set[str] = set()
    for href in parser.links:
        absolute = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.netloc not in {"www.washington.edu", "washington.edu", "www-world.cac.washington.edu"}:
            continue
        if not parsed.path.startswith(base_path) or not parsed.path.endswith(".html"):
            continue
        filename = Path(parsed.path).name.lower()
        if filename in {"index.html", "search.html", "glossary.html"}:
            continue
        pages.add(urllib.parse.urlunparse(parsed._replace(fragment="", query="")))
    return [DepartmentPage(campus, url) for url in sorted(pages)]


def extract_areas(tail: str) -> str:
    # Areas appear immediately after credits, before the prose description.
    matches = re.findall(r"\b(?:A&H|SSc|NSc|DIV|RSN|W|C)\b", tail)
    return ", ".join(dict.fromkeys(matches))


def extract_codes(text: str) -> list[str]:
    values: list[str] = []
    for prefix, number in CODE_RE.findall(text):
        code = normalize_code(prefix, number)
        if code not in values:
            values.append(code)
    return values


def parse_course_paragraph(paragraph: str, campus: str, source_url: str) -> dict | None:
    match = COURSE_HEADER.match(paragraph)
    if not match:
        return None
    prefix, number, title, credits, tail = match.groups()
    code = normalize_code(prefix, number)
    if title.lower().startswith("view course details"):
        return None

    prereq_match = re.search(
        r"Prerequisite:\s*(.*?)(?=\s+(?:Recommended:|Offered:|View course details in MyPlan:)|$)",
        paragraph,
        flags=re.IGNORECASE,
    )
    offered_match = re.search(
        r"Offered:\s*(.*?)(?=\s+View course details in MyPlan:|$)",
        paragraph,
        flags=re.IGNORECASE,
    )
    prereq_text = clean_text(prereq_match.group(1)) if prereq_match else ""
    offered = clean_text(offered_match.group(1)) if offered_match else ""

    description = tail
    description = re.sub(r"^\s*(?:A&H|SSc|NSc|DIV|RSN|W|C)(?:\s*,?\s*(?:A&H|SSc|NSc|DIV|RSN|W|C))*\s*", "", description)
    description = re.split(r"\s+Prerequisite:\s*", description, maxsplit=1, flags=re.IGNORECASE)[0]
    description = re.split(r"\s+Offered:\s*", description, maxsplit=1, flags=re.IGNORECASE)[0]
    description = re.split(r"\s+View course details in MyPlan:\s*", description, maxsplit=1, flags=re.IGNORECASE)[0]
    description = clean_text(description)

    return {
        "id": f"{campus.lower()}::{code}",
        "campus": campus,
        "department": normalize_prefix(prefix),
        "number": number,
        "code": code,
        "title": clean_text(title),
        "credits": clean_text(credits),
        "areas": extract_areas(tail),
        "prerequisiteText": prereq_text,
        "prerequisiteCodes": extract_codes(prereq_text),
        "offered": offered,
        "description": description,
        "sourceType": "official-live",
        "sourceUrl": source_url,
    }


def parse_department(page: DepartmentPage) -> tuple[DepartmentPage, list[dict], str | None]:
    try:
        parser = ParagraphParser()
        parser.feed(fetch(page.url))
        courses = []
        for paragraph in parser.paragraphs:
            course = parse_course_paragraph(paragraph, page.campus, page.url)
            if course:
                courses.append(course)
        return page, courses, None
    except Exception as exc:
        return page, [], str(exc)


def sync_catalog(output: Path = DEFAULT_OUTPUT, campuses: Iterable[str] | None = None, workers: int = 6) -> dict:
    selected = list(campuses or CATALOGS.keys())
    pages: list[DepartmentPage] = []
    print("Discovering UW department catalog pages...")
    for campus in selected:
        if campus not in CATALOGS:
            raise ValueError(f"Unknown campus: {campus}")
        found = discover_pages(campus, CATALOGS[campus])
        pages.extend(found)
        print(f"  {campus}: {len(found)} department pages")

    courses: dict[str, dict] = {}
    errors: list[dict] = []
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as pool:
        futures = [pool.submit(parse_department, page) for page in pages]
        for future in as_completed(futures):
            page, page_courses, error = future.result()
            completed += 1
            if error:
                errors.append({"campus": page.campus, "url": page.url, "error": error})
            for course in page_courses:
                courses[course["id"]] = course
            if completed % 10 == 0 or completed == len(pages):
                print(f"  Parsed {completed}/{len(pages)} pages; {len(courses)} courses", flush=True)

    sorted_courses = sorted(courses.values(), key=lambda item: (item["campus"], item["code"]))
    payload = {
        "metadata": {
            "sourceType": "official-live",
            "source": "University of Washington public course-description catalog",
            "syncedAt": datetime.now(timezone.utc).isoformat(),
            "courseCount": len(sorted_courses),
            "campuses": selected,
            "departmentPages": len(pages),
            "failedPages": len(errors),
            "errors": errors[:30],
        },
        "courses": sorted_courses,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    temporary.replace(output)
    print(f"Saved {len(sorted_courses)} courses to {output}")
    if errors:
        print(f"Warning: {len(errors)} pages failed. The successful pages were still saved.", file=sys.stderr)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync all public UW course descriptions")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--campus", choices=["all", "Seattle", "Bothell", "Tacoma"], default="all")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    campuses = None if args.campus == "all" else [args.campus]
    try:
        sync_catalog(args.output, campuses=campuses, workers=args.workers)
        return 0
    except KeyboardInterrupt:
        print("Catalog sync cancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Catalog sync failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
