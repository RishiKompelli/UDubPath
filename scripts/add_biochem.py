from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAJOR_DIR = ROOT / "data" / "majors"
INDEX_FILE = MAJOR_DIR / "index.json"
ME_FILE = MAJOR_DIR / "mechanical-engineering.json"

BS_FILE = MAJOR_DIR / "biochemistry-bs.json"
BA_FILE = MAJOR_DIR / "biochemistry-ba.json"


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


GENERAL_CHEM_PATHS = [
    {
        "label": "Standard general chemistry",
        "courses": ["CHEM 142", "CHEM 152", "CHEM 162"],
    },
    {
        "label": "Accelerated general chemistry",
        "courses": ["CHEM 143", "CHEM 153"],
    },
    {
        "label": "Honors general chemistry",
        "courses": ["CHEM 145", "CHEM 155", "CHEM 165"],
    },
]

ORGANIC_CHEM_PATHS = [
    {
        "label": "Standard organic chemistry",
        "courses": [
            "CHEM 237",
            "CHEM 238",
            "CHEM 239",
            "CHEM 241",
            "CHEM 242",
        ],
    },
    {
        "label": "Honors organic chemistry",
        "courses": [
            "CHEM 257",
            "CHEM 258",
            "CHEM 259",
            "CHEM 261",
            "CHEM 262",
        ],
    },
]

MATH_PATHS = [
    {
        "label": "Standard calculus",
        "courses": ["MATH 124", "MATH 125", "MATH 126"],
    },
    {
        "label": "Accelerated honors calculus",
        "courses": ["MATH 134", "MATH 135", "MATH 136"],
    },
]

PHYSICS_PATHS = [
    {
        "label": "Calculus-based physics — recommended",
        "courses": ["PHYS 121", "PHYS 122", "PHYS 123"],
    },
    {
        "label": "Algebra-based physics",
        "courses": ["PHYS 114", "PHYS 115", "PHYS 116"],
    },
    {
        "label": "Honors physics",
        "courses": ["PHYS 141", "PHYS 142", "PHYS 143"],
    },
]

PHYSICAL_CHEM_BS_PATHS = [
    {
        "label": "Physical chemistry for biochemists",
        "courses": ["CHEM 452", "CHEM 453"],
    },
    {
        "label": "Full physical chemistry",
        "courses": ["CHEM 455", "CHEM 456", "CHEM 457"],
    },
]

BS_SCIENCE_ELECTIVES = unique([
    "AMATH 351", "AMATH 352", "AMATH 422", "AMATH 423",
    "ATM S 358", "ATM S 458",
    "BIOL 220", "BIOL 355", "BIOL 401", "BIOL 402", "BIOL 411",
    "BIOL 457", "BIOL 459",
    "BIOST 310",
    "BSE 406",
    "CHEM 312", "CHEM 317", "CHEM 321", "CHEM 416", "CHEM 417",
    "CHEM 418", "CHEM 425", "CHEM 426", "CHEM 429", "CHEM 430",
    "CHEM 431", "CHEM 432", "CHEM 434", "CHEM 436", "CHEM 458",
    "CHEM 460", "CHEM 461", "CHEM 462", "CHEM 463", "CHEM 464",
    "CHEM 465", "CHEM 484", "CHEM 485", "CHEM 486", "CHEM 491",
    "CHEM 399", "CHEM 499", "BIOC 499",
    "CSE 427",
    "ENV H 405", "ENV H 432",
    "ESS 316", "ESS 457",
    "GENOME 372", "GENOME 373", "GENOME 465",
    "IMMUN 441",
    "MATH 207", "MATH 208",
    "MEDCH 327",
    "MICROM 402", "MICROM 410", "MICROM 411", "MICROM 412",
    "MICROM 431", "MICROM 445",
    "MSE 471", "MSE 475",
    "NEUSCI 404",
    "Q SCI 381",
    "STAT 311",
])

BA_SCIENCE_ELECTIVES = unique(
    BS_SCIENCE_ELECTIVES
    + [
        "B H 311",
        "GENOME 361",
        "PHYS 117",
        "PHYS 118",
        "PHYS 119",
    ]
)

ALL_GENERAL_CHEM = unique(
    code
    for path in GENERAL_CHEM_PATHS
    for code in path["courses"]
)
ALL_ORGANIC_CHEM = unique(
    code
    for path in ORGANIC_CHEM_PATHS
    for code in path["courses"]
)
ALL_MATH = unique(
    code
    for path in MATH_PATHS
    for code in path["courses"]
)
ALL_PHYSICS = unique(
    code
    for path in PHYSICS_PATHS
    for code in path["courses"]
)


