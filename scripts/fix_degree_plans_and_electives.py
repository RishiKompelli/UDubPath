from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from datetime import date
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "scripts" else Path.cwd()
APP_JS = ROOT / "src" / "app.js"
STYLES = ROOT / "src" / "styles.css"
MAJOR_DIR = ROOT / "data" / "majors"
CATALOG_FILES = [ROOT / "data" / "catalog-live.json", ROOT / "data" / "catalog-fallback.json"]

MSE_TECH = [
    "MSE 450", "MSE 452", "MSE 462", "MSE 463", "MSE 466", "MSE 471",
    "MSE 473", "MSE 474", "MSE 475", "MSE 476", "MSE 477", "MSE 478",
    "MSE 479", "MSE 481", "MSE 482", "MSE 483", "MSE 484", "MSE 486",
    "MSE 487", "MSE 488", "MSE 489", "MSE 490", "MSE 498", "MSE 499",
]
MSE_EXTERNAL = [
    "AMATH 352", "AMATH 353", "AMATH 383", "AMATH 401", "AMATH 403",
    "BIOC 405", "BIOC 406", "CHEM 312", "CHEM 455", "CHEM 456", "CHEM 457",
    "CHEM E 341", "ENGR 321", "ENVIR 480", "PHYS 321", "PHYS 324",
    "PHYS 325", "PHYS 334", "PHYS 335", "PHYS 434", "PHYS 441",
    "ENTRE 370", "ENTRE 440",
]
BIOE_ENGINEERING = [
    "AA 210", "AMATH 422", "AMATH 423", "AMATH 424", "AMATH 481", "AMATH 482", "AMATH 483",
    "CHEM E 310", "CHEM E 326", "CHEM E 375", "CHEM E 445", "CHEM E 457", "CHEM E 465", "NME 220",
    "CEE 220", "CEE 350", "CEE 357", "CEE 480", "CEE 495",
    "CSE 122", "CSE 123", "CSE 154", "CSE 160", "CSE 373", "CSE 410", "CSE 427",
    "EE 215", "EE 233", "EE 235", "EE 242", "EE 271", "EE 341", "EE 401", "EE 484", "EE 485",
    "IND E 250", "IND E 337", "IND E 351", "IND E 426", "IND E 470",
    "ME 123", "ME 230", "ME 410", "ME 414", "ME 461", "ME 478", "ME 498",
    "MSE 170", "MSE 273", "MSE 450", "MSE 471", "MSE 481", "MSE 482", "MSE 483",
]
CHEME_ENGINEERING = [
    "AMATH 301", "AA 210", "BIOEN 215", "BIOEN 420", "BIOEN 440", "BIOEN 467", "BIOEN 488",
    "BIOEN 490", "BIOEN 491", "BIOEN 492", "BSE 406", "BSE 420", "BSE 426", "BSE 430",
    "BSE 436", "BSE 480", "BSE 481", "CHEM E 301", "CHEM E 341", "CHEM E 355",
    "CHEM E 434", "CHEM E 440", "CHEM E 458", "CHEM E 467", "CHEM E 476", "CHEM E 477",
    "CHEM E 484", "CHEM E 490", "CHEM E 491", "CHEM E 497", "CHEM E 499", "CHEM E 511",
    "CHEM E 562", "CHEM E 563", "CHEM 429", "CHEM 460", "CEE 220", "CEE 291", "CEE 307",
    "CEE 327", "CEE 337", "CEE 348", "CEE 349", "CEE 352", "CEE 354", "CEE 356", "CEE 357",
    "CEE 367", "CEE 377", "CEE 390", "CEE 409", "CEE 420", "CEE 462", "CEE 480", "CEE 482",
    "CEE 484", "CEE 487", "CEE 488", "CEE 490", "CEE 493", "CSE 143", "CSE 160", "CSE 163",
    "CSE 373", "CSE 410", "CSE 412", "CSE 413", "CSE 414", "CSE 416", "CSE 417", "EE 215",
    "EE 233", "EE 235", "EE 486", "IND E 250", "IND E 315", "MSE 170", "MSE 298", "MSE 333",
    "MSE 463", "MSE 481", "MSE 483", "ME 123", "ME 230", "ME 341", "ME 373", "ME 374",
    "ME 406", "ME 410", "ME 414", "ME 416", "ME 426", "ME 430", "ME 469", "ME 471",
    "ME 559", "ME 568", "ENGR 321",
]
CIVIL_TECH = [
    "CEE 402", "CEE 403", "CEE 409", "CEE 410", "CEE 412", "CEE 415", "CEE 416", "CEE 419",
    "CEE 420", "CEE 422", "CEE 424", "CEE 433", "CEE 434", "CEE 436", "CEE 437", "CEE 451",
    "CEE 452", "CEE 453", "CEE 454", "CEE 457", "CEE 459", "CEE 462", "CEE 463", "CEE 465",
    "CEE 467", "CEE 473", "CEE 474", "CEE 475", "CEE 476", "CEE 477", "CEE 478", "CEE 480",
    "CEE 481", "CEE 482", "CEE 483", "CEE 484", "CEE 498", "CEE 499", "CEE 378",
]
ENVE_TECH = [
    "CEE 402", "CEE 403", "CEE 409", "CEE 415", "CEE 420", "CEE 424", "CEE 432", "CEE 437",
    "CEE 459", "CEE 462", "CEE 465", "CEE 467", "CEE 473", "CEE 474", "CEE 475", "CEE 476",
    "CEE 477", "CEE 478", "CEE 480", "CEE 481", "CEE 482", "CEE 483", "CEE 498", "CEE 499",
]
EXPLICIT_ES = [
    "AA 260", "BIOL 180", "BIOL 200", "BIOL 220", "CEE 220", "CEE 291", "CHEM 162", "CHEM 165",
    "CHEM 223", "CHEM 224", "CHEM 237", "CHEM 238", "CHEM 239", "EE 215", "ME 123", "ME 230",
    "MSE 170", "PHYS 123", "PHYS 224", "PHYS 225", "PHYS 227", "PHYS 228", "ENGR 321", "ENGR 322",
    "ENGR 498", "CEE 428", "CEE 499",
]


