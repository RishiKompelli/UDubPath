from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app.js"
CSS = ROOT / "src" / "styles.css"
HTML = ROOT / "index.html"

MARKER = "REQUIREMENT_COURSE_BROWSER_V1"
BACKUP_SUFFIX = ".before-requirement-course-browser"


def backup(path: Path) -> None:
    target = path.with_name(path.name + BACKUP_SUFFIX)
    if not target.exists():
        shutil.copy2(path, target)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"Could not patch {label}: expected one match, found {count}. "
            "Upload your current file if this project version has changed."
        )
    return text.replace(old, new, 1)


def patch_html(text: str) -> str:
    if f"<!-- {MARKER} -->" in text:
        return text

    old = '''      <div class="catalog-toolbar card-surface">'''
    new = f'''      <!-- {MARKER} -->
      <section id="catalog-requirement-banner" class="catalog-requirement-banner card-surface" hidden>
        <div class="catalog-requirement-copy">
          <div class="eyebrow">FIND A COURSE FOR THIS REQUIREMENT</div>
          <h2 id="catalog-requirement-title"></h2>
          <p id="catalog-requirement-description"></p>
          <div id="catalog-requirement-meta" class="catalog-requirement-meta"></div>
        </div>
        <button id="catalog-requirement-clear" class="button secondary" type="button">
          Clear requirement filter
        </button>
      </section>

      <div class="catalog-toolbar card-surface">'''
    return replace_once(text, old, new, "catalog requirement banner")


CSS_BLOCK = f'''

/* {MARKER} */
.catalog-requirement-banner {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 18px;
  margin-bottom: 14px;
  padding: 18px;
  border: 1px solid color-mix(in srgb, var(--uw-purple) 32%, var(--line));
  background:
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--uw-purple) 8%, white),
      color-mix(in srgb, var(--uw-gold) 8%, white)
    );
}}

.catalog-requirement-banner[hidden] {{
  display: none;
}}

.catalog-requirement-copy {{
  min-width: 0;
}}

.catalog-requirement-copy h2 {{
  margin: 3px 0 5px;
  color: var(--uw-purple);
  font-size: 20px;
}}

.catalog-requirement-copy p {{
  max-width: 850px;
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.55;
}}

.catalog-requirement-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 11px;
}}

.catalog-requirement-chip,
.catalog-match-note {{
  display: inline-flex;
  align-items: center;
  min-height: 23px;
  padding: 4px 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--uw-purple) 10%, white);
  color: var(--uw-purple);
  font-size: 10px;
  font-weight: 800;
}}

.catalog-card-description {{
  display: -webkit-box;
  min-height: 47px;
  margin-top: 8px;
  overflow: hidden;
  color: var(--muted);
  font-size: 10.5px;
  line-height: 1.48;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}}

.catalog-card .catalog-match-note {{
  margin-top: 9px;
}}

.catalog-actions.requirement-active {{
  align-items: flex-end;
  gap: 8px;
}}

.catalog-action-buttons {{
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}}

.requirement-use-button {{
  white-space: nowrap;
}}

.requirement-browse-row {{
  display: flex;
  justify-content: flex-start;
  margin: 8px 0 2px;
}}

.requirement-browse-button {{
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--uw-purple);
  cursor: pointer;
  font-size: 11px;
  font-weight: 800;
  text-decoration: underline;
  text-underline-offset: 3px;
}}

.requirement-browse-button:hover {{
  color: color-mix(in srgb, var(--uw-purple) 78%, black);
}}

.catalog-requirement-use-panel {{
  border: 1px solid color-mix(in srgb, var(--uw-purple) 28%, var(--line));
  border-radius: 12px;
  padding: 12px;
  background: color-mix(in srgb, var(--uw-purple) 6%, white);
}}

.catalog-requirement-use-panel p {{
  margin: 3px 0 10px;
}}

@media (max-width: 760px) {{
  .catalog-requirement-banner {{
    flex-direction: column;
  }}
}}
'''