def build_course_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}

    if ME_FILE.exists():
        me = read_json(ME_FILE)
        copied_codes = set(
            ALL_GENERAL_CHEM
            + ALL_ORGANIC_CHEM
            + ALL_MATH
            + ALL_PHYSICS
            + ["BIOL 180", "BIOL 200"]
        )
        for code in copied_codes:
            if code in me.get("courseOverrides", {}):
                overrides[code] = me["courseOverrides"][code]

    overrides.update({
        "CHEM 239": {
            "title": "Organic Chemistry",
            "credits": "4",
            "areas": "NSc",
            "offered": "A,W,Sp,S",
            "prerequisiteGroups": [["CHEM 238", "CHEM 258"]],
        },
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
                [
                    "CHEM 143",
                    "CHEM 145",
                    "CHEM 152",
                    "CHEM 153",
                    "CHEM 155",
                    "CHEM 220",
                    "CHEM 223",
                    "CHEM 237",
                ],
            ],
            "otherPrerequisites": (
                "Some approved chemistry choices may be taken concurrently; "
                "check the current UW catalog."
            ),
        },
        "BIOC 405": {
            "title": "Introduction to Biochemistry",
            "credits": "3",
            "areas": "NSc",
            "offered": "A,W,Sp,S",
            "prerequisiteGroups": [
                ["BIOL 200"],
                ["CHEM 224", "CHEM 239", "CHEM 259", "CHEM 337"],
                ["MATH 124", "MATH 134", "MATH 144"],
            ],
        },
        "BIOC 406": {
            "title": "Introduction to Biochemistry",
            "credits": "3",
            "areas": "NSc",
            "offered": "W,Sp",
            "prerequisiteGroups": [["BIOC 405"]],
        },
        "BIOC 426": {
            "title": "Basic Techniques in Biochemistry",
            "credits": "4",
            "areas": "NSc",
            "offered": "A,W,Sp",
            "prerequisiteGroups": [["BIOC 440"]],
            "otherPrerequisites": (
                "BIOC 440 may be taken concurrently according to the catalog. "
                "The planner may conservatively place it earlier."
            ),
        },
        "BIOC 440": {
            "title": "Biochemistry",
            "credits": "4",
            "areas": "NSc",
            "offered": "A",
            "prerequisiteGroups": [
                ["BIOL 200"],
                ["CHEM 224", "CHEM 239", "CHEM 259", "CHEM 337"],
                ["MATH 124", "MATH 134", "MATH 144"],
            ],
        },
        "BIOC 441": {
            "title": "Biochemistry",
            "credits": "4",
            "areas": "NSc",
            "offered": "W",
            "prerequisiteGroups": [["BIOC 440"]],
        },
        "BIOC 442": {
            "title": "Biochemistry",
            "credits": "4",
            "areas": "NSc",
            "offered": "Sp",
            "prerequisiteGroups": [["BIOC 441"]],
        },
        "GENOME 361": {
            "title": "Fundamentals of Genetics and Genomics",
            "credits": "3",
            "areas": "NSc",
            "offered": "W,Sp,S",
            "prerequisiteGroups": [["BIOL 200"]],
        },
        "GENOME 372": {
            "title": "Genomics and Proteomics",
            "credits": "5",
            "areas": "NSc",
            "prerequisiteGroups": [],
        },
    })

    return overrides


def general_education_requirement() -> dict[str, Any]:
    return {
        "id": "general-education",
        "title": "General Education Requirements",
        "displayCredits": "College of Arts & Sciences",
        "targetCredits": 0,
        "type": "group",
        "items": [
            {
                "id": "english-comp",
                "label": "English Composition",
                "type": "bucket",
                "targetCredits": 5,
                "area": "C",
            },
            {
                "id": "writing",
                "label": "Additional Writing",
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
                "label": "Foreign language through the third quarter",
                "type": "bucket",
                "targetCredits": 15,
                "area": "FL",
                "note": (
                    "Enter manual credits or mark fulfilled when high-school, "
                    "AP, placement, or college language work satisfies this."
                ),
            },
            {
                "id": "ah",
                "label": "Arts & Humanities",
                "type": "bucket",
                "targetCredits": 20,
                "area": "A&H",
            },
            {
                "id": "ssc",
                "label": "Social Sciences",
                "type": "bucket",
                "targetCredits": 20,
                "area": "SSc",
            },
            {
                "id": "nsc",
                "label": "Natural Sciences",
                "type": "bucket",
                "targetCredits": 20,
                "area": "NSc",
                "note": (
                    "Most Biochemistry supporting courses contribute toward "
                    "this university requirement."
                ),
            },
            {
                "id": "additional-aoi",
                "label": "Additional Areas of Inquiry",
                "type": "additional-bucket",
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
                "note": "May overlap another general-education requirement.",
            },
        ],
    }


