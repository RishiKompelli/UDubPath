from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAJOR_DIR = ROOT / "data" / "majors"
INDEX_FILE = MAJOR_DIR / "index.json"
OUTPUT_FILE = MAJOR_DIR / "mathematics-bs.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def normalize_code(value: str) -> str:
    return " ".join(str(value).upper().split())


def load_catalog() -> list[dict[str, Any]]:
    paths = [
        ROOT / "data" / "catalog-live.json",
        ROOT / "data" / "catalog-fallback.json",
    ]
    for path in paths:
        if not path.exists():
            continue
        payload = load_json(path)
        courses = payload.get("courses", payload) if isinstance(payload, dict) else payload
        if isinstance(courses, list):
            return courses
    return []


def numeric_credits(value: Any) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(match.group()) if match else 0.0


catalog = load_catalog()
seattle_by_code: dict[str, dict[str, Any]] = {}
for course in catalog:
    code = normalize_code(course.get("code", ""))
    if not code:
        continue
    if code not in seattle_by_code or course.get("campus") == "Seattle":
        seattle_by_code[code] = course


CORE_STANDARD = [
    "MATH 124", "MATH 125", "MATH 126", "MATH 207", "MATH 208",
    "MATH 200", "MATH 224", "MATH 300", "MATH 327", "MATH 424",
]
CORE_HONORS = [
    "MATH 134", "MATH 135", "MATH 136",
    "MATH 334", "MATH 335", "MATH 336",
]

SEQUENCES = {
    "Modern Algebra": ["MATH 402", "MATH 403", "MATH 404"],
    "Concepts of Analysis": ["MATH 425", "MATH 426"],
    "Complex Analysis": ["MATH 427", "MATH 428"],
    "Topology & Geometry": ["MATH 441", "MATH 442", "MATH 443"],
    "Optimization": ["MATH 407", "MATH 408", "MATH 409"],
    "Combinatorics": ["MATH 461", "MATH 462"],
    "Numerical Analysis": ["MATH 464", "MATH 465"],
    "Probability": ["MATH 491", "MATH 492", "MATH 493"],
}
SEQUENCE_CODES = unique([
    code
    for codes in SEQUENCES.values()
    for code in codes
])

EXCLUDED_MATH_ELECTIVES = {
    "MATH 300", "MATH 342", "MATH 382", "MATH 397", "MATH 398",
    "MATH 399", "MATH 411", "MATH 412", "MATH 444", "MATH 445",
    "MATH 497", "MATH 498", "MATH 499",
}

catalog_math_electives: list[str] = []
for code, course in seattle_by_code.items():
    match = re.fullmatch(r"MATH\s+(\d{3})[A-Z]?", code)
    if not match:
        continue
    level = int(match.group(1))
    if not 300 <= level <= 499:
        continue
    if code in EXCLUDED_MATH_ELECTIVES:
        continue
    catalog_math_electives.append(code)

# These are valid even if an older fallback catalog does not include them.
REQUIRED_ELECTIVE_CODES = [
    "MATH 301", "MATH 303", "MATH 318", "MATH 327", "MATH 334",
    "MATH 335", "MATH 336", "MATH 340", "MATH 380", "MATH 394",
    "MATH 395", "MATH 396", "MATH 402", "MATH 403", "MATH 404",
    "MATH 407", "MATH 408", "MATH 409", "MATH 420", "MATH 424",
    "MATH 425", "MATH 426", "MATH 427", "MATH 428", "MATH 441",
    "MATH 442", "MATH 443", "MATH 461", "MATH 462", "MATH 464",
    "MATH 465", "MATH 480", "MATH 491", "MATH 492", "MATH 493",
    "MATH 496",
]
MATH_ELECTIVE_POOL = sorted(unique(catalog_math_electives + REQUIRED_ELECTIVE_CODES))