def unique(values):
    return list(dict.fromkeys(v for v in values if v))


def normalize_code(value: str) -> str:
    value = str(value or "").strip().upper()
    value = re.sub(r"^M E\s+", "ME ", value)
    value = re.sub(r"^A A\s+", "AA ", value)
    value = re.sub(r"^E E\s+", "EE ", value)
    value = re.sub(r"^MS E\s+", "MSE ", value)
    return re.sub(r"\s+", " ", value)


def numeric_credits(value) -> float:
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    return float(match.group()) if match else 0.0


def load_catalog():
    for path in CATALOG_FILES:
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            courses = payload.get("courses", []) if isinstance(payload, dict) else []
            return {normalize_code(c.get("code")): c for c in courses if c.get("campus") == "Seattle"}
    return {}


def course_level(code: str) -> int:
    match = re.search(r"(\d{3})", code)
    return int(match.group(1)) if match else 0


def catalog_engineering_science_pool(catalog):
    departments = ("AA ", "CHEM E ", "CSE ", "IND E ", "ME ", "MSE ")
    result = []
    for code in catalog:
        level = course_level(code)
        if 300 <= level <= 499 and code.startswith(departments):
            result.append(code)
        if code.startswith("CEE ") and 300 <= level <= 499 and code not in {"CEE 440", "CEE 444", "CEE 445"}:
            result.append(code)
    return unique(EXPLICIT_ES + sorted(result))


def backup(path: Path):
    backup_path = path.with_suffix(path.suffix + ".before-degree-audit")
    if path.exists() and not backup_path.exists():
        shutil.copy2(path, backup_path)


