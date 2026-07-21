from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAJOR_DIR = ROOT / "data" / "majors"
INDEX_FILE = MAJOR_DIR / "index.json"

OUTPUT_FILE = (
    MAJOR_DIR
    / "law-societies-justice.json"
)


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


ADMISSION_CORE = [
    "LSJ 320",
    "LSJ 321",
    "LSJ 322",
    "LSJ 326",
    "LSJ 327",
    "LSJ 329",
    "LSJ 346",
    "LSJ 360",
    "LSJ 361",
    "LSJ 363",
    "LSJ 366",
    "LSJ 367",
    "LSJ 375",
    "LSJ 376",
]


CORE_300 = [
    "LSJ 300",
    "LSJ 320",
    "LSJ 321",
    "LSJ 322",
    "LSJ 326",
    "LSJ 327",
    "LSJ 329",
    "LSJ 345",
    "LSJ 346",
    "LSJ 360",
    "LSJ 361",
    "LSJ 363",
    "LSJ 366",
    "LSJ 367",
    "LSJ 375",
]


CAPSTONES = [
    "LSJ 410",
    "LSJ 412",
    "LSJ 413",
    "LSJ 421",
    "LSJ 422",
    "LSJ 425",
    "LSJ 427",
    "LSJ 429",
    "LSJ 460",
    "LSJ 476",
    "LSJ 490",
    "LSJ 491",
]


LSJ_300 = [
    "LSJ 300",
    "LSJ 320",
    "LSJ 321",
    "LSJ 322",
    "LSJ 326",
    "LSJ 327",
    "LSJ 329",
    "LSJ 331",
    "LSJ 332",
    "LSJ 345",
    "LSJ 346",
    "LSJ 360",
    "LSJ 361",
    "LSJ 363",
    "LSJ 366",
    "LSJ 367",
    "LSJ 369",
    "LSJ 370",
    "LSJ 375",
    "LSJ 376",
    "LSJ 377",
    "LSJ 380",
    "LSJ 381",
]


UPPER_ELECTIVES = [
    "LSJ 300",
    "AIS 306",
    "AIS 308",
    "GWSS 310",
    "PHIL 314",
    "POL S 313",
    "LSJ 320",
    "POL S 320",
    "LSJ 321",
    "LSJ 322",
    "LSJ 326",
    "LSJ 327",
    "LSJ 329",
    "AIS 330",
    "LSJ 331",
    "LSJ 332",
    "AIS 335",
    "LSJ 345",
    "LSJ 346",
    "LSJ 347",
    "LSJ 360",
    "LSJ 361",
    "LSJ 363",
    "POL S 364",
    "LSJ 366",
    "LSJ 367",
    "LSJ 369",
    "LSJ 370",
    "SOC 371",
    "SOC 472",
    "POL S 373",
    "SOC 374",
    "LSJ 375",
    "LSJ 376",
    "LSJ 377",
    "AIS 380",
    "LSJ 380",
    "LSJ 381",
    "AIS 385",
    "LSJ 401",
    "LSJ 410",
    "LSJ 412",
    "LSJ 413",
    "PHIL 414",
    "LSJ 415",
    "LSJ 416",
    "LSJ 421",
    "LSJ 422",
    "JSIS B 424",
    "JSIS B 441",
    "LSJ 425",
    "LSJ 426",
    "LSJ 427",
    "LSJ 428",
    "LSJ 429",
    "LSJ 430",
    "LSJ 431",
    "LSJ 433",
    "LSJ 434",
    "LSJ 437",
    "AFRAM 437",
    "LSJ 438",
    "COM 440",
    "LSJ 460",
    "POL S 462",
    "GEOG 472",
    "LSJ 476",
    "GEOG 479",
    "LSJ 480",
    "LSJ 490",
    "LSJ 491",
]


DISPLAYED_CORE = unique(
    ["LSJ 200"]
    + CORE_300
    + CAPSTONES
)

DISPLAYED_300 = [
    code
    for code in LSJ_300
    if code not in DISPLAYED_CORE
]

DISPLAYED_ELECTIVES = [
    code
    for code in UPPER_ELECTIVES
    if code not in DISPLAYED_CORE
    and code not in DISPLAYED_300
]