def patch_css(text: str) -> str:
    if f"/* {MARKER} */" in text:
        return text
    return text.rstrip() + CSS_BLOCK + "\n"


JS_BLOCK = r'''
// REQUIREMENT_COURSE_BROWSER_V1
function uniqueNormalizedCodes(values) {
  return [...new Set((values || []).filter(Boolean).map(normalizeCode))];
}

function requirementAreaRulesFromLabel(label) {
  const text = String(label || "").toLowerCase();
  const any = [];
  const all = [];

  const hasAH = /arts?\s*(?:&|and)\s*humanities|a\s*&\s*h|\bvlpa\b/.test(text);
  const hasSSc = /social sciences?|\bssc\b|\bi\s*&\s*s\b/.test(text);
  const hasNSc = /natural sciences?|\bnsc\b/.test(text);

  if (/areas? of inquiry/.test(text)) {
    any.push("A&H", "SSc", "NSc");
  } else {
    const aoi = [
      hasAH ? "A&H" : "",
      hasSSc ? "SSc" : "",
      hasNSc ? "NSc" : ""
    ].filter(Boolean);

    if (aoi.length > 1) any.push(...aoi);
    else if (aoi.length === 1) all.push(aoi[0]);
  }

  if (/composition/.test(text)) all.push("C");
  if (/additional writing|writing credit|\bwriting\b/.test(text)) all.push("W");
  if (/diversity|\bdiv\b/.test(text)) all.push("DIV");
  if (/reasoning|\brsn\b/.test(text)) all.push("RSN");

  return {
    any: [...new Set(any)],
    all: [...new Set(all)]
  };
}

function requirementLooksLikeLanguage(label) {
  return /foreign language|world language|language requirement/.test(
    String(label || "").toLowerCase()
  );
}

function requirementLooksBroad(label) {
  return /free elective|general elective|unassigned|graduation credit|other credit/.test(
    String(label || "").toLowerCase()
  );
}

function languageDepartmentCodes() {
  return new Set([
    "ARAB", "ARABIC", "ASL", "CHIN", "CHINESE", "CZECH", "DANISH",
    "DUTCH", "FINN", "FRENCH", "GERMAN", "GREEK", "HEBR", "HEBREW",
    "HINDI", "ITAL", "ITALIAN", "JAPAN", "JAPANESE", "KOREAN",
    "LATIN", "NORW", "PERSIAN", "POLSH", "PORT", "PORTUG",
    "RUSS", "RUSSIAN", "SPAN", "SPANISH", "SWAHILI", "SWED",
    "TURKIC", "UKRAIN", "VIET"
  ]);
}

function sourceCourseCodes(source) {
  if (!source) return [];

  const values = [
    ...(source.courses || []),
    ...((source.paths || []).flatMap((path) => path.courses || [])),
    ...((source.items || []).flatMap((item) => sourceCourseCodes(item)))
  ];

  return uniqueNormalizedCodes(values);
}

function contextMatchMode(context) {
  if (context.courseCodes?.length) return "Approved course list";
  if (context.areaAny?.length || context.areaAll?.length) {
    const any = context.areaAny?.length ? context.areaAny.join(" or ") : "";
    const all = context.areaAll?.length ? context.areaAll.join(" + ") : "";
    return `UW ${[any, all].filter(Boolean).join(" plus ")} designation`;
  }
  if (context.language) return "Language-course departments";
  if (context.departments?.length) return "Approved departments";
  if (context.minimumLevel) return `${context.minimumLevel}-level or above`;
  if (context.broad) return "Any applicable UW course";
  return "Requirement match";
}

function contextDescription(context) {
  if (context.courseCodes?.length) {
    return "Showing the courses explicitly stored in this major's approved requirement or elective pool. Select a card to read the full UW description and prerequisites.";
  }

  if (context.areaAny?.length || context.areaAll?.length) {
    return `Showing courses with the UW designation pattern stored for this placeholder. Some program-specific overlap, writing, diversity, and residency rules may still apply.`;
  }

  if (context.language) {
    return "Showing likely language courses from UW language departments. Placement, proficiency, high-school preparation, and sequence level can change what you actually need.";
  }

  if (context.broad) {
    return "This placeholder can be filled by broad degree credit rather than one fixed approved list. Search the catalog and verify any major, college, residency, and duplicate-credit restrictions.";
  }

  return "Showing courses that match the stored department, level, or course-list rules for this requirement.";
}

function catalogContextForSlot(item, quarterId) {
  const slot = parsePlanSlot(item);
  if (!slot) return null;

  const definition = slotPoolDefinition(slot);
  const groups = getVisibleMapGroups();
  const groupId = chooseMapGroupForPlanSlot(slot, groups);
  const group = groups.find((entry) => entry.id === groupId);

  const explicitCodes = explicitCourseCodesFromSlotLabel(slot.label);
  const definitionCodes = definition.courses || [];
  const groupCodes = group?.courses || [];
  const courseCodes = uniqueNormalizedCodes([
    ...explicitCodes,
    ...definitionCodes,
    ...groupCodes
  ]);

  const labelAreaRules = requirementAreaRulesFromLabel(slot.label);
  const areaAny = (definition.areas || []).length
    ? [...definition.areas]
    : labelAreaRules.any;
  const areaAll = (definition.areas || []).length
    ? []
    : labelAreaRules.all;
  const language = requirementLooksLikeLanguage(slot.label);
  const broad = requirementLooksBroad(slot.label)
    || (!courseCodes.length
      && !areaAny.length
      && !areaAll.length
      && !language
      && !(definition.departments || []).length
      && !Number(definition.minimumLevel || 0));

  return {
    kind: "plan-slot",
    label: slot.label,
    credits: Number(slot.credits || 0),
    item,
    quarterId,
    quarterLabel: quarterLabel(quarterId),
    courseCodes,
    areaAny,
    areaAll,
    language,
    broad,
    departments: definition.departments || [],
    minimumLevel: Number(definition.minimumLevel || 0),
    note: definition.note || "",
    sourceGroup: group?.label || ""
  };
}

function catalogContextForRequirement(id, scope = "item") {
  const match = findRequirementReference({ id, scope });
  if (!match) return null;

  const source = match.item || match.requirement;
  const label = source.label || source.title || match.requirement?.title || "Degree requirement";
  const courseCodes = sourceCourseCodes(source);
  const labelAreaRules = requirementAreaRulesFromLabel(label);
  const areaAny = [];
  const areaAll = source.area
    ? [source.area]
    : labelAreaRules.all;
  if (!source.area) areaAny.push(...labelAreaRules.any);

  const language = requirementLooksLikeLanguage(label);
  const broad = requirementLooksBroad(label);
  const flexibleType = new Set([
    "one", "count", "count-credit", "count-credit-level",
    "pool", "bucket", "additional-bucket", "path-choice"
  ]).has(source.type);

  if (!flexibleType && !areaAny.length && !areaAll.length && !language && !broad) {
    return null;
  }

  return {
    kind: "requirement",
    label,
    credits: Number(source.targetCredits || source.minCredits || 0),
    requirementId: id,
    requirementScope: scope,
    courseCodes,
    areaAny,
    areaAll,
    language,
    broad,
    departments: source.departments || [],
    minimumLevel: Number(source.minimumLevel || 0),
    note: source.note || match.requirement?.note || ""
  };
}

function courseMatchesCatalogRequirement(course, context) {
  if (!context) return true;

  const code = normalizeCode(course.code);
  const courseCodes = context.courseCodes || [];
  if (courseCodes.length && !courseCodes.includes(code)) return false;

  if (
    context.areaAny?.length
    && !context.areaAny.some((area) => areaMatches(course, area))
  ) return false;

  if (
    context.areaAll?.length
    && !context.areaAll.every((area) => areaMatches(course, area))
  ) return false;

  if (context.language) {
    const department = normalizeCode(course.department || code.replace(/\s+\d.*$/, ""));
    if (!languageDepartmentCodes().has(department)) return false;
  }

  const departments = (context.departments || []).map(normalizeCode);
  if (departments.length) {
    const department = normalizeCode(course.department || code.replace(/\s+\d.*$/, ""));
    if (!departments.includes(department)) return false;
  }

  if (context.minimumLevel) {
    const level = Number(code.match(/\d{3}/)?.[0] || 0);
    if (level < context.minimumLevel) return false;
  }

  return true;
}

function catalogMatchNote(course, context) {
  if (!context) return "";
  if (context.courseCodes?.length) return "Listed for this requirement";
  if (context.areaAny?.length || context.areaAll?.length) {
    const any = context.areaAny?.length ? context.areaAny.join(" or ") : "";
    const all = context.areaAll?.length ? context.areaAll.join(" + ") : "";
    return `${[any, all].filter(Boolean).join(" plus ")} designated`;
  }
  if (context.language) return "Possible language course";
  if (context.departments?.length) return "Approved department";
  if (context.minimumLevel) return `${context.minimumLevel}+ level`;
  return "Counts toward broad degree credit";
}

function renderCatalogRequirementBanner() {
  const banner = $("#catalog-requirement-banner");
  if (!banner) return;

  const context = app.catalogRequirementContext;
  banner.hidden = !context;
  if (!context) return;

  $("#catalog-requirement-title").textContent = context.label;
  $("#catalog-requirement-description").textContent =
    context.note || contextDescription(context);

  const chips = [
    context.credits ? `${formatNumber(context.credits)} credits` : "",
    context.quarterLabel || "",
    contextMatchMode(context),
    context.sourceGroup || ""
  ].filter(Boolean);

  $("#catalog-requirement-meta").innerHTML = chips
    .map((chip) => `<span class="catalog-requirement-chip">${escapeHtml(chip)}</span>`)
    .join("");
}

function openCatalogRequirementContext(context) {
  if (!context) return false;

  app.catalogRequirementContext = context;
  app.catalogLimit = 60;
  app.selectedCatalogId = null;

  if (context.kind === "plan-slot") {
    app.pendingPlanSlot = {
      item: context.item,
      quarterId: context.quarterId
    };
  } else {
    clearPendingPlanSlot();
  }

  const search = $("#catalog-search");
  if (search) search.value = "";

  const campus = $("#campus-filter");
  if (campus && [...campus.options].some((option) => option.value === "Seattle")) {
    campus.value = "Seattle";
  }

  const department = $("#department-filter");
  if (department) department.value = "all";

  switchView("catalog");

  const first = filteredCatalogCourses()[0];
  if (first) app.selectedCatalogId = first.id;
  renderCatalog();

  requestAnimationFrame(() => {
    $("#catalog-search")?.focus();
    $("#catalog-requirement-banner")?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
  });

  return true;
}

function browsePlanSlotCourses(item, quarterId) {
  return openCatalogRequirementContext(
    catalogContextForSlot(item, quarterId)
  );
}

function browseMapRequirement(id, scope) {
  return openCatalogRequirementContext(
    catalogContextForRequirement(id, scope)
  );
}

function clearCatalogRequirementContext() {
  const wasPlanSlot = app.catalogRequirementContext?.kind === "plan-slot";
  app.catalogRequirementContext = null;

  if (wasPlanSlot) clearPendingPlanSlot();

  app.catalogLimit = 60;
  app.selectedCatalogId = null;
  renderCatalog();
  $("#catalog-search")?.focus();
}

function useCatalogCourseForRequirement(code) {
  const context = app.catalogRequirementContext;
  if (!context?.quarterId || !context?.item) return false;

  const added = addCourseToPlan(code, context.quarterId, {
    replaceItem: context.item,
    clearPendingSlot: true
  });

  if (!added) return false;

  const quarterId = context.quarterId;
  app.catalogRequirementContext = null;
  switchView("planner");

  requestAnimationFrame(() => {
    document
      .querySelector(`[data-quarter="${quarterId}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  return true;
}

function handleRequirementBrowseClick(event) {
  const button = event.target.closest("[data-browse-requirement]");
  if (!button) return;

  event.preventDefault();
  browseMapRequirement(
    button.dataset.browseRequirement,
    button.dataset.browseRequirementScope || "item"
  );
}
'''