def patch_app_js():
    text = APP_JS.read_text(encoding="utf-8")
    backup(APP_JS)

    if "pendingPlanSlot:" not in text:
        text = text.replace("  mapRenderToken: 0\n};", "  mapRenderToken: 0,\n  pendingPlanSlot: null\n};")

    helper_marker = "function isPlanSlot(item) {"
    if helper_marker not in text:
        helpers = r'''
function isPlanSlot(item) {
  return String(item || "").startsWith("SLOT:");
}

function parsePlanSlot(item) {
  if (!isPlanSlot(item)) return null;
  const payload = String(item).slice(5);
  const match = payload.match(/^(\d+(?:\.\d+)?):(.*)$/);
  if (match) return { credits: Number(match[1]), label: match[2].trim(), raw: item };
  return { credits: 0, label: payload.trim(), raw: item };
}

function migrateLegacyPlanSlots() {
  const queues = new Map();
  for (const items of Object.values(app.major.samplePlan?.quarters || {})) {
    for (const item of items) {
      const slot = parsePlanSlot(item);
      if (!slot) continue;
      if (!queues.has(slot.label)) queues.set(slot.label, []);
      queues.get(slot.label).push(item);
    }
  }
  let changed = false;
  for (const quarter of QUARTERS) {
    app.progress.plan[quarter.id] = (app.progress.plan[quarter.id] || []).map((item) => {
      if (!isPlanSlot(item) || /^SLOT:\d+(?:\.\d+)?:/.test(item)) return item;
      const label = parsePlanSlot(item).label;
      const replacement = queues.get(label)?.shift();
      if (replacement) {
        changed = true;
        return replacement;
      }
      return item;
    });
  }
  if (changed) saveProgress();
}

function plannedCourseCodes() {
  return [...new Set(Object.values(app.progress.plan).flat().filter((item) => !isPlanSlot(item)).map(normalizeCode))];
}

function slotPoolDefinition(slot) {
  return app.major.plannerSlotPools?.[slot.label] || {};
}

function courseMatchesSlot(course, slot) {
  const definition = slotPoolDefinition(slot);
  const code = normalizeCode(course.code);
  const listed = (definition.courses || []).map(normalizeCode);
  if (listed.length && !listed.includes(code)) return false;
  const departments = definition.departments || [];
  if (departments.length && !departments.some((department) => code.startsWith(normalizeCode(department) + " "))) return false;
  const minimumLevel = Number(definition.minimumLevel || 0);
  if (minimumLevel) {
    const level = Number(code.match(/\d{3}/)?.[0] || 0);
    if (level < minimumLevel) return false;
  }
  const areas = definition.areas || [];
  if (areas.length && !areas.some((area) => areaMatches(course, area))) return false;
  const explicitCodes = [...slot.label.matchAll(/\b(?:AA|A A|AMATH|BIOEN|CHEM E|CHEM|CEE|CSE|EE|E E|ENGR|HCDE|IND E|MATH|ME|M E|MSE|MS E|NME|PHYS|STAT)\s+\d{3}[A-Z]?\b/gi)].map((match) => normalizeCode(match[0]));
  if (explicitCodes.length && !explicitCodes.includes(code)) return false;
  return true;
}

function beginFillPlanSlot(item, quarterId) {
  app.pendingPlanSlot = { item, quarterId };
  const slot = parsePlanSlot(item);
  const quarterSelect = $("#planner-add-quarter");
  if (quarterSelect) quarterSelect.value = quarterId;
  const input = $("#planner-add-search");
  if (input) {
    input.value = "";
    input.placeholder = `Search a course for ${slot.label}`;
    input.focus();
  }
  updatePlannerSearchResults();
  renderPlanner();
  showToast(`Choose a course to replace “${slot.label}”.`);
}

function clearPendingPlanSlot() {
  app.pendingPlanSlot = null;
  const input = $("#planner-add-search");
  if (input) input.placeholder = "Search a course to add to your plan";
}

'''
        text = text.replace("function renderPlanner() {", helpers + "function renderPlanner() {")


    if "migrateLegacyPlanSlots();" not in text:
        text = text.replace(
            "    app.progress = loadProgress();\n    buildCatalogIndexes();",
            "    app.progress = loadProgress();\n    migrateLegacyPlanSlots();\n    buildCatalogIndexes();",
            1,
        )

    text = re.sub(
        r"function plannedCredits\(\) \{.*?\n\}",
        '''function plannedCredits() {
  return Object.values(app.progress.plan).flat().reduce((total, item) => {
    const slot = parsePlanSlot(item);
    return total + (slot ? slot.credits : numericCredits(getCourse(item).credits));
  }, 0);
}''',
        text,
        count=1,
        flags=re.S,
    )

    if 'const addButton = $("#planner-add-button");' not in text:
        text = re.sub(
            r"function renderPlanner\(\) \{\n",
            '''function renderPlanner() {
  const addButton = $("#planner-add-button");
  if (addButton) addButton.textContent = app.pendingPlanSlot ? "Use course for requirement" : "Add course";
''',
            text,
            count=1,
        )

    text = re.sub(
        r'''function renderPlanItem\(item, quarterId, hasWarning\) \{\n  if \(item\.startsWith\("SLOT:"\)\) \{.*?\n  \}\n  const course = getCourse\(item\);''',
        '''function renderPlanItem(item, quarterId, hasWarning) {
  if (isPlanSlot(item)) {
    const slot = parsePlanSlot(item);
    return `<div class="plan-course slot" draggable="true" data-plan-item="${escapeHtml(item)}" data-from-quarter="${quarterId}">
      <div class="plan-code">Requirement · ${formatNumber(slot.credits)} cr</div>
      <div class="plan-title">${escapeHtml(slot.label)}</div>
      <button class="slot-fill" type="button" data-fill-slot="${escapeHtml(item)}" data-quarter="${quarterId}">Choose course</button>
      <button class="plan-remove" type="button" data-remove-plan="${escapeHtml(item)}" data-quarter="${quarterId}" aria-label="Remove">×</button>
    </div>`;
  }
  const course = getCourse(item);''',
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r"function quarterCredits\(quarterId\) \{.*?\n\}",
        '''function quarterCredits(quarterId) {
  return (app.progress.plan[quarterId] || []).reduce((sum, item) => {
    const slot = parsePlanSlot(item);
    return sum + (slot ? slot.credits : numericCredits(getCourse(item).credits));
  }, 0);
}''',
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r"function updatePlannerSearchResults\(\) \{.*?\n\}",
        '''function updatePlannerSearchResults() {
  const input = $("#planner-add-search");
  const select = $("#planner-add-results");
  if (!input || !select) return;
  const query = input.value.trim().toLowerCase();
  const pendingSlot = app.pendingPlanSlot ? parsePlanSlot(app.pendingPlanSlot.item) : null;
  let matches = app.courses.filter((course) => course.campus === "Seattle");
  if (pendingSlot) matches = matches.filter((course) => courseMatchesSlot(course, pendingSlot));
  if (query) {
    matches = matches.filter((course) => `${course.code} ${course.title}`.toLowerCase().includes(query));
  } else if (!pendingSlot) {
    const majorCodes = new Set(allMajorCodes());
    matches = matches.filter((course) => majorCodes.has(normalizeCode(course.code)));
  }
  matches = matches.slice(0, 60);
  const prompt = pendingSlot ? `Choose a course for ${pendingSlot.label}…` : "Choose a matching course…";
  select.innerHTML = `<option value="">${escapeHtml(prompt)}</option>${matches.map((course) => `<option value="${escapeHtml(course.code)}">${escapeHtml(course.code)} — ${escapeHtml(course.title)} (${escapeHtml(course.credits || "?")} cr)</option>`).join("")}`;
}''',
        text,
        count=1,
        flags=re.S,
    )

    text = re.sub(
        r"function addPlannerSearchCourse\(\) \{.*?\n\}",
        '''function addPlannerSearchCourse() {
  const code = $("#planner-add-results").value;
  const quarter = $("#planner-add-quarter").value;
  if (!code) return showToast("Choose a course first.");
  if (app.pendingPlanSlot) {
    const { item, quarterId } = app.pendingPlanSlot;
    app.progress.plan[quarterId] = (app.progress.plan[quarterId] || []).filter((entry) => entry !== item);
    clearPendingPlanSlot();
    addCourseToPlan(code, quarterId);
    return;
  }
  addCourseToPlan(code, quarter);
}''',
        text,
        count=1,
        flags=re.S,
    )

    if "data-fill-slot" not in re.search(r"function handlePlannerClick\(event\) \{.*?\n\}", text, re.S).group(0):
        text = text.replace(
            "function handlePlannerClick(event) {\n",
            '''function handlePlannerClick(event) {
  const fillSlot = event.target.closest("[data-fill-slot]");
  if (fillSlot) {
    event.stopPropagation();
    beginFillPlanSlot(fillSlot.dataset.fillSlot, fillSlot.dataset.quarter);
    return;
  }
''',
            1,
        )

    text = text.replace('filter((item) => !item.startsWith("SLOT:"))', 'filter((item) => !isPlanSlot(item))')
    text = text.replace('if (!item.startsWith("SLOT:")) planIndex.set(item, index);', 'if (!isPlanSlot(item)) planIndex.set(item, index);')
    text = text.replace('if (code.startsWith("SLOT:")) continue;', 'if (isPlanSlot(code)) continue;')
    text = text.replace('const normalized = code.startsWith("SLOT:") ? code : normalizeCode(code);', 'const normalized = isPlanSlot(code) ? code : normalizeCode(code);')

    text = text.replace(
        '<p class="requirement-note">Requirement slots from the sample plan have no credit value until you replace them with an actual course.</p>',
        '<p class="requirement-note"><strong>${formatNumber(plannedCredits())} / ${app.major.totalCredits}</strong> credits are represented. Requirement placeholders already carry credit values; use “Choose course” to replace each one with an actual UW course.</p>'
    )

    text = text.replace(
        'app.progress.plan = emptyPlan();\n  for (const [quarter, items] of Object.entries(app.major.samplePlan.quarters))',
        'app.progress.plan = emptyPlan();\n  clearPendingPlanSlot();\n  for (const [quarter, items] of Object.entries(app.major.samplePlan.quarters))'
    )

    APP_JS.write_text(text, encoding="utf-8")


