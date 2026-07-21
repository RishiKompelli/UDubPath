from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAJOR_DIR = ROOT / "data" / "majors"
INDEX_FILE = MAJOR_DIR / "index.json"
ME_FILE = MAJOR_DIR / "mechanical-engineering.json"
APP_FILE = ROOT / "src" / "app.js"
BS_FILE = MAJOR_DIR / "biology-bs.json"
BA_FILE = MAJOR_DIR / "biology-ba.json"


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


# Official Fall 2026+ elective lists from UW Biology.
ECOLOGY_EVOLUTION = [
    "BIOL 305", "BIOL 354", "BIOL 356", "FHL 375", "FHL 403",
    "BIOL 406", "BIOL 410", "FHL 420", "BIOL 423", "BIOL 434",
    "BIOL 441", "BIOL 442", "BIOL 443", "BIOL 444", "BIOL 445",
    "FHL 440", "BIOL 446", "FHL 446", "BIOL 447", "BIOL 448",
    "BIOL 450", "BIOL 451", "BIOL 452", "BIOL 453", "BIOL 468",
    "BIOL 472", "BIOL 476", "BIOL 480", "BIOL 481", "BIOL 483",
    "BIOL 486", "BIOL 489", "BIOL 497", "FHL 528", "BIOL 539",
    "FHL 539",
]

MCD = [
    "BIOL 302", "BIOL 355", "BIOL 400", "BIOL 401", "BIOL 402",
    "BIOL 403", "BIOL 405", "BIOL 407", "BIOL 411", "BIOL 412",
    "BIOL 415", "BIOL 416", "BIOL 426", "BIOL 428", "BIOL 429",
    "BIOL 436", "BIOL 454", "BIOL 457", "BIOL 459", "BIOL 464",
    "BIOL 466", "BIOL 485", "BIOL 495", "BIOL 497", "BIOL 536",
    "FHL 536",
]

ORGANISMAL = [
    "BIOL 315", "BIOL 350", "BIOL 385", "BIOL 404", "BIOL 408",
    "BIOL 413", "BIOL 417", "BIOL 418", "BIOL 421", "BIOL 425",
    "BIOL 427", "BIOL 430", "FHL 430", "BIOL 439", "BIOL 455",
    "BIOL 461", "BIOL 462", "BIOL 463", "BIOL 465", "BIOL 467",
    "BIOL 469", "BIOL 471", "FHL 471", "BIOL 488", "BIOL 497",
]

OTHER_APPROVED = [
    "BIOC 405", "BIOC 406", "BIOC 426", "BIOC 440", "BIOC 441",
    "BIOC 442", "BIOL 280", "BIOL 359", "BIOL 396", "BIOL 399",
    "BIOL 419", "BIOL 460", "BIOL 470", "BIOL 492", "BIOL 499",
    "BIOL 331", "ESRM 331", "BIOL 424", "ESRM 478", "BIOL 438",
    "ESS 448", "BIOL 432", "FHL 432", "BIOL 435", "FHL 435",
    "FHL 468", "FHL 470", "FHL 472", "BIOL 311", "FISH 311",
    "BIOL 473", "FISH 473", "BIOL 474", "FISH 474", "BIOL 478",
    "FISH 478", "ENVIR 478", "BIOL 433", "MARBIO 433", "BH 311",
    "BH 402", "BH 404", "BH 421", "BH 444", "BH 488", "ENVIR 280",
    "ENV H 311", "ENV H 444", "OCEAN 330", "OCEAN 402", "OCEAN 403",
    "OCEAN 432", "ESRM 250", "ESRM 325", "ESRM 350", "ESRM 400",
    "ESRM 404", "ESRM 408", "ESRM 411", "ESRM 412", "ESRM 415",
    "ESRM 422", "ESRM 430", "ESRM 435", "ESRM 452", "ESRM 456",
    "ESRM 458", "ESRM 465", "ESRM 470", "FISH 312", "FISH 406",
    "FISH 444", "FISH 450", "FISH 464", "FISH 470", "GENOME 372",
    "GENOME 465", "GENOME 466", "GENOME 475", "IMMUN 441",
    "MICROM 301", "MICROM 302", "MICROM 402", "MICROM 410",
    "MICROM 411", "MICROM 412", "MICROM 431", "MICROM 435",
    "MICROM 442", "MICROM 445", "MICROM 460", "NURS 301", "NUTR 405",
    "NUTR 406", "P BIO 376", "PGH 301", "Q SCI 482", "GWSS 357",
    "PSYCH 357", "PSYCH 300", "PSYCH 416", "PSYCH 419",
]

LAB_COURSES = [
    "BIOL 356", "BIOL 410", "FHL 420", "BIOL 434", "BIOL 441",
    "BIOL 443", "BIOL 444", "BIOL 446", "FHL 446", "BIOL 447",
    "BIOL 448", "BIOL 450", "BIOL 451", "BIOL 452", "BIOL 468",
    "BIOL 472", "BIOL 480", "BIOL 481", "BIOL 302", "BIOL 400",
    "BIOL 402", "BIOL 412", "BIOL 428", "BIOL 459", "BIOL 495",
    "BIOL 413", "BIOL 421", "BIOL 427", "BIOL 439", "BIOL 463",
    "BIOC 426", "BIOL 424", "ESRM 478", "BIOL 438", "ESS 448",
    "BIOL 311", "FISH 311", "BIOL 474", "FISH 474", "BIOL 433",
    "MARBIO 433", "ESRM 404", "ESRM 452", "FISH 406", "FISH 444",
    "MICROM 302", "MICROM 402", "MICROM 411", "MICROM 431",
    "PSYCH 419",
]

