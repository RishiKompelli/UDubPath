from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app.js"
STYLES = ROOT / "src" / "styles.css"


def backup(path: Path) -> None:
    target = path.with_name(path.name + ".before-summer-quarter")
    if not target.exists():
        shutil.copy2(path, target)


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(
        rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{.*?\n\}}(?=\n\nfunction\s|\n\nasync function\s|\n\nconst\s|\Z)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Could not find function {name} in src/app.js")
    return text[: match.start()] + replacement.rstrip() + text[match.end() :]


def replace_async_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(
        rf"async\s+function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{.*?\n\}}(?=\n\nfunction\s|\n\nasync function\s|\n\nconst\s|\Z)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Could not find async function {name} in src/app.js")
    return text[: match.start()] + replacement.rstrip() + text[match.end() :]


def patch_quarters(text: str) -> str:
    if 'id: "y1-summer"' in text:
        return text

    new_quarters = '''const QUARTERS = [
  { id: "y1-autumn", year: 1, season: "Autumn" },
  { id: "y1-winter", year: 1, season: "Winter" },
  { id: "y1-spring", year: 1, season: "Spring" },
  { id: "y1-summer", year: 1, season: "Summer" },
  { id: "y2-autumn", year: 2, season: "Autumn" },
  { id: "y2-winter", year: 2, season: "Winter" },
  { id: "y2-spring", year: 2, season: "Spring" },
  { id: "y2-summer", year: 2, season: "Summer" },
  { id: "y3-autumn", year: 3, season: "Autumn" },
  { id: "y3-winter", year: 3, season: "Winter" },
  { id: "y3-spring", year: 3, season: "Spring" },
  { id: "y3-summer", year: 3, season: "Summer" },
  { id: "y4-autumn", year: 4, season: "Autumn" },
  { id: "y4-winter", year: 4, season: "Winter" },
  { id: "y4-spring", year: 4, season: "Spring" },
  { id: "y4-summer", year: 4, season: "Summer" }
];'''

    pattern = re.compile(r"const QUARTERS = \[.*?\n\];", re.S)
    if not pattern.search(text):
        raise RuntimeError("Could not find the QUARTERS constant")
    return pattern.sub(new_quarters, text, count=1)


SUMMER_HELPERS = r'''
function summerQuarterForYear(year) {
  return QUARTERS.find((quarter) => quarter.year === Number(year) && quarter.season === "Summer");
}

function summerQuarterYear(quarterId) {
  const quarter = QUARTERS.find((entry) => entry.id === quarterId);
  return quarter?.season === "Summer" ? quarter.year : null;
}

function summerQuarterExpanded(year) {
  const numericYear = Number(year);
  const saved = app.progress?.summerExpanded?.[numericYear];
  if (typeof saved === "boolean") return saved;
  const summer = summerQuarterForYear(numericYear);
  return Boolean(summer && (app.progress?.plan?.[summer.id] || []).length);
}

function setSummerQuarterExpanded(year, expanded) {
  app.progress.summerExpanded = app.progress.summerExpanded || {};
  app.progress.summerExpanded[Number(year)] = Boolean(expanded);
}

function plannerSelectableQuarters(extraQuarterId = null) {
  return QUARTERS.filter((quarter) => (
    quarter.season !== "Summer"
    || summerQuarterExpanded(quarter.year)
    || quarter.id === extraQuarterId
  ));
}

function shortQuarterLabel(quarterId) {
  const quarter = QUARTERS.find((entry) => entry.id === quarterId);
  return quarter ? `Y${quarter.year} ${quarter.season}` : quarterId;
}

function requirementHasPlannedCourses(requirement) {
  const planned = Object.values(app.progress.plan || {})
    .flat()
    .filter((item) => !isPlanSlot(item))
    .map(normalizeCode)
    .filter((code) => !isFulfilled(code));

  if (requirement.type === "total") return planned.length > 0;

  for (const item of requirement.items || []) {
    const explicitCodes = [
      ...(item.courses || []),
      ...(item.paths || []).flatMap((path) => path.courses || [])
    ].map(normalizeCode);

    if (planned.some((code) => explicitCodes.includes(code))) return true;
    if (item.area && planned.some((code) => areaMatches(getCourse(code), item.area))) return true;
  }

  const requirementCodes = (requirement.courses || []).map(normalizeCode);
  return planned.some((code) => requirementCodes.includes(code));
}

function renderRequirementCourseChoice(code) {
  const normalized = normalizeCode(code);
  const planned = !isFulfilled(normalized) ? plannedQuarter(normalized) : null;
  return `
    <label class="requirement-course ${planned ? "planned" : ""}" title="${escapeHtml(getCourse(normalized).title)}">
      <input type="checkbox" data-requirement-course="${escapeHtml(normalized)}" ${isFulfilled(normalized) ? "checked" : ""}>
      <span>${escapeHtml(normalized)}</span>
      ${planned ? `<span class="requirement-course-planned">${escapeHtml(shortQuarterLabel(planned))}</span>` : ""}
    </label>`;
}
'''