def patch_styles():
    text = STYLES.read_text(encoding="utf-8")
    backup(STYLES)
    if ".slot-fill" not in text:
        text += '''

.slot-fill {
  margin-top: 8px;
  border: 1px solid var(--line-strong, #b7c2d0);
  border-radius: 8px;
  background: var(--surface, #fff);
  color: inherit;
  padding: 6px 9px;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}
.slot-fill:hover { transform: translateY(-1px); }
.plan-course.slot { border-style: dashed; }
'''
    STYLES.write_text(text, encoding="utf-8")


def find_requirement(major, requirement_id):
    return next((r for r in major.get("requirements", []) if r.get("id") == requirement_id), None)


def set_pool(major, requirement_id, courses, credits=None, note=None):
    requirement = find_requirement(major, requirement_id)
    if not requirement:
        return False
    requirement["type"] = "pool"
    requirement["courses"] = unique(map(normalize_code, courses))
    if credits is not None:
        requirement["targetCredits"] = credits
        requirement["minCredits"] = credits
    else:
        requirement["minCredits"] = requirement.get("targetCredits", requirement.get("minCredits", 0))
    requirement.pop("manualLabel", None)
    if note:
        requirement["note"] = note
    return True


def set_map_group_courses(major, group_ids, courses):
    for group in major.get("mapGroups", []):
        if group.get("id") in group_ids:
            group["courses"] = unique(group.get("courses", []) + list(courses))