FOUNDATIONS = ["BIOL 350", "BIOL 354", "BIOL 355", "BIOL 356"]
GENETICS = ["GENOME 361", "GENOME 371", "BIOL 340", "FISH 340"]
STATISTICS = ["Q SCI 381", "BIOST 310", "STAT 220", "STAT 311", "BIOL 359"]
CALCULUS = ["MATH 124", "MATH 134", "Q SCI 291"]
INTRO_BIOLOGY = ["BIOL 180", "BIOL 200", "BIOL 220"]

CHEMISTRY_PATHS = [
    {"label": "Allied-health chemistry", "courses": ["CHEM 120", "CHEM 220", "CHEM 221"]},
    {"label": "General + short organic", "courses": ["CHEM 142", "CHEM 152", "CHEM 223", "CHEM 224"]},
    {"label": "Accelerated general + short organic", "courses": ["CHEM 143", "CHEM 153", "CHEM 223", "CHEM 224"]},
    {"label": "Honors general + short organic", "courses": ["CHEM 145", "CHEM 155", "CHEM 223", "CHEM 224"]},
    {"label": "General + full organic", "courses": ["CHEM 142", "CHEM 152", "CHEM 162", "CHEM 237", "CHEM 238", "CHEM 239"]},
    {"label": "Accelerated general + full organic", "courses": ["CHEM 143", "CHEM 153", "CHEM 237", "CHEM 238", "CHEM 239"]},
    {"label": "Honors general + full organic", "courses": ["CHEM 145", "CHEM 155", "CHEM 165", "CHEM 237", "CHEM 238", "CHEM 239"]},
    {"label": "General + honors organic", "courses": ["CHEM 142", "CHEM 152", "CHEM 162", "CHEM 257", "CHEM 258", "CHEM 259"]},
    {"label": "Accelerated general + honors organic", "courses": ["CHEM 143", "CHEM 153", "CHEM 257", "CHEM 258", "CHEM 259"]},
    {"label": "Honors general + honors organic", "courses": ["CHEM 145", "CHEM 155", "CHEM 165", "CHEM 257", "CHEM 258", "CHEM 259"]},
]

