from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
ROOT_CANDIDATES = [
    Path.cwd(),
    SCRIPT_PATH.parent,
    SCRIPT_PATH.parent.parent,
]
ROOT = next(
    (candidate for candidate in ROOT_CANDIDATES if (candidate / "data" / "majors").exists()),
    None,
)
if ROOT is None:
    raise SystemExit(
        "Could not find the project root. Save this file in the project's scripts folder "
        "and run it from the project root."
    )

MAJOR_DIR = ROOT / "data" / "majors"
INDEX_FILE = MAJOR_DIR / "index.json"
ME_FILE = MAJOR_DIR / "mechanical-engineering.json"
CATALOG_FILE = ROOT / "data" / "catalog-live.json"
if not CATALOG_FILE.exists():
    CATALOG_FILE = ROOT / "data" / "catalog-fallback.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, value):
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def unique(values):
    return list(dict.fromkeys(values))


def course_number(code: str) -> int:
    match = re.search(r"\b(\d{3})[A-Z]?\b", code)
    return int(match.group(1)) if match else 0


me = load_json(ME_FILE)
catalog_payload = load_json(CATALOG_FILE)
if CATALOG_FILE.name == "catalog-fallback.json":
    print(
        "Note: data/catalog-live.json was not found. Run 'py server.py --sync-only' "
        "before this script for the newest UW course catalog and elective pools."
    )
catalog = [
    row for row in catalog_payload.get("courses", [])
    if row.get("campus") == "Seattle"
]


def catalog_codes(prefixes, minimum=0, maximum=999, title_terms=()):
    prefixes = (prefixes,) if isinstance(prefixes, str) else tuple(prefixes)
    results = []
    for row in catalog:
        code = str(row.get("code", "")).strip().upper()
        if not any(code.startswith(prefix + " ") for prefix in prefixes):
            continue
        number = course_number(code)
        if number < minimum or number > maximum:
            continue
        if title_terms:
            title = str(row.get("title", "")).lower()
            if not any(term.lower() in title for term in title_terms):
                continue
        results.append(code)
    return unique(sorted(results, key=lambda code: (code.rsplit(" ", 1)[0], course_number(code), code)))


COMMON_OVERRIDE_CODES = [
    "MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136",
    "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "MATH 209", "MATH 224",
    "IND E 315", "STAT 290", "STAT 311", "STAT 390", "Q SCI 381",
    "CHEM 142", "CHEM 152", "CHEM 162", "CHEM 143", "CHEM 153",
    "CHEM 145", "CHEM 155", "CHEM 165",
    "PHYS 121", "PHYS 122", "PHYS 123", "PHYS 141", "PHYS 142", "PHYS 143",
    "ENGR 101", "GEN ST 199", "AMATH 301", "AA 210", "AA 260", "CEE 220",
    "ME 123", "ME 230", "MSE 170", "EE 215", "CSE 121", "CSE 122", "CSE 123",
    "CSE 143", "CSE 160", "CSE 163", "IND E 250", "ECON 200",
]
COMMON_OVERRIDES = {
    code: deepcopy(me.get("courseOverrides", {}).get(code, {}))
    for code in COMMON_OVERRIDE_CODES
    if code in me.get("courseOverrides", {})
}
SUBSTITUTIONS = deepcopy(me.get("prerequisiteSubstitutions", {}))


def paths_calculus(include_linear_diff=True):
    standard = ["MATH 124", "MATH 125", "MATH 126"]
    honors = ["MATH 134", "MATH 135", "MATH 136"]
    items = [{
        "id": "calc-sequence",
        "label": "Calculus sequence",
        "type": "path-choice",
        "paths": [
            {"label": "Standard calculus", "courses": standard},
            {"label": "Accelerated honors mathematics", "courses": honors},
        ],
    }]
    if include_linear_diff:
        items += [
            {
                "id": "differential-equations",
                "label": "Differential equations",
                "type": "path-choice",
                "paths": [
                    {"label": "MATH 207", "courses": ["MATH 207"]},
                    {"label": "AMATH 351", "courses": ["AMATH 351"]},
                    {"label": "Included in MATH 134–136", "courses": honors},
                ],
            },
            {
                "id": "linear-algebra",
                "label": "Linear algebra",
                "type": "path-choice",
                "paths": [
                    {"label": "MATH 208", "courses": ["MATH 208"]},
                    {"label": "AMATH 352", "courses": ["AMATH 352"]},
                    {"label": "Included in MATH 134–136", "courses": honors},
                ],
            },
        ]
    return items


def gen_ed(display="29–41 cr", extra_ahssc=4, writing_courses=None, extra_nsc=0):
    writing_courses = writing_courses or []
    writing_item = (
        {
            "id": "major-writing",
            "label": "Writing met by coursework in the major",
            "type": "all",
            "courses": writing_courses,
        }
        if writing_courses
        else {
            "id": "writing",
            "label": "Writing",
            "type": "bucket",
            "targetCredits": 7,
            "area": "W",
        }
    )
    items = [
        {"id": "english-comp", "label": "English Composition", "type": "bucket", "targetCredits": 5, "area": "C"},
        writing_item,
        {"id": "ah", "label": "Arts & Humanities", "type": "bucket", "targetCredits": 10, "area": "A&H"},
        {"id": "ssc", "label": "Social Sciences", "type": "bucket", "targetCredits": 10, "area": "SSc"},
        {
            "id": "areas-extra",
            "label": "Additional Arts & Humanities or Social Sciences",
            "type": "additional-bucket",
            "targetCredits": extra_ahssc,
            "baseCredits": 20,
            "area": "A&H/SSc",
        },
    ]
    if extra_nsc:
        items.append({
            "id": "additional-nsc",
            "label": "Additional Natural Science",
            "type": "bucket",
            "targetCredits": extra_nsc,
            "area": "NSc",
        })
    items.append({"id": "div", "label": "Diversity", "type": "bucket", "targetCredits": 5, "area": "DIV", "note": "May overlap with Areas of Inquiry or Writing."})
    return {
        "id": "gen-ed",
        "title": "General Education Requirements",
        "displayCredits": display,
        "targetCredits": 0,
        "type": "group",
        "items": items,
    }


def efig_requirement():
    return {
        "id": "efig",
        "title": "Engineering First-year Interest Group (E-FIG)",
        "displayCredits": "2 cr",
        "targetCredits": 2,
        "type": "group",
        "items": [{"id": "efig-courses", "label": "E-FIG courses", "type": "all", "courses": ["ENGR 101", "GEN ST 199"]}],
    }


def placement_requirement(options, chem152_required=False):
    items = [
        {"id": "placement-engr101", "label": "Engineering exploration", "type": "all", "courses": ["ENGR 101"]},
        {
            "id": "placement-calculus",
            "label": "Calculus preparation",
            "type": "path-choice",
            "paths": [
                {"label": "Standard calculus", "courses": ["MATH 124", "MATH 125", "MATH 126"]},
                {"label": "Accelerated honors mathematics", "courses": ["MATH 134", "MATH 135", "MATH 136"]},
            ],
        },
        {
            "id": "placement-chemistry",
            "label": "First chemistry course",
            "type": "one",
            "courses": ["CHEM 142", "CHEM 143", "CHEM 145"],
        },
        {
            "id": "placement-physics",
            "label": "First calculus-based physics course",
            "type": "one",
            "courses": ["PHYS 121", "PHYS 141"],
        },
        {"id": "placement-composition", "label": "English Composition", "type": "bucket", "targetCredits": 5, "area": "C"},
    ]
    if chem152_required:
        items.append({
            "id": "placement-chem152",
            "label": "Second chemistry course",
            "type": "one",
            "courses": ["CHEM 152", "CHEM 153", "CHEM 155"],
        })
    else:
        items.append({"id": "placement-additional", "label": "Additional placement course", "type": "one", "courses": options})
    return {
        "id": "engrud-placement",
        "title": "ENGRUD Placement Checkpoint",
        "displayCredits": "After Year 1",
        "targetCredits": 0,
        "type": "group",
        "note": "Placement requirements are shown separately but also count toward degree requirements.",
        "items": items,
    }