def insert_helpers(text: str) -> str:
    if "function summerQuarterForYear(" in text:
        return text
    marker = "function createDefaultProgress() {"
    if marker not in text:
        raise RuntimeError("Could not find createDefaultProgress")
    return text.replace(marker, SUMMER_HELPERS.strip() + "\n\n" + marker, 1)


def patch_progress(text: str) -> str:
    if "summerExpanded: {}" not in text:
        text = text.replace(
            "    plan: emptyPlan(),\n",
            "    plan: emptyPlan(),\n    summerExpanded: {},\n",
            1,
        )

    load_line = "      plan: { ...defaults.plan, ...(parsed.plan || {}) },\n"
    if load_line in text and "...(parsed.summerExpanded || {})" not in text:
        text = text.replace(
            load_line,
            load_line + "      summerExpanded: { ...defaults.summerExpanded, ...(parsed.summerExpanded || {}) },\n",
            1,
        )

    import_line = "      plan: { ...defaults.plan, ...(parsed.progress.plan || {}) },\n"
    if import_line in text and "...(parsed.progress.summerExpanded || {})" not in text:
        text = text.replace(
            import_line,
            import_line + "      summerExpanded: { ...defaults.summerExpanded, ...(parsed.progress.summerExpanded || {}) },\n",
            1,
        )
    return text


POPULATE_QUARTERS = r'''function populateQuarterSelects(extraQuarterId = null) {
  const select = $("#planner-add-quarter");
  if (!select) return;
  const previous = extraQuarterId || select.value;
  const quarters = plannerSelectableQuarters(extraQuarterId);
  select.innerHTML = quarters.map((quarter) => (
    `<option value="${quarter.id}">Year ${quarter.year} · ${quarter.season}</option>`
  )).join("");
  if (quarters.some((quarter) => quarter.id === previous)) select.value = previous;
}'''


RENDER_PLANNER = r'''function renderPlanner() {
  const warnings = validatePlan();
  $("#planner-grid").innerHTML = [1, 2, 3, 4].map((year) => {
    const standardQuarters = QUARTERS.filter(
      (quarter) => quarter.year === year && quarter.season !== "Summer"
    );
    const summerQuarter = summerQuarterForYear(year);
    const summerOpen = summerQuarterExpanded(year);
    const yearQuarters = QUARTERS.filter((quarter) => quarter.year === year);
    const yearCredits = yearQuarters.reduce(
      (sum, quarter) => sum + quarterCredits(quarter.id),
      0
    );
    const summerCredits = summerQuarter ? quarterCredits(summerQuarter.id) : 0;
    const summerItems = summerQuarter ? (app.progress.plan[summerQuarter.id] || []).length : 0;
    const summerSummary = summerCredits
      ? ` · ${formatNumber(summerCredits)} cr`
      : summerItems
        ? ` · ${summerItems} item${summerItems === 1 ? "" : "s"}`
        : "";

    return `<section class="plan-year ${summerOpen ? "summer-open" : ""}">
      <div class="year-heading">
        <div class="year-heading-copy">
          <h2>Year ${year}</h2>
          <span>${formatNumber(yearCredits)} planned credits</span>
        </div>
        <button
          class="summer-quarter-toggle ${summerItems ? "has-content" : ""}"
          type="button"
          data-toggle-summer="${year}"
          aria-expanded="${summerOpen ? "true" : "false"}"
        >
          <span class="summer-toggle-symbol">${summerOpen ? "−" : "+"}</span>
          ${summerOpen ? "Hide Summer" : "Summer quarter"}${summerSummary}
        </button>
      </div>
      <div class="year-quarters ${summerOpen ? "has-summer" : ""}">
        ${standardQuarters.map((quarter) => renderQuarter(quarter, warnings)).join("")}
        ${summerOpen && summerQuarter ? renderQuarter(summerQuarter, warnings) : ""}
      </div>
    </section>`;
  }).join("");

  populateQuarterSelects();
  renderPlannerInsights(warnings);
  updatePlannerSearchResults();
}'''