course_overrides = {
    "LSJ 416": {
        "title": "Juvenile Parole Practicum",
        "credits": "1-5",
        "areas": "SSc",
        "prerequisiteGroups": [
            ["LSJ 415"]
        ],
    },
    "LSJ 426": {
        "title": (
            "Reconciliation: The Politics of "
            "Forgiveness in a Global Age"
        ),
        "credits": "5",
        "areas": "SSc, DIV",
        "prerequisiteGroups": [
            [
                "LSJ 320",
                "LSJ 321",
                "LSJ 322",
                "PHIL 338",
            ]
        ],
    },
    "LSJ 430": {
        "title": "Topics in Disability Studies",
        "credits": "1-5",
        "areas": "SSc",
        "prerequisiteGroups": [
            [
                "LSJ 230",
                "LSJ 332",
                "LSJ 433",
                "LSJ 434",
            ]
        ],
    },
    "LSJ 489": {
        "title": (
            "Honors in Law, Societies, "
            "and Justice II"
        ),
        "credits": "5",
        "areas": "SSc",
        "prerequisiteGroups": [
            ["LSJ 488"]
        ],
    },
    "LSJ 490": {
        "title": (
            "Special Topics in Comparative "
            "Legal Institutions"
        ),
        "credits": "3-5",
        "areas": "SSc",
        "prerequisiteGroups": [],
    },
    "LSJ 491": {
        "title": "Special Topics in Rights",
        "credits": "3-5",
        "areas": "SSc",
        "prerequisiteGroups": [],
    },
}