def general_education_refs() -> list[dict[str, Any]]:
    return [
        {
            "id": "english-comp",
            "scope": "item",
            "label": "English Composition",
            "credits": "5 cr",
        },
        {
            "id": "writing",
            "scope": "item",
            "label": "Additional Writing",
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
            "label": "Arts & Humanities",
            "credits": "20 cr",
        },
        {
            "id": "ssc",
            "scope": "item",
            "label": "Social Sciences",
            "credits": "20 cr",
        },
        {
            "id": "nsc",
            "scope": "item",
            "label": "Natural Sciences",
            "credits": "20 cr",
        },
        {
            "id": "additional-aoi",
            "scope": "item",
            "label": "Additional Areas of Inquiry",
            "credits": "15 cr",
        },
        {
            "id": "div",
            "scope": "item",
            "label": "Diversity",
            "credits": "5 cr",
        },
    ]


def admission_requirement(kind: str) -> dict[str, Any]:
    is_bs = kind == "bs"
    return {
        "id": "biochem-admission",
        "title": "Biochemistry Admission Checkpoint",
        "displayCredits": "Before applying",
        "targetCredits": 0,
        "type": "group",
        "note": (
            "Biochemistry is capacity-constrained. Direct first-year and "
            "direct-transfer pathways have separate procedures. This section "
            "tracks the regular-admission academic preparation."
        ),
        "items": [
            {
                "id": "admission-general-chem",
                "label": "Complete one general chemistry sequence",
                "type": "path-choice",
                "paths": GENERAL_CHEM_PATHS,
            },
            {
                "id": "admission-biology",
                "label": "Introductory Biology",
                "type": "all",
                "courses": ["BIOL 180"],
            },
            {
                "id": "admission-math",
                "label": "First two calculus courses",
                "type": "path-choice",
                "paths": [
                    {
                        "label": "Standard calculus",
                        "courses": ["MATH 124", "MATH 125"],
                    },
                    {
                        "label": "Accelerated honors calculus",
                        "courses": ["MATH 134", "MATH 135"],
                    },
                ],
            },
            {
                "id": "admission-course-grades",
                "label": (
                    "Minimum 2.0 in each admission course"
                    if is_bs
                    else "Minimum 1.7 in each admission course"
                ),
                "type": "check",
            },
            {
                "id": "admission-gpa",
                "label": (
                    "Minimum 2.80 admission-course GPA"
                    if is_bs
                    else "Minimum 2.50 admission-course GPA"
                ),
                "type": "check",
            },
        ],
    }