HANDLE_PLANNER_CLICK = r'''function handlePlannerClick(event) {
  const summerToggle = event.target.closest("[data-toggle-summer]");
  if (summerToggle) {
    event.preventDefault();
    const year = Number(summerToggle.dataset.toggleSummer);
    setSummerQuarterExpanded(year, !summerQuarterExpanded(year));
    saveProgress();
    renderPlanner();
    return;
  }

  const fillSlot = event.target.closest("[data-fill-slot]");
  if (fillSlot) {
    event.stopPropagation();
    beginFillPlanSlot(fillSlot.dataset.fillSlot, fillSlot.dataset.quarter);
    return;
  }
  const remove = event.target.closest("[data-remove-plan]");
  if (remove) {
    event.stopPropagation();
    removePlanItem(remove.dataset.removePlan, remove.dataset.quarter);
    return;
  }
  const course = event.target.closest("[data-open-course]");
  if (course) {
    app.selectedCode = course.dataset.openCourse;
    switchView("map");
    renderMap();
    scrollNodeIntoView(app.selectedCode);
  }
}'''


LOAD_SAMPLE = r'''async function loadSamplePlan() {
  const ok = await confirmAction("Load the official sample plan? This replaces only your planned quarters. It does not mark any course fulfilled.", "Load sample plan");
  if (!ok) return;
  app.progress.plan = emptyPlan();
  app.progress.summerExpanded = {};
  for (const [quarter, items] of Object.entries(app.major.samplePlan.quarters)) {
    app.progress.plan[quarter] = [...items];
    const summerYear = summerQuarterYear(quarter);
    if (summerYear && items.length) setSummerQuarterExpanded(summerYear, true);
  }
  saveProgress();
  renderAll();
  showToast("Official sample plan loaded. Every course on the plan is automatically marked Planned; nothing is marked completed.");
}'''


CLEAR_PLAN = r'''async function clearPlan() {
  const ok = await confirmAction("Remove every course from the four-year plan? Fulfilled courses and requirement overrides will remain unchanged.", "Clear plan");
  if (!ok) return;
  app.progress.plan = emptyPlan();
  app.progress.summerExpanded = {};
  saveProgress();
  renderAll();
}'''


RENDER_REQUIREMENT_ITEM = r'''function renderRequirementItem(item, evaluation) {
  const courses = item.courses || [];
  const showManual = item.type === "bucket" || item.type === "additional-bucket";
  const plannedAreaCourses = item.area
    ? Object.values(app.progress.plan || {})
        .flat()
        .filter((entry) => !isPlanSlot(entry))
        .map(normalizeCode)
        .filter((code) => !isFulfilled(code) && areaMatches(getCourse(code), item.area))
    : [];
  const pathHtml = item.type === "path-choice" ? `<div class="requirement-paths">${(evaluation.paths || []).map((path) => `
    <div class="requirement-path ${path.satisfied ? "satisfied" : ""}">
      <div class="requirement-path-head"><strong>${escapeHtml(path.label)}</strong><span>${path.completed.length}/${path.courses.length}</span></div>
      <div class="requirement-course-list">${path.courses.map(renderRequirementCourseChoice).join("")}</div>
    </div>`).join("")}</div>` : "";
  return `<div id="requirement-item-${safeId(item.id)}" class="requirement-item ${evaluation.satisfied ? "satisfied" : ""}">
    <div class="requirement-item-head">
      <span class="requirement-item-title">${escapeHtml(item.label)}</span>
      <span class="requirement-item-status">${escapeHtml(evaluation.label)}</span>
    </div>
    ${pathHtml}
    ${courses.length ? `<div class="requirement-course-list">${courses.map(renderRequirementCourseChoice).join("")}</div>` : ""}
    ${plannedAreaCourses.length ? `<div class="requirement-planned-area"><strong>Planned:</strong> ${plannedAreaCourses.map((code) => `${escapeHtml(code)} · ${escapeHtml(shortQuarterLabel(plannedQuarter(code)))}`).join(" · ")}</div>` : ""}
    ${showManual ? manualCreditInput(item.id, app.progress.manualCredits[item.id] || 0, item.targetCredits) : ""}
    ${item.note ? `<p class="requirement-note">${escapeHtml(item.note)}</p>` : ""}
    <label class="requirement-manual"><input type="checkbox" data-requirement-override="${escapeHtml(item.id)}" ${app.progress.requirementOverrides[item.id] ? "checked" : ""}> Already fulfilled by another approved course or credit</label>
  </div>`;
}'''