def map_ref(ref_id, label, credits, scope="item"):
    return {"id": ref_id, "scope": scope, "label": label, "credits": credits}


def total_requirement():
    return {
        "id": "total",
        "title": "Total Degree Credits",
        "displayCredits": "180 cr",
        "targetCredits": 180,
        "type": "total",
        "note": "Free electives and other approved coursework bring the degree total to 180 credits.",
    }


def base_major(major_id, name, degree, source_url):
    return {
        "id": major_id,
        "university": "University of Washington Seattle",
        "name": name,
        "degree": degree,
        "catalogYear": "AUT 2026 entrant framework",
        "totalCredits": 180,
        "sources": [
            {"label": f"UW Engineering {name} degree requirements and sample plan", "url": source_url},
            {"label": "UW Engineering ENGRUD placement requirements", "url": "https://www.engr.washington.edu/admission/department/comparemajors"},
            {"label": "UW course-description catalog", "url": "https://www.washington.edu/students/crscat/"},
        ],
        "tracks": [{"id": "standard", "name": "Standard degree path", "description": "Official AUT26 degree structure."}],
        "courseOverrides": deepcopy(COMMON_OVERRIDES),
        "prerequisiteSubstitutions": deepcopy(SUBSTITUTIONS),
    }


def plan(**quarters):
    keys = [
        "y1-autumn", "y1-winter", "y1-spring", "y2-autumn", "y2-winter", "y2-spring",
        "y3-autumn", "y3-winter", "y3-spring", "y4-autumn", "y4-winter", "y4-spring",
    ]
    return {key: quarters.get(key.replace("-", "_"), []) for key in keys}


majors = []