def shared_major_requirements(kind: str) -> list[dict[str, Any]]:
    is_bs = kind == "bs"
    return [
        {
            "id": "mathematics",
            "title": "Mathematics",
            "displayCredits": "15 cr",
            "targetCredits": 15,
            "type": "group",
            "items": [
                {
                    "id": "calculus-sequence",
                    "label": "Complete one calculus sequence",
                    "type": "path-choice",
                    "paths": MATH_PATHS,
                }
            ],
        },
        {
            "id": "general-chemistry",
            "title": "General Chemistry",
            "displayCredits": "12–15 cr",
            "targetCredits": 12,
            "type": "group",
            "items": [
                {
                    "id": "general-chem-sequence",
                    "label": "Complete one general chemistry sequence",
                    "type": "path-choice",
                    "paths": GENERAL_CHEM_PATHS,
                }
            ],
        },
        {
            "id": "organic-chemistry",
            "title": "Organic Chemistry",
            "displayCredits": "18 cr",
            "targetCredits": 18,
            "type": "group",
            "items": [
                {
                    "id": "organic-chem-sequence",
                    "label": "Lecture and laboratory sequence",
                    "type": "path-choice",
                    "paths": ORGANIC_CHEM_PATHS,
                }
            ],
        },
        {
            "id": "biology",
            "title": "Biology",
            "displayCredits": "10 cr",
            "targetCredits": 10,
            "type": "group",
            "items": [
                {
                    "id": "biology-fixed",
                    "label": "Introductory Biology",
                    "type": "all",
                    "courses": ["BIOL 180", "BIOL 200"],
                }
            ],
        },
        {
            "id": "physics",
            "title": "Physics",
            "displayCredits": "12–15 cr",
            "targetCredits": 12,
            "type": "group",
            "items": [
                {
                    "id": "physics-sequence",
                    "label": "Complete one physics sequence",
                    "type": "path-choice",
                    "paths": PHYSICS_PATHS,
                }
            ],
        },
        {
            "id": "grade-standards",
            "title": "Major Grade Standards",
            "displayCredits": "Required",
            "targetCredits": 0,
            "type": "group",
            "items": [
                {
                    "id": "major-course-minimum",
                    "label": (
                        "Minimum 2.0 in each required CHEM, BIOL, and BIOC course"
                        if is_bs
                        else "Minimum 1.7 in each required CHEM, BIOL, and BIOC course"
                    ),
                    "type": "check",
                },
                {
                    "id": "major-gpa",
                    "label": (
                        "Minimum 2.50 cumulative major GPA"
                        if is_bs
                        else "Minimum 2.00 cumulative major GPA"
                    ),
                    "type": "check",
                },
                {
                    "id": "overall-gpa",
                    "label": (
                        "Minimum 2.50 overall GPA"
                        if is_bs
                        else "Minimum 2.00 overall GPA"
                    ),
                    "type": "check",
                },
            ],
        },
        {
            "id": "outside-major",
            "title": "College of Arts & Sciences Outside-Major Credits",
            "displayCredits": "90 cr outside major department",
            "targetCredits": 0,
            "type": "group",
            "items": [
                {
                    "id": "outside-major-check",
                    "label": "At least 90 credits outside the major department",
                    "type": "check",
                }
            ],
        },
    ]