def patch_add_course(text: str) -> str:
    pattern = re.compile(
        r"function\s+addCourseToPlan\s*\([^)]*\)\s*\{.*?\n\}(?=\n\nfunction\s|\n\nasync function\s|\Z)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Could not find addCourseToPlan")
    body = match.group(0)
    if "setSummerQuarterExpanded(summerYear, true);" in body:
        return text
    target = "  app.progress.plan = proposed;\n  saveProgress();"
    replacement = '''  app.progress.plan = proposed;
  const summerYear = summerQuarterYear(quarterId);
  if (summerYear) setSummerQuarterExpanded(summerYear, true);
  saveProgress();'''
    if target not in body:
        # Support the older, non-validation version.
        target = "  app.progress.plan[quarterId].push(normalized);\n  saveProgress();"
        replacement = '''  app.progress.plan[quarterId].push(normalized);
  const summerYear = summerQuarterYear(quarterId);
  if (summerYear) setSummerQuarterExpanded(summerYear, true);
  saveProgress();'''
    if target not in body:
        raise RuntimeError("Could not find the save point inside addCourseToPlan")
    body = body.replace(target, replacement, 1)
    return text[: match.start()] + body + text[match.end() :]


def patch_requirement_card(text: str) -> str:
    fn_pattern = re.compile(
        r"function\s+renderRequirementCard\s*\([^)]*\)\s*\{.*?\n\}(?=\n\nfunction\s|\n\nasync function\s|\Z)",
        re.S,
    )
    match = fn_pattern.search(text)
    if not match:
        raise RuntimeError("Could not find renderRequirementCard")
    body = match.group(0)
    if "const hasPlanned = requirementHasPlannedCourses(requirement);" not in body:
        body = body.replace(
            "  const percent = evaluation.target ? Math.min(100, (evaluation.current / evaluation.target) * 100) : 0;\n",
            "  const percent = evaluation.target ? Math.min(100, (evaluation.current / evaluation.target) * 100) : 0;\n  const hasPlanned = !evaluation.satisfied && requirementHasPlannedCourses(requirement);\n",
            1,
        )
    body = body.replace(
        'class="requirement-card ${evaluation.satisfied ? "complete" : ""}"',
        'class="requirement-card ${evaluation.satisfied ? "complete" : hasPlanned ? "planned" : ""}"',
    )
    body = body.replace(
        '${evaluation.satisfied ? "COMPLETE" : "IN PROGRESS"}',
        '${evaluation.satisfied ? "COMPLETE" : hasPlanned ? "PLANNED" : "IN PROGRESS"}',
    )
    return text[: match.start()] + body + text[match.end() :]


def patch_select_options(text: str) -> str:
    # Course detail panel.
    text = text.replace(
        '${QUARTERS.map((quarter) => `<option value="${quarter.id}" ${planQuarter === quarter.id ? "selected" : ""}>Year ${quarter.year} · ${quarter.season}</option>`).join("")}',
        '${plannerSelectableQuarters(planQuarter).map((quarter) => `<option value="${quarter.id}" ${planQuarter === quarter.id ? "selected" : ""}>Year ${quarter.year} · ${quarter.season}</option>`).join("")}',
    )
    # Catalog detail panel.
    text = text.replace(
        '${QUARTERS.map((quarter) => `<option value="${quarter.id}" ${planQuarter === quarter.id ? "selected" : ""}>Y${quarter.year} ${quarter.season}</option>`).join("")}',
        '${plannerSelectableQuarters(planQuarter).map((quarter) => `<option value="${quarter.id}" ${planQuarter === quarter.id ? "selected" : ""}>Y${quarter.year} ${quarter.season}</option>`).join("")}',
    )
    return text


def patch_insights(text: str) -> str:
    pattern = re.compile(
        r"function\s+renderPlannerInsights\s*\([^)]*\)\s*\{.*?\n\}(?=\n\nfunction\s|\n\nasync function\s|\Z)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Could not find renderPlannerInsights")
    body = match.group(0)
    body = body.replace(
        "  const totals = QUARTERS.map((quarter) => ({ quarter, credits: quarterCredits(quarter.id) }));",
        '''  const totals = QUARTERS
    .filter((quarter) => (
      quarter.season !== "Summer"
      || summerQuarterExpanded(quarter.year)
      || quarterCredits(quarter.id) > 0
    ))
    .map((quarter) => ({ quarter, credits: quarterCredits(quarter.id) }));''',
    )
    return text[: match.start()] + body + text[match.end() :]