def patch_elective_pools(major, catalog):
    major_id = major.get("id")
    es_pool = catalog_engineering_science_pool(catalog)

    if major_id == "uw-seattle-mse":
        standard = find_requirement(major, "tech-standard") or find_requirement(major, "technical-electives")
        total = unique(MSE_TECH + MSE_EXTERNAL)
        if standard:
            standard.update({
                "type": "group", "targetCredits": 15, "displayCredits": "15 cr",
                "items": [
                    {"id": "mse-tech-min", "label": "At least 6 credits of MSE technical electives", "type": "pool", "minCredits": 6, "courses": MSE_TECH},
                    {"id": "mse-tech-total", "label": "At least 15 approved technical-elective credits", "type": "pool", "minCredits": 15, "courses": total,
                     "note": "A maximum of 9 credits may come from approved courses outside MSE."},
                ],
            })
            standard.pop("courses", None)
        set_map_group_courses(major, {"options", "technical-electives", "tech"}, total)
        major.setdefault("sources", []).append({"label": "UW MSE approved technical electives", "url": "https://mse.washington.edu/current/undergrad/courses"})

    elif major_id == "uw-seattle-bioe":
        set_pool(major, "approved-engineering", BIOE_ENGINEERING, 9,
                 "Complete 9–12 credits from the department-approved engineering elective list; the exact amount depends on capstone choice.")
        set_map_group_courses(major, {"engineering-electives", "approved-engineering", "options"}, BIOE_ENGINEERING)

    elif major_id == "uw-seattle-cheme":
        set_pool(major, "engineering-electives", CHEME_ENGINEERING, 16,
                 "Complete 16 credits from the current UW Chemical Engineering approved engineering-elective list.")
        set_map_group_courses(major, {"engineering-electives", "options", "electives"}, CHEME_ENGINEERING)

    elif major_id == "uw-seattle-cive":
        set_pool(major, "cive-tech", CIVIL_TECH, 15,
                 "Complete 15 credits and include courses from at least three Civil Engineering areas of emphasis.")
        set_pool(major, "cive-es", es_pool, 12,
                 "Complete 12 approved upper-division engineering and science elective credits. Department exclusions and petition rules still apply.")
        set_map_group_courses(major, {"tech", "technical-electives"}, CIVIL_TECH)
        set_map_group_courses(major, {"engineering-science", "es-electives"}, es_pool)

    elif major_id == "uw-seattle-enve":
        set_pool(major, "enve-tech", ENVE_TECH, 15,
                 "Complete 15 credits from the current BSENVE technical-elective list.")
        set_pool(major, "enve-es", es_pool, 13,
                 "Complete 13 approved engineering and science elective credits. Department exclusions and petition rules still apply.")
        set_map_group_courses(major, {"tech", "technical-electives"}, ENVE_TECH)
        set_map_group_courses(major, {"engineering-science", "es-electives"}, es_pool)