def build_bs_major(overrides: dict[str, Any], substitutions: dict[str, Any]) -> dict[str, Any]:
    requirements = [
        admission_requirement("bs"),
        general_education_requirement(),
        *shared_major_requirements("bs"),
        {
            "id": "biochemistry-core",
            "title": "Biochemistry",
            "displayCredits": "16 cr",
            "targetCredits": 16,
            "type": "group",
            "items": [
                {
                    "id": "bioc-sequence",
                    "label": "Biochemistry sequence",
                    "type": "all",
                    "courses": ["BIOC 440", "BIOC 441", "BIOC 442"],
                },
                {
                    "id": "bioc-lab",
                    "label": "Biochemistry laboratory",
                    "type": "all",
                    "courses": ["BIOC 426"],
                    "note": (
                        "An approved research experience may be petitioned as "
                        "an exemption from BIOC 426."
                    ),
                },
                {
                    "id": "bioc-sequence-gpa",
                    "label": "Minimum 2.50 GPA across BIOC 440, 441, and 442",
                    "type": "check",
                },
            ],
        },
        {
            "id": "physical-chemistry",
            "title": "Physical Chemistry",
            "displayCredits": "6–9 cr",
            "targetCredits": 6,
            "type": "group",
            "items": [
                {
                    "id": "physical-chem-sequence",
                    "label": "Complete one physical chemistry sequence",
                    "type": "path-choice",
                    "paths": PHYSICAL_CHEM_BS_PATHS,
                }
            ],
        },
        {
            "id": "genome-science",
            "title": "Genome Science",
            "displayCredits": "3–5 cr",
            "targetCredits": 3,
            "type": "group",
            "items": [
                {
                    "id": "genome-choice",
                    "label": "Choose one Genome Science course",
                    "type": "one",
                    "courses": ["GENOME 361", "GENOME 372"],
                }
            ],
        },
        {
            "id": "science-electives",
            "title": "Science Electives",
            "displayCredits": "11 cr",
            "targetCredits": 11,
            "type": "group",
            "items": [
                {
                    "id": "science-elective-pool",
                    "label": "Approved upper-division science electives",
                    "type": "pool",
                    "minCredits": 11,
                    "courses": BS_SCIENCE_ELECTIVES,
                    "note": (
                        "Up to 9 approved advanced-research credits may count. "
                        "Only one of BIOST 310, Q SCI 381, and STAT 311 may count. "
                        "Overlapping MATH/AMATH pairs cannot both count."
                    ),
                }
            ],
        },
        {
            "id": "total",
            "title": "Total Degree Credits",
            "displayCredits": "193 cr",
            "targetCredits": 193,
            "type": "total",
            "note": "The UW Biochemistry BS requires at least 193 total credits.",
        },
    ]

    sample_plan = {
        "name": "Official department sample plan, updated for current CHEM 239 credits",
        "quarters": {
            "y1-autumn": [
                "MATH 124",
                "CHEM 142",
                "SLOT:5:Foreign Language",
            ],
            "y1-winter": [
                "MATH 125",
                "CHEM 152",
                "SLOT:5:Foreign Language",
            ],
            "y1-spring": [
                "MATH 126",
                "CHEM 162",
                "SLOT:5:Foreign Language",
                "SLOT:2:Free Elective",
            ],
            "y2-autumn": [
                "BIOL 180",
                "CHEM 237",
                "SLOT:7:Free Elective",
            ],
            "y2-winter": [
                "BIOL 200",
                "CHEM 238",
                "CHEM 241",
                "SLOT:5:Social Sciences",
            ],
            "y2-spring": [
                "CHEM 239",
                "CHEM 242",
                "SLOT:5:English Composition",
                "SLOT:5:Arts & Humanities",
            ],
            "y3-autumn": [
                "BIOC 440",
                "PHYS 121",
                "SLOT:5:Social Sciences",
                "SLOT:2:Free Elective",
            ],
            "y3-winter": [
                "BIOC 441",
                "PHYS 122",
                "SLOT:5:Arts & Humanities",
                "SLOT:3:Free Elective",
            ],
            "y3-spring": [
                "BIOC 442",
                "PHYS 123",
                "SLOT:5:Arts & Humanities / Writing",
                "SLOT:3:Free Elective",
            ],
            "y4-autumn": [
                "BIOC 426",
                "SLOT:5:Social Sciences / Writing",
                "SLOT:8:Science Elective",
            ],
            "y4-winter": [
                "CHEM 452",
                "SLOT:3:Science Elective",
                "SLOT:5:Arts & Humanities",
                "SLOT:4:Free Elective",
            ],
            "y4-spring": [
                "CHEM 453",
                "GENOME 361",
                "SLOT:5:Social Sciences",
                "SLOT:3:Free Elective",
            ],
        },
    }

    return {
        "id": "uw-seattle-biochemistry-bs",
        "university": "University of Washington Seattle",
        "name": "Biochemistry (BS)",
        "degree": "Bachelor of Science with a major in Biochemistry",
        "catalogYear": "Current UW Chemistry Department requirements",
        "totalCredits": 193,
        "sources": [
            {
                "label": "UW Chemistry — BS in Biochemistry",
                "url": "https://chem.washington.edu/bs-biochemistry",
            },
            {
                "label": "UW Chemistry — Biochemistry admissions",
                "url": (
                    "https://chem.washington.edu/"
                    "undergraduate-prerequisites-and-admissions-biochemistry"
                ),
            },
            {
                "label": "UW General Catalog — Biochemistry",
                "url": (
                    "https://www.washington.edu/students/gencat/program/S/"
                    "Chemistry-117.html"
                ),
            },
            {
                "label": "UW course catalog",
                "url": "https://www.washington.edu/students/crscat/",
            },
        ],
        "tracks": [
            {
                "id": "standard",
                "name": "Biochemistry BS",
                "description": (
                    "In-depth Biochemistry preparation including advanced "
                    "laboratory work and 11 science-elective credits."
                ),
            }
        ],
        "courseOverrides": overrides,
        "mapGroups": [
            {
                "id": "admission",
                "label": "Biochemistry Admission Checkpoint",
                "shortLabel": "Admission",
                "credits": "Before applying",
                "description": "Regular-admission preparation and grade checks.",
                "courses": [],
                "requirementRefs": [
                    {
                        "id": "biochem-admission",
                        "scope": "requirement",
                        "label": "Biochemistry application preparation",
                        "credits": "Before applying",
                    }
                ],
            },
            {
                "id": "general-education",
                "label": "General Education Requirements",
                "shortLabel": "General Education",
                "credits": "College of Arts & Sciences",
                "description": (
                    "Composition, writing, language, Areas of Inquiry, "
                    "Reasoning, and Diversity."
                ),
                "courses": [],
                "requirementRefs": general_education_refs(),
            },
            {
                "id": "mathematics",
                "label": "Mathematics",
                "credits": "15 cr",
                "description": "Standard or accelerated honors calculus.",
                "courses": ALL_MATH,
            },
            {
                "id": "general-chemistry",
                "label": "General Chemistry",
                "credits": "12–15 cr",
                "description": "Standard, accelerated, or honors sequence.",
                "courses": ALL_GENERAL_CHEM,
            },
            {
                "id": "organic-chemistry",
                "label": "Organic Chemistry",
                "credits": "18 cr",
                "description": "Lecture and laboratory sequence.",
                "courses": ALL_ORGANIC_CHEM,
            },
            {
                "id": "biology-physics",
                "label": "Biology & Physics",
                "credits": "22–25 cr",
                "description": "BIOL 180/200 and one complete physics sequence.",
                "courses": ["BIOL 180", "BIOL 200", *ALL_PHYSICS],
            },
            {
                "id": "biochemistry-core",
                "label": "Biochemistry & Physical Chemistry",
                "shortLabel": "Biochemistry Core",
                "credits": "22–25 cr",
                "description": (
                    "BIOC 440–442, BIOC 426, and one physical chemistry path."
                ),
                "courses": [
                    "BIOC 440", "BIOC 441", "BIOC 442", "BIOC 426",
                    "CHEM 452", "CHEM 453", "CHEM 455", "CHEM 456", "CHEM 457",
                ],
            },
            {
                "id": "genome-science",
                "label": "Genome Science",
                "credits": "3–5 cr",
                "description": "Choose GENOME 361 or GENOME 372.",
                "courses": ["GENOME 361", "GENOME 372"],
            },
            {
                "id": "science-electives",
                "label": "Science Electives",
                "credits": "11 cr",
                "description": "Current department-approved science elective list.",
                "courses": BS_SCIENCE_ELECTIVES,
            },
            {
                "id": "free-electives",
                "label": "Free Electives",
                "credits": "To reach 193 cr",
                "description": "Other approved coursework needed for the degree total.",
                "courses": [],
                "requirementRefs": [
                    {
                        "id": "total",
                        "scope": "requirement",
                        "label": "Total degree credits",
                        "credits": "193 cr",
                    }
                ],
            },
        ],
        "requirements": requirements,
        "samplePlan": sample_plan,
        "prerequisiteSubstitutions": substitutions,
    }