# ---------------------------------------------------------------------------
# Aeronautics & Astronautics
# ---------------------------------------------------------------------------
aa_core = [
    "AA 301", "AA 302", "AA 310", "AA 311", "AA 312", "AA 320", "AA 321", "AA 322",
    "AA 331", "AA 332", "AA 395", "AA 447", "AA 460",
]
aa_design = ["AA 410", "AA 411", "AA 420", "AA 421"]
aa_electives = [code for code in catalog_codes("AA", 400, 499) if code not in aa_core + aa_design]
aa = base_major(
    "uw-seattle-aa", "Aeronautics & Astronautics", "Bachelor of Science in Aeronautical and Astronautical Engineering",
    "https://www.engr.washington.edu/current/academics/4-year-plans/aa-degree-requirements",
)
aa["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "shortLabel": "E-FIG", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "27 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "MATH 208", "MATH 224"]},
    {"id": "science", "label": "Sciences", "credits": "25 cr", "courses": ["CHEM 142", "CHEM 143", "CHEM 145", "CHEM 152", "ME 123", "CSE 160", "PHYS 121", "PHYS 122", "PHYS 123", "PHYS 141", "PHYS 142", "PHYS 143"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "29–41 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "4 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "20 cr", "courses": ["AA 210", "AA 260", "CEE 220", "ME 230", "AMATH 301"]},
    {"id": "core", "label": "Major Core Requirements", "credits": "54 cr", "courses": aa_core + aa_design},
    {"id": "electives", "label": "Senior Technical Electives", "credits": "15 cr", "courses": aa_electives},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
aa["requirements"] = [
    placement_requirement(["AMATH 301", "CHEM 152", "ME 123", "PHYS 122", "PHYS 123"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "27 cr", "targetCredits": 27, "type": "group", "items": paths_calculus() + [{"id": "math224", "label": "Advanced multivariable calculus", "type": "all", "courses": ["MATH 224"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "25 cr", "targetCredits": 25, "type": "group", "items": [
        {"id": "chem-first", "label": "General chemistry", "type": "one", "courses": ["CHEM 142", "CHEM 143", "CHEM 145"]},
        {"id": "science-choice", "label": "Additional approved natural science", "type": "one", "courses": ["CHEM 152", "CHEM 153", "CHEM 155", "ME 123", "CSE 160"]},
        {"id": "physics", "label": "Calculus-based physics sequence", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122", "PHYS 123"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142", "PHYS 143"]}]},
    ]},
    gen_ed("29–41 cr", 4, ["AA 321", "AA 322"]),
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "20 cr", "targetCredits": 20, "type": "group", "items": [{"id": "fund-fixed", "label": "Required engineering fundamentals", "type": "all", "courses": ["AA 210", "AA 260", "CEE 220", "ME 230", "AMATH 301"]}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "54 cr", "targetCredits": 54, "type": "group", "items": [
        {"id": "aa-core-fixed", "label": "Required A&A core", "type": "all", "courses": aa_core},
        {"id": "aa-design", "label": "Aircraft or spacecraft design sequence", "type": "path-choice", "paths": [{"label": "Aircraft design", "courses": ["AA 410", "AA 411"]}, {"label": "Spacecraft and space-systems design", "courses": ["AA 420", "AA 421"]}]},
    ]},
    {"id": "aa-electives", "title": "Senior Technical Electives", "displayCredits": "15 cr", "targetCredits": 15, "type": "pool", "minCredits": 15, "courses": aa_electives, "note": "Designated 400-level AA courses not used elsewhere in the degree."},
    total_requirement(),
]
aa["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "CHEM 152", "SLOT:English Composition"],
    y1_spring=["MATH 126", "PHYS 121", "SLOT:A&H / SSc"],
    y2_autumn=["MATH 207", "PHYS 122", "AA 210", "SLOT:A&H / SSc"],
    y2_winter=["MATH 208", "PHYS 123", "ME 230", "SLOT:A&H / SSc"],
    y2_spring=["AA 260", "CEE 220", "MATH 224", "AMATH 301"],
    y3_autumn=["AA 310", "AA 311", "AA 320", "AA 395", "SLOT:A&H / SSc"],
    y3_winter=["AA 302", "AA 312", "AA 321", "AA 331"],
    y3_spring=["AA 301", "AA 322", "AA 332", "AA 447"],
    y4_autumn=["AA 460", "SLOT:AA Technical Elective", "SLOT:AA Technical Elective", "SLOT:AA Technical Elective"],
    y4_winter=["SLOT:AA 410 or AA 420", "SLOT:AA Technical Elective", "SLOT:AA Technical Elective", "SLOT:Free Elective"],
    y4_spring=["SLOT:AA 411 or AA 421", "SLOT:Free Elective", "SLOT:A&H / SSc", "SLOT:Free Elective"],
)}
majors.append((aa, "aeronautics-astronautics.json", "BSAAE"))

# ---------------------------------------------------------------------------
# Bioengineering
# ---------------------------------------------------------------------------
bioe_core = ["BIOEN 315", "BIOEN 316", "BIOEN 317", "BIOEN 325", "BIOEN 326", "BIOEN 327", "BIOEN 335", "BIOEN 336", "BIOEN 337", "BIOEN 345", "BIOEN 400"]
bioe_electives = [
    code for code in catalog_codes("BIOEN", 400, 499)
    if code not in bioe_core + ["BIOEN 401", "BIOEN 402", "BIOEN 404", "BIOEN 405"]
]
bioe = base_major("uw-seattle-bioe", "Bioengineering", "Bachelor of Science in Bioengineering", "https://www.engr.washington.edu/current/academics/4-year-plans/bioe-degree-requirements")
bioe["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "24–28 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "IND E 315", "STAT 311", "STAT 390", "Q SCI 381"]},
    {"id": "science", "label": "Sciences", "credits": "44 cr", "courses": ["CHEM 142", "CHEM 152", "CHEM 162", "CHEM 143", "CHEM 153", "CHEM 145", "CHEM 155", "CHEM 165", "CHEM 223", "CHEM 237", "PHYS 121", "PHYS 122", "PHYS 141", "PHYS 142", "BIOL 180", "BIOL 200", "BIOL 220"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "29–41 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "4 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "4–5 cr", "courses": ["AMATH 301", "CSE 121", "CSE 122", "CSE 123", "CSE 160", "BIOEN 217"]},
    {"id": "core", "label": "Major Core Requirements", "credits": "37 cr", "courses": ["BIOEN 215", "ENGR 115"] + bioe_core},
    {"id": "senior-electives", "label": "Senior Electives", "credits": "15 cr", "courses": bioe_electives},
    {"id": "capstone", "label": "Capstone", "credits": "7–10 cr", "courses": ["BIOEN 401", "BIOEN 402", "BIOEN 404", "BIOEN 405"]},
    {"id": "approved-engineering", "label": "Approved Engineering Electives", "credits": "9–12 cr", "courses": [], "requirementRefs": [map_ref("approved-engineering", "Approved engineering elective credits", "9–12 cr", "requirement")]},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
bioe["requirements"] = [
    placement_requirement(["BIOEN 215", "ENGR 115", "AMATH 301", "CSE 121", "CSE 122", "CSE 160", "CHEM 152", "CHEM 162", "PHYS 122"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "24–28 cr", "targetCredits": 24, "type": "group", "items": paths_calculus() + [{"id": "statistics", "label": "Approved probability or statistics", "type": "one", "courses": ["IND E 315", "STAT 311", "STAT 390", "Q SCI 381"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "44 cr", "targetCredits": 44, "type": "group", "items": [
        {"id": "chemistry-sequence", "label": "General chemistry sequence", "type": "path-choice", "paths": [{"label": "Standard chemistry", "courses": ["CHEM 142", "CHEM 152", "CHEM 162"]}, {"label": "Accelerated chemistry", "courses": ["CHEM 143", "CHEM 153", "CHEM 162"]}, {"label": "Honors chemistry", "courses": ["CHEM 145", "CHEM 155", "CHEM 165"]}]},
        {"id": "organic", "label": "Organic chemistry", "type": "one", "courses": ["CHEM 223", "CHEM 237"]},
        {"id": "physics", "label": "Mechanics and electromagnetism", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142"]}]},
        {"id": "biology", "label": "Introductory biology sequence", "type": "all", "courses": ["BIOL 180", "BIOL 200", "BIOL 220"]},
    ]},
    gen_ed("29–41 cr", 4, ["BIOEN 401", "BIOEN 402", "BIOEN 404", "BIOEN 405"]),
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "4–5 cr", "targetCredits": 4, "type": "group", "items": [{"id": "programming", "label": "Scientific computing or programming path", "type": "path-choice", "paths": [{"label": "AMATH 301", "courses": ["AMATH 301"]}, {"label": "CSE 121 + BIOEN 217", "courses": ["CSE 121", "BIOEN 217"]}, {"label": "CSE 122 + BIOEN 217", "courses": ["CSE 122", "BIOEN 217"]}, {"label": "CSE 123 + BIOEN 217", "courses": ["CSE 123", "BIOEN 217"]}, {"label": "CSE 160 + BIOEN 217", "courses": ["CSE 160", "BIOEN 217"]}]}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "37 cr", "targetCredits": 37, "type": "group", "items": [{"id": "bioe-intro", "label": "Introductory BioE course", "type": "one", "courses": ["BIOEN 215", "ENGR 115"]}, {"id": "bioe-core-fixed", "label": "Required Bioengineering core", "type": "all", "courses": bioe_core}]},
    {"id": "senior-electives", "title": "Senior Electives", "displayCredits": "15 cr", "targetCredits": 15, "type": "pool", "minCredits": 15, "courses": bioe_electives, "note": "Approved 400-level and above BIOEN-prefixed engineering courses."},
    {"id": "capstone", "title": "Capstone", "displayCredits": "7–10 cr", "targetCredits": 7, "type": "group", "items": [
        {"id": "bioe-capstone", "label": "Capstone sequence", "type": "path-choice", "paths": [{"label": "Integrated design and research", "courses": ["BIOEN 401", "BIOEN 402"]}, {"label": "Team design", "courses": ["BIOEN 404", "BIOEN 405"]}]}
    ]},
    {"id": "approved-engineering", "title": "Approved Engineering Electives", "displayCredits": "9–12 cr", "targetCredits": 9, "type": "manual", "manualLabel": "Approved engineering elective credits completed", "maxCredits": 12, "note": "Option A requires 9 credits and Option B requires 12. Use the current BioE-approved list and enter the completed credits here."},
    total_requirement(),
]
bioe["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "CHEM 152", "SLOT:English Composition"],
    y1_spring=["MATH 126", "CHEM 162", "PHYS 121"],
    y2_autumn=["BIOL 180", "CHEM 223", "BIOEN 215", "SLOT:A&H / SSc"],
    y2_winter=["BIOL 200", "AMATH 301", "SLOT:A&H / SSc / DIV"],
    y2_spring=["MATH 207", "BIOEN 315", "BIOEN 316", "BIOEN 317", "PHYS 122"],
    y3_autumn=["BIOEN 325", "BIOEN 326", "BIOEN 327", "MATH 208", "SLOT:A&H / SSc"],
    y3_winter=["BIOEN 335", "BIOEN 336", "BIOEN 337", "BIOL 220", "IND E 315"],
    y3_spring=["BIOEN 345", "BIOEN 400", "SLOT:BIOEN Elective", "SLOT:A&H / SSc", "BIOEN 401"],
    y4_autumn=["BIOEN 402", "SLOT:BIOEN Elective", "SLOT:Engineering Elective", "SLOT:A&H / SSc / Writing"],
    y4_winter=["BIOEN 402", "SLOT:BIOEN Elective", "SLOT:BIOEN Elective", "SLOT:A&H / SSc"],
    y4_spring=["BIOEN 402", "SLOT:BIOEN Elective", "SLOT:Engineering Elective", "SLOT:General Elective / Writing"],
)}
majors.append((bioe, "bioengineering.json", "BSBioE"))

# ---------------------------------------------------------------------------
# Chemical Engineering
# ---------------------------------------------------------------------------
cheme_core = ["CHEM E 310", "CHEM E 325", "CHEM E 326", "CHEM E 330", "CHEM E 340", "CHEM E 375", "CHEM E 435", "CHEM E 436", "CHEM E 437", "CHEM E 457", "CHEM E 465", "CHEM E 480", "CHEM E 485", "CHEM E 486"]
cheme = base_major("uw-seattle-cheme", "Chemical Engineering", "Bachelor of Science in Chemical Engineering", "https://www.engr.washington.edu/current/academics/4-year-plans/cheme-degree-requirements")
cheme["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "24–27 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "IND E 315", "MATH 209", "STAT 390", "MATH 224", "AMATH 353"]},
    {"id": "science", "label": "Sciences", "credits": "41 cr", "courses": ["CHEM 142", "CHEM 152", "CHEM 162", "CHEM 143", "CHEM 153", "CHEM 145", "CHEM 155", "CHEM 165", "CHEM 237", "CHEM 223", "CHEM 238", "CHEM 224", "CHEM E 456", "CHEM 455", "PHYS 121", "PHYS 122", "PHYS 123", "PHYS 141", "PHYS 142", "PHYS 143"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "29–41 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "4 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "core", "label": "Major Core Requirements", "credits": "54 cr", "courses": cheme_core},
    {"id": "molecular", "label": "Molecular & Nanoscience Engineering", "credits": "3 cr", "courses": ["CHEM E 455", "CHEM E 460"]},
    {"id": "electives", "label": "Engineering Electives", "credits": "16 cr", "courses": [], "requirementRefs": [map_ref("engineering-electives", "Approved engineering elective credits", "16 cr", "requirement")]},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
cheme["requirements"] = [
    placement_requirement([], chem152_required=True),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "24–27 cr", "targetCredits": 24, "type": "group", "items": paths_calculus() + [{"id": "math-elective", "label": "Approved mathematics elective", "type": "one", "courses": ["IND E 315", "MATH 209", "STAT 390", "MATH 224", "AMATH 353"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "41 cr", "targetCredits": 41, "type": "group", "items": [
        {"id": "chem-sequence", "label": "General chemistry sequence", "type": "path-choice", "paths": [{"label": "Standard chemistry", "courses": ["CHEM 142", "CHEM 152", "CHEM 162"]}, {"label": "Accelerated chemistry", "courses": ["CHEM 143", "CHEM 153", "CHEM 162"]}, {"label": "Honors chemistry", "courses": ["CHEM 145", "CHEM 155", "CHEM 165"]}]},
        {"id": "organic-sequence", "label": "Organic chemistry sequence", "type": "path-choice", "paths": [{"label": "CHEM 237–238", "courses": ["CHEM 237", "CHEM 238"]}, {"label": "CHEM 223–224", "courses": ["CHEM 223", "CHEM 224"]}]},
        {"id": "physical-chemistry", "label": "Physical or quantum chemistry", "type": "one", "courses": ["CHEM E 456", "CHEM 455"]},
        {"id": "physics", "label": "Calculus-based physics sequence", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122", "PHYS 123"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142", "PHYS 143"]}]},
    ]},
    gen_ed("29–41 cr", 4, ["CHEM E 436", "CHEM E 437", "CHEM E 485", "CHEM E 486"]),
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "54 cr", "targetCredits": 54, "type": "group", "items": [{"id": "cheme-core", "label": "Required Chemical Engineering core", "type": "all", "courses": cheme_core}]},
    {"id": "molecular", "title": "Molecular and Nanoscience Engineering", "displayCredits": "3 cr", "targetCredits": 3, "type": "group", "items": [{"id": "molecular-choice", "label": "Laboratory choice", "type": "one", "courses": ["CHEM E 455", "CHEM E 460"]}]},
    {"id": "engineering-electives", "title": "Engineering Electives", "displayCredits": "16 cr", "targetCredits": 16, "type": "manual", "manualLabel": "Approved engineering elective credits completed", "note": "Use the current Chemical Engineering approved-elective list and enter the completed credits here."},
    total_requirement(),
]
cheme["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "CHEM 152", "SLOT:English Composition"],
    y1_spring=["MATH 126", "CHEM 162", "PHYS 121"],
    y2_autumn=["MATH 207", "PHYS 122", "CHEM 237", "SLOT:A&H / SSc / DIV"],
    y2_winter=["PHYS 123", "CHEM 238", "MATH 208", "SLOT:Free Elective"],
    y2_spring=["CHEM E 310", "CHEM E 375", "SLOT:Math Elective", "SLOT:Free Elective"],
    y3_autumn=["CHEM E 325", "CHEM E 330", "CHEM E 456", "SLOT:A&H / SSc"],
    y3_winter=["CHEM E 326", "CHEM E 340", "SLOT:Engineering Elective", "SLOT:A&H / SSc"],
    y3_spring=["CHEM E 436", "CHEM E 457", "SLOT:Engineering Elective", "SLOT:A&H / SSc"],
    y4_autumn=["CHEM E 435", "CHEM E 455", "CHEM E 465", "SLOT:Free Elective"],
    y4_winter=["CHEM E 437", "CHEM E 485", "SLOT:Engineering Elective", "SLOT:Free Elective"],
    y4_spring=["CHEM E 486", "SLOT:Engineering Elective", "CHEM E 480"],
)}
majors.append((cheme, "chemical-engineering.json", "BSChemE"))

# ---------------------------------------------------------------------------
# Civil Engineering
# ---------------------------------------------------------------------------
cee_core = ["CEE 307", "CEE 317", "CEE 327", "CEE 337", "CEE 347", "CEE 357", "CEE 367", "CEE 377"]
cee_capstones = ["CEE 441", "CEE 442", "CEE 444", "CEE 445"]
cee_400 = [code for code in catalog_codes("CEE", 400, 499) if code not in cee_capstones]
cive = base_major("uw-seattle-cive", "Civil Engineering", "Bachelor of Science in Civil Engineering", "https://www.engr.washington.edu/current/academics/4-year-plans/cive-degree-requirements")
cive["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "24–28 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "IND E 315", "STAT 390", "Q SCI 381"]},
    {"id": "science", "label": "Sciences", "credits": "28–30 cr", "courses": ["CHEM 142", "CHEM 152", "CHEM 143", "CHEM 153", "CHEM 145", "CHEM 155", "PHYS 121", "PHYS 122", "PHYS 123", "PHYS 141", "PHYS 142", "PHYS 143"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "29–41 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("writing", "Writing", "7 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "4 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "economics", "label": "Economics", "credits": "4–5 cr", "courses": ["ECON 200", "IND E 250", "ESRM 235", "ECON 235", "ENVIR 235"]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "16 cr", "courses": ["AMATH 301", "CSE 121", "CSE 122", "CSE 123", "CSE 160", "AA 210", "CEE 220", "ME 230"]},
    {"id": "core", "label": "Major Core Requirements", "credits": "40 cr", "courses": cee_core},
    {"id": "practice", "label": "Professional Practice", "credits": "2 cr", "courses": ["CEE 200"]},
    {"id": "capstone", "label": "Capstone", "credits": "5 cr", "courses": cee_capstones},
    {"id": "tech", "label": "Civil Engineering Technical Electives", "credits": "15 cr", "courses": [], "requirementRefs": [map_ref("cive-tech", "Approved CEE technical elective credits", "15 cr", "requirement")]},
    {"id": "engineering-science", "label": "Engineering & Science Electives", "credits": "12–14 cr", "courses": [], "requirementRefs": [map_ref("cive-es", "Approved engineering and science elective credits", "12–14 cr", "requirement")]},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
cive["requirements"] = [
    placement_requirement(["AMATH 301", "CHEM 152", "CSE 122", "ME 123", "MSE 170", "PHYS 122", "PHYS 123"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "24–28 cr", "targetCredits": 24, "type": "group", "items": paths_calculus() + [{"id": "statistics", "label": "Approved probability or statistics", "type": "one", "courses": ["IND E 315", "STAT 390", "Q SCI 381"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "28–30 cr", "targetCredits": 28, "type": "group", "items": [
        {"id": "chemistry", "label": "General chemistry", "type": "path-choice", "paths": [{"label": "Standard chemistry", "courses": ["CHEM 142", "CHEM 152"]}, {"label": "Accelerated chemistry", "courses": ["CHEM 143", "CHEM 153"]}, {"label": "Honors chemistry", "courses": ["CHEM 145", "CHEM 155"]}]},
        {"id": "physics", "label": "Calculus-based physics", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122", "PHYS 123"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142", "PHYS 143"]}]},
        {"id": "basic-science", "label": "Approved basic science elective", "type": "bucket", "targetCredits": 3, "area": "NSc"},
    ]},
    gen_ed("29–41 cr", 4),
    {"id": "economics", "title": "Economics", "displayCredits": "4–5 cr", "targetCredits": 4, "type": "group", "items": [{"id": "economics-choice", "label": "Economics requirement", "type": "one", "courses": ["ECON 200", "IND E 250", "ESRM 235", "ECON 235", "ENVIR 235"]}]},
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "16 cr", "targetCredits": 16, "type": "group", "items": [{"id": "programming", "label": "Programming", "type": "one", "courses": ["AMATH 301", "CSE 121", "CSE 122", "CSE 123", "CSE 160"]}, {"id": "fund-fixed", "label": "Mechanics fundamentals", "type": "all", "courses": ["AA 210", "CEE 220", "ME 230"]}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "40 cr", "targetCredits": 40, "type": "group", "items": [{"id": "cive-core", "label": "Required Civil Engineering core", "type": "all", "courses": cee_core}]},
    {"id": "practice", "title": "Professional Practice", "displayCredits": "2 cr", "targetCredits": 2, "type": "group", "items": [{"id": "cee200", "label": "Introduction to Civil and Environmental Engineering", "type": "all", "courses": ["CEE 200"]}], "note": "The overview page lists this as a 2-credit section while CEE 200 is shown as 1 credit; confirm the current department rule."},
    {"id": "capstone", "title": "Capstone", "displayCredits": "5 cr", "targetCredits": 5, "type": "group", "items": [{"id": "capstone-choice", "label": "Capstone design project", "type": "one", "courses": cee_capstones}]},
    {"id": "cive-tech", "title": "Civil Engineering Technical Electives", "displayCredits": "15 cr", "targetCredits": 15, "type": "manual", "manualLabel": "Approved CEE technical elective credits completed", "note": "Use approved 400-level courses from at least three separate Civil Engineering areas of concentration."},
    {"id": "cive-es", "title": "Engineering and Science Electives", "displayCredits": "12–14 cr", "targetCredits": 12, "type": "manual", "manualLabel": "Approved engineering and science elective credits completed", "maxCredits": 14, "note": "Use the current department-approved list. A maximum of 3 credits of CEE 499 may apply."},
    total_requirement(),
]
cive["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "CHEM 152", "SLOT:Social Sciences"],
    y1_spring=["MATH 126", "PHYS 121", "SLOT:English Composition"],
    y2_autumn=["MATH 208", "PHYS 122", "AA 210", "IND E 250"],
    y2_winter=["MATH 207", "PHYS 123", "CEE 220"],
    y2_spring=["AMATH 301", "IND E 315", "ME 230", "SLOT:SSc and DIV"],
    y3_autumn=["CEE 317", "CEE 337", "CEE 377", "CEE 200"],
    y3_winter=["CEE 307", "CEE 347", "CEE 357"],
    y3_spring=["CEE 327", "CEE 367", "SLOT:CEE Technical Elective"],
    y4_autumn=["SLOT:CEE Technical Elective", "SLOT:CEE Technical Elective", "SLOT:CEE Technical Elective", "SLOT:Upper-Division Engineering & Science Elective"],
    y4_winter=["SLOT:Upper-Division Engineering & Science Elective", "SLOT:CEE Technical Elective", "SLOT:Basic Science Elective", "SLOT:A&H / SSc with Writing"],
    y4_spring=["SLOT:CEE Capstone", "SLOT:Upper-Division Engineering & Science Elective", "SLOT:Upper-Division Engineering & Science Elective", "SLOT:A&H with Writing"],
)}
majors.append((cive, "civil-engineering.json", "BSCivE"))

# ---------------------------------------------------------------------------
# Electrical & Computer Engineering
# ---------------------------------------------------------------------------
ece_core = ["EE 201", "EE 215", "EE 241", "CSE 163", "EE 242", "EE 271", "EE 280"]
ee_capstones = [code for code in catalog_codes("EE", 400, 499, ("capstone", "design")) if code not in ["EE 393"]]
ee_advanced = [
    code for code in unique(["EE 233", "CSE 373", "CSE 374", "ENGR 321"] + catalog_codes("EE", 300, 499))
    if code not in ee_capstones and code != "EE 393"
]
ece = base_major("uw-seattle-ece", "Electrical & Computer Engineering", "Bachelor of Science in Electrical and Computer Engineering", "https://www.engr.washington.edu/current/academics/4-year-plans/ece-degree-requirements")
ece["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "24–27 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "IND E 315", "STAT 390"]},
    {"id": "science", "label": "Sciences", "credits": "19–20 cr", "courses": ["CHEM 142", "CHEM 143", "CHEM 145", "PHYS 121", "PHYS 122", "PHYS 141", "PHYS 142", "BIOL 130", "BIOL 220", "MATH 224", "PHYS 123", "PHYS 143"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "41 cr", "courses": ["EE 393"], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("major-writing", "Additional Writing", "3 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "4 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "4–5 cr", "courses": ["CSE 123", "CSE 143"]},
    {"id": "core", "label": "Major Core Requirements", "credits": "22–24 cr", "courses": ece_core},
    {"id": "advanced", "label": "Advanced ECE Electives", "credits": "39 cr", "courses": ee_advanced},
    {"id": "capstone", "label": "Capstone", "credits": "4–8 cr", "courses": ee_capstones},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
ece["requirements"] = [
    placement_requirement(["CSE 121", "CSE 122", "CSE 123", "PHYS 122", "PHYS 123"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "24–27 cr", "targetCredits": 24, "type": "group", "items": paths_calculus() + [{"id": "statistics", "label": "Approved probability or statistics", "type": "one", "courses": ["IND E 315", "STAT 390"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "19–20 cr", "targetCredits": 19, "type": "group", "items": [
        {"id": "chem", "label": "General chemistry", "type": "one", "courses": ["CHEM 142", "CHEM 143", "CHEM 145"]},
        {"id": "physics", "label": "Mechanics and electromagnetism", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142"]}]},
        {"id": "science-choice", "label": "Additional approved science", "type": "one", "courses": ["BIOL 130", "BIOL 220", "MATH 224", "PHYS 123", "PHYS 143"]},
    ]},
    gen_ed("41 cr", 4, ["EE 393"], 5),
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "4–5 cr", "targetCredits": 4, "type": "group", "items": [{"id": "programming", "label": "Programming", "type": "one", "courses": ["CSE 123", "CSE 143"]}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "22–24 cr", "targetCredits": 22, "type": "group", "items": [
        {"id": "ece-fixed", "label": "Required ECE core", "type": "all", "courses": ["EE 201", "EE 215", "EE 242", "EE 271", "EE 280"]},
        {"id": "ece-programming", "label": "Signal and information programming", "type": "one", "courses": ["EE 241", "CSE 163"]},
    ]},
    {"id": "advanced", "title": "Advanced Electrical & Computer Engineering Electives", "displayCredits": "39 cr", "targetCredits": 39, "type": "pool", "minCredits": 39, "courses": ee_advanced, "note": "At least 20 credits must be at the 400 level. Seminar, ENGR 321, and EE 499 limits apply; verify pathway rules with ECE advising."},
    {"id": "capstone", "title": "Capstone", "displayCredits": "4–8 cr", "targetCredits": 4, "type": "pool", "minCredits": 4, "courses": ee_capstones, "note": "The approved capstone list changes; verify the current ECE list."},
    total_requirement(),
]
ece["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "SLOT:English Composition", "CSE 121"],
    y1_spring=["MATH 126", "PHYS 121", "SLOT:Diversity"],
    y2_autumn=["PHYS 122", "MATH 207", "CSE 122", "SLOT:Writing"],
    y2_winter=["MATH 208", "EE 215", "SLOT:Free Elective", "CSE 123"],
    y2_spring=["EE 280", "EE 241", "SLOT:Free Elective", "SLOT:A&H / SSc"],
    y3_autumn=["EE 242", "EE 271", "IND E 315", "SLOT:Free Elective"],
    y3_winter=["EE 201", "EE 393", "SLOT:Advanced ECE Elective", "SLOT:Additional Approved NSc"],
    y3_spring=["SLOT:Advanced ECE Elective", "SLOT:Advanced ECE Elective", "SLOT:A&H / SSc", "SLOT:Free Elective"],
    y4_autumn=["SLOT:Advanced ECE Elective", "SLOT:Advanced ECE Elective", "SLOT:Professional Issues", "SLOT:A&H / SSc"],
    y4_winter=["SLOT:Capstone", "SLOT:Advanced ECE Elective", "SLOT:Advanced ECE Elective"],
    y4_spring=["SLOT:Capstone", "SLOT:Advanced ECE Elective", "SLOT:A&H / SSc"],
)}
majors.append((ece, "electrical-computer-engineering.json", "BSECE"))

# ---------------------------------------------------------------------------
# Environmental Engineering
# ---------------------------------------------------------------------------
enve_core = ["CEE 347", "CEE 348", "CEE 349", "CEE 350", "CEE 352", "CEE 354", "CEE 356"]
enve_capstone = ["CEE 444", "CEE 445"]
enve_400 = [code for code in catalog_codes("CEE", 400, 499) if code not in enve_capstone]
enve = base_major("uw-seattle-enve", "Environmental Engineering", "Bachelor of Science in Environmental Engineering", "https://www.engr.washington.edu/current/academics/4-year-plans/enve-degree-requirements")
enve["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "24–28 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "IND E 315", "STAT 390", "Q SCI 381"]},
    {"id": "science", "label": "Sciences", "credits": "28–30 cr", "courses": ["BIOL 180", "CHEM 142", "CHEM 152", "CHEM 143", "CHEM 153", "CHEM 145", "CHEM 155", "PHYS 121", "PHYS 122", "PHYS 141", "PHYS 142"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "29–41 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("writing", "Writing", "7 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "4 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "economics", "label": "Economics", "credits": "4–5 cr", "courses": ["ECON 200", "IND E 250", "ESRM 235", "ECON 235", "ENVIR 235"]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "12–13 cr", "courses": ["AMATH 301", "CSE 121", "CSE 122", "CSE 123", "CSE 160", "AA 210", "AA 260", "ME 323"]},
    {"id": "core", "label": "Major Core Requirements", "credits": "30 cr", "courses": enve_core},
    {"id": "practice", "label": "Professional Practice", "credits": "2 cr", "courses": ["CEE 200"]},
    {"id": "capstone", "label": "Capstone", "credits": "5 cr", "courses": enve_capstone},
    {"id": "tech", "label": "Environmental Engineering Technical Electives", "credits": "15 cr", "courses": [], "requirementRefs": [map_ref("enve-tech", "Approved EnvE technical elective credits", "15 cr", "requirement")]},
    {"id": "engineering-science", "label": "Engineering & Science Electives", "credits": "13 cr", "courses": [], "requirementRefs": [map_ref("enve-es", "Approved engineering and science elective credits", "13 cr", "requirement")]},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
enve["requirements"] = [
    placement_requirement(["AMATH 301", "CHEM 152", "CHEM 162", "CSE 122", "CSE 160", "PHYS 122", "PHYS 123"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "24–28 cr", "targetCredits": 24, "type": "group", "items": paths_calculus() + [{"id": "statistics", "label": "Approved probability or statistics", "type": "one", "courses": ["IND E 315", "STAT 390", "Q SCI 381"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "28–30 cr", "targetCredits": 28, "type": "group", "items": [
        {"id": "bio", "label": "Introductory biology", "type": "all", "courses": ["BIOL 180"]},
        {"id": "chemistry", "label": "General chemistry", "type": "path-choice", "paths": [{"label": "Standard chemistry", "courses": ["CHEM 142", "CHEM 152"]}, {"label": "Accelerated chemistry", "courses": ["CHEM 143", "CHEM 153"]}, {"label": "Honors chemistry", "courses": ["CHEM 145", "CHEM 155"]}]},
        {"id": "physics", "label": "Mechanics and electromagnetism", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142"]}]},
        {"id": "basic-science", "label": "Approved basic science elective", "type": "bucket", "targetCredits": 3, "area": "NSc"},
    ]},
    gen_ed("29–41 cr", 4),
    {"id": "economics", "title": "Economics", "displayCredits": "4–5 cr", "targetCredits": 4, "type": "group", "items": [{"id": "economics-choice", "label": "Economics requirement", "type": "one", "courses": ["ECON 200", "IND E 250", "ESRM 235", "ECON 235", "ENVIR 235"]}]},
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "12–13 cr", "targetCredits": 12, "type": "group", "items": [{"id": "programming", "label": "Programming", "type": "one", "courses": ["AMATH 301", "CSE 121", "CSE 122", "CSE 123", "CSE 160"]}, {"id": "statics", "label": "Engineering statics", "type": "all", "courses": ["AA 210"]}, {"id": "thermo", "label": "Thermodynamics", "type": "one", "courses": ["AA 260", "ME 323"]}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "30 cr", "targetCredits": 30, "type": "group", "items": [{"id": "enve-core", "label": "Required Environmental Engineering core", "type": "all", "courses": enve_core}]},
    {"id": "practice", "title": "Professional Practice", "displayCredits": "2 cr", "targetCredits": 2, "type": "group", "items": [{"id": "cee200", "label": "Introduction to Civil and Environmental Engineering", "type": "all", "courses": ["CEE 200"]}], "note": "The overview page lists this as a 2-credit section while CEE 200 is shown as 1 credit; confirm the current department rule."},
    {"id": "capstone", "title": "Capstone", "displayCredits": "5 cr", "targetCredits": 5, "type": "group", "items": [{"id": "capstone-choice", "label": "Capstone design project", "type": "one", "courses": enve_capstone}]},
    {"id": "enve-tech", "title": "Environmental Engineering Technical Electives", "displayCredits": "15 cr", "targetCredits": 15, "type": "manual", "manualLabel": "Approved EnvE technical elective credits completed", "note": "Use the current department list of approved CEE 400-level coursework."},
    {"id": "enve-es", "title": "Engineering & Science Electives", "displayCredits": "13 cr", "targetCredits": 13, "type": "manual", "manualLabel": "Approved engineering and science elective credits completed", "note": "Use the current department-approved list of additional CEE 400-level courses."},
    total_requirement(),
]
enve["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "CHEM 152", "SLOT:English Composition"],
    y1_spring=["MATH 126", "CHEM 162", "PHYS 121"],
    y2_autumn=["AMATH 351", "PHYS 122", "AA 210", "SLOT:A&H / SSc"],
    y2_winter=["AMATH 352", "SLOT:Basic Science Elective", "SLOT:A&H / SSc with Writing"],
    y2_spring=["AMATH 301", "BIOL 180", "AA 260", "SLOT:Basic Science Elective"],
    y3_autumn=["CEE 349", "CEE 350", "CEE 352", "CEE 200"],
    y3_winter=["CEE 347", "CEE 354", "IND E 315"],
    y3_spring=["CEE 348", "CEE 356", "IND E 250", "SLOT:Technical Elective"],
    y4_autumn=["SLOT:Technical Elective", "SLOT:Technical Elective", "SLOT:Engineering & Science Elective", "SLOT:A&H / SSc"],
    y4_winter=["SLOT:Engineering & Science Elective", "SLOT:Technical Elective", "SLOT:Diversity", "SLOT:A&H / SSc with Writing"],
    y4_spring=["SLOT:CEE 444 or CEE 445", "SLOT:Technical Elective", "SLOT:Engineering & Science Elective", "SLOT:Engineering & Science Elective"],
)}
majors.append((enve, "environmental-engineering.json", "BSEnvE"))

# ---------------------------------------------------------------------------
# Human Centered Design & Engineering
# ---------------------------------------------------------------------------
hcde_core = ["HCDE 302", "HCDE 303", "HCDE 308", "HCDE 310", "HCDE 313", "HCDE 321", "HCDE 322", "HCDE 351", "HCDE 492", "HCDE 493"]
hcde_choice = ["HCDE 315", "HCDE 316"]
hcde_experience = ["ENGR 321", "ENGR 490", "HCDE 496", "HCDE 497", "HCDE 499"]
hcde_upper = [code for code in catalog_codes("HCDE", 300, 499) if code not in hcde_core + hcde_choice + hcde_experience]
hcde_fundamentals = ["AA 210", "AMATH 301", "BIOEN 215", "CEE 220", "CSE 163", "CSE 180", "EE 215", "ENGR 115", "ME 123", "ME 230", "MSE 170", "NME 220"]
hcde = base_major("uw-seattle-hcde", "Human Centered Design & Engineering", "Bachelor of Science in Human Centered Design and Engineering", "https://www.engr.washington.edu/current/academics/4-year-plans/hcde-degree-requirements")
hcde["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics & Statistics", "credits": "15–20 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "STAT 290", "STAT 311", "Q SCI 381", "STAT 220"]},
    {"id": "science", "label": "Sciences & Additional Math/Science", "credits": "30–35 cr", "courses": ["CHEM 142", "CHEM 143", "CHEM 145", "PHYS 121", "PHYS 141", "CHEM 152", "CHEM 162", "PHYS 122", "PHYS 123", "PHYS 142", "PHYS 143"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "35 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("writing", "Writing", "7 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "10 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "12 cr", "courses": ["CSE 121", "CSE 122", "CSE 123", "CSE 160"] + hcde_fundamentals},
    {"id": "core", "label": "Major Core Requirements", "credits": "46 cr", "courses": hcde_core + hcde_choice},
    {"id": "experience", "label": "Experiential Learning", "credits": "2 cr", "courses": hcde_experience},
    {"id": "electives", "label": "HCDE Electives", "credits": "23 cr", "courses": hcde_upper},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
hcde["requirements"] = [
    placement_requirement(["AMATH 301", "BIOEN 215", "CHEM 152", "CHEM 162", "CSE 121", "CSE 122", "CSE 123", "CSE 160", "ENGR 115", "ME 123", "MSE 170", "PHYS 122", "PHYS 123", "STAT 220"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics and Statistics", "displayCredits": "15–20 cr", "targetCredits": 15, "type": "group", "items": paths_calculus(include_linear_diff=False) + [{"id": "statistics", "label": "Approved statistics course", "type": "one", "courses": ["STAT 290", "STAT 311", "Q SCI 381", "STAT 220"]}]},
    {"id": "science", "title": "Sciences and Additional Math/Statistics/Science", "displayCredits": "30–35 cr", "targetCredits": 30, "type": "group", "items": [
        {"id": "chem", "label": "General chemistry", "type": "one", "courses": ["CHEM 142", "CHEM 143", "CHEM 145"]},
        {"id": "physics", "label": "Mechanics", "type": "one", "courses": ["PHYS 121", "PHYS 141"]},
        {"id": "additional-mss", "label": "Additional approved math, statistics, or science", "type": "pool", "minCredits": 15, "courses": unique(["CHEM 152", "CHEM 162", "PHYS 122", "PHYS 123", "PHYS 142", "PHYS 143"] + catalog_codes(("MATH", "STAT", "Q SCI", "BIOL", "CHEM", "PHYS"), 100, 499))},
    ]},
    gen_ed("35 cr", 10),
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "12 cr", "targetCredits": 12, "type": "group", "items": [{"id": "programming", "label": "Programming course", "type": "one", "courses": ["CSE 121", "CSE 122", "CSE 123", "CSE 160"]}, {"id": "fund-electives", "label": "Additional engineering fundamentals", "type": "pool", "minCredits": 8, "courses": hcde_fundamentals}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "46 cr", "targetCredits": 46, "type": "group", "items": [{"id": "hcde-fixed", "label": "Required HCDE core", "type": "all", "courses": hcde_core}, {"id": "inclusive-sustainable", "label": "Inclusive or sustainable design", "type": "one", "courses": hcde_choice}]},
    {"id": "experience", "title": "Experiential Learning", "displayCredits": "2 cr", "targetCredits": 2, "type": "pool", "minCredits": 2, "courses": hcde_experience},
    {"id": "hcde-electives", "title": "HCDE Electives", "displayCredits": "23 cr", "targetCredits": 23, "type": "pool", "minCredits": 23, "courses": hcde_upper, "note": "Complete 15 credits from HCDE engineering electives and 8 credits from the Systems and Society list. Confirm category placement on the current HCDE list."},
    total_requirement(),
]
hcde["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc / DIV"],
    y1_winter=["MATH 125", "SLOT:English Composition", "STAT 220"],
    y1_spring=["MATH 126", "PHYS 121", "CSE 121"],
    y2_autumn=["SLOT:Arts & Humanities", "SLOT:Approved Natural Science", "SLOT:Engineering Fundamentals", "SLOT:Free Elective"],
    y2_winter=["SLOT:Social Sciences", "SLOT:Approved Math / Statistics / Science", "SLOT:Engineering Fundamentals", "SLOT:A&H or SSc"],
    y2_spring=["SLOT:SSc / Writing", "SLOT:Approved Math / Statistics / Science", "SLOT:Arts & Humanities"],
    y3_autumn=["HCDE 310", "HCDE 302", "HCDE 313"],
    y3_winter=["HCDE 303", "HCDE 315", "HCDE 321", "HCDE 496"],
    y3_spring=["HCDE 351", "HCDE 308", "HCDE 322", "SLOT:Free Elective"],
    y4_autumn=["SLOT:HCDE Elective", "SLOT:HCDE Elective", "SLOT:Approved Math / Science", "SLOT:Free Elective"],
    y4_winter=["HCDE 492", "SLOT:HCDE Engineering Elective", "SLOT:HCDE Engineering Elective", "SLOT:Free Elective"],
    y4_spring=["HCDE 493", "SLOT:HCDE Systems & Society Elective", "SLOT:A&H / SSc"],
)}
majors.append((hcde, "human-centered-design-engineering.json", "BSHCDE"))

# ---------------------------------------------------------------------------
# Industrial Engineering
# ---------------------------------------------------------------------------
ise_core = ["IND E 310", "IND E 311", "IND E 316", "IND E 321", "IND E 337", "IND E 338", "IND E 351", "IND E 491", "IND E 494", "IND E 495"]
ise_area_a = ["IND E 430", "IND E 439"]
ise_area_b = ["IND E 412", "IND E 427", "IND E 455"]
ise_electives = [code for code in catalog_codes("IND E", 300, 499) if code not in ise_core + ise_area_a + ise_area_b + ["IND E 315"]]
ise = base_major("uw-seattle-ise", "Industrial Engineering", "Bachelor of Science in Industrial Engineering", "https://www.engr.washington.edu/current/academics/4-year-plans/ise-degree-requirements")
ise["mapGroups"] = [
    {"id": "placement", "label": "ENGRUD Placement", "credits": "After Year 1", "courses": [], "requirementRefs": [map_ref("engrud-placement", "ENGRUD placement checkpoint", "After Year 1", "requirement")]},
    {"id": "efig", "label": "Engineering First-year Interest Group", "credits": "2 cr", "courses": ["ENGR 101", "GEN ST 199"]},
    {"id": "math", "label": "Mathematics", "credits": "24–27 cr", "courses": ["MATH 124", "MATH 125", "MATH 126", "MATH 134", "MATH 135", "MATH 136", "MATH 207", "AMATH 351", "MATH 208", "AMATH 352", "IND E 315"]},
    {"id": "science", "label": "Sciences", "credits": "25 cr", "courses": ["CHEM 142", "CHEM 152", "CHEM 143", "CHEM 153", "CHEM 145", "CHEM 155", "PHYS 121", "PHYS 122", "PHYS 123", "PHYS 141", "PHYS 142", "PHYS 143"]},
    {"id": "general-education", "label": "General Education Requirements", "credits": "34–40 cr", "courses": [], "requirementRefs": [map_ref("english-comp", "English Composition", "5 cr"), map_ref("major-writing", "Writing met by IND E 337", "4 cr"), map_ref("ah", "Arts & Humanities", "10 cr"), map_ref("ssc", "Social Sciences", "10 cr"), map_ref("areas-extra", "Additional A&H or SSc", "10 cr"), map_ref("div", "Diversity", "5 cr")]},
    {"id": "fundamentals", "label": "Engineering Fundamentals", "credits": "28 cr", "courses": ["AA 210", "CSE 122", "CEE 220", "EE 215", "IND E 250", "ME 230", "MSE 170"]},
    {"id": "core", "label": "Major Core Requirements", "credits": "37 cr", "courses": ise_core},
    {"id": "production", "label": "Production Requirement", "credits": "4 cr", "courses": ise_area_a},
    {"id": "systems", "label": "Systems Requirement", "credits": "4 cr", "courses": ise_area_b},
    {"id": "electives", "label": "Technical Electives", "credits": "16 cr", "courses": ise_electives},
    {"id": "free", "label": "Free Electives", "credits": "To reach 180 cr", "courses": [], "requirementRefs": [map_ref("total", "Total degree credits", "180 cr", "requirement")]},
]
ise["requirements"] = [
    placement_requirement(["CHEM 152", "CSE 122", "PHYS 122", "PHYS 123"]),
    efig_requirement(),
    {"id": "math", "title": "Mathematics", "displayCredits": "24–27 cr", "targetCredits": 24, "type": "group", "items": paths_calculus() + [{"id": "statistics", "label": "Probability and statistics for engineers", "type": "all", "courses": ["IND E 315"]}]},
    {"id": "science", "title": "Sciences", "displayCredits": "25 cr", "targetCredits": 25, "type": "group", "items": [{"id": "chemistry", "label": "General chemistry", "type": "path-choice", "paths": [{"label": "Standard chemistry", "courses": ["CHEM 142", "CHEM 152"]}, {"label": "Accelerated chemistry", "courses": ["CHEM 143", "CHEM 153"]}, {"label": "Honors chemistry", "courses": ["CHEM 145", "CHEM 155"]}]}, {"id": "physics", "label": "Calculus-based physics", "type": "path-choice", "paths": [{"label": "Standard physics", "courses": ["PHYS 121", "PHYS 122", "PHYS 123"]}, {"label": "Honors physics", "courses": ["PHYS 141", "PHYS 142", "PHYS 143"]}]}]},
    gen_ed("34–40 cr", 10, ["IND E 337"]),
    {"id": "fundamentals", "title": "Engineering Fundamentals", "displayCredits": "28 cr", "targetCredits": 28, "type": "group", "items": [{"id": "fund-fixed", "label": "Required engineering fundamentals", "type": "all", "courses": ["AA 210", "CSE 122", "CEE 220", "EE 215", "IND E 250", "ME 230", "MSE 170"]}]},
    {"id": "core", "title": "Major Core Requirements", "displayCredits": "37 cr", "targetCredits": 37, "type": "group", "items": [{"id": "ise-core", "label": "Required Industrial Engineering core", "type": "all", "courses": ise_core}]},
    {"id": "production", "title": "Production Requirement", "displayCredits": "4 cr", "targetCredits": 4, "type": "group", "items": [{"id": "production-choice", "label": "Production course", "type": "one", "courses": ise_area_a}]},
    {"id": "systems", "title": "Systems Requirement", "displayCredits": "4 cr", "targetCredits": 4, "type": "group", "items": [{"id": "systems-choice", "label": "Systems course", "type": "one", "courses": ise_area_b}]},
    {"id": "technical-electives", "title": "Technical Electives", "displayCredits": "16 cr", "targetCredits": 16, "type": "pool", "minCredits": 16, "courses": ise_electives, "note": "Candidate IND E technical electives are displayed. Confirm the department-approved list."},
    total_requirement(),
]
ise["samplePlan"] = {"name": "Official AUT26 sample four-year plan", "quarters": plan(
    y1_autumn=["MATH 124", "CHEM 142", "ENGR 101", "GEN ST 199", "SLOT:A&H / SSc"],
    y1_winter=["MATH 125", "CHEM 152", "SLOT:English Composition"],
    y1_spring=["MATH 126", "PHYS 121", "CSE 122"],
    y2_autumn=["PHYS 122", "AA 210", "MATH 207", "SLOT:A&H / SSc / Writing"],
    y2_winter=["PHYS 123", "MATH 208", "CEE 220", "SLOT:A&H / SSc"],
    y2_spring=["IND E 250", "ME 230", "MSE 170", "IND E 315"],
    y3_autumn=["IND E 337", "IND E 310", "IND E 491", "EE 215", "SLOT:A&H / SSc"],
    y3_winter=["IND E 311", "IND E 316", "IND E 338", "SLOT:A&H / SSc"],
    y3_spring=["IND E 321", "IND E 351", "SLOT:IND E 412 or Technical Elective", "SLOT:A&H / SSc"],
    y4_autumn=["SLOT:IND E 430 or IND E 439", "SLOT:IND E 427 / 455 / Technical Elective", "SLOT:IND E Technical Elective", "SLOT:A&H / SSc"],
    y4_winter=["IND E 494", "SLOT:IND E Technical Elective", "SLOT:A&H / SSc"],
    y4_spring=["IND E 495", "SLOT:IND E Technical Elective", "SLOT:A&H / SSc / DIV"],
)}
majors.append((ise, "industrial-engineering.json", "BSIE"))

# ---------------------------------------------------------------------------
# Write all files and update the index without removing other majors.
# ---------------------------------------------------------------------------
MAJOR_DIR.mkdir(parents=True, exist_ok=True)
index = load_json(INDEX_FILE)
existing = {item.get("id"): item for item in index.get("majors", [])}

for major, filename, degree_code in majors:
    save_json(MAJOR_DIR / filename, major)
    existing[major["id"]] = {
        "id": major["id"],
        "name": major["name"],
        "degree": degree_code,
        "status": "complete",
        "file": filename,
        "source": major["sources"][0]["url"],
    }
    print(f"Created data/majors/{filename}")

# Preserve the original order, replacing matching entries in place, then append any new IDs.
ordered = []
seen = set()
for item in index.get("majors", []):
    major_id = item.get("id")
    if major_id in existing:
        ordered.append(existing[major_id])
        seen.add(major_id)
for major, _, _ in majors:
    if major["id"] not in seen:
        ordered.append(existing[major["id"]])
        seen.add(major["id"])
# Preserve custom majors such as Computer Science and LSJ even if they were appended later.
for major_id, item in existing.items():
    if major_id not in seen:
        ordered.append(item)
        seen.add(major_id)

index["majors"] = ordered
save_json(INDEX_FILE, index)
print("Updated data/majors/index.json")
print(f"Added {len(majors)} engineering majors.")