def requirement_course_pools(major):
    pools = []
    for requirement in major.get("requirements", []):
        title = f"{requirement.get('title', '')} {requirement.get('sectionTitle', '')}".lower()
        courses = list(requirement.get("courses", []))
        for item in requirement.get("items", []):
            courses += item.get("courses", [])
            for path in item.get("paths", []):
                courses += path.get("courses", [])
        if courses:
            pools.append((title, unique(map(normalize_code, courses))))
    return pools


def area_definition(label):
    upper = label.upper()
    areas = []
    if "COMPOSITION" in upper or "ENGL COMP" in upper:
        areas.append("C")
    if "WRITING" in upper:
        areas.append("W")
    if "A&H" in upper or "ARTS & HUMANITIES" in upper:
        areas.append("A&H")
    if "SSC" in upper or "SOCIAL SCI" in upper or "SOCIAL SCIENCES" in upper:
        areas.append("SSc")
    if "DIV" in upper or "DIVERSITY" in upper:
        areas.append("DIV")
    if "NSC" in upper or "NATURAL SCI" in upper or "BASIC SCI" in upper or "SCIENCE ELECTIVE" in upper:
        areas.append("NSc")
    return unique(areas)


def default_slot_credits(label, pool, credit_lookup):
    upper = label.upper()
    explicit = [normalize_code(x) for x in re.findall(r"(?:AA|A A|AMATH|BIOEN|CHEM E|CHEM|CEE|CSE|EE|E E|ENGR|HCDE|IND E|MATH|ME|M E|MSE|MS E|NME|PHYS|STAT)\s+\d{3}[A-Z]?", label, re.I)]
    explicit_values = [credit_lookup.get(code, 0) for code in explicit if credit_lookup.get(code, 0)]
    if explicit_values:
        return int(round(min(explicit_values)))
    if "COMPOSITION" in upper: return 5
    if any(word in upper for word in ["A&H", "SSC", "SOCIAL", "DIVERSITY", "DIV", "WRITING", "NATURAL SCI", "BASIC SCI"]): return 5
    if "CAPSTONE" in upper: return 5
    if "FREE ELECTIVE" in upper or "GENERAL ELECTIVE" in upper: return 3
    if "MATH ELECTIVE" in upper or "STATISTICS" in upper: return 3
    pool_values = [credit_lookup.get(code, 0) for code in pool if credit_lookup.get(code, 0)]
    if pool_values:
        return max(1, int(round(median(pool_values))))
    if "ELECTIVE" in upper or "ENGINEERING FUNDAMENTALS" in upper: return 3
    return 5