def build_ba_major(overrides: dict[str, Any], substitutions: dict[str, Any]) -> dict[str, Any]:
    requirements = [
        admission_requirement("ba"),
        general_education_requirement(),
        *shared_major_requirements("ba"),
        {
            "id": "biochemistry-core",
            "title": "Biochemistry",
            "displayCredits": "6 cr",
            "targetCredits": 6,
            "type": "group",
            "items": [
                {
                    "id": "bioc-sequence",
                    "label": "Introductory Biochemistry sequence",
                    "type": "all",
                    "courses": ["BIOC 405", "BIOC 406"],
                }
            ],
        },
        {
            "id": "physical-chemistry",
            "title": "Physical Chemistry",
            "displayCredits": "6 cr",
            "targetCredits": 6,
            "type": "group",
            "items": [
                {
                    "id": "physical-chem-fixed",
                    "label": "Physical Chemistry for Biochemists",
                    "type": "all",
                    "courses": ["CHEM 452", "CHEM 453"],
                }
            ],
        },
        {
            "id": "science-electives",
            "title": "Science Electives",
            "displayCredits": "9 cr",
            "targetCredits": 9,
            "type": "group",
            "items": [
                {
                    "id": "science-elective-pool",
                    "label": "Approved science electives",
                    "type": "pool",
                    "minCredits": 9,
                    "courses": BA_SCIENCE_ELECTIVES,
                    "note": (
                        "Up to 3 approved advanced-research credits may count. "
                        "One physics-laboratory credit may count with the "
                        "algebra-based physics route. The department notes that "
                        "one credit from the calculus-based physics route may "
                        "also be applied; confirm that adjustment with advising."
                    ),
                }
            ],
        },
        {
            "id": "total",
            "title": "Total Degree Credits",
            "displayCredits": "180 cr",
            "targetCredits": 180,
            "type": "total",
        },
    ]

    sample_plan = {
        "name": "Official department sample plan, updated for current CHEM 239 credits",
        "quarters": {
            "y1-autumn": [
                "MATH 124",
                "CHEM 142",
                "SLOT:5:Foreign Language",
            ],
            "y1-winter": [
                "MATH 125",
                "CHEM 152",
                "SLOT:5:Foreign Language",
            ],
            "y1-spring": [
                "MATH 126",
                "CHEM 162",
                "SLOT:5:Foreign Language",
            ],
            "y2-autumn": [
                "BIOL 180",
                "CHEM 237",
                "SLOT:5:English Composition",
            ],
            "y2-winter": [
                "BIOL 200",
                "CHEM 238",
                "CHEM 241",
                "SLOT:3:Free Elective",
            ],
            "y2-spring": [
                "CHEM 239",
                "CHEM 242",
                "SLOT:5:Arts & Humanities",
                "SLOT:5:Free Elective",
            ],
            "y3-autumn": [
                "BIOC 405",
                "PHYS 121",
                "SLOT:5:Arts & Humanities / Writing",
                "SLOT:3:Free Elective",
            ],
            "y3-winter": [
                "BIOC 406",
                "PHYS 122",
                "SLOT:5:Arts & Humanities",
                "SLOT:3:Free Elective",
            ],
            "y3-spring": [
                "PHYS 123",
                "SLOT:5:Social Sciences / Writing",
                "SLOT:5:Arts & Humanities",
            ],
            "y4-autumn": [
                "CHEM 452",
                "SLOT:3:Science Elective",
                "SLOT:5:Social Sciences",
                "SLOT:5:Free Elective",
            ],
            "y4-winter": [
                "CHEM 453",
                "SLOT:3:Science Elective",
                "SLOT:5:Social Sciences",
                "SLOT:3:Free Elective",
            ],
            "y4-spring": [
                "SLOT:3:Science Elective",
                "SLOT:5:Social Sciences",
                "SLOT:4:Free Elective",
            ],
        },
    }

    return {
        "id": "uw-seattle-biochemistry-ba",
        "university": "University of Washington Seattle",
        "name": "Biochemistry (BA)",
        "degree": "Bachelor of Arts with a major in Biochemistry",
        "catalogYear": "Current UW Chemistry Department requirements",
        "totalCredits": 180,
        "sources": [
            {
                "label": "UW Chemistry — BA in Biochemistry",
                "url": "https://chem.washington.edu/ba-biochemistry",
            },
            {
                "label": "UW Chemistry — Biochemistry admissions",
                "url": (
                    "https://chem.washington.edu/"
                    "undergraduate-prerequisites-and-admissions-biochemistry"
                ),
            },
            {
                "label": "UW General Catalog — Biochemistry",
                "url": (
                    "https://www.washington.edu/students/gencat/program/S/"
                    "Chemistry-117.html"
                ),
            },
            {
                "label": "UW course catalog",
                "url": "https://www.washington.edu/students/crscat/",
            },
        ],
        "tracks": [
            {
                "id": "standard",
                "name": "Biochemistry BA",
                "description": (
                    "Broad Biochemistry training with BIOC 405–406 and "
                    "9 approved science-elective credits."
                ),
            }
        ],
        "courseOverrides": overrides,
        "mapGroups": [
            {
                "id": "admission",
                "label": "Biochemistry Admission Checkpoint",
                "shortLabel": "Admission",
                "credits": "Before applying",
                "description": "Regular-admission preparation and grade checks.",
                "courses": [],
                "requirementRefs": [
                    {
                        "id": "biochem-admission",
                        "scope": "requirement",
                        "label": "Biochemistry application preparation",
                        "credits": "Before applying",
                    }
                ],
            },
            {
                "id": "general-education",
                "label": "General Education Requirements",
                "shortLabel": "General Education",
                "credits": "College of Arts & Sciences",
                "description": (
                    "Composition, writing, language, Areas of Inquiry, "
                    "Reasoning, and Diversity."
                ),
                "courses": [],
                "requirementRefs": general_education_refs(),
            },
            {
                "id": "mathematics",
                "label": "Mathematics",
                "credits": "15 cr",
                "description": "Standard or accelerated honors calculus.",
                "courses": ALL_MATH,
            },
            {
                "id": "general-chemistry",
                "label": "General Chemistry",
                "credits": "12–15 cr",
                "description": "Standard, accelerated, or honors sequence.",
                "courses": ALL_GENERAL_CHEM,
            },
            {
                "id": "organic-chemistry",
                "label": "Organic Chemistry",
                "credits": "18 cr",
                "description": "Lecture and laboratory sequence.",
                "courses": ALL_ORGANIC_CHEM,
            },
            {
                "id": "biology-physics",
                "label": "Biology & Physics",
                "credits": "22–25 cr",
                "description": "BIOL 180/200 and one complete physics sequence.",
                "courses": ["BIOL 180", "BIOL 200", *ALL_PHYSICS],
            },
            {
                "id": "biochemistry-core",
                "label": "Biochemistry & Physical Chemistry",
                "shortLabel": "Biochemistry Core",
                "credits": "12 cr",
                "description": "BIOC 405–406 and CHEM 452–453.",
                "courses": ["BIOC 405", "BIOC 406", "CHEM 452", "CHEM 453"],
            },
            {
                "id": "science-electives",
                "label": "Science Electives",
                "credits": "9 cr",
                "description": "Current department-approved science elective list.",
                "courses": BA_SCIENCE_ELECTIVES,
            },
            {
                "id": "free-electives",
                "label": "Free Electives",
                "credits": "To reach 180 cr",
                "description": "Other approved coursework needed for the degree total.",
                "courses": [],
                "requirementRefs": [
                    {
                        "id": "total",
                        "scope": "requirement",
                        "label": "Total degree credits",
                        "credits": "180 cr",
                    }
                ],
            },
        ],
        "requirements": requirements,
        "samplePlan": sample_plan,
        "prerequisiteSubstitutions": substitutions,
    }