major = {
    "id": "uw-seattle-lsj",
    "university": (
        "University of Washington Seattle"
    ),
    "name": "Law, Societies & Justice",
    "degree": (
        "Bachelor of Arts in "
        "Law, Societies, and Justice"
    ),
    "catalogYear": (
        "Gold Curriculum — "
        "Autumn 2024 onward"
    ),
    "totalCredits": 180,
    "sources": [
        {
            "label": (
                "LSJ Gold Curriculum "
                "requirements"
            ),
            "url": (
                "https://lsj.washington.edu/"
                "lsj-gold-curriculum-requirements"
            ),
        },
        {
            "label": "Apply to the LSJ major",
            "url": (
                "https://lsj.washington.edu/"
                "apply-lsj-major"
            ),
        },
        {
            "label": "UW LSJ course catalog",
            "url": (
                "https://www.washington.edu/"
                "students/crscat/lsj.html"
            ),
        },
        {
            "label": (
                "UW General Catalog — LSJ"
            ),
            "url": (
                "https://www.washington.edu/"
                "students/gencat/program/S/"
                "Law%2CSocieties%2CandJustice"
                "-1057.html"
            ),
        },
    ],
    "tracks": [
        {
            "id": "gold",
            "name": (
                "Gold Curriculum "
                "(Autumn 2024 onward)"
            ),
            "description": (
                "Current LSJ curriculum "
                "requiring 56–60 major credits."
            ),
        }
    ],
    "courseOverrides": course_overrides,
    "mapGroups": [
        {
            "id": "admission",
            "label": (
                "LSJ Admission Checkpoint"
            ),
            "shortLabel": "Admission",
            "credits": "Before applying",
            "description": (
                "Current UW admission "
                "prerequisites and manual "
                "GPA/enrollment checks."
            ),
            "courses": [],
            "requirementRefs": [
                {
                    "id": "lsj-admission",
                    "scope": "requirement",
                    "label": (
                        "LSJ application "
                        "prerequisites"
                    ),
                    "credits": (
                        "Before applying"
                    ),
                }
            ],
        },
        {
            "id": "general-education",
            "label": (
                "General Education Requirements"
            ),
            "shortLabel": (
                "General Education"
            ),
            "credits": (
                "College of Arts & Sciences"
            ),
            "description": (
                "Composition, writing, reasoning, "
                "language, Areas of Inquiry, "
                "and Diversity."
            ),
            "courses": [],
            "requirementRefs": [
                {
                    "id": "english-comp",
                    "scope": "item",
                    "label": (
                        "English Composition"
                    ),
                    "credits": "5 cr",
                },
                {
                    "id": "writing",
                    "scope": "item",
                    "label": (
                        "Additional Writing"
                    ),
                    "credits": "10 cr",
                },
                {
                    "id": "rsn",
                    "scope": "item",
                    "label": "Reasoning",
                    "credits": "5 cr",
                },
                {
                    "id": "foreign-language",
                    "scope": "item",
                    "label": "Foreign Language",
                    "credits": "0–15 cr",
                },
                {
                    "id": "ah",
                    "scope": "item",
                    "label": (
                        "Arts & Humanities"
                    ),
                    "credits": "20 cr",
                },
                {
                    "id": "ssc",
                    "scope": "item",
                    "label": (
                        "Social Sciences"
                    ),
                    "credits": "20 cr",
                },
                {
                    "id": "nsc",
                    "scope": "item",
                    "label": (
                        "Natural Sciences"
                    ),
                    "credits": "20 cr",
                },
                {
                    "id": "additional-aoi",
                    "scope": "item",
                    "label": (
                        "Additional Areas "
                        "of Inquiry"
                    ),
                    "credits": "15 cr",
                },
                {
                    "id": "div",
                    "scope": "item",
                    "label": "Diversity",
                    "credits": "5 cr",
                },
            ],
        },
        {
            "id": "core",
            "label": "Core Courses",
            "credits": "20 cr",
            "description": (
                "LSJ 200, two approved "
                "300-level Human Rights or Law "
                "courses, and one LSJ "
                "capstone seminar."
            ),
            "courses": DISPLAYED_CORE,
        },
        {
            "id": "three-hundred",
            "label": (
                "300-Level LSJ Courses"
            ),
            "shortLabel": "300-Level LSJ",
            "credits": "Minimum 20 cr",
            "description": (
                "Four LSJ courses at the "
                "300 level, allocated separately "
                "from the core."
            ),
            "courses": DISPLAYED_300,
        },
        {
            "id": "upper-electives",
            "label": (
                "Upper-Division Electives"
            ),
            "shortLabel": (
                "Upper Electives"
            ),
            "credits": "16–20 cr",
            "description": (
                "At least four approved courses "
                "totaling 16 credits, including "
                "one 400-level course."
            ),
            "courses": DISPLAYED_ELECTIVES,
        },
        {
            "id": "free-electives",
            "label": "Free Electives",
            "credits": "To reach 180 cr",
            "description": (
                "Other approved coursework "
                "used to reach the university "
                "graduation total."
            ),
            "courses": [],
            "requirementRefs": [
                {
                    "id": "total",
                    "scope": "requirement",
                    "label": (
                        "Total degree credits"
                    ),
                    "credits": "180 cr",
                }
            ],
        },
    ],
    "requirements": [
        {
            "id": "lsj-admission",
            "title": (
                "LSJ Admission Checkpoint"
            ),
            "displayCredits": (
                "Before applying"
            ),
            "targetCredits": 0,
            "type": "group",
            "note": (
                "The department is "
                "capacity-constrained. All "
                "course prerequisites must be "
                "completed and graded before "
                "applying."
            ),
            "items": [
                {
                    "id": (
                        "admission-enrollment"
                    ),
                    "label": (
                        "Currently enrolled as a "
                        "UW Seattle undergraduate"
                    ),
                    "type": "check",
                },
                {
                    "id": "admission-gpa",
                    "label": (
                        "Cumulative UW GPA "
                        "of at least 2.5"
                    ),
                    "type": "check",
                },
                {
                    "id": (
                        "admission-composition"
                    ),
                    "label": (
                        "One approved English "
                        "Composition course"
                    ),
                    "type": "bucket",
                    "targetCredits": 5,
                    "area": "C",
                },
                {
                    "id": "admission-lsj200",
                    "label": "LSJ 200",
                    "type": "all",
                    "courses": ["LSJ 200"],
                },
                {
                    "id": (
                        "admission-core300"
                    ),
                    "label": (
                        "One approved LSJ "
                        "300-level admission course"
                    ),
                    "type": "one",
                    "courses": ADMISSION_CORE,
                },
            ],
        },
        {
            "id": "general-education",
            "title": (
                "General Education Requirements"
            ),
            "displayCredits": (
                "College of Arts & Sciences"
            ),
            "targetCredits": 0,
            "type": "group",
            "items": [
                {
                    "id": "english-comp",
                    "label": (
                        "English Composition"
                    ),
                    "type": "bucket",
                    "targetCredits": 5,
                    "area": "C",
                    "note": (
                        "LSJ requires a grade "
                        "of 2.0 or higher."
                    ),
                },
                {
                    "id": "writing",
                    "label": (
                        "Additional Writing"
                    ),
                    "type": "bucket",
                    "targetCredits": 10,
                    "area": "W",
                },
                {
                    "id": "rsn",
                    "label": "Reasoning",
                    "type": "bucket",
                    "targetCredits": 5,
                    "area": "RSN",
                },
                {
                    "id": "foreign-language",
                    "label": (
                        "College of Arts & Sciences "
                        "foreign-language requirement"
                    ),
                    "type": "bucket",
                    "targetCredits": 15,
                    "area": "FL",
                    "note": (
                        "Enter manual credits or "
                        "mark fulfilled if prior "
                        "language study satisfies "
                        "the requirement."
                    ),
                },
                {
                    "id": "ah",
                    "label": (
                        "Arts & Humanities"
                    ),
                    "type": "bucket",
                    "targetCredits": 20,
                    "area": "A&H",
                },
                {
                    "id": "ssc",
                    "label": (
                        "Social Sciences"
                    ),
                    "type": "bucket",
                    "targetCredits": 20,
                    "area": "SSc",
                },
                {
                    "id": "nsc",
                    "label": (
                        "Natural Sciences"
                    ),
                    "type": "bucket",
                    "targetCredits": 20,
                    "area": "NSc",
                },
                {
                    "id": "additional-aoi",
                    "label": (
                        "Additional Areas "
                        "of Inquiry"
                    ),
                    "type": (
                        "additional-bucket"
                    ),
                    "targetCredits": 15,
                    "baseCredits": 60,
                    "area": "A&H/SSc/NSc",
                },
                {
                    "id": "div",
                    "label": "Diversity",
                    "type": "bucket",
                    "targetCredits": 5,
                    "area": "DIV",
                    "note": (
                        "May overlap with "
                        "another requirement."
                    ),
                },
            ],
        },
        {
            "id": "lsj-core",
            "title": "Core Courses",
            "displayCredits": "20 cr",
            "targetCredits": 20,
            "type": "group",
            "exclusiveSet": (
                "lsj-major-allocation"
            ),
            "exclusivePriority": 1,
            "note": (
                "Courses allocated here are not "
                "counted again in the 300-level "
                "or elective sections."
            ),
            "items": [
                {
                    "id": "core-lsj200",
                    "label": (
                        "Introduction to Law, "
                        "Societies & Justice"
                    ),
                    "type": "all",
                    "courses": ["LSJ 200"],
                },
                {
                    "id": "core-rights-law",
                    "label": (
                        "Two approved 300-level "
                        "Human Rights or Law courses"
                    ),
                    "type": "count",
                    "minCount": 2,
                    "courses": CORE_300,
                },
                {
                    "id": "core-capstone",
                    "label": (
                        "One LSJ 400-level "
                        "capstone seminar"
                    ),
                    "type": "one",
                    "courses": CAPSTONES,
                },
            ],
        },
        {
            "id": "lsj-300-level",
            "title": (
                "300-Level LSJ Courses"
            ),
            "displayCredits": (
                "Minimum 20 cr"
            ),
            "targetCredits": 20,
            "type": "group",
            "exclusiveSet": (
                "lsj-major-allocation"
            ),
            "exclusivePriority": 2,
            "note": (
                "At least four approved LSJ "
                "courses at the 300 level. "
                "Courses already allocated to "
                "the core are excluded "
                "automatically."
            ),
            "items": [
                {
                    "id": "lsj-300-count",
                    "label": (
                        "Four LSJ courses "
                        "at the 300 level"
                    ),
                    "type": "count",
                    "minCount": 4,
                    "courses": LSJ_300,
                }
            ],
        },
        {
            "id": "lsj-upper-electives",
            "title": (
                "Upper-Division Electives"
            ),
            "displayCredits": "16–20 cr",
            "targetCredits": 16,
            "type": "group",
            "exclusiveSet": (
                "lsj-major-allocation"
            ),
            "exclusivePriority": 3,
            "note": (
                "At least four approved "
                "upper-division courses, each "
                "at least 3 credits, totaling "
                "at least 16 credits. At least "
                "one must be 400-level. Courses "
                "used in earlier LSJ sections "
                "are excluded automatically."
            ),
            "items": [
                {
                    "id": (
                        "lsj-upper-elective-pool"
                    ),
                    "label": (
                        "Approved upper-division "
                        "electives"
                    ),
                    "type": (
                        "count-credit-level"
                    ),
                    "minCount": 4,
                    "minCredits": 16,
                    "minLevel": 400,
                    "minLevelCount": 1,
                    "courses": UPPER_ELECTIVES,
                }
            ],
        },
        {
            "id": "total",
            "title": (
                "Total Degree Credits"
            ),
            "displayCredits": "180 cr",
            "targetCredits": 180,
            "type": "total",
            "note": (
                "Use free electives and other "
                "approved coursework to reach "
                "180 credits."
            ),
        },
    ],
    "samplePlan": {
        "name": (
            "Suggested four-year LSJ plan "
            "(not an official UW schedule)"
        ),
        "quarters": {
            "y1-autumn": [
                "SLOT:English Composition",
                "SLOT:Foreign Language",
                "SLOT:Arts & Humanities",
            ],
            "y1-winter": [
                "SLOT:Reasoning",
                "SLOT:Foreign Language",
                "SLOT:Natural Sciences",
            ],
            "y1-spring": [
                "LSJ 200",
                "SLOT:Foreign Language",
                "SLOT:Arts & Humanities",
            ],
            "y2-autumn": [
                "LSJ 320",
                "SLOT:Social Sciences",
                "SLOT:Natural Sciences",
            ],
            "y2-winter": [
                "LSJ 300",
                "LSJ 331",
                "SLOT:Writing",
            ],
            "y2-spring": [
                "LSJ 332",
                "SLOT:Arts & Humanities",
                "SLOT:Natural Sciences",
            ],
            "y3-autumn": [
                "LSJ 369",
                "LSJ 376",
                "SLOT:Social Sciences",
            ],
            "y3-winter": [
                "LSJ 410",
                "PHIL 314",
                "SLOT:Writing",
            ],
            "y3-spring": [
                "LSJ 401",
                "SOC 371",
                "SLOT:Arts & Humanities",
            ],
            "y4-autumn": [
                "LSJ 438",
                (
                    "SLOT:Additional Areas "
                    "of Inquiry"
                ),
                "SLOT:Free Elective",
            ],
            "y4-winter": [
                (
                    "SLOT:Additional Areas "
                    "of Inquiry"
                ),
                "SLOT:Diversity",
                "SLOT:Free Elective",
            ],
            "y4-spring": [
                "SLOT:Free Elective",
                "SLOT:Free Elective",
                "SLOT:Free Elective",
            ],
        },
    },
    "prerequisiteSubstitutions": {},
}


MAJOR_DIR.mkdir(
    parents=True,
    exist_ok=True
)

with OUTPUT_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        major,
        file,
        indent=2,
        ensure_ascii=False
    )
    file.write("\n")


with INDEX_FILE.open(
    "r",
    encoding="utf-8"
) as file:
    index = json.load(file)


entry = {
    "id": "uw-seattle-lsj",
    "name": "Law, Societies & Justice",
    "degree": "BA",
    "status": "complete",
    "file": (
        "law-societies-justice.json"
    ),
    "source": (
        "https://lsj.washington.edu/"
        "lsj-gold-curriculum-requirements"
    ),
}


index["majors"] = [
    item
    for item in index.get("majors", [])
    if item.get("id") != entry["id"]
]

index["majors"].append(entry)


with INDEX_FILE.open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(
        index,
        file,
        indent=2,
        ensure_ascii=False
    )
    file.write("\n")


print(
    f"Created "
    f"{OUTPUT_FILE.relative_to(ROOT)}"
)

print(
    f"Updated "
    f"{INDEX_FILE.relative_to(ROOT)}"
)