def pick_pool_for_label(label, pools):
    words = set(re.findall(r"[A-Z0-9]+", label.upper())) - {"SLOT", "OR", "AND", "THE", "COURSE", "APPROVED"}
    best = []
    best_score = 0
    for title, courses in pools:
        title_words = set(re.findall(r"[A-Z0-9]+", title.upper()))
        score = len(words & title_words)
        if "TECHNICAL" in words and "TECHNICAL" in title_words: score += 3
        if "ENGINEERING" in words and "ENGINEERING" in title_words: score += 2
        if "CAPSTONE" in words and "CAPSTONE" in title_words: score += 4
        if score > best_score:
            best_score = score
            best = courses
    return best if best_score else []


def quarter_course_total(items, credit_lookup):
    total = 0
    for item in items:
        if item.startswith("SLOT:"):
            match = re.match(r"SLOT:(\d+(?:\.\d+)?):", item)
            total += float(match.group(1)) if match else 0
        else:
            total += credit_lookup.get(normalize_code(item), 0)
    return total


def convert_and_balance_plan(major, catalog):
    sample = major.get("samplePlan")
    if not sample or not sample.get("quarters"):
        return []
    credit_lookup = {code: numeric_credits(course.get("credits")) for code, course in catalog.items()}
    for code, override in major.get("courseOverrides", {}).items():
        if numeric_credits(override.get("credits")):
            credit_lookup[normalize_code(code)] = numeric_credits(override.get("credits"))
    pools = requirement_course_pools(major)
    planner_pools = major.setdefault("plannerSlotPools", {})

    for quarter, items in sample["quarters"].items():
        converted = []
        for item in items:
            if not item.startswith("SLOT:"):
                converted.append(item)
                continue
            payload = item[5:]
            numeric_match = re.match(r"^(\d+(?:\.\d+)?):(.*)$", payload)
            label = numeric_match.group(2).strip() if numeric_match else payload.strip()
            pool = pick_pool_for_label(label, pools)
            credits = float(numeric_match.group(1)) if numeric_match else default_slot_credits(label, pool, credit_lookup)
            credit_value = int(credits) if float(credits).is_integer() else credits
            converted.append(f"SLOT:{credit_value}:{label}")
            definition = planner_pools.setdefault(label, {})
            if pool:
                definition["courses"] = pool
            areas = area_definition(label)
            if areas:
                definition["areas"] = areas
            if "FREE ELECTIVE" in label.upper() or "UNASSIGNED" in label.upper():
                definition["allowAny"] = True
        sample["quarters"][quarter] = converted

    total = sum(quarter_course_total(items, credit_lookup) for items in sample["quarters"].values())
    target = float(major.get("totalCredits", 180))

    if total > target:
        adjustable = []
        for quarter, items in sample["quarters"].items():
            for index, item in enumerate(items):
                match = re.match(r"SLOT:(\d+(?:\.\d+)?):(.*)$", item)
                if not match: continue
                credits = float(match.group(1)); label = match.group(2)
                upper = label.upper()
                priority = 0 if "FREE" in upper or "UNASSIGNED" in upper or "GENERAL ELECTIVE" in upper else 1 if any(x in upper for x in ["A&H", "SSC", "SOCIAL", "WRITING", "DIV"]) else 2
                adjustable.append((priority, quarter, index, credits, label))
        for _, quarter, index, credits, label in sorted(adjustable):
            if total <= target: break
            reduction = min(credits - 1, total - target)
            if reduction <= 0: continue
            new_credits = credits - reduction
            sample["quarters"][quarter][index] = f"SLOT:{int(new_credits) if new_credits.is_integer() else new_credits}:{label}"
            total -= reduction

    quarter_order = list(sample["quarters"])
    while total < target - 0.001:
        credits = min(5, target - total)
        lightest = min(quarter_order, key=lambda q: quarter_course_total(sample["quarters"][q], credit_lookup))
        label = "Unassigned graduation credits"
        sample["quarters"][lightest].append(f"SLOT:{int(credits) if float(credits).is_integer() else credits}:{label}")
        planner_pools.setdefault(label, {"allowAny": True})
        total += credits

    sample["creditTotal"] = round(total, 1)
    sample["note"] = "Every credit needed to reach the degree total is represented. Replace requirement placeholders with actual approved courses."
    return [f"sample plan totals {total:g}/{target:g} credits"]