def plan_credits(plan: dict[str, Any], overrides: dict[str, Any]) -> float:
    known = {
        "MATH 124": 5, "MATH 125": 5, "MATH 126": 5,
        "CHEM 142": 5, "CHEM 152": 5, "CHEM 162": 5,
        "CHEM 237": 4, "CHEM 238": 4, "CHEM 239": 4,
        "CHEM 241": 3, "CHEM 242": 3,
        "BIOL 180": 5, "BIOL 200": 5,
        "PHYS 121": 5, "PHYS 122": 5, "PHYS 123": 5,
        "BIOC 405": 3, "BIOC 406": 3,
        "BIOC 426": 4, "BIOC 440": 4, "BIOC 441": 4, "BIOC 442": 4,
        "CHEM 452": 3, "CHEM 453": 3,
        "GENOME 361": 3,
    }

    total = 0.0
    for entries in plan["quarters"].values():
        for entry in entries:
            if entry.startswith("SLOT:"):
                parts = entry.split(":", 2)
                total += float(parts[1])
            else:
                total += known.get(entry, 0)
    return total


def update_index() -> None:
    index = read_json(INDEX_FILE)

    additions = [
        {
            "id": "uw-seattle-biochemistry-bs",
            "name": "Biochemistry (BS)",
            "degree": "BS",
            "status": "complete",
            "file": "biochemistry-bs.json",
            "source": "https://chem.washington.edu/bs-biochemistry",
        },
        {
            "id": "uw-seattle-biochemistry-ba",
            "name": "Biochemistry (BA)",
            "degree": "BA",
            "status": "complete",
            "file": "biochemistry-ba.json",
            "source": "https://chem.washington.edu/ba-biochemistry",
        },
    ]

    addition_ids = {item["id"] for item in additions}
    index["majors"] = [
        item
        for item in index.get("majors", [])
        if item.get("id") not in addition_ids
    ]
    index["majors"].extend(additions)
    write_json(INDEX_FILE, index)