def patch_app(text: str) -> str:
    text = patch_quarters(text)
    text = insert_helpers(text)
    text = patch_progress(text)
    text = replace_function(text, "populateQuarterSelects", POPULATE_QUARTERS)
    text = replace_function(text, "renderPlanner", RENDER_PLANNER)
    text = replace_function(text, "handlePlannerClick", HANDLE_PLANNER_CLICK)
    text = replace_async_function(text, "loadSamplePlan", LOAD_SAMPLE)
    text = replace_async_function(text, "clearPlan", CLEAR_PLAN)
    text = patch_add_course(text)
    text = replace_function(text, "renderRequirementItem", RENDER_REQUIREMENT_ITEM)
    text = patch_requirement_card(text)
    text = patch_select_options(text)
    text = patch_insights(text)
    text = text.replace(
        '    if (season === "Spring") return normalized.includes("sp");\n',
        '    if (season === "Spring") return normalized.includes("sp");\n    if (season === "Summer") return normalized.replaceAll("sp", "").includes("s");\n',
        1,
    )
    return text


STYLE_BLOCK = r'''

/* Optional Summer quarter in the four-year planner */
.year-heading-copy {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;
}

.summer-quarter-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 34px;
  padding: 7px 11px;
  border: 1px solid rgba(255, 255, 255, 0.34);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.09);
  color: white;
  font: inherit;
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
}

.summer-quarter-toggle:hover,
.summer-quarter-toggle:focus-visible {
  background: rgba(255, 255, 255, 0.18);
  outline: none;
}

.summer-quarter-toggle.has-content {
  border-color: rgba(255, 197, 54, 0.8);
}

.summer-toggle-symbol {
  display: grid;
  width: 20px;
  height: 20px;
  place-items: center;
  border-radius: 50%;
  background: white;
  color: var(--uw-purple);
  font-size: 16px;
  line-height: 1;
}

.year-quarters.has-summer {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.year-quarters.has-summer .quarter:nth-child(3) {
  border-right: 1px solid var(--line);
}

.requirement-card.planned {
  border-color: #cfc2e7;
  box-shadow: inset 0 3px 0 var(--uw-purple);
}

.requirement-course.planned {
  border-color: #c9b8e5;
  background: #f8f4ff;
}

.requirement-course-planned {
  padding: 2px 5px;
  border-radius: 999px;
  background: var(--uw-purple-soft);
  color: var(--uw-purple);
  font-size: 8px;
  font-weight: 900;
  white-space: nowrap;
}

.requirement-planned-area {
  margin-top: 8px;
  padding: 7px 9px;
  border: 1px solid #d9cdec;
  border-radius: 8px;
  background: #faf7ff;
  color: var(--uw-purple);
  font-size: 10px;
  line-height: 1.45;
}

@media (max-width: 1000px) {
  .year-heading {
    align-items: flex-start;
    gap: 10px;
  }

  .year-heading-copy {
    align-items: flex-start;
    flex-direction: column;
    gap: 3px;
  }

  .year-quarters.has-summer {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .year-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .summer-quarter-toggle {
    justify-content: center;
    width: 100%;
  }

  .year-quarters.has-summer {
    grid-template-columns: 1fr;
  }
}
'''


def main() -> None:
    if not APP.exists() or not STYLES.exists():
        raise SystemExit(
            "Run this script from the project it belongs to: "
            "py scripts\\add_collapsible_summer_and_planned_status.py"
        )

    backup(APP)
    backup(STYLES)

    app_text = APP.read_text(encoding="utf-8")
    app_text = patch_app(app_text)
    APP.write_text(app_text, encoding="utf-8")

    style_text = STYLES.read_text(encoding="utf-8")
    if "/* Optional Summer quarter in the four-year planner */" not in style_text:
        style_text += STYLE_BLOCK
    STYLES.write_text(style_text, encoding="utf-8")

    print("Added optional, collapsible Summer quarters to all four years.")
    print("Autumn, Winter, and Spring remain unchanged until Summer is expanded.")
    print("Courses placed in any quarter now appear as Planned on the map and requirement cards.")
    print("Prerequisite ordering treats Summer after Spring and before the next Autumn.")
    print("Updated src/app.js and src/styles.css.")
    print("Backups use the suffix .before-summer-quarter")


if __name__ == "__main__":
    main()