def audit_major(major):
    issues = []
    if major.get("totalCredits") != 180:
        issues.append(f"totalCredits is {major.get('totalCredits')}, expected 180")
    sample_total = major.get("samplePlan", {}).get("creditTotal")
    if sample_total != 180:
        issues.append(f"sample plan totals {sample_total}, expected 180")
    for requirement in major.get("requirements", []):
        if requirement.get("type") == "pool" and requirement.get("minCredits", requirement.get("targetCredits", 0)) and not requirement.get("courses"):
            issues.append(f"empty elective pool: {requirement.get('id')}")
    return issues


def main():
    if not APP_JS.exists() or not MAJOR_DIR.exists():
        raise SystemExit("Run this script from the root of the UW Degree Mapper project.")
    catalog = load_catalog()
    patch_app_js()
    patch_styles()
    report = {"audited": str(date.today()), "majors": {}}

    for path in sorted(MAJOR_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        major = json.loads(path.read_text(encoding="utf-8"))
        backup(path)
        patch_elective_pools(major, catalog)
        notes = convert_and_balance_plan(major, catalog)
        issues = audit_major(major)
        major["dataAudit"] = {
            "auditedOn": str(date.today()),
            "degreeTotalChecked": 180,
            "samplePlanCredits": major.get("samplePlan", {}).get("creditTotal"),
            "officialPlanningNote": "Planning aid only; confirm substitutions, variable-credit courses, and changing elective approvals with the department adviser.",
        }
        path.write_text(json.dumps(major, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["majors"][major.get("id", path.stem)] = {"name": major.get("name"), "notes": notes, "issues": issues}
        status = "OK" if not issues else "CHECK: " + "; ".join(issues)
        print(f"{major.get('name', path.stem)}: {status}")

    report_path = ROOT / "data" / "degree-audit.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nUpdated planner code and {len(report['majors'])} major files.")
    print(f"Audit report: {report_path.relative_to(ROOT)}")
    print("Backups were created with the suffix .before-degree-audit")


if __name__ == "__main__":
    main()