PHYSICS_PATHS = [
    {"label": "Algebra-based physics", "courses": ["PHYS 114", "PHYS 115"]},
    {"label": "Calculus-based physics", "courses": ["PHYS 121", "PHYS 122"]},
    {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142"]},
]

ALL_CONCEPT = unique(MCD + ORGANISMAL + ECOLOGY_EVOLUTION)
ALL_APPROVED_ELECTIVES = unique(ALL_CONCEPT + OTHER_APPROVED)
ALL_UPPER_BIOL = unique([
    code for code in ALL_APPROVED_ELECTIVES + FOUNDATIONS + GENETICS
    if code.startswith("BIOL ") and int(re.search(r"(\d{3})", code).group(1)) >= 300
])
ALL_CHEMISTRY = unique(code for path in CHEMISTRY_PATHS for code in path["courses"])
ALL_PHYSICS = unique(code for path in PHYSICS_PATHS for code in path["courses"])


# Copy carefully curated honors/accelerated overrides from the existing ME file.
def build_course_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    if ME_FILE.exists():
        me = read_json(ME_FILE)
        common = {
            "MATH 124", "MATH 134", "CHEM 120", "CHEM 142", "CHEM 143",
            "CHEM 145", "CHEM 152", "CHEM 153", "CHEM 155", "CHEM 162",
            "CHEM 165", "CHEM 220", "CHEM 221", "CHEM 223", "CHEM 224",
            "CHEM 237", "CHEM 238", "CHEM 239", "CHEM 257", "CHEM 258",
            "CHEM 259", "PHYS 114", "PHYS 115", "PHYS 121", "PHYS 122",
            "PHYS 141", "PHYS 142",
        }
        for code in common:
            if code in me.get("courseOverrides", {}):
                overrides[code] = me["courseOverrides"][code]

    overrides.update({
        "BIOL 180": {
            "title": "Introductory Biology",
            "credits": "5",
            "areas": "NSc",
            "offered": "A,W,Sp,S",
            "prerequisiteGroups": [],
        },
        "BIOL 200": {
            "title": "Introductory Biology",
            "credits": "5",
            "areas": "NSc",
            "offered": "A,W,Sp,S",
            "prerequisiteGroups": [
                ["BIOL 180"],
                ["CHEM 143", "CHEM 145", "CHEM 223", "CHEM 237", "CHEM 152", "CHEM 153", "CHEM 155", "CHEM 220"],
            ],
            "otherPrerequisites": "Some chemistry choices may be taken concurrently; the planner conservatively places them earlier.",
        },
        "BIOL 220": {
            "title": "Introductory Biology",
            "credits": "5",
            "areas": "NSc",
            "offered": "A,W,Sp,S",
            "prerequisiteGroups": [["BIOL 200"]],
        },
        "PHYS 114": {
            "title": "General Physics",
            "credits": "4",
            "areas": "NSc, RSN",
            "prerequisiteGroups": [],
            "otherPrerequisites": "UW mathematics placement or the catalog-listed mathematics preparation may apply.",
        },
        "PHYS 115": {
            "title": "General Physics",
            "credits": "4",
            "areas": "NSc, RSN",
            "prerequisiteGroups": [["PHYS 114"]],
        },
        "GENOME 361": {
            "title": "Fundamentals of Genetics and Genomics",
            "credits": "3",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 180"], ["BIOL 200"]],
        },
        "GENOME 371": {
            "title": "Advanced Genetics and Genomics",
            "credits": "5",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 180"], ["BIOL 200"]],
        },
        "BIOL 340": {
            "title": "Genetics and Molecular Ecology",
            "credits": "5",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 200"]],
        },
        "FISH 340": {
            "title": "Genetics and Molecular Ecology",
            "credits": "5",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 200"]],
        },
        "BIOL 350": {
            "title": "Foundations in Physiology",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 220"]],
        },
        "BIOL 354": {
            "title": "Foundations in Evolution and Systematics",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 180"]],
        },
        "BIOL 355": {
            "title": "Foundations in Molecular Cell Biology",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 200"]],
        },
        "BIOL 356": {
            "title": "Foundations in Ecology",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 180"]],
        },
        "BIOL 302": {
            "title": "Laboratory Techniques in Cell and Molecular Biology",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 355", "BIOL 200"]],
        },
        "BIOL 305": {
            "title": "Science Communication: Video Storytelling in Biology",
            "credits": "3",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 180"]],
        },
        "BIOL 400": {
            "title": "Experiments in Molecular Biology",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 355"]],
        },
        "BIOL 404": {
            "title": "Animal Physiology: Cellular Aspects",
            "credits": "3",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 350", "BIOL 355"]],
        },
        "BIOL 425": {
            "title": "Ecological and Evolutionary Physiology of Animals",
            "credits": "5",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 220"]],
        },
        "BIOC 405": {
            "title": "Introduction to Biochemistry",
            "credits": "3",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 200"], ["CHEM 224", "CHEM 239", "CHEM 337"], ["MATH 124", "MATH 134"]],
        },
        "GENOME 372": {
            "title": "Genomics and Proteomics",
            "credits": "5",
            "areas": "NSc",
            "prerequisiteGroups": [["GENOME 361", "GENOME 371"]],
        },
        "MICROM 301": {
            "title": "General Microbiology",
            "credits": "3",
            "areas": "NSc",
            "prerequisiteGroups": [["CHEM 120", "CHEM 142", "CHEM 145"]],
        },
        "BIOL 280": {
            "title": "The History of Life",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [],
        },
        "BIOL 460": {
            "title": "Systems Biology I",
            "credits": "3",
            "prerequisiteGroups": [],
        },
        "BIOL 469": {
            "title": "Evolution and Medicine",
            "credits": "3",
            "areas": "NSc",
            "prerequisiteGroups": [["BIOL 180"]],
        },
        "BIOL 492": {
            "title": "Teaching Biology Inclusively to Diverse Audiences",
            "credits": "3",
            "prerequisiteGroups": [["BIOL 350", "BIOL 354", "BIOL 355", "BIOL 356"]],
        },
        "BIOL 419": {
            "title": "Approved Biology elective (verify current offering)",
            "credits": "4",
            "areas": "NSc",
            "prerequisiteGroups": [],
            "otherPrerequisites": "Listed on the Fall 2026 Biology elective page but not found in the current course-description catalog; verify with Biology advising.",
        },
    })
    return overrides


def general_education_requirement() -> dict[str, Any]:
    return {
        "id": "general-education",
        "title": "College of Arts & Sciences General Education",
        "displayCredits": "University and college requirements",
        "targetCredits": 0,
        "type": "group",
        "items": [
            {"id": "english-comp", "label": "English Composition", "type": "bucket", "targetCredits": 5, "area": "C"},
            {"id": "foreign-language", "label": "Foreign language through the third quarter", "type": "bucket", "targetCredits": 15, "area": "FL", "note": "May be fulfilled by prior high-school or college language study; use the manual override when applicable."},
            {"id": "reasoning", "label": "Reasoning", "type": "bucket", "targetCredits": 5, "area": "RSN"},
            {"id": "writing", "label": "Writing in Context", "type": "bucket", "targetCredits": 10, "area": "W"},
            {"id": "ah", "label": "Arts & Humanities", "type": "bucket", "targetCredits": 20, "area": "A&H"},
            {"id": "ssc", "label": "Social Sciences", "type": "bucket", "targetCredits": 20, "area": "SSc"},
            {"id": "nsc", "label": "Natural Sciences", "type": "bucket", "targetCredits": 20, "area": "NSc", "note": "Biology, chemistry, mathematics, statistics, and physics courses in the degree can satisfy much of this requirement."},
            {"id": "additional-aoi", "label": "Additional Areas of Inquiry", "type": "additional-bucket", "targetCredits": 15, "baseCredits": 60, "area": "A&H/SSc/NSc"},
            {"id": "div", "label": "Diversity", "type": "bucket", "targetCredits": 5, "area": "DIV", "note": "May overlap with another general-education category."},
        ],
    }


def exclusive_credit_requirement(req_id: str, title: str, credits: int, courses: list[str], priority: int) -> dict[str, Any]:
    return {
        "id": req_id,
        "title": title,
        "displayCredits": f"{credits} cr",
        "targetCredits": credits,
        "type": "group",
        "exclusiveSet": "biology-major-allocation",
        "exclusivePriority": priority,
        "note": "A course is allocated to only one Biology major category so it is not double-counted.",
        "items": [{
            "id": f"{req_id}-pool",
            "label": title,
            "type": "count-credit-level",
            "minCount": 0,
            "minCredits": credits,
            "minLevel": 0,
            "minLevelCount": 0,
            "courses": courses,
        }],
    }


def build_requirements(is_bs: bool) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = [
        {
            "id": "biology-admission",
            "title": "Biology Admission Checkpoint",
            "displayCredits": "Before applying",
            "targetCredits": 0,
            "type": "group",
            "note": "Admission is competitive. BIOL 180, 200, and 220 require at least a 2.0 in each course; supporting coursework completed at application must have at least a 2.5 cumulative GPA.",
            "items": [
                {"id": "admission-intro", "label": "Introductory Biology series", "type": "all", "courses": INTRO_BIOLOGY},
            ],
        },
        {
            "id": "admission-standing",
            "title": "UW Seattle enrollment and good academic standing",
            "displayCredits": "Confirm manually",
            "targetCredits": 1,
            "type": "manual",
            "note": "Enter 1 or mark fulfilled after confirming this admission condition.",
        },
        {
            "id": "admission-supporting-gpa",
            "title": "Minimum 2.5 GPA in completed supporting coursework",
            "displayCredits": "Confirm manually",
            "targetCredits": 1,
            "type": "manual",
            "note": "Enter 1 or mark fulfilled after confirming the GPA condition.",
        },
        general_education_requirement(),
        {
            "id": "intro-biology",
            "title": "Introductory Biology Series",
            "displayCredits": "15 cr",
            "targetCredits": 15,
            "type": "group",
            "items": [{"id": "intro-biology-all", "label": "BIOL 180, 200, and 220", "type": "all", "courses": INTRO_BIOLOGY}],
        },
        {
            "id": "chemistry",
            "title": "Chemistry",
            "displayCredits": "Choose one approved sequence",
            "targetCredits": 0,
            "type": "group",
            "items": [{"id": "chemistry-path", "label": "Approved chemistry sequence", "type": "path-choice", "paths": CHEMISTRY_PATHS}],
        },
        {
            "id": "mathematics",
            "title": "Mathematics",
            "displayCredits": "8–10 cr",
            "targetCredits": 8,
            "type": "group",
            "items": [
                {"id": "biology-statistics", "label": "Statistics or quantitative science", "type": "one", "courses": STATISTICS},
                {"id": "biology-calculus", "label": "Calculus", "type": "one", "courses": CALCULUS},
            ],
        },
    ]

    if is_bs:
        requirements.append({
            "id": "physics",
            "title": "Physics",
            "displayCredits": "8–10 cr",
            "targetCredits": 8,
            "type": "group",
            "items": [{"id": "physics-path", "label": "Approved physics sequence", "type": "path-choice", "paths": PHYSICS_PATHS}],
        })

    requirements.extend([
        {
            "id": "genetics",
            "title": "Genetics",
            "displayCredits": "3–5 cr",
            "targetCredits": 3,
            "type": "group",
            "items": [{"id": "genetics-choice", "label": "One approved genetics course", "type": "one", "courses": GENETICS}],
        },
        {
            "id": "biology-foundation",
            "title": "Biology Foundations",
            "displayCredits": "4 cr",
            "targetCredits": 4,
            "type": "group",
            "exclusiveSet": "biology-major-allocation",
            "exclusivePriority": 1,
            "note": "The selected foundation course is allocated here and is not counted again in another Biology major category.",
            "items": [{"id": "foundation-choice", "label": "One foundations course", "type": "one", "courses": FOUNDATIONS}],
        },
        exclusive_credit_requirement("mcd", "Molecular, Cellular & Developmental Biology", 6, MCD, 2),
        exclusive_credit_requirement("organismal", "Organismal Physiology", 6, ORGANISMAL, 3),
        exclusive_credit_requirement("ecology-evolution", "Ecology & Evolutionary Biology", 6, ECOLOGY_EVOLUTION, 4),
        exclusive_credit_requirement("biology-electives", "Approved Upper-Division Biology Electives", 18 if is_bs else 23, ALL_APPROVED_ELECTIVES, 5),
        {
            "id": "laboratories",
            "title": "Upper-Division Laboratory Requirement",
            "displayCredits": "2 courses",
            "targetCredits": 2,
            "type": "group",
            "note": "Laboratory courses may also count toward a core-concept or elective category.",
            "items": [{"id": "lab-count", "label": "At least two approved 300- or 400-level laboratory courses", "type": "count", "minCount": 2, "courses": LAB_COURSES}],
        },
        {
            "id": "biology-residency",
            "title": "Upper-Division BIOL Credits at UW Seattle",
            "displayCredits": "15 cr",
            "targetCredits": 15,
            "type": "pool",
            "minCredits": 15,
            "courses": ALL_UPPER_BIOL,
            "note": "The app counts fulfilled BIOL courses. Transfer-equivalent fulfillment should be reviewed manually because this requirement specifically says taken through UW Seattle.",
        },
        {
            "id": "major-gpa",
            "title": "Minimum 2.00 cumulative GPA in courses applied to the major",
            "displayCredits": "Confirm manually",
            "targetCredits": 1,
            "type": "manual",
            "note": "Enter 1 or mark fulfilled after confirming the GPA condition.",
        },
        {
            "id": "outside-major",
            "title": "Credits Outside the Biology Department",
            "displayCredits": "At least 90 cr",
            "targetCredits": 90,
            "type": "manual",
            "note": "College of Arts & Sciences requirement. Enter the number of completed credits outside BIOL; many supporting and general-education courses count.",
        },
        {
            "id": "total",
            "title": "Total Degree Credits",
            "displayCredits": "180 cr",
            "targetCredits": 180,
            "type": "total",
            "note": "General education, supporting science, Biology major courses, and free electives must total at least 180 credits.",
        },
    ])
    return requirements


def build_map_groups(is_bs: bool) -> list[dict[str, Any]]:
    general_refs = [
        {"id": "english-comp", "scope": "item", "label": "English Composition", "credits": "5 cr"},
        {"id": "foreign-language", "scope": "item", "label": "Foreign Language", "credits": "0–15 cr"},
        {"id": "reasoning", "scope": "item", "label": "Reasoning", "credits": "5 cr"},
        {"id": "writing", "scope": "item", "label": "Writing in Context", "credits": "10 cr"},
        {"id": "ah", "scope": "item", "label": "Arts & Humanities", "credits": "20 cr"},
        {"id": "ssc", "scope": "item", "label": "Social Sciences", "credits": "20 cr"},
        {"id": "nsc", "scope": "item", "label": "Natural Sciences", "credits": "20 cr"},
        {"id": "additional-aoi", "scope": "item", "label": "Additional Areas of Inquiry", "credits": "15 cr"},
        {"id": "div", "scope": "item", "label": "Diversity", "credits": "5 cr"},
    ]

    groups = [
        {
            "id": "admission",
            "label": "Biology Admission Checkpoint",
            "shortLabel": "Admission",
            "credits": "Before applying",
            "description": "Introductory Biology plus UW standing and supporting-course GPA checks.",
            "courses": INTRO_BIOLOGY,
            "requirementRefs": [
                {"id": "admission-standing", "scope": "requirement", "label": "UW Seattle standing", "credits": "Confirm"},
                {"id": "admission-supporting-gpa", "scope": "requirement", "label": "Supporting-course GPA", "credits": "2.5 minimum"},
            ],
        },
        {
            "id": "general-education",
            "label": "General Education Requirements",
            "shortLabel": "General Education",
            "credits": "College of Arts & Sciences",
            "description": "Language skills, reasoning and writing, Areas of Inquiry, and Diversity.",
            "courses": [],
            "requirementRefs": general_refs,
        },
        {
            "id": "intro-biology",
            "label": "Introductory Biology",
            "credits": "15 cr",
            "description": "BIOL 180, 200, and 220.",
            "courses": INTRO_BIOLOGY,
        },
        {
            "id": "chemistry",
            "label": "Chemistry",
            "credits": "Choose one sequence",
            "description": "All approved allied-health, general, accelerated, honors, and organic chemistry routes.",
            "courses": ALL_CHEMISTRY,
        },
        {
            "id": "math-science",
            "label": "Mathematics" + (" & Physics" if is_bs else ""),
            "shortLabel": "Math" + (" & Physics" if is_bs else ""),
            "credits": "Required supporting science",
            "description": "One statistics/quantitative course, one calculus course" + (", and one physics sequence." if is_bs else "."),
            "courses": unique(STATISTICS + CALCULUS + (ALL_PHYSICS if is_bs else [])),
        },
        {
            "id": "genetics-foundations",
            "label": "Genetics & Biology Foundations",
            "shortLabel": "Genetics & Foundations",
            "credits": "7–9 cr",
            "description": "One genetics course and one foundations course.",
            "courses": unique(GENETICS + FOUNDATIONS),
        },
        {
            "id": "concepts",
            "label": "Biology Core Concepts",
            "credits": "18 cr",
            "description": "Six credits each in molecular/cellular/developmental, organismal physiology, and ecology/evolution.",
            "courses": ALL_CONCEPT,
        },
        {
            "id": "biology-electives-map",
            "label": "Approved Biology Electives",
            "shortLabel": "Biology Electives",
            "credits": "18 cr BS · 23 cr BA",
            "description": "Additional approved Biology or related-department courses. Concept-list courses can also fill the elective total when not used elsewhere.",
            "courses": OTHER_APPROVED,
        },
        {
            "id": "additional-major",
            "label": "Additional Major Requirements",
            "shortLabel": "Additional Requirements",
            "credits": "Labs, residency, GPA",
            "description": "Two labs, 15 UW Seattle upper-division BIOL credits, and minimum major GPA.",
            "courses": LAB_COURSES,
            "requirementRefs": [
                {"id": "laboratories", "scope": "requirement", "label": "Upper-division laboratories", "credits": "2 courses"},
                {"id": "biology-residency", "scope": "requirement", "label": "UW Seattle BIOL residency", "credits": "15 cr"},
                {"id": "major-gpa", "scope": "requirement", "label": "Major GPA", "credits": "2.00 minimum"},
            ],
        },
        {
            "id": "free-electives",
            "label": "Free Electives & Degree Total",
            "shortLabel": "Degree Total",
            "credits": "To reach 180 cr",
            "description": "Courses needed to reach the university total and the 90-credit outside-major minimum.",
            "courses": [],
            "requirementRefs": [
                {"id": "outside-major", "scope": "requirement", "label": "Credits outside BIOL", "credits": "90 cr"},
                {"id": "total", "scope": "requirement", "label": "Total degree credits", "credits": "180 cr"},
            ],
        },
    ]
    return groups


BS_PLAN = {
    "name": "Suggested four-year Biology BS plan (editable; not an official UW schedule)",
    "quarters": {
        "y1-autumn": ["CHEM 142", "MATH 124", "SLOT:5:English Composition"],
        "y1-winter": ["CHEM 152", "BIOL 180", "SLOT:5:Arts & Humanities"],
        "y1-spring": ["CHEM 223", "STAT 220", "SLOT:5:Social Sciences"],
        "y2-autumn": ["CHEM 224", "BIOL 200", "SLOT:5:Foreign Language"],
        "y2-winter": ["BIOL 220", "PHYS 114", "SLOT:5:Arts & Humanities"],
        "y2-spring": ["PHYS 115", "GENOME 361", "SLOT:5:Social Sciences", "SLOT:5:Foreign Language"],
        "y3-autumn": ["BIOL 355", "BIOL 354", "BIOL 302", "SLOT:5:Writing in Context"],
        "y3-winter": ["BIOL 400", "BIOL 425", "BIOC 405", "SLOT:5:Arts & Humanities"],
        "y3-spring": ["BIOL 404", "BIOL 305", "GENOME 372", "SLOT:5:Social Sciences"],
        "y4-autumn": ["MICROM 301", "BIOL 469", "BIOL 280", "SLOT:1:Free Elective", "SLOT:5:Writing in Context"],
        "y4-winter": ["SLOT:5:Arts & Humanities", "SLOT:5:Social Sciences", "SLOT:5:Foreign Language"],
        "y4-spring": ["SLOT:5:Additional Areas of Inquiry", "SLOT:5:Diversity"],
    },
}

BA_PLAN = {
    "name": "Suggested four-year Biology BA plan (editable; not an official UW schedule)",
    "quarters": {
        "y1-autumn": ["CHEM 142", "MATH 124", "SLOT:5:English Composition"],
        "y1-winter": ["CHEM 152", "BIOL 180", "SLOT:5:Arts & Humanities"],
        "y1-spring": ["CHEM 223", "STAT 220", "SLOT:5:Social Sciences"],
        "y2-autumn": ["CHEM 224", "BIOL 200", "SLOT:5:Foreign Language"],
        "y2-winter": ["BIOL 220", "SLOT:5:Arts & Humanities", "SLOT:5:Social Sciences"],
        "y2-spring": ["GENOME 361", "SLOT:5:Social Sciences", "SLOT:5:Foreign Language", "SLOT:5:Arts & Humanities"],
        "y3-autumn": ["BIOL 355", "BIOL 354", "BIOL 302", "SLOT:5:Writing in Context"],
        "y3-winter": ["BIOL 400", "BIOL 425", "BIOC 405", "SLOT:5:Arts & Humanities"],
        "y3-spring": ["BIOL 404", "BIOL 305", "GENOME 372", "SLOT:5:Social Sciences"],
        "y4-autumn": ["MICROM 301", "BIOL 469", "BIOL 460", "SLOT:2:Free Elective", "SLOT:5:Writing in Context"],
        "y4-winter": ["BIOL 492", "BIOL 280", "SLOT:5:Foreign Language"],
        "y4-spring": ["SLOT:5:Additional Areas of Inquiry", "SLOT:5:Diversity", "SLOT:1:Free Elective"],
    },
}

SAMPLE_CREDITS = {
    "CHEM 142": 5, "MATH 124": 5, "CHEM 152": 5, "BIOL 180": 5,
    "CHEM 223": 4, "STAT 220": 5, "CHEM 224": 4, "BIOL 200": 5,
    "BIOL 220": 5, "PHYS 114": 4, "PHYS 115": 4, "GENOME 361": 3,
    "BIOL 355": 4, "BIOL 354": 4, "BIOL 302": 4, "BIOL 400": 4,
    "BIOL 425": 5, "BIOC 405": 3, "BIOL 404": 3, "BIOL 305": 3,
    "GENOME 372": 5, "MICROM 301": 3, "BIOL 469": 3, "BIOL 280": 4,
    "BIOL 492": 3, "BIOL 460": 3,
}


def plan_total(plan: dict[str, Any]) -> int:
    total = 0
    for entries in plan["quarters"].values():
        for entry in entries:
            if entry.startswith("SLOT:"):
                parts = entry.split(":", 2)
                total += int(float(parts[1]))
            else:
                total += SAMPLE_CREDITS[entry]
    return total


def sources() -> list[dict[str, str]]:
    return [
        {"label": "UW Biology degree requirements — Fall 2026 onward", "url": "https://biology.washington.edu/degree-requirements-fall-2026-onwards"},
        {"label": "UW Biology Fall 2026 elective lists", "url": "https://biology.washington.edu/elective-lists"},
        {"label": "UW Biology admissions and major requirements", "url": "https://biology.washington.edu/admissions-major-requirements"},
        {"label": "UW Biology course-description catalog", "url": "https://www.washington.edu/students/crscat/biology.html"},
        {"label": "UW Chemistry course-description catalog", "url": "https://www.washington.edu/students/crscat/chem.html"},
        {"label": "UW College of Arts & Sciences graduation requirements", "url": "https://www.washington.edu/students/gencat/program/S/college_arts_sciences.html"},
    ]


def substitutions() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {
        "MATH 124": ["MATH 134"],
        "CHEM 142": ["CHEM 143", "CHEM 145"],
        "CHEM 152": ["CHEM 153", "CHEM 155"],
        "CHEM 162": ["CHEM 165"],
        "PHYS 114": ["PHYS 121", "PHYS 141"],
        "PHYS 115": ["PHYS 122", "PHYS 142"],
        "PHYS 121": ["PHYS 141"],
        "PHYS 122": ["PHYS 142"],
        "GENOME 361": ["GENOME 371", "BIOL 340", "FISH 340"],
        "BIOL 340": ["FISH 340"],
    }
    if ME_FILE.exists():
        me = read_json(ME_FILE)
        for code, values in me.get("prerequisiteSubstitutions", {}).items():
            result[code] = unique(result.get(code, []) + values)
    return result


def build_major(is_bs: bool) -> dict[str, Any]:
    degree_short = "BS" if is_bs else "BA"
    return {
        "id": f"uw-seattle-biology-{degree_short.lower()}",
        "university": "University of Washington Seattle",
        "name": f"Biology ({degree_short})",
        "degree": f"Bachelor of {'Science' if is_bs else 'Arts'} in Biology",
        "catalogYear": "Fall 2026 onward",
        "totalCredits": 180,
        "sources": sources(),
        "tracks": [{
            "id": "standard",
            "name": f"Biology {degree_short}",
            "description": "Fall 2026 onward Biology curriculum.",
        }],
        "courseOverrides": build_course_overrides(),
        "mapGroups": build_map_groups(is_bs),
        "requirements": build_requirements(is_bs),
        "samplePlan": BS_PLAN if is_bs else BA_PLAN,
        "prerequisiteSubstitutions": substitutions(),
    }


EXCLUSIVE_SUPPORT = r'''
function courseLevel(code) {
  const match = normalizeCode(code).match(/\s(\d{3})[A-Z]?$/);
  return match ? Number(match[1]) : 0;
}

function evaluateExclusiveItem(item, usedCodes) {
  const overridden = Boolean(app.progress.requirementOverrides[item.id]);
  const courses = (item.courses || []).map(normalizeCode);
  const available = courses.filter((code) => isFulfilled(code) && !usedCodes.has(code));
  let completed = [];
  let current = 0;
  let target = 1;
  let label = "";
  let satisfied = overridden;

  if (item.type === "all") {
    completed = available;
    current = completed.length;
    target = courses.length;
    satisfied ||= current >= target;
    label = `${current}/${target} courses`;
  } else if (item.type === "one") {
    completed = available.slice(0, 1);
    current = completed.length;
    target = 1;
    satisfied ||= current >= 1;
    label = satisfied ? "Satisfied" : "Choose one";
  } else if (item.type === "count") {
    const needed = Number(item.minCount || 1);
    completed = available.slice(0, needed);
    current = completed.length;
    target = needed;
    satisfied ||= current >= target;
    label = `${current}/${target} courses`;
  } else if (item.type === "count-credit-level") {
    const neededCount = Number(item.minCount || 0);
    const neededCredits = Number(item.minCredits || 0);
    const minimumLevel = Number(item.minLevel || 0);
    const neededAtLevel = Number(item.minLevelCount || 0);
    const sorted = [...available].sort((a, b) => courseLevel(b) - courseLevel(a));
    for (const code of sorted) {
      const credits = completed.reduce((sum, entry) => sum + numericCredits(getCourse(entry).credits), 0);
      const levelCount = completed.filter((entry) => courseLevel(entry) >= minimumLevel).length;
      if (completed.length >= neededCount && credits >= neededCredits && levelCount >= neededAtLevel) break;
      completed.push(code);
    }
    const credits = completed.reduce((sum, code) => sum + numericCredits(getCourse(code).credits), 0);
    const levelCount = completed.filter((code) => courseLevel(code) >= minimumLevel).length;
    current = Math.min(
      neededCount ? completed.length / neededCount : 1,
      neededCredits ? credits / neededCredits : 1,
      neededAtLevel ? levelCount / neededAtLevel : 1
    );
    target = 1;
    satisfied ||= completed.length >= neededCount && credits >= neededCredits && levelCount >= neededAtLevel;
    label = `${formatNumber(credits)}/${neededCredits} credits`;
  } else {
    return evaluateItem(item);
  }

  if (!overridden) completed.forEach((code) => usedCodes.add(code));
  const credits = completed.reduce((sum, code) => sum + numericCredits(getCourse(code).credits), 0);
  return { satisfied, current, target, label, completed, credits, overridden };
}

function evaluateExclusiveSet(setId) {
  const usedCodes = new Set();
  const results = new Map();
  const requirements = getActiveRequirements()
    .filter((requirement) => requirement.exclusiveSet === setId)
    .sort((a, b) => Number(a.exclusivePriority || 0) - Number(b.exclusivePriority || 0));

  for (const requirement of requirements) {
    const overridden = Boolean(app.progress.requirementOverrides[requirement.id]);
    const allocationSet = overridden ? new Set() : usedCodes;
    const items = (requirement.items || []).map((item) => evaluateExclusiveItem(item, allocationSet));
    const current = items.filter((item) => item.satisfied).length;
    results.set(requirement.id, {
      satisfied: overridden || current === items.length,
      current,
      target: items.length,
      items,
      label: `${current}/${items.length} parts`
    });
  }
  return results;
}
'''


def ensure_app_support() -> None:
    if not APP_FILE.exists():
        return
    text = APP_FILE.read_text(encoding="utf-8")
    original = text

    # College of Arts & Sciences uses an additional-AoI bucket spanning all three AoI areas.
    if 'area === "A&H/SSc/NSc"' not in text:
        marker = '  if (area === "A&H/SSc") return areaMatches(course, "A&H") || areaMatches(course, "SSc");\n'
        replacement = marker + '  if (area === "A&H/SSc/NSc") return areaMatches(course, "A&H") || areaMatches(course, "SSc") || areaMatches(course, "NSc");\n'
        if marker not in text:
            raise RuntimeError("Could not locate areaMatches() in src/app.js.")
        text = text.replace(marker, replacement, 1)

    if "function evaluateExclusiveSet(" not in text:
        marker = "function evaluateRequirement(requirement) {"
        if marker not in text:
            raise RuntimeError("Could not locate evaluateRequirement() in src/app.js.")
        text = text.replace(marker, EXCLUSIVE_SUPPORT + "\n" + marker, 1)

        old = "function evaluateRequirement(requirement) {\n  const overridden = Boolean(app.progress.requirementOverrides[requirement.id]);"
        new = "function evaluateRequirement(requirement) {\n  if (requirement.exclusiveSet) {\n    return evaluateExclusiveSet(requirement.exclusiveSet).get(requirement.id);\n  }\n  const overridden = Boolean(app.progress.requirementOverrides[requirement.id]);"
        if old not in text:
            raise RuntimeError("Could not add exclusive-requirement dispatch to src/app.js.")
        text = text.replace(old, new, 1)

    if text != original:
        backup = APP_FILE.with_suffix(".js.before-biology")
        if not backup.exists():
            backup.write_text(original, encoding="utf-8")
        APP_FILE.write_text(text, encoding="utf-8")


def update_index() -> None:
    index = read_json(INDEX_FILE)
    entries = [
        {
            "id": "uw-seattle-biology-bs",
            "name": "Biology (BS)",
            "degree": "BS",
            "status": "complete",
            "file": "biology-bs.json",
            "source": "https://biology.washington.edu/degree-requirements-fall-2026-onwards",
        },
        {
            "id": "uw-seattle-biology-ba",
            "name": "Biology (BA)",
            "degree": "BA",
            "status": "complete",
            "file": "biology-ba.json",
            "source": "https://biology.washington.edu/degree-requirements-fall-2026-onwards",
        },
    ]
    ids = {entry["id"] for entry in entries}
    index["majors"] = [item for item in index.get("majors", []) if item.get("id") not in ids]
    index["majors"].extend(entries)
    write_json(INDEX_FILE, index)


def main() -> None:
    if not INDEX_FILE.exists() or not APP_FILE.exists():
        raise SystemExit("Run this script from the degree-mapper project by placing it in the scripts folder.")

    assert plan_total(BS_PLAN) == 180, f"BS sample plan totals {plan_total(BS_PLAN)}, not 180"
    assert plan_total(BA_PLAN) == 180, f"BA sample plan totals {plan_total(BA_PLAN)}, not 180"

    ensure_app_support()
    write_json(BS_FILE, build_major(True))
    write_json(BA_FILE, build_major(False))
    update_index()

    print(f"Created {BS_FILE.relative_to(ROOT)}")
    print(f"Created {BA_FILE.relative_to(ROOT)}")
    print(f"Updated {INDEX_FILE.relative_to(ROOT)}")
    print("Verified both suggested four-year plans represent 180 credits.")
    print("Biology Fall 2026 elective pools and no-double-counting allocation are enabled.")


if __name__ == "__main__":
    main()