# Core courses generally cannot be reused in Advanced Core & Electives.
# MATH 335 and MATH 336 have explicit double-use allowances on the department page.
ADVANCED_COUNT_POOL = [
    code for code in MATH_ELECTIVE_POOL
    if code not in set(CORE_STANDARD + ["MATH 134", "MATH 135", "MATH 136", "MATH 334"])
]

OUTSIDE_APPROVED = [
    "AMATH 383", "AMATH 402", "AMATH 403",
    "CSE 332", "CSE 333", "CSE 373", "CSE 374", "CSE 417", "CSE 421",
    "ECON 400", "ECON 424", "ECON 484",
    "E E 416", "E E 418",
    "PHYS 321", "PHYS 322", "PHYS 324",
    "PHIL 470", "PHIL 471", "PHIL 472",
]


def override(
    title: str,
    credits: str,
    prereqs: list[list[str]] | None = None,
    offered: str = "",
    areas: str = "NSc",
    other: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "title": title,
        "credits": credits,
        "prerequisiteGroups": prereqs or [],
    }
    if offered:
        result["offered"] = offered
    if areas:
        result["areas"] = areas
    if other:
        result["otherPrerequisites"] = other
    return result


course_overrides: dict[str, dict[str, Any]] = {
    "MATH 124": override("Calculus with Analytic Geometry I", "5", offered="A,W,Sp,S", areas="NSc, RSN", other="Requires placement or an accepted prerequisite route."),
    "MATH 125": override("Calculus with Analytic Geometry II", "5", [["MATH 124"]], "A,W,Sp,S"),
    "MATH 126": override("Calculus with Analytic Geometry III", "5", [["MATH 125"]], "A,W,Sp,S"),
    "MATH 134": override("Accelerated [Honors] Calculus", "5", offered="A", areas="NSc, RSN", other="First course of the accelerated honors sequence."),
    "MATH 135": override("Accelerated [Honors] Calculus", "5", [["MATH 134"]], "W"),
    "MATH 136": override("Accelerated [Honors] Calculus", "5", [["MATH 135"]], "Sp"),
    "MATH 200": override("Discrete Mathematics I", "5", offered="A,W,Sp,S", areas="NSc, RSN", other="Recommended: Mathematics Guided Self-Placement."),
    "MATH 207": override("Introduction to Differential Equations", "4", [["MATH 125"]], "A,W,Sp,S"),
    "MATH 208": override("Matrix Algebra with Applications", "4", offered="A,W,Sp,S", areas="NSc, RSN", other="Recommended: Mathematics Guided Self-Placement."),
    "MATH 224": override("Advanced Multivariable Calculus", "4", [["MATH 126", "MATH 136"]], "A,W,Sp,S"),
    "MATH 300": override("Introduction to Mathematical Reasoning", "4", [["MATH 126", "MATH 136"]], "A,W,Sp,S"),
    "MATH 327": override("Introductory Real Analysis I", "4", [["MATH 300", "MATH 334"]], "A,W,Sp,S"),
    "MATH 334": override("Accelerated [Honors] Advanced Calculus", "5", [["MATH 136", "MATH 126"], ["MATH 136", "MATH 207"], ["MATH 136", "MATH 208"]], "A"),
    "MATH 335": override("Accelerated [Honors] Advanced Calculus", "5", [["MATH 334"]], "W"),
    "MATH 336": override("Accelerated [Honors] Advanced Calculus", "5", [["MATH 335"]], "Sp"),
    "MATH 402": override("Introduction to Modern Algebra", "4", [["MATH 334", "MATH 300"], ["MATH 334", "MATH 208", "MATH 136"]], "A,W,S"),
    "MATH 403": override("Introduction to Modern Algebra", "4", [["MATH 402"]], "W,Sp"),
    "MATH 404": override("Introduction to Modern Algebra", "4", [["MATH 403"]], "Sp"),
    "MATH 407": override("Linear Optimization", "4", [["MATH 136", "MATH 208", "AMATH 352"]], "A,W"),
    "MATH 408": override("Nonlinear Optimization", "4", [["MATH 327", "MATH 334"], ["MATH 407", "MATH 464"]], "W"),
    "MATH 409": override("Discrete Optimization", "4", [["MATH 407"], ["MATH 300", "MATH 334"]], "Sp"),
    "MATH 424": override("Fundamental Concepts of Analysis", "4", [["MATH 327", "MATH 335"]], "A,W,Sp,S"),
    "MATH 425": override("Fundamental Concepts of Analysis", "4", [["MATH 136", "MATH 208"], ["MATH 335", "MATH 424"]], "W,Sp"),
    "MATH 426": override("Fundamental Concepts of Analysis", "4", [["MATH 425"]], "Sp"),
    "MATH 427": override("Complex Analysis", "4", [["MATH 327", "MATH 335"]], "A,S"),
    "MATH 428": override("Complex Analysis", "4", [["MATH 427"]], "W"),
    "MATH 441": override("Topology", "4", [["MATH 327", "MATH 335"]], "A,S"),
    "MATH 442": override("Differential Geometry", "4", [["MATH 441"], ["MATH 334", "MATH 208"], ["MATH 334", "MATH 224"]], "W"),
    "MATH 443": override("Differential Geometry", "4", [["MATH 442"]], "Sp"),
    "MATH 461": override("Combinatorial Theory I", "4", [["MATH 334", "MATH 300"], ["MATH 334", "MATH 136", "MATH 208"]]),
    "MATH 462": override("Combinatorial Theory II", "4", [["MATH 461", "CSE 421"]]),
    "MATH 464": override("Numerical Analysis I", "4", [["MATH 136", "MATH 126"], ["MATH 136", "MATH 208"]], "A"),
    "MATH 465": override("Numerical Analysis II", "4", [["MATH 464"]], "W"),
    "MATH 491": override("Introduction to Stochastic Processes I", "4", [["MATH 394", "STAT 394", "STAT 340"], ["MATH 395", "STAT 395", "MATH 396", "STAT 396"]], "A"),
    "MATH 492": override("Introduction to Stochastic Processes II", "4", [["MATH 491", "STAT 491"]]),
    "MATH 493": override("Stochastic Calculus for Option Pricing", "4", [["MATH 491", "STAT 491"]]),
    "MATH 301": override("Elementary Number Theory", "4", [["MATH 136", "MATH 334", "MATH 126"], ["MATH 136", "MATH 334", "MATH 300"]]),
    "MATH 318": override("Advanced Linear Algebra: Tools and Applications", "4", [["MATH 208", "MATH 136"]]),
    "MATH 340": override("Abstract Linear Algebra", "4", [["MATH 334", "MATH 208"], ["MATH 334", "MATH 300"]]),
    "MATH 394": override("Probability I", "4", [["MATH 126", "MATH 136"]], "A,W,Sp,S"),
    "MATH 420": override("History of Mathematics", "4", [["MATH 126", "MATH 136"]], areas="NSc, DIV"),
}