def patch_js(text: str) -> str:
    if f"// {MARKER}" in text:
        return text

    if "catalogRequirementContext:" not in text:
        text = replace_once(
            text,
            '''  selectedCatalogId: null,
  activeView: "map",''',
            '''  selectedCatalogId: null,
  catalogRequirementContext: null,
  activeView: "map",''',
            "catalog requirement state",
        )

    text = replace_once(
        text,
        "\nfunction getApExam(examId) {",
        "\n" + JS_BLOCK + "\n\nfunction getApExam(examId) {",
        "requirement course-browser functions",
    )

    text = replace_once(
        text,
        '''  if (planSlotNode) {
    openMapPlanSlot(planSlotNode.dataset.mapPlanSlot, planSlotNode.dataset.mapPlanQuarter);
    return;
  }''',
        '''  if (planSlotNode) {
    browsePlanSlotCourses(
      planSlotNode.dataset.mapPlanSlot,
      planSlotNode.dataset.mapPlanQuarter
    );
    return;
  }''',
        "map plan-slot browsing",
    )

    old_requirement_click = '''  if (requirementNode) {
    const id = requirementNode.dataset.mapRequirement;
    const scope = requirementNode.dataset.mapRequirementScope || "item";
    switchView("requirements");
    requestAnimationFrame(() => {
      const selector = scope === "requirement" ? `#requirement-${safeId(id)}` : `#requirement-item-${safeId(id)}`;
      document.querySelector(selector)?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    return;
  }'''
    new_requirement_click = '''  if (requirementNode) {
    const id = requirementNode.dataset.mapRequirement;
    const scope = requirementNode.dataset.mapRequirementScope || "item";

    if (browseMapRequirement(id, scope)) return;

    switchView("requirements");
    requestAnimationFrame(() => {
      const selector = scope === "requirement" ? `#requirement-${safeId(id)}` : `#requirement-item-${safeId(id)}`;
      document.querySelector(selector)?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    return;
  }'''
    text = replace_once(
        text,
        old_requirement_click,
        new_requirement_click,
        "map requirement browsing",
    )

    text = replace_once(
        text,
        '''  if (fillSlot) {
    event.stopPropagation();
    beginFillPlanSlot(fillSlot.dataset.fillSlot, fillSlot.dataset.quarter);
    return;
  }''',
        '''  if (fillSlot) {
    event.stopPropagation();
    browsePlanSlotCourses(
      fillSlot.dataset.fillSlot,
      fillSlot.dataset.quarter
    );
    return;
  }''',
        "planner placeholder browsing",
    )

    text = text.replace(
        '''data-quarter="${quarterId}">Choose course</button>''',
        '''data-quarter="${quarterId}">Browse courses</button>''',
    )
    text = text.replace(
        '''${currentlyInPlan ? "Choose course" : "Suggested"} · ${escapeHtml(slot.quarterText)}''',
        '''${currentlyInPlan ? "Browse matching courses" : "Browse suggested courses"} · ${escapeHtml(slot.quarterText)}''',
    )

    old_requirement_item = '''  const pathHtml = item.type === "path-choice" ? `<div class="requirement-paths">${(evaluation.paths || []).map((path) => `'''
    new_requirement_item = '''  const browseContext = catalogContextForRequirement(item.id, "item");
  const browseHtml = browseContext
    ? `<div class="requirement-browse-row"><button class="requirement-browse-button" type="button" data-browse-requirement="${escapeHtml(item.id)}" data-browse-requirement-scope="item">Browse courses that fill this requirement →</button></div>`
    : "";
  const pathHtml = item.type === "path-choice" ? `<div class="requirement-paths">${(evaluation.paths || []).map((path) => `'''
    text = replace_once(
        text,
        old_requirement_item,
        new_requirement_item,
        "requirement browse control",
    )

    text = replace_once(
        text,
        '''    ${pathHtml}
    ${courses.length ?''',
        '''    ${browseHtml}
    ${pathHtml}
    ${courses.length ?''',
        "requirement browse link rendering",
    )

    text = replace_once(
        text,
        '''  $("#requirements-grid").addEventListener("change", handleRequirementChange);''',
        '''  $("#requirements-grid").addEventListener("click", handleRequirementBrowseClick);
  $("#requirements-grid").addEventListener("change", handleRequirementChange);''',
        "requirement browse listener",
    )

    text = replace_once(
        text,
        '''  $("#catalog-results").addEventListener("click", handleCatalogClick);''',
        '''  $("#catalog-requirement-clear").addEventListener("click", clearCatalogRequirementContext);
  $("#catalog-results").addEventListener("click", handleCatalogClick);''',
        "catalog filter clear listener",
    )

    text = replace_once(
        text,
        '''  return app.courses.filter((course) => {
    if (campus !== "all" && course.campus !== campus) return false;''',
        '''  return app.courses.filter((course) => {
    if (
      app.catalogRequirementContext
      && !courseMatchesCatalogRequirement(course, app.catalogRequirementContext)
    ) return false;
    if (campus !== "all" && course.campus !== campus) return false;''',
        "catalog requirement filtering",
    )

    text = replace_once(
        text,
        '''function renderCatalog() {
  if (!app.catalogPayload) return;
  const filtered = filteredCatalogCourses();''',
        '''function renderCatalog() {
  if (!app.catalogPayload) return;
  renderCatalogRequirementBanner();
  const filtered = filteredCatalogCourses();''',
        "catalog banner rendering",
    )

    text = replace_once(
        text,
        '''  $("#catalog-result-count").textContent = `${filtered.length.toLocaleString()} matching course${filtered.length === 1 ? "" : "s"}`;''',
        '''  const context = app.catalogRequirementContext;
  $("#catalog-result-count").textContent = context
    ? `${filtered.length.toLocaleString()} course${filtered.length === 1 ? "" : "s"} matching ${context.label}`
    : `${filtered.length.toLocaleString()} matching course${filtered.length === 1 ? "" : "s"}`;''',
        "contextual catalog count",
    )

    old_card_start = '''function renderCatalogCard(course) {
  const selected = course.id === app.selectedCatalogId;
  return `<article'''
    new_card_start = '''function renderCatalogCard(course) {
  const selected = course.id === app.selectedCatalogId;
  const context = app.catalogRequirementContext;
  const description = course.description
    || "Open this course to view available catalog and prerequisite information.";
  const useButton = context?.quarterId
    ? `<button class="button small primary requirement-use-button" type="button" data-use-requirement-course="${escapeHtml(course.code)}">Use for ${escapeHtml(context.quarterLabel || "plan")}</button>`
    : "";
  return `<article'''
    text = replace_once(
        text,
        old_card_start,
        new_card_start,
        "catalog card context",
    )

    text = replace_once(
        text,
        '''    <div class="catalog-meta">
      <span class="tiny-chip">${escapeHtml(course.credits || "?")} cr</span>
      ${course.areas ? `<span class="tiny-chip">${escapeHtml(course.areas)}</span>` : ""}
      ${course.offered ? `<span class="tiny-chip">${escapeHtml(course.offered)}</span>` : ""}
    </div>
    <div class="catalog-actions">''',
        '''    <div class="catalog-meta">
      <span class="tiny-chip">${escapeHtml(course.credits || "?")} cr</span>
      ${course.areas ? `<span class="tiny-chip">${escapeHtml(course.areas)}</span>` : ""}
      ${course.offered ? `<span class="tiny-chip">${escapeHtml(course.offered)}</span>` : ""}
    </div>
    <div class="catalog-card-description">${escapeHtml(description)}</div>
    ${context ? `<span class="catalog-match-note">${escapeHtml(catalogMatchNote(course, context))}</span>` : ""}
    <div class="catalog-actions ${context ? "requirement-active" : ""}">
      <div class="catalog-action-buttons">
        ${useButton}''',
        "catalog card descriptions",
    )

    text = replace_once(
        text,
        '''      <button class="button small secondary" type="button" data-open-catalog="${escapeHtml(course.id)}">View path</button>
      <label onclick="event.stopPropagation()">''',
        '''      <button class="button small secondary" type="button" data-open-catalog="${escapeHtml(course.id)}">Read details</button>
      </div>
      <label onclick="event.stopPropagation()">''',
        "catalog card action grouping",
    )

    text = replace_once(
        text,
        '''function handleCatalogClick(event) {
  const open = event.target.closest("[data-open-catalog]");''',
        '''function handleCatalogClick(event) {
  const use = event.target.closest("[data-use-requirement-course]");
  if (use) {
    event.preventDefault();
    event.stopPropagation();
    useCatalogCourseForRequirement(use.dataset.useRequirementCourse);
    return;
  }

  const open = event.target.closest("[data-open-catalog]");''',
        "catalog result use action",
    )

    text = replace_once(
        text,
        '''    </div>

    <div class="detail-section">
      <h3>Add to four-year plan</h3>
      <div class="plan-add-row">
        <select data-catalog-quarter>''',
        '''    </div>

    ${app.catalogRequirementContext?.quarterId && courseMatchesCatalogRequirement(course, app.catalogRequirementContext) ? `
    <div class="detail-section catalog-requirement-use-panel">
      <h3>Use for ${escapeHtml(app.catalogRequirementContext.label)}</h3>
      <p class="detail-description">This replaces the ${formatNumber(app.catalogRequirementContext.credits || 0)}-credit placeholder in ${escapeHtml(app.catalogRequirementContext.quarterLabel)}.</p>
      <button class="button primary" type="button" data-catalog-panel="use-requirement" data-code="${escapeHtml(course.code)}">Use ${escapeHtml(course.code)} for this requirement</button>
    </div>` : ""}

    <div class="detail-section">
      <h3>Add to four-year plan</h3>
      <div class="plan-add-row">
        <select data-catalog-quarter>''',
        "catalog detail use action",
    )

    text = replace_once(
        text,
        '''  if (action?.dataset.catalogPanel === "add") {
    const quarter = $("[data-catalog-quarter]", $("#catalog-panel")).value;
    addCourseToPlan(action.dataset.code, quarter);
  }''',
        '''  if (action?.dataset.catalogPanel === "use-requirement") {
    useCatalogCourseForRequirement(action.dataset.code);
    return;
  }
  if (action?.dataset.catalogPanel === "add") {
    const quarter = $("[data-catalog-quarter]", $("#catalog-panel")).value;
    addCourseToPlan(action.dataset.code, quarter);
  }''',
        "catalog panel use action",
    )

    text = replace_once(
        text,
        '''    app.selectedCode = null;
    app.selectedCatalogId = null;
    populateGlobalControls();''',
        '''    app.selectedCode = null;
    app.selectedCatalogId = null;
    app.catalogRequirementContext = null;
    app.pendingPlanSlot = null;
    populateGlobalControls();''',
        "clear requirement browser when changing majors",
    )

    return text


def main() -> None:
    for path in (APP, CSS, HTML):
        if not path.exists():
            raise FileNotFoundError(
                f"Could not find {path.relative_to(ROOT)}. "
                "Place this script in the project's scripts folder."
            )

    html = HTML.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = APP.read_text(encoding="utf-8")

    new_html = patch_html(html)
    new_css = patch_css(css)
    new_js = patch_js(js)

    for path in (APP, CSS, HTML):
        backup(path)

    HTML.write_text(new_html, encoding="utf-8")
    CSS.write_text(new_css, encoding="utf-8")
    APP.write_text(new_js, encoding="utf-8")

    print("Added requirement-aware course browsing for plan placeholders.")
    print("General-education placeholders filter by UW course-area designations.")
    print("Elective placeholders use exact approved pools when the major stores them.")
    print("Catalog cards now show description previews and direct placeholder replacement.")
    print("Requirement cards include a Browse courses link when matching rules are available.")
    print(f"Backups use the suffix {BACKUP_SUFFIX}")


if __name__ == "__main__":
    main()