def main() -> None:
    MAJOR_DIR.mkdir(parents=True, exist_ok=True)

    overrides = build_course_overrides()
    substitutions: dict[str, Any] = {}

    if ME_FILE.exists():
        me = read_json(ME_FILE)
        substitutions = me.get("prerequisiteSubstitutions", {})

    bs = build_bs_major(overrides, substitutions)
    ba = build_ba_major(overrides, substitutions)

    bs_total = plan_credits(bs["samplePlan"], overrides)
    ba_total = plan_credits(ba["samplePlan"], overrides)

    if bs_total != 193:
        raise RuntimeError(
            f"Biochemistry BS sample plan represents {bs_total} credits, not 193."
        )
    if ba_total != 180:
        raise RuntimeError(
            f"Biochemistry BA sample plan represents {ba_total} credits, not 180."
        )

    write_json(BS_FILE, bs)
    write_json(BA_FILE, ba)
    update_index()

    print(f"Created {BS_FILE.relative_to(ROOT)}")
    print(f"Created {BA_FILE.relative_to(ROOT)}")
    print(f"Updated {INDEX_FILE.relative_to(ROOT)}")
    print("Verified BS sample plan at 193 credits.")
    print("Verified BA sample plan at 180 credits.")
    print("The double-major / dual-degree patch was not changed or applied.")


if __name__ == "__main__":
    main()