# Preserve catalog names/credits for visible courses that do not need curated prerequisite logic.
for code in unique(ADVANCED_COUNT_POOL + OUTSIDE_APPROVED):
    if code in course_overrides:
        continue
    record = seattle_by_code.get(code)
    if not record:
        continue
    course_overrides[code] = {
        key: record.get(key, "")
        for key in ("title", "credits", "areas", "offered")
        if record.get(key, "") not in (None, "")
    }


major = {
    "id": "uw-seattle-math-bs",
    "university": "University of Washington Seattle",
    "name": "Mathematics",
    "degree": "Bachelor of Science in Mathematics",
    "catalogYear": "Students admitted to the major Winter 2026 or after",
    "totalCredits": 180,
    "sources": [
        {
            "label": "B.S. Mathematics major requirements — Winter 2026 onward",
            "url": "https://math.washington.edu/bs-mathematics-major-requirements-0",
        },
        {
            "label": "Mathematics major declaration pathways",
            "url": "https://math.washington.edu/math-major-declaration",
        },
        {
            "label": "UW Mathematics course catalog",
            "url": "https://www.washington.edu/students/crscat/math.html",
        },
        {
            "label": "College of Arts & Sciences graduation requirements",
            "url": "https://www.washington.edu/students/gencat/program/S/college_arts_sciences.html",
        },
    ],
    "tracks": [
        {
            "id": "standard",
            "name": "B.S. Mathematics",
            "description": "Current 74–88 credit B.S. Mathematics curriculum for students admitted Winter 2026 or later.",
        }
    ],
    "courseOverrides": course_overrides,
    "mapGroups": [
        {
            "id": "admission",
            "label": "Mathematics Major Declaration",
            "shortLabel": "Admission",
            "credits": "Before declaring",
            "description": "Early Entrance or Standard Entry pathway, including grade requirements.",
            "courses": [],
            "requirementRefs": [
                {
                    "id": "math-admission",
                    "scope": "requirement",
                    "label": "Declaration pathway",
                    "credits": "Before declaring",
                }
            ],
        },
        {
            "id": "general-education",
            "label": "General Education Requirements",
            "shortLabel": "General Education",
            "credits": "College of Arts & Sciences",
            "description": "Composition, language, writing, reasoning, Areas of Inquiry, and Diversity.",
            "courses": [],
            "requirementRefs": [
                {"id": "english-comp", "scope": "item", "label": "English Composition", "credits": "5 cr"},
                {"id": "foreign-language", "scope": "item", "label": "Foreign Language", "credits": "0–15 cr"},
                {"id": "reasoning", "scope": "item", "label": "Reasoning", "credits": "5 cr"},
                {"id": "writing", "scope": "item", "label": "Additional Writing", "credits": "10 cr"},
                {"id": "ah", "scope": "item", "label": "Arts & Humanities", "credits": "20 cr"},
                {"id": "ssc", "scope": "item", "label": "Social Sciences", "credits": "20 cr"},
                {"id": "nsc", "scope": "item", "label": "Natural Sciences", "credits": "20 cr"},
                {"id": "additional-aoi", "scope": "item", "label": "Additional Areas of Inquiry", "credits": "15 cr"},
                {"id": "div", "scope": "item", "label": "Diversity", "credits": "5 cr"},
            ],
        },
        {
            "id": "calculus-linear",
            "label": "Calculus, Differential Equations & Linear Algebra",
            "shortLabel": "Calculus & Linear Algebra",
            "credits": "15–23 cr",
            "description": "Choose the standard five-course route or the accelerated honors calculus sequence.",
            "courses": [
                "MATH 124", "MATH 125", "MATH 126", "MATH 207", "MATH 208",
                "MATH 134", "MATH 135", "MATH 136",
            ],
        },
        {
            "id": "proof-analysis-core",
            "label": "Proof & Analysis Core",
            "shortLabel": "Proof & Analysis",
            "credits": "15–21 cr",
            "description": "Choose the standard proof/analysis route or accelerated advanced honors sequence.",
            "courses": [
                "MATH 200", "MATH 224", "MATH 300", "MATH 327", "MATH 424",
                "MATH 334", "MATH 335", "MATH 336",
            ],
        },
        {
            "id": "advanced-sequences",
            "label": "Advanced Mathematics Sequences",
            "shortLabel": "Advanced Sequences",
            "credits": "5–6 sequence courses",
            "description": "Complete two three-quarter or three two-quarter sequences, including at least one sequence in algebra, analysis, topology/geometry, or complex analysis.",
            "courses": SEQUENCE_CODES,
        },
        {
            "id": "major-electives",
            "label": "Mathematics Major Electives",
            "shortLabel": "Major Electives",
            "credits": "44 cr combined with sequences",
            "description": "A total of 11 advanced-sequence and approved elective courses. No more than two MATH 380/480 special-topic courses.",
            "courses": [
                code for code in ADVANCED_COUNT_POOL
                if code not in set(SEQUENCE_CODES)
            ],
        },
        {
            "id": "outside-options",
            "label": "Approved Outside-Department Options",
            "shortLabel": "Outside Options",
            "credits": "Up to 2 courses",
            "description": "With adviser approval, up to two listed courses from one outside department may replace Math electives.",
            "courses": OUTSIDE_APPROVED,
        },
        {
            "id": "additional-checks",
            "label": "Additional Degree Checks",
            "credits": "Residency and GPA",
            "description": "UW Seattle Mathematics residency, grade, outside-department, and continuation requirements.",
            "courses": [],
            "requirementRefs": [
                {"id": "math-policies", "scope": "requirement", "label": "Major policies", "credits": "Manual checks"},
                {"id": "outside-department", "scope": "requirement", "label": "Credits outside MATH", "credits": "At least 90 cr"},
            ],
        },
        {
            "id": "free-electives",
            "label": "Free Electives",
            "credits": "To reach 180 cr",
            "description": "Additional coursework needed to reach the baccalaureate credit total and the 90-credit outside-MATH requirement.",
            "courses": [],
            "requirementRefs": [
                {"id": "total", "scope": "requirement", "label": "Total degree credits", "credits": "180 cr"}
            ],
        },
    ],
    "requirements": [
        {
            "id": "math-admission",
            "title": "Mathematics Major Declaration",
            "displayCredits": "Before declaring",
            "targetCredits": 0,
            "type": "group",
            "note": "Courses must be completed when declaring. AP/IB and Washington community-college equivalencies may be used where UW awards the listed course credit.",
            "items": [
                {
                    "id": "admission-path",
                    "label": "Complete one declaration pathway",
                    "type": "path-choice",
                    "paths": [
                        {"label": "Early Entrance — MATH 200", "courses": ["MATH 208", "MATH 200"]},
                        {"label": "Early Entrance — MATH 300", "courses": ["MATH 208", "MATH 300"]},
                        {"label": "Standard Entry — standard calculus + MATH 200", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 208", "MATH 200"]},
                        {"label": "Standard Entry — standard calculus + MATH 300", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 208", "MATH 300"]},
                        {"label": "Standard Entry — accelerated honors calculus", "courses": ["MATH 134", "MATH 135", "MATH 136"]},
                    ],
                },
                {
                    "id": "admission-grade-check",
                    "label": "Declaration grade requirement confirmed",
                    "type": "check",
                    "note": "Early Entrance requires at least 3.8 in both courses. Standard Entry requires at least 2.0 in each required course and at least a 3.20 cumulative GPA across those courses.",
                },
            ],
        },
        {
            "id": "general-education",
            "title": "General Education Requirements",
            "displayCredits": "College of Arts & Sciences",
            "targetCredits": 0,
            "type": "group",
            "items": [
                {"id": "english-comp", "label": "English Composition", "type": "bucket", "targetCredits": 5, "area": "C"},
                {"id": "foreign-language", "label": "Foreign language through the third college quarter", "type": "bucket", "targetCredits": 15, "area": "FL", "note": "This is 0–15 credits depending on high-school preparation, placement, AP/IB, or college coursework."},
                {"id": "reasoning", "label": "Reasoning", "type": "bucket", "targetCredits": 5, "area": "RSN", "note": "Required mathematics courses normally satisfy this requirement."},
                {"id": "writing", "label": "Additional Writing", "type": "bucket", "targetCredits": 10, "area": "W"},
                {"id": "ah", "label": "Arts & Humanities", "type": "bucket", "targetCredits": 20, "area": "A&H"},
                {"id": "ssc", "label": "Social Sciences", "type": "bucket", "targetCredits": 20, "area": "SSc"},
                {"id": "nsc", "label": "Natural Sciences", "type": "bucket", "targetCredits": 20, "area": "NSc", "note": "Required MATH courses contribute heavily to this area."},
                {"id": "additional-aoi", "label": "Additional Areas of Inquiry", "type": "additional-bucket", "targetCredits": 15, "baseCredits": 60, "area": "A&H/SSc/NSc"},
                {"id": "div", "label": "Diversity", "type": "bucket", "targetCredits": 5, "area": "DIV", "note": "May overlap with another requirement."},
            ],
        },
        {
            "id": "math-core",
            "title": "Mathematics Core",
            "displayCredits": "30–44 cr",
            "targetCredits": 30,
            "type": "group",
            "items": [
                {
                    "id": "calc-linear-path",
                    "label": "Calculus, differential equations, and linear algebra",
                    "type": "path-choice",
                    "paths": [
                        {"label": "Standard route", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 207", "MATH 208"]},
                        {"label": "Accelerated honors route", "courses": ["MATH 134", "MATH 135", "MATH 136"]},
                    ],
                },
                {
                    "id": "proof-analysis-path",
                    "label": "Proof and analysis core",
                    "type": "path-choice",
                    "paths": [
                        {"label": "Standard route", "courses": ["MATH 200", "MATH 224", "MATH 300", "MATH 327", "MATH 424"]},
                        {"label": "Accelerated advanced honors route", "courses": ["MATH 334", "MATH 335", "MATH 336"]},
                    ],
                    "note": "MATH 335 may also be used as one upper-division elective. MATH 336 may also be used as MATH 427 or as one upper-division elective.",
                },
            ],
        },
        {
            "id": "advanced-electives",
            "title": "Advanced Core & Electives",
            "displayCredits": "44 cr · 11 courses",
            "targetCredits": 44,
            "type": "group",
            "note": "Complete 11 courses among advanced sequences and major electives. Courses used in the regular core are not counted again except for the department's explicit MATH 335/336 allowances.",
            "items": [
                {
                    "id": "advanced-course-count",
                    "label": "Eleven approved advanced-sequence and major-elective courses",
                    "type": "count",
                    "minCount": 11,
                    "courses": ADVANCED_COUNT_POOL,
                },
                {
                    "id": "sequence-structure-check",
                    "label": "Advanced sequence structure confirmed",
                    "type": "check",
                    "note": "Complete two three-quarter sequences or three two-quarter sequences, totaling 5–6 sequence courses. At least one sequence must be Modern Algebra, Concepts of Analysis, Topology & Geometry, or Complex Analysis. MATH 424 may act as the first Analysis course, which increases the separate elective count.",
                },
                {
                    "id": "special-topic-limit",
                    "label": "Special-topic and outside-department limits confirmed",
                    "type": "check",
                    "note": "No more than two MATH 380/480 courses. Up to two approved courses from one outside department may be used only after Mathematics advising applies them to the major.",
                },
            ],
        },
        {
            "id": "math-policies",
            "title": "Mathematics Major Policies",
            "displayCredits": "Residency and grades",
            "targetCredits": 0,
            "type": "group",
            "items": [
                {"id": "math-minimum-grades", "label": "Minimum 2.0 numerical grade in every course applied to the major", "type": "check"},
                {"id": "math-major-gpa", "label": "Minimum 2.00 cumulative GPA in all UW Mathematics courses", "type": "check"},
                {"id": "math-residency", "label": "At least 18 graded credits of 300-level or higher MATH taken at UW Seattle", "type": "check"},
                {"id": "math-quarterly-progress", "label": "At least one major course completed each enrolled quarter except Summer", "type": "check"},
            ],
        },
        {
            "id": "outside-department",
            "title": "Credits Outside the Mathematics Department",
            "displayCredits": "At least 90 cr",
            "targetCredits": 90,
            "type": "group",
            "note": "The College of Arts & Sciences requires at least 90 of the 180 degree credits outside the major department.",
            "items": [
                {"id": "outside-math-credits", "label": "At least 90 credits outside MATH", "type": "bucket", "targetCredits": 90, "area": "OUTSIDE-MAJOR"}
            ],
        },
        {
            "id": "total",
            "title": "Total Degree Credits",
            "displayCredits": "180 cr",
            "targetCredits": 180,
            "type": "total",
            "note": "Free electives and general-education courses bring the full degree plan to at least 180 credits.",
        },
    ],
    "samplePlan": {
        "name": "Suggested four-year B.S. Mathematics plan — standard route",
        "quarters": {
            "y1-autumn": ["MATH 124", "SLOT:5:English Composition", "SLOT:5:Arts & Humanities"],
            "y1-winter": ["MATH 125", "SLOT:5:Foreign Language", "SLOT:5:Social Sciences"],
            "y1-spring": ["MATH 126", "MATH 208", "SLOT:5:Foreign Language", "SLOT:1:Free Elective"],
            "y2-autumn": ["MATH 200", "MATH 300", "SLOT:5:Foreign Language", "SLOT:1:Free Elective"],
            "y2-winter": ["MATH 224", "MATH 327", "SLOT:5:Arts & Humanities", "SLOT:2:Free Elective"],
            "y2-spring": ["MATH 207", "MATH 424", "SLOT:5:Social Sciences", "SLOT:2:Free Elective"],
            "y3-autumn": ["MATH 402", "MATH 407", "SLOT:5:Additional Writing", "SLOT:2:Free Elective"],
            "y3-winter": ["MATH 403", "MATH 408", "SLOT:5:Arts & Humanities", "SLOT:2:Free Elective"],
            "y3-spring": ["MATH 404", "MATH 409", "SLOT:5:Social Sciences", "SLOT:2:Free Elective"],
            "y4-autumn": ["MATH 301", "MATH 318", "SLOT:5:Additional Writing", "SLOT:2:Free Elective"],
            "y4-winter": ["MATH 340", "MATH 394", "SLOT:5:Arts & Humanities / Diversity", "SLOT:2:Free Elective"],
            "y4-spring": ["MATH 420", "SLOT:5:Social Sciences", "SLOT:6:Free Elective"],
        },
    },
    "prerequisiteSubstitutions": {
        "MATH 124": ["MATH 134"],
        "MATH 125": ["MATH 135", "MATH 136"],
        "MATH 126": ["MATH 136"],
        "MATH 207": ["MATH 136"],
        "MATH 208": ["MATH 136"],
    },
}


# Verify the suggested plan represents exactly 180 credits.
plan_total = 0.0
for courses in major["samplePlan"]["quarters"].values():
    for entry in courses:
        if entry.startswith("SLOT:"):
            parts = entry.split(":", 2)
            plan_total += float(parts[1]) if len(parts) >= 3 else 0.0
            continue
        code = normalize_code(entry)
        value = course_overrides.get(code, {}).get("credits")
        if value in (None, ""):
            value = seattle_by_code.get(code, {}).get("credits", "")
        plan_total += numeric_credits(value)

if abs(plan_total - 180.0) > 0.001:
    raise RuntimeError(f"Suggested plan represents {plan_total:g} credits instead of 180.")

save_json(OUTPUT_FILE, major)

index = load_json(INDEX_FILE)
entry = {
    "id": "uw-seattle-math-bs",
    "name": "Mathematics (BS)",
    "degree": "BS",
    "status": "complete",
    "file": "mathematics-bs.json",
    "source": "https://math.washington.edu/bs-mathematics-major-requirements-0",
}
index["majors"] = [
    item for item in index.get("majors", [])
    if item.get("id") != entry["id"]
]
index["majors"].append(entry)
index["majors"].sort(key=lambda item: item.get("name", ""))
save_json(INDEX_FILE, index)

print(f"Created {OUTPUT_FILE.relative_to(ROOT)}")
print(f"Updated {INDEX_FILE.relative_to(ROOT)}")
print(f"Suggested plan verified at {plan_total:g} credits.")
print(f"Loaded {len(MATH_ELECTIVE_POOL)} eligible 300/400-level MATH elective records.")