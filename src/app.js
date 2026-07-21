"use strict";

const STORAGE_PREFIX = "uw-degree-mapper-v5";
const QUARTERS = [
  { id: "y1-autumn", year: 1, season: "Autumn" },
  { id: "y1-winter", year: 1, season: "Winter" },
  { id: "y1-spring", year: 1, season: "Spring" },
  { id: "y2-autumn", year: 2, season: "Autumn" },
  { id: "y2-winter", year: 2, season: "Winter" },
  { id: "y2-spring", year: 2, season: "Spring" },
  { id: "y3-autumn", year: 3, season: "Autumn" },
  { id: "y3-winter", year: 3, season: "Winter" },
  { id: "y3-spring", year: 3, season: "Spring" },
  { id: "y4-autumn", year: 4, season: "Autumn" },
  { id: "y4-winter", year: 4, season: "Winter" },
  { id: "y4-spring", year: 4, season: "Spring" }
];

const OFFICIAL_COURSE_OVERLAP_GROUPS = [
  ["PHYS 114", "PHYS 117", "PHYS 121", "PHYS 141"],
  ["PHYS 115", "PHYS 118", "PHYS 122", "PHYS 142"],
  ["PHYS 116", "PHYS 119", "PHYS 123", "PHYS 143"],
  ["CHEM 120", "CHEM 142", "CHEM 143", "CHEM 145"],
  ["CHEM 152", "CHEM 153", "CHEM 155"],
  ["CHEM 162", "CHEM 165"],
  ["MATH 124", "MATH 134"],
  ["MATH 125", "MATH 135"],
  ["MATH 126", "MATH 136"],
  ["MATH 207", "MATH 135", "MATH 136"],
  ["MATH 208", "MATH 136"],
  ["CSE 123", "CSE 143"]
];

function clonePlan(plan = app.progress.plan) {
  return Object.fromEntries(
    QUARTERS.map((quarter) => [quarter.id, [...(plan?.[quarter.id] || [])]])
  );
}

function planQuarterIndex(quarterId) {
  return QUARTERS.findIndex((quarter) => quarter.id === quarterId);
}

function courseOverlapGroups() {
  const groups = OFFICIAL_COURSE_OVERLAP_GROUPS.map((group) => group.map(normalizeCode));
  for (const [standard, substitutes] of Object.entries(app.major.prerequisiteSubstitutions || {})) {
    for (const substitute of substitutes || []) {
      groups.push([normalizeCode(standard), normalizeCode(substitute)]);
    }
  }

  const seen = new Set();
  return groups.filter((group) => {
    const key = [...new Set(group)].sort().join("|");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function planCourseIndex(plan) {
  const result = new Map();
  QUARTERS.forEach((quarter, index) => {
    for (const item of plan?.[quarter.id] || []) {
      if (!isPlanSlot(item)) result.set(normalizeCode(item), index);
    }
  });
  return result;
}

function prerequisitePlanConflicts(plan) {
  const conflicts = [];
  const courseIndex = planCourseIndex(plan);

  QUARTERS.forEach((quarter, quarterIndex) => {
    for (const rawCode of plan?.[quarter.id] || []) {
      if (isPlanSlot(rawCode)) continue;
      const code = normalizeCode(rawCode);
      const groups = getPrerequisiteGroups(code);

      groups.forEach((group, groupIndex) => {
        const options = [...new Set(group.flatMap((prerequisite) => [
          normalizeCode(prerequisite),
          ...prerequisiteSubstitutes(prerequisite)
        ]))];

        const satisfied = options.some((option) => (
          isFulfilled(option)
          || (courseIndex.has(option) && courseIndex.get(option) < quarterIndex)
        ));

        if (!satisfied) {
          conflicts.push({
            key: `prereq:${quarter.id}:${code}:${groupIndex}`,
            type: "prerequisite",
            code,
            quarter: quarter.id,
            options,
            message: `${code} needs ${options.join(" or ")} fulfilled by AP/IB, Running Start/transfer, completed credit, or planned in an earlier quarter.`
          });
        }
      });
    }
  });

  return conflicts;
}

function overlapPlanConflicts(plan) {
  const conflicts = [];
  const groups = courseOverlapGroups();

  for (const quarter of QUARTERS) {
    const codes = new Set(
      (plan?.[quarter.id] || [])
        .filter((item) => !isPlanSlot(item))
        .map(normalizeCode)
    );

    groups.forEach((group, groupIndex) => {
      const present = [...new Set(group.filter((code) => codes.has(code)))];
      if (present.length < 2) return;
      const sorted = [...present].sort();
      conflicts.push({
        key: `overlap:${quarter.id}:${groupIndex}:${sorted.join("+")}`,
        type: "overlap",
        code: sorted.join(" / "),
        quarter: quarter.id,
        courses: sorted,
        message: `${sorted.join(" and ")} cannot be planned in the same quarter because they are overlapping or equivalent course paths.`
      });
    });
  }

  return conflicts;
}

function structuralPlanConflicts(plan) {
  return [...prerequisitePlanConflicts(plan), ...overlapPlanConflicts(plan)];
}

function newlyIntroducedPlanConflicts(currentPlan, proposedPlan) {
  const currentKeys = new Set(structuralPlanConflicts(currentPlan).map((conflict) => conflict.key));
  return structuralPlanConflicts(proposedPlan).filter((conflict) => !currentKeys.has(conflict.key));
}

function showPlanConflict(conflict) {
  if (!conflict) return;
  showToast(conflict.message);
}

function proposedPlanWithCourse(code, quarterId, replaceItem = null) {
  const normalized = isPlanSlot(code) ? code : normalizeCode(code);
  const proposed = clonePlan();

  for (const quarter of QUARTERS) {
    proposed[quarter.id] = (proposed[quarter.id] || []).filter((item) => item !== normalized);
  }

  if (replaceItem) {
    proposed[quarterId] = (proposed[quarterId] || []).filter((item) => item !== replaceItem);
  }

  proposed[quarterId] = proposed[quarterId] || [];
  proposed[quarterId].push(normalized);
  return proposed;
}

const app = {
  majorIndex: null,
  major: null,
  catalogPayload: null,
  apCredit: { exams: [], source: {} },
  courses: [],
  catalogById: new Map(),
  catalogByCode: new Map(),
  reversePrereqs: new Map(),
  progress: null,
  selectedCode: null,
  selectedCatalogId: null,
  activeView: "map",
  catalogLimit: 60,
  confirmResolver: null,
  mapRenderToken: 0,
  pendingPlanSlot: null,
  plannerSelectedCourseCode: null,
  plannerSearchMatches: [],
  plannerSearchIndex: -1,
  mapPanEnabled: false,
  mapPanState: null,
  mapDidPan: false,
  mapScrollSyncing: false
};

const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeCode(value) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/^M E\s+/, "ME ")
    .replace(/^A A\s+/, "AA ")
    .replace(/^E E\s+/, "EE ")
    .replace(/\s+/g, " ");
}

function numericCredits(value) {
  const match = String(value ?? "").match(/\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : 0;
}

function formatNumber(value) {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function emptyPlan() {
  return Object.fromEntries(QUARTERS.map((quarter) => [quarter.id, []]));
}

function createDefaultProgress() {
  return {
    version: 5,
    track: "standard",
    fulfilled: {},
    plan: emptyPlan(),
    requirementOverrides: {},
    manualCredits: {},
    fulfillmentSources: {},
    apSelections: {},
    transferCourses: {}
  };
}

function storageKey() {
  return `${STORAGE_PREFIX}::${app.major?.id || "unknown"}`;
}

function loadProgress() {
  const defaults = createDefaultProgress();
  try {
    const raw = localStorage.getItem(storageKey());
    if (!raw) return defaults;
    const parsed = JSON.parse(raw);
    return {
      ...defaults,
      ...parsed,
      fulfilled: { ...defaults.fulfilled, ...(parsed.fulfilled || {}) },
      plan: { ...defaults.plan, ...(parsed.plan || {}) },
      requirementOverrides: { ...defaults.requirementOverrides, ...(parsed.requirementOverrides || {}) },
      manualCredits: { ...defaults.manualCredits, ...(parsed.manualCredits || {}) },
      fulfillmentSources: { ...defaults.fulfillmentSources, ...(parsed.fulfillmentSources || {}) },
      apSelections: { ...defaults.apSelections, ...(parsed.apSelections || {}) },
      transferCourses: { ...defaults.transferCourses, ...(parsed.transferCourses || {}) }
    };
  } catch (error) {
    console.warn("Could not load saved progress", error);
    return defaults;
  }
}

function saveProgress() {
  localStorage.setItem(storageKey(), JSON.stringify(app.progress));
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

async function fetchFirstAvailableJson(urls) {
  let lastError;
  for (const url of urls) {
    try {
      return await fetchJson(url);
    } catch (error) {
      lastError = error;
      console.warn(`Could not load ${url}; trying the next catalog source.`, error);
    }
  }
  throw lastError || new Error("No catalog source was available.");
}

async function initialize() {
  try {
    const majorIndex = await fetchJson("data/majors/index.json");
    const defaultMajor = majorIndex.majors.find((entry) => entry.status === "complete" && entry.file);
    if (!defaultMajor) throw new Error("No completed major definition was found.");
    const [major, catalogPayload, apCredit] = await Promise.all([
      fetchJson(`data/majors/${defaultMajor.file}`),
      fetchFirstAvailableJson([
        "data/catalog-live.json",
        "data/catalog-fallback.json"
      ]),
      fetchJson("data/ap-credit.json")
    ]);
    app.majorIndex = majorIndex;
    app.major = major;
    app.catalogPayload = catalogPayload;
    app.apCredit = apCredit;
    app.progress = loadProgress();
    migrateLegacyPlanSlots();
    buildCatalogIndexes();
    populateGlobalControls();
    bindEvents();
    renderAll();
    requestAnimationFrame(() => $("#loading-screen").classList.add("hidden"));
  } catch (error) {
    console.error(error);
    $("#loading-screen").innerHTML = `
      <div class="loading-mark">!</div>
      <h1>Could not start the website</h1>
      <p>${escapeHtml(error.message)}</p>
      <p style="margin-top:12px">For local use, run <strong>py server.py</strong>. For Vercel, make sure the complete <strong>data</strong> folder is deployed.</p>`;
  }
}

function buildCatalogIndexes() {
  app.courses = Array.isArray(app.catalogPayload?.courses) ? app.catalogPayload.courses : [];
  app.catalogById.clear();
  app.catalogByCode.clear();
  app.reversePrereqs.clear();

  for (const course of app.courses) {
    course.code = normalizeCode(course.code);
    app.catalogById.set(course.id, course);
    if (!app.catalogByCode.has(course.code)) app.catalogByCode.set(course.code, []);
    app.catalogByCode.get(course.code).push(course);
    for (const prerequisite of course.prerequisiteCodes || []) {
      const code = normalizeCode(prerequisite);
      if (!app.reversePrereqs.has(code)) app.reversePrereqs.set(code, []);
      app.reversePrereqs.get(code).push(course.id);
    }
  }

  for (const values of app.catalogByCode.values()) {
    values.sort((a, b) => campusRank(a.campus) - campusRank(b.campus));
  }
}

function campusRank(campus) {
  return campus === "Seattle" ? 0 : campus === "Bothell" ? 1 : 2;
}

function getCatalogCourse(code, campus = "Seattle") {
  const list = app.catalogByCode.get(normalizeCode(code)) || [];
  return list.find((course) => course.campus === campus) || list[0] || null;
}

function getCourse(code) {
  const normalized = normalizeCode(code);
  const base = getCatalogCourse(normalized) || {
    id: `seattle::${normalized}`,
    campus: "Seattle",
    department: normalized.replace(/\s+\d.*$/, ""),
    number: normalized.match(/\d{3}[A-Z]?$/)?.[0] || "",
    code: normalized,
    title: "Course information unavailable in offline catalog",
    credits: "",
    areas: "",
    prerequisiteText: "",
    prerequisiteCodes: [],
    offered: "",
    description: "",
    sourceType: "major-definition"
  };
  const override = app.major.courseOverrides?.[normalized] || {};
  return {
    ...base,
    ...override,
    code: normalized,
    prerequisiteGroups: override.prerequisiteGroups ?? genericPrerequisiteGroups(base)
  };
}

function genericPrerequisiteGroups(course) {
  return (course?.prerequisiteCodes || []).map((code) => [normalizeCode(code)]);
}

function getPrerequisiteGroups(codeOrCourse) {
  const course = typeof codeOrCourse === "string" ? getCourse(codeOrCourse) : codeOrCourse;
  return course.prerequisiteGroups ?? genericPrerequisiteGroups(course);
}

function prerequisiteSubstitutes(code) {
  return (app.major.prerequisiteSubstitutions?.[normalizeCode(code)] || []).map(normalizeCode);
}

function expandedPrerequisiteOptions(group) {
  return [...new Set(group.flatMap((code) => [normalizeCode(code), ...prerequisiteSubstitutes(code)]))];
}

function prerequisiteOptionSatisfied(code, extraFulfilled = new Set()) {
  const options = [normalizeCode(code), ...prerequisiteSubstitutes(code)];
  return options.some((option) => isFulfilled(option) || extraFulfilled.has(option));
}

function prerequisiteFulfillmentVia(code) {
  const normalized = normalizeCode(code);
  if (isFulfilled(normalized)) return normalized;
  return prerequisiteSubstitutes(normalized).find(isFulfilled) || null;
}

function populateGlobalControls() {
  const majorSelect = $("#major-select");
  majorSelect.innerHTML = app.majorIndex.majors.map((major) =>
    `<option value="${escapeHtml(major.id)}" ${major.status !== "complete" ? "disabled" : ""}>${escapeHtml(major.name)}${major.status !== "complete" ? " — future" : ""}</option>`
  ).join("");
  majorSelect.value = app.major.id;

  const trackSelect = $("#track-select");
  trackSelect.innerHTML = app.major.tracks.map((track) => `<option value="${track.id}">${escapeHtml(track.name)}</option>`).join("");
  trackSelect.value = app.progress.track;

  populateQuarterSelects();
  populateApExamSelect();
  populateCatalogFilters();
  updateDataBadge();
}

function populateQuarterSelects() {
  const options = QUARTERS.map((quarter) => `<option value="${quarter.id}">Year ${quarter.year} · ${quarter.season}</option>`).join("");
  $("#planner-add-quarter").innerHTML = options;
}

function populateCatalogFilters() {
  const campuses = [...new Set(app.courses.map((course) => course.campus).filter(Boolean))].sort();
  $("#campus-filter").innerHTML = `<option value="all">All campuses</option>${campuses.map((campus) => `<option value="${escapeHtml(campus)}">${escapeHtml(campus)}</option>`).join("")}`;
  updateDepartmentFilter();
}

function updateDepartmentFilter() {
  const campus = $("#campus-filter").value || "all";
  const current = $("#department-filter").value;
  const departments = [...new Set(app.courses
    .filter((course) => campus === "all" || course.campus === campus)
    .map((course) => course.department)
    .filter(Boolean))].sort();
  $("#department-filter").innerHTML = `<option value="all">All departments</option>${departments.map((department) => `<option value="${escapeHtml(department)}">${escapeHtml(department)}</option>`).join("")}`;
  if (departments.includes(current)) $("#department-filter").value = current;
}

function updateDataBadge() {
  const metadata = app.catalogPayload.metadata || {};
  const isLive = metadata.sourceType === "official-live";
  $("#data-status").classList.toggle("live", isLive);
  $("#data-status-text").textContent = isLive ? "Official catalog synced" : "Offline catalog";
  $("#catalog-total").textContent = Number(metadata.courseCount || app.courses.length).toLocaleString();
  $("#catalog-description").textContent = isLive
    ? "Search the locally synced official UW Seattle, Bothell, and Tacoma course-description catalog."
    : "Search the bundled UW catalog, then run the official sync command for current descriptions and prerequisites.";
}

function bindEvents() {
  $$(".tab").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
  $("#track-select").addEventListener("change", (event) => {
    app.progress.track = event.target.value;
    saveProgress();
    renderAll();
  });
  $("#major-select").addEventListener("change", (event) => changeMajor(event.target.value));

  $("#map-search").addEventListener("input", debounce(renderMap, 90));
  $("#available-only").addEventListener("change", renderMap);
  $("#show-all-connections").addEventListener("change", drawMapEdges);
  $("#fit-map-button").addEventListener("click", () => $("#map-scroll").scrollTo({ left: 0, top: 0, behavior: "smooth" }));
  $("#pan-map-button").addEventListener("click", toggleMapPan);
  $("#map-scroll").addEventListener("click", handleMapClick);
  $("#map-scroll").addEventListener("scroll", syncMapScrollFromMain, { passive: true });
  $("#map-scroll-top").addEventListener("scroll", syncMapScrollFromTop, { passive: true });
  $("#map-scroll").addEventListener("pointerdown", startMapPan);
  $("#map-scroll").addEventListener("pointermove", moveMapPan);
  $("#map-scroll").addEventListener("pointerup", endMapPan);
  $("#map-scroll").addEventListener("pointercancel", endMapPan);
  $("#map-scroll").addEventListener("contextmenu", (event) => event.preventDefault());
  updatePanButton();
  $("#course-panel").addEventListener("click", handleCoursePanelClick);
  $("#course-panel").addEventListener("change", handleCoursePanelChange);

  $("#requirements-grid").addEventListener("change", handleRequirementChange);

  const plannerSearch = $("#planner-add-search");
  plannerSearch.addEventListener("input", debounce(() => {
    app.plannerSelectedCourseCode = null;
    updatePlannerSearchResults();
    openPlannerCourseMenu();
  }, 80));
  plannerSearch.addEventListener("focus", () => {
    updatePlannerSearchResults();
    openPlannerCourseMenu();
  });
  plannerSearch.addEventListener("keydown", handlePlannerSearchKeydown);
  $("#planner-course-toggle").addEventListener("click", togglePlannerCourseMenu);
  $("#planner-add-menu").addEventListener("mousedown", handlePlannerMenuClick);
  document.addEventListener("click", handlePlannerOutsideClick);
  $("#planner-add-button").addEventListener("click", addPlannerSearchCourse);
  $("#planner-grid").addEventListener("click", handlePlannerClick);
  $("#planner-grid").addEventListener("dragstart", handleDragStart);
  $("#planner-grid").addEventListener("dragover", handleDragOver);
  $("#planner-grid").addEventListener("dragleave", handleDragLeave);
  $("#planner-grid").addEventListener("drop", handleDrop);
  $("#load-sample-button").addEventListener("click", loadSamplePlan);
  $("#clear-plan-button").addEventListener("click", clearPlan);

  $("#ap-exam-select").addEventListener("change", populateApScoreSelect);
  $("#ap-add-button").addEventListener("click", addApExamSelection);
  $("#ap-selected-list").addEventListener("click", handleCreditClick);
  $("#transfer-course-search").addEventListener("input", debounce(renderTransferCourseOptions, 80));
  $("#transfer-major-only").addEventListener("change", renderTransferCourseOptions);
  $("#transfer-course-options").addEventListener("change", handleTransferCourseChange);
  $("#transfer-selected-list").addEventListener("click", handleCreditClick);
  $("#external-credit-table").addEventListener("click", handleCreditClick);
  $("#clear-external-credit").addEventListener("click", clearExternalCredits);

  $("#catalog-search").addEventListener("input", debounce(() => { app.catalogLimit = 60; renderCatalog(); }, 100));
  $("#campus-filter").addEventListener("change", () => { updateDepartmentFilter(); app.catalogLimit = 60; renderCatalog(); });
  $("#department-filter").addEventListener("change", () => { app.catalogLimit = 60; renderCatalog(); });
  $("#catalog-results").addEventListener("click", handleCatalogClick);
  $("#catalog-results").addEventListener("change", handleCatalogChange);
  $("#catalog-panel").addEventListener("click", handleCatalogPanelClick);
  $("#catalog-panel").addEventListener("change", handleCatalogPanelChange);
  $("#show-more-button").addEventListener("click", () => { app.catalogLimit += 60; renderCatalog(); });

  $("#reset-button").addEventListener("click", resetAll);
  $("#export-button").addEventListener("click", exportProgress);
  $("#import-button").addEventListener("click", () => $("#import-file").click());
  $("#import-file").addEventListener("change", importProgress);

  $("#data-status").addEventListener("click", openDataModal);
  $("#data-modal .modal-close").addEventListener("click", () => $("#data-modal").hidden = true);
  $("#data-modal").addEventListener("click", (event) => { if (event.target === $("#data-modal")) $("#data-modal").hidden = true; });

  $("#confirm-cancel").addEventListener("click", () => resolveConfirm(false));
  $("#confirm-ok").addEventListener("click", () => resolveConfirm(true));
  $("#confirm-modal").addEventListener("click", (event) => { if (event.target === $("#confirm-modal")) resolveConfirm(false); });

  window.addEventListener("resize", debounce(drawMapEdges, 120));
}


async function changeMajor(majorId) {
  const definition = app.majorIndex.majors.find((entry) => entry.id === majorId);
  if (!definition?.file || definition.status !== "complete") {
    $("#major-select").value = app.major.id;
    showToast("That major definition has not been added yet.");
    return;
  }
  try {
    const major = await fetchJson(`data/majors/${definition.file}`);
    app.major = major;
    app.progress = loadProgress();
    app.selectedCode = null;
    app.selectedCatalogId = null;
    populateGlobalControls();
    renderAll();
    showToast(`${major.name} loaded.`);
  } catch (error) {
    $("#major-select").value = app.major.id;
    showToast(`Could not load that major: ${error.message}`);
  }
}

function switchView(view) {
  app.activeView = view;
  $$(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.view === view));
  $$(".view").forEach((section) => section.classList.toggle("active", section.id === `view-${view}`));
  if (view === "map") requestAnimationFrame(drawMapEdges);
  if (view === "catalog") renderCatalog();
  if (view === "credits") renderCredits();
}

function renderAll() {
  $("#track-select").value = app.progress.track;
  $("#map-title").textContent = `${app.major.name} · ${trackName(app.progress.track)}`;
  renderMap();
  renderRequirements();
  renderPlanner();
  renderCredits();
  renderCatalog();
}

function trackName(id) {
  return app.major.tracks.find((track) => track.id === id)?.name || id;
}

function getActiveRequirements() {
  return app.major.requirements.filter((requirement) => !requirement.track || requirement.track === app.progress.track);
}

function requirementCourseSet(requirement) {
  const result = new Set((requirement.courses || []).map(normalizeCode));
  for (const path of requirement.paths || []) {
    for (const code of path.courses || []) result.add(normalizeCode(code));
  }
  for (const item of requirement.items || []) {
    for (const code of item.courses || []) result.add(normalizeCode(code));
    for (const path of item.paths || []) {
      for (const code of path.courses || []) result.add(normalizeCode(code));
    }
  }
  return result;
}

function optionCoursesForTrack() {
  const requirement = app.major.requirements.find((entry) => entry.track === app.progress.track);
  return requirement ? requirementCourseSet(requirement) : new Set();
}

function getVisibleMapCodes() {
  const optionSet = optionCoursesForTrack();
  return [...new Set(app.major.mapGroups.flatMap((group) => {
    const courses = group.id === "options" ? group.courses.filter((code) => optionSet.has(code)) : group.courses;
    return courses.map(normalizeCode);
  }))];
}

function mapCategory(code) {
  const normalized = normalizeCode(code);
  return app.major.mapGroups.find((group) => group.courses.map(normalizeCode).includes(normalized))?.label || "Degree course";
}

function computeMapLevels(codes) {
  const codeSet = new Set(codes);
  const memo = new Map();
  const visiting = new Set();

  const resolve = (code) => {
    if (memo.has(code)) return memo.get(code);
    if (visiting.has(code)) return 0;
    visiting.add(code);
    const groups = getPrerequisiteGroups(code);
    const requiredLevels = [];
    for (const group of groups) {
      const mapped = expandedPrerequisiteOptions(group).filter((prereq) => codeSet.has(prereq));
      if (!mapped.length) continue;
      requiredLevels.push(Math.min(...mapped.map(resolve)));
    }
    visiting.delete(code);
    const level = requiredLevels.length ? Math.max(...requiredLevels) + 1 : 0;
    memo.set(code, level);
    return level;
  };

  for (const code of codes) resolve(code);
  return memo;
}

function getVisibleMapGroups() {
  const optionSet = optionCoursesForTrack();
  return app.major.mapGroups.map((group) => ({
    ...group,
    courses: (group.id === "options" ? group.courses.filter((code) => optionSet.has(normalizeCode(code))) : group.courses)
      .map(normalizeCode)
  }));
}

function findRequirementReference(reference) {
  const activeRequirements = getActiveRequirements();
  if (reference.scope === "requirement") {
    const requirement = activeRequirements.find((entry) => entry.id === reference.id);
    return requirement ? { requirement, item: null, evaluation: evaluateRequirement(requirement) } : null;
  }
  for (const requirement of activeRequirements) {
    const index = (requirement.items || []).findIndex((item) => item.id === reference.id);
    if (index >= 0) {
      const requirementEvaluation = evaluateRequirement(requirement);
      return { requirement, item: requirement.items[index], evaluation: requirementEvaluation.items[index] };
    }
  }
  return null;
}

function renderMapRequirementCard(reference) {
  const match = findRequirementReference(reference);
  const satisfied = Boolean(match?.evaluation?.satisfied);
  const status = match?.evaluation?.label || "Open requirement details";
  const targetId = reference.scope === "requirement" ? reference.id : reference.id;
  return `<button class="map-requirement-node ${satisfied ? "satisfied" : ""}" type="button" data-map-requirement="${escapeHtml(targetId)}" data-map-requirement-scope="${escapeHtml(reference.scope || "item")}">
    <span class="map-requirement-top"><strong>${escapeHtml(reference.label)}</strong><em>${escapeHtml(reference.credits || "")}</em></span>
    <span class="map-requirement-status">${satisfied ? "✓ Fulfilled" : escapeHtml(status)}</span>
  </button>`;
}


function getSamplePlanMapSlots() {
  const result = [];
  const quarters = app.major.samplePlan?.quarters || {};

  for (const quarter of QUARTERS) {
    const items = quarters[quarter.id] || [];
    items.forEach((item, index) => {
      if (!String(item || "").startsWith("SLOT:")) return;
      const slot = typeof parsePlanSlot === "function"
        ? parsePlanSlot(item)
        : (() => {
            const payload = String(item).slice(5);
            const match = payload.match(/^(\d+(?:\.\d+)?):(.*)$/);
            return match
              ? { credits: Number(match[1]), label: match[2].trim(), raw: item }
              : { credits: 0, label: payload.trim(), raw: item };
          })();

      result.push({
        ...slot,
        quarterId: quarter.id,
        quarterText: `Year ${quarter.year} ${quarter.season}`,
        key: `${quarter.id}-${index}-${item}`
      });
    });
  }

  return result;
}

function mapGroupText(group) {
  return `${group.id || ""} ${group.label || ""} ${group.shortLabel || ""} ${group.description || ""}`.toLowerCase();
}

function firstMapGroup(groups, patterns) {
  for (const pattern of patterns) {
    const match = groups.find((group) => pattern.test(mapGroupText(group)));
    if (match) return match.id;
  }
  return null;
}

function explicitCourseCodesFromSlotLabel(label) {
  return [...String(label || "").matchAll(/\b(?:AA|A A|AMATH|BIOEN|CHEM E|CHEM|CEE|CSE|EE|E E|ENGR|HCDE|IND E|MATH|ME|M E|MSE|MS E|NME|PHYS|STAT)\s+\d{3}[A-Z]?\b/gi)]
    .map((match) => normalizeCode(match[0]));
}

function chooseMapGroupForPlanSlot(slot, groups) {
  const label = String(slot.label || "").toLowerCase();
  const definition = app.major.plannerSlotPools?.[slot.label] || {};

  if (definition.mapGroup && groups.some((group) => group.id === definition.mapGroup)) {
    return definition.mapGroup;
  }

  const explicitCodes = explicitCourseCodesFromSlotLabel(slot.label);
  if (explicitCodes.length) {
    const exactGroup = groups.find((group) => {
      const codes = new Set((group.courses || []).map(normalizeCode));
      return explicitCodes.some((code) => codes.has(code));
    });
    if (exactGroup) return exactGroup.id;
  }

  if (/unassigned|graduation credits?|free elective|general elective/.test(label)) {
    return firstMapGroup(groups, [/free/, /elective/]) || groups.at(-1)?.id;
  }

  if (/composition|writing|a\s*&\s*h|arts?\s*&?\s*humanities|ssc|social sciences?|diversity|foreign language|reasoning|areas? of inquiry/.test(label)) {
    return firstMapGroup(groups, [/general.education/, /general studies?/, /areas? of inquiry/]);
  }

  if (/math|statistics?/.test(label) && !/science/.test(label)) {
    return firstMapGroup(groups, [/mathematics/, /\bmath\b/, /statistics/]);
  }

  if (/science|natural science|nsc|biology|chemistry|physics/.test(label)) {
    return firstMapGroup(groups, [/\bscience/, /math.*science/]);
  }

  if (/engineering fundamentals?/.test(label)) {
    return firstMapGroup(groups, [/fundamentals?/]);
  }

  if (/capstone/.test(label)) {
    return firstMapGroup(groups, [/capstone/, /major core/, /\bcore\b/]);
  }

  if (/engineering\s*&?\s*science elective/.test(label)) {
    return firstMapGroup(groups, [/engineering.*science/, /approved engineering/, /elective/]);
  }

  if (/engineering elective/.test(label)) {
    return firstMapGroup(groups, [/approved engineering/, /engineering electives?/, /elective/]);
  }

  if (/technical elective|option elective|advanced .*elective|senior elective|major elective|bioen elective|cse senior elective|mse technical elective|hcde elective|ind e technical elective/.test(label)) {
    return firstMapGroup(groups, [/technical elective/, /senior elective/, /advanced/, /options?/, /electives?/]);
  }

  if (/professional issues/.test(label)) {
    return firstMapGroup(groups, [/advanced/, /core/, /elective/]);
  }

  const poolCodes = (definition.courses || []).map(normalizeCode);
  if (poolCodes.length) {
    let best = null;
    let bestCount = 0;
    for (const group of groups) {
      const groupCodes = new Set((group.courses || []).map(normalizeCode));
      const overlap = poolCodes.reduce((count, code) => count + (groupCodes.has(code) ? 1 : 0), 0);
      if (overlap > bestCount) {
        best = group.id;
        bestCount = overlap;
      }
    }
    if (best) return best;
  }

  const ignored = new Set(["approved", "additional", "course", "courses", "credit", "credits", "elective", "requirement", "requirements", "with", "and", "or"]);
  const tokens = label.split(/[^a-z0-9]+/).filter((token) => token.length > 2 && !ignored.has(token));
  let best = null;
  let bestScore = 0;
  for (const group of groups) {
    const haystack = mapGroupText(group);
    const score = tokens.reduce((sum, token) => sum + (haystack.includes(token) ? 1 : 0), 0);
    if (score > bestScore) {
      best = group.id;
      bestScore = score;
    }
  }
  if (best) return best;

  return firstMapGroup(groups, [/general.education/, /free/]) || groups.at(-1)?.id;
}

function getMapPlanSlotsByGroup(groups) {
  const result = new Map(groups.map((group) => [group.id, []]));
  for (const slot of getSamplePlanMapSlots()) {
    const groupId = chooseMapGroupForPlanSlot(slot, groups);
    if (!result.has(groupId)) result.set(groupId, []);
    result.get(groupId).push(slot);
  }
  return result;
}

function renderMapPlanSlotCard(slot, rawQuery = "") {
  const query = String(rawQuery || "").toLowerCase();
  const matches = !query || `${slot.label} ${slot.quarterText}`.toLowerCase().includes(query);
  const currentlyInPlan = (app.progress.plan?.[slot.quarterId] || []).includes(slot.raw);

  return `<button class="map-plan-slot-node ${matches ? "" : "dimmed"}" type="button"
    data-map-plan-slot="${escapeHtml(slot.raw)}"
    data-map-plan-quarter="${escapeHtml(slot.quarterId)}">
    <span class="map-plan-slot-top">
      <strong>${escapeHtml(slot.label)}</strong>
      <em>${formatNumber(slot.credits)} cr</em>
    </span>
    <span class="map-plan-slot-status">${currentlyInPlan ? "Choose course" : "Suggested"} · ${escapeHtml(slot.quarterText)}</span>
  </button>`;
}

function openMapPlanSlot(item, quarterId) {
  switchView("planner");
  requestAnimationFrame(() => {
    if (typeof beginFillPlanSlot === "function") {
      beginFillPlanSlot(item, quarterId);
    } else {
      const quarterSelect = $("#planner-add-quarter");
      if (quarterSelect) quarterSelect.value = quarterId;
      showToast("Choose a course for this requirement in the four-year planner.");
    }
    document.querySelector(`[data-quarter="${quarterId}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
}

function getApExam(examId) {
  return (app.apCredit.exams || []).find((exam) => exam.id === examId) || null;
}

function getApAward(examId, score = null) {
  const exam = getApExam(examId);
  const numericScore = Number(score ?? app.progress.apSelections[examId]);
  return exam?.awards?.find((award) => (award.scores || []).includes(numericScore)) || null;
}

function apSourcesForCourse(code) {
  const normalized = normalizeCode(code);
  return Object.entries(app.progress.apSelections || {}).flatMap(([examId, score]) => {
    const award = getApAward(examId, score);
    if (!(award?.courses || []).map(normalizeCode).includes(normalized)) return [];
    const exam = getApExam(examId);
    return [{ id: examId, label: `AP ${exam?.name || examId} (${score})` }];
  });
}

function hasTransferCredit(code) {
  return Boolean(app.progress.transferCourses?.[normalizeCode(code)]);
}

function externalSourcesForCourse(code) {
  const normalized = normalizeCode(code);
  const sources = apSourcesForCourse(normalized);
  if (hasTransferCredit(normalized)) sources.push({ id: "transfer", label: app.progress.transferCourses[normalized] || "Running Start / college credit" });
  return sources;
}

function isManuallyFulfilled(code) {
  return Boolean(app.progress.fulfilled[normalizeCode(code)]);
}

function isFulfilled(code) {
  const normalized = normalizeCode(code);
  return isManuallyFulfilled(normalized) || externalSourcesForCourse(normalized).length > 0;
}

function fulfilledCourseCodes() {
  const result = new Set(Object.keys(app.progress.fulfilled || {}).map(normalizeCode));
  for (const code of Object.keys(app.progress.transferCourses || {})) result.add(normalizeCode(code));
  for (const [examId, score] of Object.entries(app.progress.apSelections || {})) {
    for (const code of getApAward(examId, score)?.courses || []) result.add(normalizeCode(code));
  }
  return [...result].filter(isFulfilled);
}

function fulfillmentSourceLabels(code) {
  const normalized = normalizeCode(code);
  const labels = externalSourcesForCourse(normalized).map((source) => source.label);
  if (isManuallyFulfilled(normalized)) labels.unshift(app.progress.fulfillmentSources[normalized] || "Completed UW course");
  return labels;
}

function plannedQuarter(code) {
  const normalized = normalizeCode(code);
  for (const quarter of QUARTERS) {
    if ((app.progress.plan[quarter.id] || []).includes(normalized)) return quarter.id;
  }
  return null;
}

function prerequisitesSatisfied(code, extraFulfilled = new Set()) {
  const groups = getPrerequisiteGroups(code);
  return groups.every((group) => group.some((prereq) => prerequisiteOptionSatisfied(prereq, extraFulfilled)));
}

function courseStatus(code) {
  const normalized = normalizeCode(code);
  if (isFulfilled(normalized)) return "fulfilled";
  if (plannedQuarter(normalized)) return "planned";
  const course = getCourse(normalized);
  const override = app.major.courseOverrides?.[normalized];
  const hasCuratedRule = override && Object.prototype.hasOwnProperty.call(override, "prerequisiteGroups");
  const catalogIsLive = course.sourceType === "official-live";
  const hasCatalogRule = Boolean(course.prerequisiteText) || (course.prerequisiteCodes || []).length > 0;
  if (!hasCuratedRule && !catalogIsLive && !hasCatalogRule && (override?.prerequisiteAccuracy === "catalog" || course.sourceType === "major-definition")) return "unknown";
  return prerequisitesSatisfied(normalized) ? "available" : "locked";
}

function allMajorCodes() {
  return [...new Set(app.major.mapGroups.flatMap((group) => group.courses).map(normalizeCode))];
}

function getMajorSuccessors(code, visibleOnly = false) {
  const normalized = normalizeCode(code);
  const candidates = visibleOnly ? getVisibleMapGroups().flatMap((group) => group.courses) : allMajorCodes();
  return [...new Set(candidates.filter((candidate) =>
    getPrerequisiteGroups(candidate).some((group) => expandedPrerequisiteOptions(group).includes(normalized))
  ))];
}

function newlyUnlockedBy(code) {
  const normalized = normalizeCode(code);
  if (isFulfilled(normalized)) return [];
  const extra = new Set([normalized]);
  return getMajorSuccessors(normalized).filter((successor) =>
    courseStatus(successor) === "locked" && prerequisitesSatisfied(successor, extra)
  );
}

function updateMapTopScrollbar() {
  const main = $("#map-scroll");
  const stage = $("#map-stage");
  const top = $("#map-scroll-top");
  const content = $("#map-scroll-top-content");
  if (!main || !stage || !top || !content) return;
  content.style.width = `${Math.max(stage.scrollWidth, main.clientWidth)}px`;
  if (!app.mapScrollSyncing) top.scrollLeft = main.scrollLeft;
}

function syncMapScrollFromMain() {
  const main = $("#map-scroll");
  const top = $("#map-scroll-top");
  if (!main || !top || app.mapScrollSyncing) return;
  app.mapScrollSyncing = true;
  top.scrollLeft = main.scrollLeft;
  requestAnimationFrame(() => { app.mapScrollSyncing = false; });
}

function syncMapScrollFromTop() {
  const main = $("#map-scroll");
  const top = $("#map-scroll-top");
  if (!main || !top || app.mapScrollSyncing) return;
  app.mapScrollSyncing = true;
  main.scrollLeft = top.scrollLeft;
  requestAnimationFrame(() => { app.mapScrollSyncing = false; });
}

function updatePanButton() {
  const button = $("#pan-map-button");
  const scroll = $("#map-scroll");
  if (!button || !scroll) return;
  button.setAttribute("aria-pressed", app.mapPanEnabled ? "true" : "false");
  button.textContent = app.mapPanEnabled ? "Pan map: on" : "Pan map: off";
  scroll.classList.toggle("pan-enabled", app.mapPanEnabled);
}

function toggleMapPan() {
  app.mapPanEnabled = !app.mapPanEnabled;
  updatePanButton();
  showToast(app.mapPanEnabled
    ? "Pan mode on. Drag with the left mouse button, or right-drag anytime."
    : "Pan mode off. Right-drag still pans the map.");
}

function startMapPan(event) {
  const useRightButton = event.button === 2;
  const useToggleButton = app.mapPanEnabled && event.button === 0;
  if (!useRightButton && !useToggleButton) return;

  const scroll = $("#map-scroll");
  if (!scroll) return;
  event.preventDefault();
  app.mapDidPan = false;
  app.mapPanState = {
    pointerId: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    left: scroll.scrollLeft,
    top: scroll.scrollTop
  };
  scroll.classList.add("panning");
  try { scroll.setPointerCapture(event.pointerId); } catch (_) {}
}

function moveMapPan(event) {
  const state = app.mapPanState;
  const scroll = $("#map-scroll");
  if (!state || !scroll || state.pointerId !== event.pointerId) return;
  const dx = event.clientX - state.x;
  const dy = event.clientY - state.y;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) app.mapDidPan = true;
  scroll.scrollLeft = state.left - dx;
  scroll.scrollTop = state.top - dy;
}

function endMapPan(event) {
  const state = app.mapPanState;
  const scroll = $("#map-scroll");
  if (!state || !scroll || state.pointerId !== event.pointerId) return;
  app.mapPanState = null;
  scroll.classList.remove("panning");
  try { scroll.releasePointerCapture(event.pointerId); } catch (_) {}
}

function renderMap() {
  const query = normalizeCode($("#map-search")?.value || "");
  const rawQuery = ($("#map-search")?.value || "").trim().toLowerCase();
  const availableOnly = $("#available-only")?.checked;
  const groups = getVisibleMapGroups();
  const planSlotsByGroup = getMapPlanSlotsByGroup(groups);
  const selected = app.selectedCode;
  const neighbors = new Set(selected ? [selected, ...getMajorSuccessors(selected), ...getPrerequisiteGroups(selected).flatMap(expandedPrerequisiteOptions)] : []);

  $("#map-columns").innerHTML = groups.map((group) => {
    const nodes = group.courses.map((code) => {
      const course = getCourse(code);
      const status = courseStatus(code);
      const matches = !rawQuery || course.code.toLowerCase().includes(rawQuery) || course.title.toLowerCase().includes(rawQuery);
      const hidden = availableOnly && status !== "available" && code !== selected;
      const dimmed = (rawQuery && !matches) || (selected && !neighbors.has(code));
      return `
        <article class="course-node ${status} ${code === selected ? "selected" : ""} ${dimmed ? "dimmed" : ""} ${hidden ? "hidden-node" : ""}"
          data-course-code="${escapeHtml(code)}" id="node-${safeId(code)}" tabindex="0">
          <span class="node-port left" aria-hidden="true"></span><span class="node-port right" aria-hidden="true"></span>
          <div class="node-top">
            <span class="node-code">${escapeHtml(course.code)}</span>
            <span class="node-credits">${escapeHtml(course.credits || "?")} cr</span>
          </div>
          <div class="node-category">${escapeHtml(mapCategory(code))}</div>
          <div class="node-title">${escapeHtml(course.title)}</div>
          <div class="node-bottom">
            <span class="status-label">${statusText(status)}</span>
            <span class="node-actions">
              ${externalSourcesForCourse(code).length ? `<span class="external-credit-badge" title="${escapeHtml(fulfillmentSourceLabels(code).join(" · "))}">CREDIT</span>` : ""}
              <label class="course-check" title="Already fulfilled" onclick="event.stopPropagation()">
                <input type="checkbox" data-action="toggle-fulfilled" data-code="${escapeHtml(code)}" ${isFulfilled(code) ? "checked" : ""} aria-label="Mark ${escapeHtml(code)} fulfilled">
              </label>
            </span>
          </div>
        </article>`;
    }).join("");
    const requirementCards = (group.requirementRefs || []).map(renderMapRequirementCard).join("");
    const planSlots = planSlotsByGroup.get(group.id) || [];
    const planSlotCards = planSlots.map((slot) => renderMapPlanSlotCard(slot, rawQuery)).join("");
    const itemCount = group.courses.length + (group.requirementRefs || []).length + planSlots.length;
    return `
      <section class="map-column ${group.courses.length > 14 ? "dense" : ""} ${!group.courses.length ? "requirements-only" : ""}" data-group="${escapeHtml(group.id)}">
        <div class="map-column-header">
          <div class="map-column-title-row">
            <span>${escapeHtml(group.shortLabel || group.label)}</span>
            <b>${escapeHtml(group.credits || `${itemCount} items`)}</b>
          </div>
          ${group.shortLabel ? `<strong>${escapeHtml(group.label)}</strong>` : ""}
          ${group.description ? `<p>${escapeHtml(group.description)}</p>` : ""}
        </div>
        ${requirementCards ? `<div class="map-requirement-list">${requirementCards}</div>` : ""}
        ${planSlotCards ? `<div class="map-plan-slot-section"><div class="map-plan-slot-heading">Course placeholders</div><div class="map-plan-slot-list">${planSlotCards}</div></div>` : ""}
        <div class="map-node-list">${nodes}</div>
      </section>`;
  }).join("");

  renderCoursePanel();
  const token = ++app.mapRenderToken;
  requestAnimationFrame(() => { if (token === app.mapRenderToken) drawMapEdges(); });
}

function safeId(value) {
  return value.replace(/[^A-Za-z0-9_-]/g, "-");
}

function statusText(status) {
  return { fulfilled: "Fulfilled", planned: "Planned", available: "Available next", locked: "Prerequisites needed", unknown: "Check current catalog" }[status] || status;
}

function drawMapEdges() {
  if (app.activeView !== "map") return;
  const stage = $("#map-stage");
  const svg = $("#map-edges");
  if (!stage || !svg) return;
  const stageRect = stage.getBoundingClientRect();
  const paths = [];
  const visibleCodes = new Set($$(".course-node:not(.hidden-node)", stage).map((node) => node.dataset.courseCode));
  const selected = app.selectedCode;
  const showAll = Boolean($("#show-all-connections")?.checked);

  for (const targetCode of visibleCodes) {
    const target = $(`#node-${safeId(targetCode)}`);
    if (!target) continue;
    for (const sourceCode of new Set(getPrerequisiteGroups(targetCode).flatMap(expandedPrerequisiteOptions))) {
      if (!visibleCodes.has(sourceCode)) continue;
      const isIncoming = targetCode === selected;
      const isOutgoing = sourceCode === selected;
      if (!showAll && !isIncoming && !isOutgoing) continue;
      const source = $(`#node-${safeId(sourceCode)}`);
      if (!source) continue;
      const a = source.getBoundingClientRect();
      const b = target.getBoundingClientRect();
      const sameColumn = source.closest(".map-column") === target.closest(".map-column");
      const y1 = a.top + a.height / 2 - stageRect.top;
      const y2 = b.top + b.height / 2 - stageRect.top;
      let d;
      if (sameColumn) {
        const x1 = a.right - stageRect.left;
        const x2 = b.right - stageRect.left;
        const separation = Math.abs(y2 - y1);
        const loopX = Math.max(x1, x2) + 28 + Math.min(70, separation * .11);
        d = `M ${x1} ${y1} C ${loopX} ${y1}, ${loopX} ${y2}, ${x2} ${y2}`;
      } else {
        const x1 = a.right - stageRect.left;
        const x2 = b.left - stageRect.left;
        if (x2 > x1 + 16) {
          const bend = Math.max(34, (x2 - x1) * .46);
          d = `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`;
        } else {
          const loopX = Math.max(x1, x2) + 48;
          d = `M ${x1} ${y1} C ${loopX} ${y1}, ${loopX} ${y2}, ${x2} ${y2}`;
        }
      }
      const kind = isIncoming ? "incoming" : isOutgoing ? "outgoing" : "default";
      paths.push(`<path class="map-edge-halo ${kind}" d="${d}"/>`);
      paths.push(`<path class="map-edge ${kind}" marker-end="url(#arrow-${kind})" d="${d}"/>`);
    }
  }
  svg.setAttribute("width", String(stage.scrollWidth));
  svg.setAttribute("height", String(stage.scrollHeight));
  svg.setAttribute("viewBox", `0 0 ${stage.scrollWidth} ${stage.scrollHeight}`);
  svg.innerHTML = `<defs>
    <marker id="arrow-default" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 z" class="arrow-default"/></marker>
    <marker id="arrow-incoming" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L9,4.5 L0,9 z" class="arrow-incoming"/></marker>
    <marker id="arrow-outgoing" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L9,4.5 L0,9 z" class="arrow-outgoing"/></marker>
  </defs>${paths.join("")}`;
  updateMapTopScrollbar();
}

function handleMapClick(event) {
  const planSlotNode = event.target.closest("[data-map-plan-slot]");
  if (planSlotNode) {
    openMapPlanSlot(planSlotNode.dataset.mapPlanSlot, planSlotNode.dataset.mapPlanQuarter);
    return;
  }
  const requirementNode = event.target.closest("[data-map-requirement]");
  if (requirementNode) {
    const id = requirementNode.dataset.mapRequirement;
    const scope = requirementNode.dataset.mapRequirementScope || "item";
    switchView("requirements");
    requestAnimationFrame(() => {
      const selector = scope === "requirement" ? `#requirement-${safeId(id)}` : `#requirement-item-${safeId(id)}`;
      document.querySelector(selector)?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    return;
  }
  const checkbox = event.target.closest('[data-action="toggle-fulfilled"]');
  if (checkbox) {
    setFulfilled(checkbox.dataset.code, checkbox.checked);
    return;
  }
  if (app.mapDidPan) {
    app.mapDidPan = false;
    return;
  }
  const node = event.target.closest(".course-node");
  if (!node) {
    if (app.selectedCode) {
      app.selectedCode = null;
      renderMap();
    }
    return;
  }
  app.selectedCode = node.dataset.courseCode;
  renderMap();
}

function setFulfilled(code, fulfilled, source = null) {
  const normalized = normalizeCode(code);
  if (fulfilled) {
    app.progress.fulfilled[normalized] = true;
    app.progress.fulfillmentSources[normalized] = source || app.progress.fulfillmentSources[normalized] || "Completed UW course";
  } else {
    delete app.progress.fulfilled[normalized];
    delete app.progress.fulfillmentSources[normalized];
    if (externalSourcesForCourse(normalized).length) {
      showToast(`${normalized} is still fulfilled by AP or transfer credit. Remove that source in the AP & transfer credit tab.`);
    }
  }
  saveProgress();
  renderAll();
}

function renderCoursePanel() {
  const panel = $("#course-panel");
  if (!app.selectedCode) {
    const available = allMajorCodes().filter((code) => courseStatus(code) === "available").slice(0, 12);
    panel.innerHTML = `
      <div class="empty-panel">
        <div>
          <div class="empty-panel-icon">⌘</div>
          <h2>Select a course</h2>
          <p>Click a course to inspect prerequisites, mark it fulfilled, and see what it unlocks.</p>
          <div class="detail-section" style="text-align:left">
            <h3>Available from the start</h3>
            <div class="course-link-list">${available.map(courseChip).join("")}</div>
          </div>
        </div>
      </div>`;
    return;
  }

  const course = getCourse(app.selectedCode);
  const status = courseStatus(course.code);
  const groups = getPrerequisiteGroups(course).map(expandedPrerequisiteOptions);
  const successors = getMajorSuccessors(course.code).slice(0, 20);
  const unlocked = newlyUnlockedBy(course.code);
  const source = app.progress.fulfillmentSources[course.code] || "Completed UW course";
  const externalSources = externalSourcesForCourse(course.code);
  const manualFulfilled = isManuallyFulfilled(course.code);
  const planQuarter = plannedQuarter(course.code);
  const sourceUrl = course.sourceUrl || "https://www.washington.edu/students/crscat/";
  const approximate = !app.major.courseOverrides?.[course.code] && groups.length > 0;

  panel.innerHTML = `
    <div class="detail-code">
      <div><div class="eyebrow">COURSE</div><h2>${escapeHtml(course.code)}</h2></div>
      <span class="status-chip ${status}">${statusText(status)}</span>
    </div>
    <div class="detail-title">${escapeHtml(course.title)}</div>
    <div class="course-link-list">
      <span class="tiny-chip">${escapeHtml(course.credits || "?")} credits</span>
      ${course.areas ? `<span class="tiny-chip">${escapeHtml(course.areas)}</span>` : ""}
      ${course.offered ? `<span class="tiny-chip">${escapeHtml(course.offered)}</span>` : ""}
    </div>
    ${course.description ? `<p class="detail-description">${escapeHtml(course.description)}</p>` : `<p class="detail-description">A live catalog sync will add the current official description when it is available.</p>`}

    <div class="detail-section">
      <div class="fulfillment-box">
        <label><input type="checkbox" data-panel-action="fulfilled" data-code="${escapeHtml(course.code)}" ${isFulfilled(course.code) ? "checked" : ""}> Already fulfilled</label>
        <select data-panel-action="source" data-code="${escapeHtml(course.code)}" ${manualFulfilled ? "" : "disabled"}>
          ${["Completed UW course","AP / IB credit","Running Start / college credit","Transfer or equivalent credit","Other approved fulfillment"].map((value) => `<option ${source === value ? "selected" : ""}>${value}</option>`).join("")}
        </select>
        ${externalSources.length ? `<div class="external-source-list">${externalSources.map((entry) => `<span>${escapeHtml(entry.label)}</span>`).join("")}</div><a class="credit-manage-link" href="#" data-panel-action="open-credits">Manage outside credit →</a>` : ""}
      </div>
    </div>

    <div class="detail-section">
      <h3>Prerequisites</h3>
      ${groups.length ? `<p class="prereq-help">Complete every numbered row. Within a row, any one course separated by <strong>OR</strong> works. Honors and accelerated substitutions are shown as additional options.</p><div class="prereq-groups">${groups.map((group, groupIndex) => `
        <div class="prereq-group ${group.some(isFulfilled) ? "satisfied" : "missing"}"><span class="prereq-number">${groupIndex + 1}</span><div class="prereq-options">${group.map((code, index) => `${index ? '<span class="prereq-or">OR</span>' : ''}${courseChip(code)}`).join("")}</div><span class="prereq-state">${group.some(isFulfilled) ? "✓ met" : "needed"}</span></div>`).join("")}</div>` : `<p class="detail-description">No required prior course is represented in this map.</p>`}
      ${course.otherPrerequisites ? `<div class="other-prereq"><strong>Placement, exam, or concurrent-entry options</strong><span>${escapeHtml(course.otherPrerequisites)}</span></div>` : ""}
      ${approximate ? `<p class="requirement-note">The all-course catalog relationship is an estimate generated from catalog text. Read the official prerequisite text before registering.</p>` : ""}
    </div>

    ${unlocked.length ? `<div class="detail-section"><h3>Completing this would unlock</h3><div class="course-link-list">${unlocked.map(courseChip).join("")}</div></div>` : ""}
    ${successors.length ? `<div class="detail-section"><h3>Courses that depend on it</h3><div class="course-link-list">${successors.map(courseChip).join("")}</div></div>` : ""}

    <div class="detail-section">
      <h3>Add to four-year plan</h3>
      <div class="plan-add-row">
        <select data-panel-quarter>${QUARTERS.map((quarter) => `<option value="${quarter.id}" ${planQuarter === quarter.id ? "selected" : ""}>Year ${quarter.year} · ${quarter.season}</option>`).join("")}</select>
        <button class="button primary" data-panel-action="add-plan" data-code="${escapeHtml(course.code)}">${planQuarter ? "Move" : "Add"}</button>
      </div>
    </div>

    <div class="detail-section">
      ${course.prerequisiteText ? `<h3>Official prerequisite text</h3><p class="detail-description">${escapeHtml(course.prerequisiteText)}</p>` : ""}
      <a class="source-link" href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Open UW catalog source ↗</a>
    </div>`;
}

function courseChip(code) {
  const normalized = normalizeCode(code);
  return `<button class="course-link-chip ${isFulfilled(normalized) ? "done" : ""}" type="button" data-course-link="${escapeHtml(normalized)}">${escapeHtml(normalized)}</button>`;
}

function prerequisiteChip(code) {
  const normalized = normalizeCode(code);
  const via = prerequisiteFulfillmentVia(normalized);
  const substituted = via && via !== normalized;
  const label = substituted ? `${normalized} · via ${via}` : normalized;
  const title = substituted ? `${normalized} prerequisite satisfied by ${via}` : normalized;
  return `<button class="course-link-chip ${via ? "done" : ""} ${substituted ? "substituted" : ""}" type="button" data-course-link="${escapeHtml(via || normalized)}" title="${escapeHtml(title)}">${escapeHtml(label)}</button>`;
}

function handleCoursePanelClick(event) {
  const linked = event.target.closest("[data-course-link]");
  if (linked) {
    app.selectedCode = linked.dataset.courseLink;
    renderMap();
    scrollNodeIntoView(app.selectedCode);
    return;
  }
  const action = event.target.closest("[data-panel-action]");
  if (!action) return;
  if (action.dataset.panelAction === "add-plan") {
    const quarter = $("[data-panel-quarter]", $("#course-panel")).value;
    addCourseToPlan(action.dataset.code, quarter);
  }
  if (action.dataset.panelAction === "open-credits") {
    event.preventDefault();
    switchView("credits");
  }
}

function handleCoursePanelChange(event) {
  const action = event.target.dataset.panelAction;
  const code = event.target.dataset.code;
  if (action === "fulfilled") setFulfilled(code, event.target.checked);
  if (action === "source") {
    app.progress.fulfillmentSources[normalizeCode(code)] = event.target.value;
    saveProgress();
  }
}

function scrollNodeIntoView(code) {
  requestAnimationFrame(() => $(`#node-${safeId(code)}`)?.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" }));
}

function fulfilledCredits() {
  return fulfilledCourseCodes().reduce((total, code) => total + numericCredits(getCourse(code).credits), 0);
}

function plannedCredits() {
  return Object.values(app.progress.plan).flat().reduce((total, item) => {
    const slot = parsePlanSlot(item);
    return total + (slot ? slot.credits : numericCredits(getCourse(item).credits));
  }, 0);
}

function areaMatches(course, area) {
  const text = String(course.areas || "").toUpperCase();
  if (area === "A&H") return text.includes("A&H") || text.includes("VLPA");
  if (area === "SSc") return text.includes("SSC") || text.includes("I&S");
  
  if (area === "A&H/SSc") {
    return areaMatches(course, "A&H") || areaMatches(course, "SSc");
  }

  if (area === "A&H/SSc/NSc") {
    return (
      areaMatches(course, "A&H") || areaMatches(course, "SSc") || areaMatches(course, "NSc")
    );
  }

  if (area === "C") {
    return /(^|[,\s])C($|[,\s])/.test(text) || text.includes("COMPOSITION");
  }
  
  return text.includes(area.toUpperCase());
}

function areaCredits(area) {
  return fulfilledCourseCodes().reduce((total, code) => {
    const course = getCourse(code);
    return total + (areaMatches(course, area) ? numericCredits(course.credits) : 0);
  }, 0);
}

function evaluateItem(item) {
  const overridden = Boolean(app.progress.requirementOverrides[item.id]);
  const courses = (item.courses || []).map(normalizeCode);
  const completed = courses.filter(isFulfilled);
  const credits = completed.reduce((sum, code) => sum + numericCredits(getCourse(code).credits), 0);
  let satisfied = overridden;
  let current = 0;
  let target = 1;
  let label = "";

  if (item.type === "path-choice") {
    const paths = (item.paths || []).map((path) => {
      const pathCourses = (path.courses || []).map(normalizeCode);
      const pathCompleted = pathCourses.filter(isFulfilled);
      return { ...path, courses: pathCourses, completed: pathCompleted, satisfied: pathCompleted.length === pathCourses.length, ratio: pathCourses.length ? pathCompleted.length / pathCourses.length : 0 };
    });
    const completePath = paths.find((path) => path.satisfied);
    const bestPath = completePath || paths.sort((a, b) => b.ratio - a.ratio)[0] || { label: "Path", courses: [], completed: [], ratio: 0 };
    current = bestPath.completed.length;
    target = bestPath.courses.length || 1;
    satisfied ||= Boolean(completePath);
    label = completePath ? `${completePath.label} complete` : `${current}/${target} on ${bestPath.label}`;
    return { satisfied, current, target, label, completed: bestPath.completed, credits: bestPath.completed.reduce((sum, code) => sum + numericCredits(getCourse(code).credits), 0), overridden, paths };
  } else if (item.type === "all") {
    current = completed.length;
    target = courses.length;
    satisfied ||= current >= target;
    label = `${current}/${target} courses`;
  } else if (item.type === "one") {
    current = completed.length ? 1 : 0;
    target = 1;
    satisfied ||= current >= 1;
    label = satisfied ? "Satisfied" : "Choose one";
  } else if (item.type === "count") {
    current = completed.length;
    target = item.minCount;
    satisfied ||= current >= target;
    label = `${current}/${target} courses`;
  } else if (item.type === "count-credit") {
    current = Math.min(completed.length / item.minCount, credits / item.minCredits);
    target = 1;
    satisfied ||= completed.length >= item.minCount && credits >= item.minCredits;
    label = `${completed.length}/${item.minCount} courses · ${formatNumber(credits)}/${item.minCredits} cr`;
  } else if (item.type === "pool") {
    current = credits;
    target = item.minCredits;
    satisfied ||= credits >= target;
    label = `${formatNumber(credits)}/${target} credits`;
  } else if (item.type === "additional-bucket") {
    const manual = Number(app.progress.manualCredits[item.id] || 0);
    const totalAreaCredits = areaCredits(item.area);
    current = Math.max(0, totalAreaCredits - Number(item.baseCredits || 0)) + manual;
    target = item.targetCredits;
    satisfied ||= current >= target;
    label = `${formatNumber(current)}/${target} additional credits`;
  } else if (item.type === "bucket") {
    const manual = Number(app.progress.manualCredits[item.id] || 0);
    current = areaCredits(item.area) + manual;
    target = item.targetCredits;
    satisfied ||= current >= target;
    label = `${formatNumber(current)}/${target} credits`;
  } else if (item.type === "check") {
    current = overridden ? 1 : 0;
    target = 1;
    satisfied = overridden;
    label = satisfied ? "Confirmed" : "Confirm manually";
  }
return { satisfied, current, target, label, completed, credits, overridden };
}

function courseLevel(code) {
  const match = normalizeCode(code).match(/\s(\d{3})[A-Z]?$/);
  return match ? Number(match[1]) : 0;
}

function evaluateExclusiveItem(item, usedCodes) {
  const overridden = Boolean(
    app.progress.requirementOverrides[item.id]
  );

  const courses = (item.courses || []).map(normalizeCode);

  const available = courses.filter(
    (code) => isFulfilled(code) && !usedCodes.has(code)
  );

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

    completed = available.slice(
      0,
      Math.min(available.length, needed)
    );

    current = completed.length;
    target = needed;
    satisfied ||= current >= target;
    label = `${current}/${target} courses`;
  } else if (item.type === "count-credit-level") {
    const neededCount = Number(item.minCount || 0);
    const neededCredits = Number(item.minCredits || 0);
    const minimumLevel = Number(item.minLevel || 400);
    const neededAtLevel = Number(item.minLevelCount || 0);

    const highLevel = available.filter(
      (code) => courseLevel(code) >= minimumLevel
    );

    const other = available.filter(
      (code) => courseLevel(code) < minimumLevel
    );

    completed.push(
      ...highLevel.slice(0, neededAtLevel)
    );

    const remaining = [
      ...highLevel.slice(neededAtLevel),
      ...other
    ];

    for (const code of remaining) {
      const credits = completed.reduce(
        (sum, entry) => (
          sum + numericCredits(getCourse(entry).credits)
        ),
        0
      );

      const levelCount = completed.filter(
        (entry) => courseLevel(entry) >= minimumLevel
      ).length;

      const requirementsMet = (
        completed.length >= neededCount
        && credits >= neededCredits
        && levelCount >= neededAtLevel
      );

      if (requirementsMet) {
        break;
      }

      completed.push(code);
    }

    const credits = completed.reduce(
      (sum, code) => (
        sum + numericCredits(getCourse(code).credits)
      ),
      0
    );

    const levelCount = completed.filter(
      (code) => courseLevel(code) >= minimumLevel
    ).length;

    current = Math.min(
      neededCount
        ? completed.length / neededCount
        : 1,
      neededCredits
        ? credits / neededCredits
        : 1,
      neededAtLevel
        ? levelCount / neededAtLevel
        : 1
    );

    target = 1;

    satisfied ||= (
      completed.length >= neededCount
      && credits >= neededCredits
      && levelCount >= neededAtLevel
    );

    label = (
      `${completed.length}/${neededCount} courses`
      + ` · ${formatNumber(credits)}/${neededCredits} cr`
      + ` · ${levelCount}/${neededAtLevel}`
      + ` at ${minimumLevel}-level`
    );
  } else if (item.type === "check") {
    current = overridden ? 1 : 0;
    target = 1;
    satisfied = overridden;
    label = satisfied
      ? "Confirmed"
      : "Confirm manually";
  } else {
    return evaluateItem(item);
  }

  if (!overridden) {
    completed.forEach(
      (code) => usedCodes.add(code)
    );
  }

  const credits = completed.reduce(
    (sum, code) => (
      sum + numericCredits(getCourse(code).credits)
    ),
    0
  );

  return {
    satisfied,
    current,
    target,
    label,
    completed,
    credits,
    overridden
  };
}

function evaluateExclusiveSet(setId) {
  const usedCodes = new Set();
  const results = new Map();

  const requirements = getActiveRequirements()
    .filter(
      (requirement) => (
        requirement.exclusiveSet === setId
      )
    )
    .sort(
      (a, b) => (
        Number(a.exclusivePriority || 0)
        - Number(b.exclusivePriority || 0)
      )
    );

  for (const requirement of requirements) {
    const overridden = Boolean(
      app.progress.requirementOverrides[
        requirement.id
      ]
    );

    const allocationSet = overridden
      ? new Set()
      : usedCodes;

    const items = (requirement.items || []).map(
      (item) => (
        evaluateExclusiveItem(
          item,
          allocationSet
        )
      )
    );

    const current = items.filter(
      (item) => item.satisfied
    ).length;

    results.set(
      requirement.id,
      {
        satisfied: (
          overridden
          || current === items.length
        ),
        current,
        target: items.length,
        items,
        label: `${current}/${items.length} parts`
      }
    );
  }

  return results;
}

function evaluateRequirement(requirement) {
  if (requirement.exclusiveSet) {
    return evaluateExclusiveSet(
      requirement.exclusiveSet
    ).get(requirement.id);
  }
  const overridden = Boolean(app.progress.requirementOverrides[requirement.id]);
  if (requirement.type === "group") {
    const items = requirement.items.map(evaluateItem);
    const current = items.filter((item) => item.satisfied).length;
    return { satisfied: overridden || current === items.length, current, target: items.length, items, label: `${current}/${items.length} parts` };
  }
  if (requirement.type === "pool") {
    const item = evaluateItem({ ...requirement, id: `${requirement.id}-pool` });
    return { ...item, satisfied: overridden || item.satisfied, items: [item] };
  }
  if (requirement.type === "manual") {
    const current = Number(app.progress.manualCredits[requirement.id] || 0);
    return { satisfied: overridden || current >= requirement.targetCredits, current, target: requirement.targetCredits, items: [], label: `${formatNumber(current)}/${requirement.targetCredits} credits` };
  }
  if (requirement.type === "total") {
    const current = fulfilledCredits() + Number(app.progress.manualCredits["total-extra"] || 0);
    return { satisfied: overridden || current >= requirement.targetCredits, current, target: requirement.targetCredits, items: [], label: `${formatNumber(current)}/${requirement.targetCredits} credits` };
  }
  return { satisfied: overridden, current: 0, target: 1, items: [], label: "" };
}

function renderRequirements() {
  const requirements = getActiveRequirements();
  const evaluations = requirements.map((requirement) => [requirement, evaluateRequirement(requirement)]);
  const completedRequirements = evaluations.filter(([, evaluation]) => evaluation.satisfied).length;
  const availableCount = allMajorCodes().filter((code) => courseStatus(code) === "available").length;
  const degreeCredits = fulfilledCredits() + Number(app.progress.manualCredits["total-extra"] || 0);

  $("#requirement-summary").innerHTML = [
    metricCard("Degree credits represented", `${formatNumber(degreeCredits)} / ${app.major.totalCredits}`, degreeCredits / app.major.totalCredits, "Courses marked fulfilled plus other completed credits"),
    metricCard("Requirement sections", `${completedRequirements} / ${requirements.length}`, completedRequirements / requirements.length, `${trackName(app.progress.track)} selected`),
    metricCard("Courses fulfilled", fulfilledCourseCodes().length, 0, "Includes UW, AP, Running Start, and transfer credit"),
    metricCard("Available next", availableCount, 0, "Based on fulfilled prerequisites")
  ].join("");

  $("#requirements-grid").innerHTML = evaluations.map(([requirement, evaluation]) => renderRequirementCard(requirement, evaluation)).join("");
}

function metricCard(label, value, ratio, caption) {
  return `<article class="metric-card">
    <div class="metric-label">${escapeHtml(label)}</div>
    <div class="metric-value">${escapeHtml(value)}</div>
    <div class="metric-caption">${escapeHtml(caption)}</div>
    ${ratio ? `<div class="metric-progress"><span style="width:${Math.min(100, ratio * 100)}%"></span></div>` : ""}
  </article>`;
}

function renderRequirementCard(requirement, evaluation) {
  const percent = evaluation.target ? Math.min(100, (evaluation.current / evaluation.target) * 100) : 0;
  let body = "";
  if (requirement.type === "group") {
    body = `<div class="requirement-items">${requirement.items.map((item, index) => renderRequirementItem(item, evaluation.items[index])).join("")}</div>`;
  } else if (requirement.type === "pool") {
    body = renderRequirementItem({ ...requirement, id: `${requirement.id}-pool`, label: "Approved option courses" }, evaluation.items[0]);
  } else if (requirement.type === "manual") {
    body = `<div class="requirement-item ${evaluation.satisfied ? "satisfied" : ""}">
      <div class="requirement-item-head"><span class="requirement-item-title">${escapeHtml(requirement.manualLabel || "Credits completed")}</span><span class="requirement-item-status">${evaluation.label}</span></div>
      ${manualCreditInput(requirement.id, app.progress.manualCredits[requirement.id] || 0, requirement.maxCredits || requirement.targetCredits)}
    </div>`;
  } else if (requirement.type === "total") {
    body = `<div class="requirement-item ${evaluation.satisfied ? "satisfied" : ""}">
      <div class="requirement-item-head"><span class="requirement-item-title">Other completed credits not represented above</span><span class="requirement-item-status">${evaluation.label}</span></div>
      ${manualCreditInput("total-extra", app.progress.manualCredits["total-extra"] || 0, requirement.targetCredits)}
    </div>`;
  }

  const displayTitle = requirement.sectionTitle || requirement.title;
  return `<article id="requirement-${safeId(requirement.id)}" class="requirement-card ${evaluation.satisfied ? "complete" : ""}">
    <div class="requirement-head">
      <div><div class="eyebrow">${evaluation.satisfied ? "COMPLETE" : "IN PROGRESS"}</div><h2>${escapeHtml(displayTitle)}</h2>${requirement.sectionTitle && requirement.title !== requirement.sectionTitle ? `<p class="requirement-track-name">${escapeHtml(requirement.title)}</p>` : ""}</div>
      <div class="requirement-score">${requirement.displayCredits ? `<span class="requirement-credit-pill">${escapeHtml(requirement.displayCredits)}</span>` : ""}<span>${escapeHtml(evaluation.label)}</span></div>
    </div>
    <div class="progress-bar"><span style="width:${percent}%"></span></div>
    ${body}
    ${requirement.note ? `<p class="requirement-note">${escapeHtml(requirement.note)}</p>` : ""}
    <label class="requirement-override"><input type="checkbox" data-requirement-override="${escapeHtml(requirement.id)}" ${app.progress.requirementOverrides[requirement.id] ? "checked" : ""}> Mark this entire requirement already fulfilled</label>
  </article>`;
}

function renderRequirementItem(item, evaluation) {
  const courses = item.courses || [];
  const showManual = item.type === "bucket" || item.type === "additional-bucket";
  const pathHtml = item.type === "path-choice" ? `<div class="requirement-paths">${(evaluation.paths || []).map((path) => `
    <div class="requirement-path ${path.satisfied ? "satisfied" : ""}">
      <div class="requirement-path-head"><strong>${escapeHtml(path.label)}</strong><span>${path.completed.length}/${path.courses.length}</span></div>
      <div class="requirement-course-list">${path.courses.map((code) => `
        <label class="requirement-course" title="${escapeHtml(getCourse(code).title)}">
          <input type="checkbox" data-requirement-course="${escapeHtml(code)}" ${isFulfilled(code) ? "checked" : ""}> ${escapeHtml(code)}
        </label>`).join("")}</div>
    </div>`).join("")}</div>` : "";
  return `<div id="requirement-item-${safeId(item.id)}" class="requirement-item ${evaluation.satisfied ? "satisfied" : ""}">
    <div class="requirement-item-head">
      <span class="requirement-item-title">${escapeHtml(item.label)}</span>
      <span class="requirement-item-status">${escapeHtml(evaluation.label)}</span>
    </div>
    ${pathHtml}
    ${courses.length ? `<div class="requirement-course-list">${courses.map((code) => `
      <label class="requirement-course" title="${escapeHtml(getCourse(code).title)}">
        <input type="checkbox" data-requirement-course="${escapeHtml(code)}" ${isFulfilled(code) ? "checked" : ""}> ${escapeHtml(code)}
      </label>`).join("")}</div>` : ""}
    ${showManual ? manualCreditInput(item.id, app.progress.manualCredits[item.id] || 0, item.targetCredits) : ""}
    ${item.note ? `<p class="requirement-note">${escapeHtml(item.note)}</p>` : ""}
    <label class="requirement-manual"><input type="checkbox" data-requirement-override="${escapeHtml(item.id)}" ${app.progress.requirementOverrides[item.id] ? "checked" : ""}> Already fulfilled by another approved course or credit</label>
  </div>`;
}

function manualCreditInput(id, value, max) {
  return `<label class="requirement-manual">Manually fulfilled credits <input type="number" min="0" max="${max}" step="1" value="${escapeHtml(value)}" data-manual-credit="${escapeHtml(id)}"></label>`;
}

function handleRequirementChange(event) {
  if (event.target.dataset.requirementCourse) {
    setFulfilled(event.target.dataset.requirementCourse, event.target.checked);
    return;
  }
  if (event.target.dataset.requirementOverride) {
    const id = event.target.dataset.requirementOverride;
    if (event.target.checked) app.progress.requirementOverrides[id] = true;
    else delete app.progress.requirementOverrides[id];
    saveProgress();
    renderRequirements();
    return;
  }
  if (event.target.dataset.manualCredit) {
    app.progress.manualCredits[event.target.dataset.manualCredit] = Math.max(0, Number(event.target.value || 0));
    saveProgress();
    renderRequirements();
  }
}


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
  app.plannerSelectedCourseCode = null;
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

function renderPlanner() {
  const addButton = $("#planner-add-button");
  if (addButton) addButton.textContent = app.pendingPlanSlot ? "Use course for requirement" : "Add course";
  const warnings = validatePlan();
  $("#planner-grid").innerHTML = [1,2,3,4].map((year) => {
    const quarters = QUARTERS.filter((quarter) => quarter.year === year);
    const yearCredits = quarters.reduce((sum, quarter) => sum + quarterCredits(quarter.id), 0);
    return `<section class="plan-year">
      <div class="year-heading"><h2>Year ${year}</h2><span>${formatNumber(yearCredits)} planned credits</span></div>
      <div class="year-quarters">${quarters.map((quarter) => renderQuarter(quarter, warnings)).join("")}</div>
    </section>`;
  }).join("");
  renderPlannerInsights(warnings);
  updatePlannerSearchResults();
}

function renderQuarter(quarter, warnings) {
  const items = app.progress.plan[quarter.id] || [];
  const warningCodes = new Set(warnings.filter((warning) => warning.quarter === quarter.id).map((warning) => warning.code));
  return `<article class="quarter" data-quarter="${quarter.id}">
    <div class="quarter-head"><h3>${quarter.season}</h3><span class="quarter-credit">${formatNumber(quarterCredits(quarter.id))} credits</span></div>
    <div class="plan-course-list">${items.length ? items.map((item) => renderPlanItem(item, quarter.id, warningCodes.has(item))).join("") : `<div class="empty-quarter">Drop a course here<br>or add one using the search above</div>`}</div>
  </article>`;
}

function renderPlanItem(item, quarterId, hasWarning) {
  if (isPlanSlot(item)) {
    const slot = parsePlanSlot(item);
    return `<div class="plan-course slot" draggable="true" data-plan-item="${escapeHtml(item)}" data-from-quarter="${quarterId}">
      <div class="plan-code">Requirement · ${formatNumber(slot.credits)} cr</div>
      <div class="plan-title">${escapeHtml(slot.label)}</div>
      <button class="slot-fill" type="button" data-fill-slot="${escapeHtml(item)}" data-quarter="${quarterId}">Choose course</button>
      <button class="plan-remove" type="button" data-remove-plan="${escapeHtml(item)}" data-quarter="${quarterId}" aria-label="Remove">×</button>
    </div>`;
  }
  const course = getCourse(item);
  return `<div class="plan-course ${isFulfilled(item) ? "fulfilled" : ""} ${hasWarning ? "warning" : ""}" draggable="true" data-plan-item="${escapeHtml(item)}" data-from-quarter="${quarterId}" data-open-course="${escapeHtml(item)}">
    <div class="plan-code">${escapeHtml(item)} · ${escapeHtml(course.credits || "?")} cr</div>
    <div class="plan-title">${escapeHtml(course.title)}</div>
    <button class="plan-remove" type="button" data-remove-plan="${escapeHtml(item)}" data-quarter="${quarterId}" aria-label="Remove">×</button>
  </div>`;
}

function quarterCredits(quarterId) {
  return (app.progress.plan[quarterId] || []).reduce((sum, item) => {
    const slot = parsePlanSlot(item);
    return sum + (slot ? slot.credits : numericCredits(getCourse(item).credits));
  }, 0);
}

function plannerCourseDisplay(courseOrCode) {
  const course = typeof courseOrCode === "string" ? getCourse(courseOrCode) : courseOrCode;
  const code = normalizeCode(course?.code || courseOrCode || "");
  const title = course?.title || getCourse(code).title || "Course information unavailable";
  return `${code} — ${title}`;
}

function openPlannerCourseMenu() {
  const menu = $("#planner-add-menu");
  const input = $("#planner-add-search");
  const toggle = $("#planner-course-toggle");
  if (!menu || !input) return;
  menu.hidden = false;
  input.setAttribute("aria-expanded", "true");
  if (toggle) toggle.setAttribute("aria-expanded", "true");
}

function closePlannerCourseMenu() {
  const menu = $("#planner-add-menu");
  const input = $("#planner-add-search");
  const toggle = $("#planner-course-toggle");
  if (!menu || !input) return;
  menu.hidden = true;
  input.setAttribute("aria-expanded", "false");
  input.removeAttribute("aria-activedescendant");
  if (toggle) toggle.setAttribute("aria-expanded", "false");
  app.plannerSearchIndex = -1;
}

function togglePlannerCourseMenu(event) {
  event.preventDefault();
  const menu = $("#planner-add-menu");
  const input = $("#planner-add-search");
  if (!menu || !input) return;
  if (menu.hidden) {
    updatePlannerSearchResults();
    openPlannerCourseMenu();
    input.focus();
  } else {
    closePlannerCourseMenu();
  }
}

function updatePlannerSearchResults() {
  const input = $("#planner-add-search");
  const menu = $("#planner-add-menu");
  if (!input || !menu) return;

  const query = input.value.trim().toLowerCase();
  const pendingSlot = app.pendingPlanSlot ? parsePlanSlot(app.pendingPlanSlot.item) : null;
  let matches = app.courses.filter((course) => course.campus === "Seattle");

  if (pendingSlot) {
    matches = matches.filter((course) => courseMatchesSlot(course, pendingSlot));
  }

  if (query && !app.plannerSelectedCourseCode) {
    matches = matches.filter((course) =>
      `${course.code} ${course.title}`.toLowerCase().includes(query)
    );
  } else if (!pendingSlot && !query) {
    const majorCodes = new Set(allMajorCodes());
    matches = matches.filter((course) => majorCodes.has(normalizeCode(course.code)));
  }

  matches = matches.slice(0, 60);
  app.plannerSearchMatches = matches;
  app.plannerSearchIndex = -1;

  const emptyMessage = pendingSlot
    ? `No matching courses found for ${pendingSlot.label}.`
    : "No matching courses found.";

  menu.innerHTML = matches.length
    ? matches.map((course, index) => `
      <button
        id="planner-course-option-${index}"
        class="planner-course-option"
        type="button"
        role="option"
        data-planner-course="${escapeHtml(course.code)}"
        aria-selected="false"
      >
        <span class="planner-option-code">${escapeHtml(course.code)}</span>
        <span class="planner-option-title">${escapeHtml(course.title)}</span>
        <span class="planner-option-credits">${escapeHtml(course.credits || "?")} cr</span>
      </button>
    `).join("")
    : `<div class="planner-course-empty">${escapeHtml(emptyMessage)}</div>`;
}

function selectPlannerCourse(code) {
  const normalized = normalizeCode(code);
  const course = getCourse(normalized);
  const input = $("#planner-add-search");
  app.plannerSelectedCourseCode = normalized;
  if (input) input.value = plannerCourseDisplay(course);
  closePlannerCourseMenu();
}

function setPlannerSearchHighlight(index) {
  const matches = app.plannerSearchMatches || [];
  if (!matches.length) return;

  const bounded = (index + matches.length) % matches.length;
  app.plannerSearchIndex = bounded;

  $$(".planner-course-option", $("#planner-add-menu")).forEach((option, optionIndex) => {
    const active = optionIndex === bounded;
    option.classList.toggle("active", active);
    option.setAttribute("aria-selected", active ? "true" : "false");
    if (active) {
      $("#planner-add-search").setAttribute("aria-activedescendant", option.id);
      option.scrollIntoView({ block: "nearest" });
    }
  });
}

function handlePlannerSearchKeydown(event) {
  const menu = $("#planner-add-menu");
  const matches = app.plannerSearchMatches || [];

  if (event.key === "ArrowDown") {
    event.preventDefault();
    if (menu.hidden) openPlannerCourseMenu();
    setPlannerSearchHighlight((app.plannerSearchIndex ?? -1) + 1);
    return;
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    if (menu.hidden) openPlannerCourseMenu();
    setPlannerSearchHighlight((app.plannerSearchIndex ?? 0) - 1);
    return;
  }

  if (event.key === "Enter") {
    if (!menu.hidden && matches.length) {
      event.preventDefault();
      const index = app.plannerSearchIndex >= 0 ? app.plannerSearchIndex : 0;
      selectPlannerCourse(matches[index].code);
    }
    return;
  }

  if (event.key === "Escape") {
    closePlannerCourseMenu();
  }
}

function handlePlannerMenuClick(event) {
  const option = event.target.closest("[data-planner-course]");
  if (!option) return;
  event.preventDefault();
  selectPlannerCourse(option.dataset.plannerCourse);
}

function handlePlannerOutsideClick(event) {
  if (!event.target.closest(".planner-course-combobox")) {
    closePlannerCourseMenu();
  }
}

function addPlannerSearchCourse() {
  const input = $("#planner-add-search");
  const raw = input?.value.trim() || "";
  const rawCode = normalizeCode(raw.split("—")[0]);
  const exactCourse = getCatalogCourse(rawCode)
    || app.courses.find((course) => plannerCourseDisplay(course).toLowerCase() === raw.toLowerCase());
  const code = app.plannerSelectedCourseCode || exactCourse?.code;
  const quarter = $("#planner-add-quarter").value;

  if (!code) {
    openPlannerCourseMenu();
    return showToast("Choose a course from the search dropdown first.");
  }

  if (app.pendingPlanSlot) {
    const { item, quarterId } = app.pendingPlanSlot;
    const added = addCourseToPlan(code, quarterId, {
      replaceItem: item,
      clearPendingSlot: true
    });
    if (!added) return;
  } else {
    const added = addCourseToPlan(code, quarter);
    if (!added) return;
  }

  app.plannerSelectedCourseCode = null;
  if (input) input.value = "";
  closePlannerCourseMenu();
}

function addCourseToPlan(code, quarterId, options = {}) {
  const normalized = isPlanSlot(code) ? code : normalizeCode(code);
  const proposed = proposedPlanWithCourse(normalized, quarterId, options.replaceItem || null);
  const conflicts = isPlanSlot(normalized)
    ? []
    : newlyIntroducedPlanConflicts(app.progress.plan, proposed);

  if (conflicts.length) {
    showPlanConflict(conflicts[0]);
    return false;
  }

  if (options.clearPendingSlot) clearPendingPlanSlot();
  app.progress.plan = proposed;
  saveProgress();
  renderAll();
  showToast(`${normalized} added to ${quarterLabel(quarterId)}.`);
  return true;
}

function quarterLabel(id) {
  const quarter = QUARTERS.find((entry) => entry.id === id);
  return quarter ? `Year ${quarter.year} ${quarter.season}` : id;
}

function removePlanItem(item, quarterId) {
  const proposed = clonePlan();
  proposed[quarterId] = (proposed[quarterId] || []).filter((value) => value !== item);
  const conflicts = newlyIntroducedPlanConflicts(app.progress.plan, proposed);
  if (conflicts.length) {
    showPlanConflict(conflicts[0]);
    return false;
  }
  app.progress.plan = proposed;
  saveProgress();
  renderAll();
  return true;
}

function handlePlannerClick(event) {
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
}

function handleDragStart(event) {
  const item = event.target.closest("[data-plan-item]");
  if (!item) return;
  event.dataTransfer.setData("application/json", JSON.stringify({ item: item.dataset.planItem, from: item.dataset.fromQuarter }));
  event.dataTransfer.effectAllowed = "move";
}

function handleDragOver(event) {
  const quarter = event.target.closest("[data-quarter]");
  if (!quarter) return;
  event.preventDefault();
  quarter.classList.add("drag-over");
}

function handleDragLeave(event) {
  const quarter = event.target.closest("[data-quarter]");
  if (quarter && !quarter.contains(event.relatedTarget)) quarter.classList.remove("drag-over");
}

function handleDrop(event) {
  const quarter = event.target.closest("[data-quarter]");
  if (!quarter) return;
  event.preventDefault();
  quarter.classList.remove("drag-over");
  try {
    const payload = JSON.parse(event.dataTransfer.getData("application/json"));
    addCourseToPlan(payload.item, quarter.dataset.quarter);
  } catch (error) {
    console.warn("Invalid drag payload", error);
  }
}

async function loadSamplePlan() {
  const ok = await confirmAction("Load the official sample plan? This replaces only your planned quarters. It does not mark any course fulfilled.", "Load sample plan");
  if (!ok) return;
  app.progress.plan = emptyPlan();
  clearPendingPlanSlot();
  for (const [quarter, items] of Object.entries(app.major.samplePlan.quarters)) app.progress.plan[quarter] = [...items];
  saveProgress();
  renderAll();
  showToast("Official sample plan loaded. Every item remains editable.");
}

async function clearPlan() {
  const ok = await confirmAction("Remove every course from the four-year plan? Fulfilled courses and requirement overrides will remain unchanged.", "Clear plan");
  if (!ok) return;
  app.progress.plan = emptyPlan();
  saveProgress();
  renderAll();
}

function validatePlan() {
  const warnings = structuralPlanConflicts(app.progress.plan).map((conflict) => ({
    code: conflict.code,
    quarter: conflict.quarter,
    message: conflict.message
  }));

  for (const quarter of QUARTERS) {
    for (const code of app.progress.plan[quarter.id] || []) {
      if (isPlanSlot(code)) continue;
      const course = getCourse(code);
      if (course.offered && !offeringIncludes(course.offered, quarter.season)) {
        warnings.push({
          code,
          quarter: quarter.id,
          message: `${code} may not normally be offered in ${quarter.season}. Catalog listing: ${course.offered}.`
        });
      }
    }
  }

  return warnings;
}

function offeringIncludes(offered, season) {
  const text = String(offered).toLowerCase();
  if (!text || text.includes("varies") || text.includes("arranged")) return true;
  const markers = {
    Autumn: ["autumn", "fall", "a"],
    Winter: ["winter", "w"],
    Spring: ["spring", "sp"],
    Summer: ["summer", "s"]
  };
  if (text.length <= 10 && /^[awsp,\s]+$/i.test(text)) {
    const normalized = text.replaceAll(",", "").replaceAll(" ", "");
    if (season === "Autumn") return normalized.includes("a");
    if (season === "Winter") return normalized.includes("w");
    if (season === "Spring") return normalized.includes("sp");
  }
  return markers[season].some((marker) => marker.length > 1 && text.includes(marker));
}

function renderPlannerInsights(warnings) {
  const totals = QUARTERS.map((quarter) => ({ quarter, credits: quarterCredits(quarter.id) }));
  const max = Math.max(18, ...totals.map((entry) => entry.credits));
  $("#planner-insights").innerHTML = `
    <article class="insight-card">
      <h2>Plan checks</h2>
      ${warnings.length ? `<div class="warning-list">${warnings.slice(0, 30).map((warning) => `<div class="warning-row"><strong>!</strong><span>${escapeHtml(warning.message)}</span></div>`).join("")}</div>` : `<div class="success-row">No prerequisite or offering conflicts were found in the current plan.</div>`}
      ${warnings.length > 30 ? `<p class="requirement-note">${warnings.length - 30} additional warnings are not shown.</p>` : ""}
    </article>
    <article class="insight-card">
      <h2>Credit load</h2>
      <div class="credit-chart">${totals.map(({ quarter, credits }) => `<div class="credit-row"><span>Y${quarter.year} ${quarter.season.slice(0,2)}</span><div class="credit-track"><span style="width:${(credits/max)*100}%"></span></div><strong>${formatNumber(credits)}</strong></div>`).join("")}</div>
      <p class="requirement-note"><strong>${formatNumber(plannedCredits())} / ${app.major.totalCredits}</strong> credits are represented. Requirement placeholders already carry credit values; use “Choose course” to replace each one with an actual UW course.</p>
    </article>`;
}


function populateApExamSelect() {
  const select = $("#ap-exam-select");
  if (!select) return;
  const current = select.value;
  const exams = [...(app.apCredit.exams || [])].sort((a, b) => a.name.localeCompare(b.name));
  select.innerHTML = exams.map((exam) => `<option value="${escapeHtml(exam.id)}">${escapeHtml(exam.name)}</option>`).join("");
  if (exams.some((exam) => exam.id === current)) select.value = current;
  populateApScoreSelect();
}

function populateApScoreSelect() {
  const examId = $("#ap-exam-select")?.value;
  const select = $("#ap-score-select");
  if (!select) return;
  const exam = getApExam(examId);
  const scores = [...new Set((exam?.awards || []).flatMap((award) => award.scores || []))].sort((a, b) => b - a);
  select.innerHTML = scores.map((score) => {
    const award = getApAward(examId, score);
    const courses = (award?.courses || []).join(", ") || "placement only";
    return `<option value="${score}">${score} → ${escapeHtml(courses)}</option>`;
  }).join("");
}

function addApExamSelection() {
  const examId = $("#ap-exam-select").value;
  const score = Number($("#ap-score-select").value);
  if (!examId || !getApAward(examId, score)) return showToast("Choose an AP exam and a qualifying score.");
  app.progress.apSelections[examId] = score;
  saveProgress();
  renderAll();
  showToast(`AP ${getApExam(examId).name} score ${score} applied.`);
}

function apSelectionEntries() {
  return Object.entries(app.progress.apSelections || {}).map(([examId, score]) => ({
    examId,
    score: Number(score),
    exam: getApExam(examId),
    award: getApAward(examId, score)
  })).filter((entry) => entry.exam && entry.award).sort((a, b) => a.exam.name.localeCompare(b.exam.name));
}

function uniqueSeattleCourses(codes = null) {
  const seen = new Set();
  const result = [];
  const source = codes ? codes.map((code) => getCourse(code)) : app.courses.filter((course) => course.campus === "Seattle");
  for (const course of source) {
    if (!course?.code || seen.has(course.code)) continue;
    seen.add(course.code);
    result.push(course);
  }
  return result;
}

function renderCredits() {
  if (!$("#credit-summary")) return;
  const apEntries = apSelectionEntries();
  const apCourses = new Set(apEntries.flatMap((entry) => (entry.award.courses || []).map(normalizeCode)));
  const transferCourses = Object.keys(app.progress.transferCourses || {}).map(normalizeCode);
  const externalCourses = [...new Set([...apCourses, ...transferCourses])];
  const apCredits = apEntries.reduce((sum, entry) => sum + Number(entry.award.credits || 0), 0);

  $("#credit-summary").innerHTML = [
    metricCard("AP exams entered", apEntries.length, 0, `${formatNumber(apCredits)} official exam credits represented`),
    metricCard("AP course equivalents", apCourses.size, 0, "Direct UW course awards from selected scores"),
    metricCard("College / transfer equivalents", transferCourses.length, 0, "Selected in bulk from the UW catalog"),
    metricCard("Outside-credit courses", externalCourses.length, 0, "Unique course boxes updated across the site")
  ].join("");

  $("#ap-policy-link").href = app.apCredit.source?.url || "https://admit.washington.edu/apply/transfer/exams-for-credit/ap/";
  $("#ap-policy-note").textContent = app.apCredit.source?.note || "Confirm current AP awards with UW Admissions.";

  $("#ap-selected-list").innerHTML = apEntries.length ? apEntries.map((entry) => `
    <div class="credit-selection-row">
      <div><strong>AP ${escapeHtml(entry.exam.name)}</strong><span>Score ${entry.score} · ${entry.award.credits || "?"} credits</span>
        <div class="credit-course-chips">${(entry.award.courses || []).map((code) => `<button type="button" data-open-credit-course="${escapeHtml(code)}">${escapeHtml(code)}</button>`).join("")}</div>
        ${entry.exam.note ? `<p>${escapeHtml(entry.exam.note)}</p>` : ""}
      </div>
      <button class="plan-remove credit-remove" type="button" data-remove-ap="${escapeHtml(entry.examId)}" aria-label="Remove AP exam">×</button>
    </div>`).join("") : `<div class="credit-empty">No AP exams added yet.</div>`;

  const selectedTransfers = transferCourses.sort();
  $("#transfer-selected-list").innerHTML = selectedTransfers.length ? `<div class="selected-credit-chips">${selectedTransfers.map((code) => `<span><button type="button" data-open-credit-course="${escapeHtml(code)}">${escapeHtml(code)}</button><button type="button" data-remove-transfer="${escapeHtml(code)}" aria-label="Remove ${escapeHtml(code)}">×</button></span>`).join("")}</div>` : `<div class="credit-empty">No Running Start, community-college, or transfer equivalents selected.</div>`;
  $("#transfer-picker-label").textContent = selectedTransfers.length ? `${selectedTransfers.length} UW equivalent course${selectedTransfers.length === 1 ? "" : "s"} selected` : "Choose UW course equivalents…";

  $("#external-credit-table").innerHTML = externalCourses.length ? externalCourses.sort().map((code) => {
    const course = getCourse(code);
    const sources = externalSourcesForCourse(code);
    return `<div class="external-credit-row">
      <button class="external-credit-course" type="button" data-open-credit-course="${escapeHtml(code)}"><strong>${escapeHtml(code)}</strong><span>${escapeHtml(course.title)}</span></button>
      <div class="external-credit-sources">${sources.map((source) => `<span>${escapeHtml(source.label)}</span>`).join("")}</div>
      <span class="external-credit-status">✓ fulfilled</span>
    </div>`;
  }).join("") : `<div class="credit-empty large">No outside credit has been applied. The degree map still starts completely blank.</div>`;

  renderTransferCourseOptions();
}

function renderTransferCourseOptions() {
  const container = $("#transfer-course-options");
  if (!container) return;
  const query = $("#transfer-course-search")?.value.trim().toLowerCase() || "";
  const majorOnly = $("#transfer-major-only")?.checked ?? true;
  let courses = majorOnly ? uniqueSeattleCourses(getVisibleMapCodes()) : uniqueSeattleCourses();
  if (query) {
    const tokens = query.split(/\s+/).filter(Boolean);
    courses = courses.filter((course) => {
      const text = `${course.code} ${course.title} ${course.description || ""}`.toLowerCase();
      return tokens.every((token) => text.includes(token));
    });
  } else if (!majorOnly) {
    courses = courses.slice(0, 180);
  }
  courses.sort((a, b) => a.code.localeCompare(b.code));
  const limit = query ? 250 : courses.length;
  const visible = courses.slice(0, limit);
  container.innerHTML = visible.length ? visible.map((course) => `
    <label class="multi-select-option">
      <input type="checkbox" data-transfer-course="${escapeHtml(course.code)}" ${hasTransferCredit(course.code) ? "checked" : ""}>
      <span><strong>${escapeHtml(course.code)}</strong><small>${escapeHtml(course.title)}</small></span>
      <em>${escapeHtml(course.credits || "?")} cr</em>
    </label>`).join("") : `<div class="credit-empty">No matching UW courses.</div>`;
  if (!majorOnly && !query) container.insertAdjacentHTML("afterbegin", `<p class="multi-select-hint">Showing the first 180 Seattle courses. Search to reach any course in the full catalog.</p>`);
}

function handleTransferCourseChange(event) {
  const code = event.target.dataset.transferCourse;
  if (!code) return;
  const normalized = normalizeCode(code);
  if (event.target.checked) app.progress.transferCourses[normalized] = "Running Start / college / transfer credit";
  else delete app.progress.transferCourses[normalized];
  saveProgress();
  renderAll();
}

function openCreditCourse(code) {
  const normalized = normalizeCode(code);
  if (allMajorCodes().includes(normalized)) {
    app.selectedCode = normalized;
    switchView("map");
    renderMap();
    scrollNodeIntoView(normalized);
    return;
  }
  const course = getCatalogCourse(normalized);
  if (course) {
    app.selectedCatalogId = course.id;
    switchView("catalog");
    renderCatalog();
  }
}

function handleCreditClick(event) {
  const apRemove = event.target.closest("[data-remove-ap]");
  if (apRemove) {
    delete app.progress.apSelections[apRemove.dataset.removeAp];
    saveProgress();
    renderAll();
    return;
  }
  const transferRemove = event.target.closest("[data-remove-transfer]");
  if (transferRemove) {
    delete app.progress.transferCourses[normalizeCode(transferRemove.dataset.removeTransfer)];
    saveProgress();
    renderAll();
    return;
  }
  const open = event.target.closest("[data-open-credit-course]");
  if (open) openCreditCourse(open.dataset.openCreditCourse);
}

async function clearExternalCredits() {
  const ok = await confirmAction("Clear all AP exam selections and all Running Start, college, and transfer course equivalents? Manually completed UW courses will stay fulfilled.", "Clear outside credit");
  if (!ok) return;
  app.progress.apSelections = {};
  app.progress.transferCourses = {};
  saveProgress();
  renderAll();
  showToast("AP and transfer credit cleared.");
}

function filteredCatalogCourses() {
  const query = $("#catalog-search").value.trim().toLowerCase();
  const campus = $("#campus-filter").value;
  const department = $("#department-filter").value;
  const tokens = query.split(/\s+/).filter(Boolean);
  return app.courses.filter((course) => {
    if (campus !== "all" && course.campus !== campus) return false;
    if (department !== "all" && course.department !== department) return false;
    if (!tokens.length) return true;
    const haystack = `${course.code} ${course.title} ${course.description || ""} ${course.prerequisiteText || ""} ${course.areas || ""}`.toLowerCase();
    return tokens.every((token) => haystack.includes(token));
  });
}

function renderCatalog() {
  if (!app.catalogPayload) return;
  const filtered = filteredCatalogCourses();
  const visible = filtered.slice(0, app.catalogLimit);
  $("#catalog-result-count").textContent = `${filtered.length.toLocaleString()} matching course${filtered.length === 1 ? "" : "s"}`;
  $("#show-more-button").hidden = visible.length >= filtered.length;
  $("#catalog-results").innerHTML = visible.length ? visible.map(renderCatalogCard).join("") : `<div class="empty-panel" style="grid-column:1/-1"><div><div class="empty-panel-icon">⌕</div><h2>No matches</h2><p>Try a course code, a broader topic, or remove a filter.</p></div></div>`;
  renderCatalogPanel();
}

function renderCatalogCard(course) {
  const selected = course.id === app.selectedCatalogId;
  return `<article class="catalog-card ${selected ? "selected" : ""}" data-catalog-id="${escapeHtml(course.id)}">
    <div class="catalog-card-top"><span class="catalog-code">${escapeHtml(course.code)}</span><span class="catalog-campus">${escapeHtml(course.campus)}</span></div>
    <div class="catalog-title">${escapeHtml(course.title)}</div>
    <div class="catalog-meta">
      <span class="tiny-chip">${escapeHtml(course.credits || "?")} cr</span>
      ${course.areas ? `<span class="tiny-chip">${escapeHtml(course.areas)}</span>` : ""}
      ${course.offered ? `<span class="tiny-chip">${escapeHtml(course.offered)}</span>` : ""}
    </div>
    <div class="catalog-actions">
      <button class="button small secondary" type="button" data-open-catalog="${escapeHtml(course.id)}">View path</button>
      <label onclick="event.stopPropagation()"><input type="checkbox" data-catalog-fulfilled="${escapeHtml(course.code)}" ${isFulfilled(course.code) ? "checked" : ""}> Fulfilled</label>
    </div>
  </article>`;
}

function handleCatalogClick(event) {
  const open = event.target.closest("[data-open-catalog]");
  const card = event.target.closest("[data-catalog-id]");
  const id = open?.dataset.openCatalog || card?.dataset.catalogId;
  if (!id) return;
  app.selectedCatalogId = id;
  renderCatalog();
}

function handleCatalogChange(event) {
  if (event.target.dataset.catalogFulfilled) setFulfilled(event.target.dataset.catalogFulfilled, event.target.checked);
}

function renderCatalogPanel() {
  const panel = $("#catalog-panel");
  const course = app.catalogById.get(app.selectedCatalogId);
  if (!course) {
    panel.innerHTML = `<div class="empty-panel"><div><div class="empty-panel-icon">⌕</div><h2>Explore a course path</h2><p>Select any catalog card to see its prerequisites, courses that reference it, and planning controls.</p></div></div>`;
    return;
  }
  const merged = app.major.courseOverrides?.[course.code] ? getCourse(course.code) : { ...course, prerequisiteGroups: genericPrerequisiteGroups(course) };
  const prereqs = getPrerequisiteGroups(merged).flat();
  const next = (app.reversePrereqs.get(course.code) || []).map((id) => app.catalogById.get(id)).filter(Boolean).slice(0, 18);
  const planQuarter = plannedQuarter(course.code);
  const source = app.progress.fulfillmentSources[course.code] || "Completed UW course";
  const externalSources = externalSourcesForCourse(course.code);
  const manualFulfilled = isManuallyFulfilled(course.code);

  panel.innerHTML = `
    <div class="detail-code"><div><div class="eyebrow">${escapeHtml(course.campus)} CATALOG</div><h2>${escapeHtml(course.code)}</h2></div><span class="status-chip ${courseStatus(course.code)}">${statusText(courseStatus(course.code))}</span></div>
    <div class="detail-title">${escapeHtml(course.title)}</div>
    <div class="course-link-list"><span class="tiny-chip">${escapeHtml(course.credits || "?")} credits</span>${course.areas ? `<span class="tiny-chip">${escapeHtml(course.areas)}</span>` : ""}</div>
    <p class="detail-description">${escapeHtml(course.description || "No description is included in the bundled offline catalog. Run the official sync to download current descriptions.")}</p>

    <div class="relationship-map">
      <div class="relationship-column">${prereqs.length ? prereqs.slice(0,5).map((code) => `<button class="relationship-node" data-catalog-code-link="${escapeHtml(code)}">${escapeHtml(code)}</button>`).join("") : `<div class="relationship-node">No listed course prerequisites</div>`}</div>
      <div class="relationship-arrow">→</div>
      <div class="relationship-node center">${escapeHtml(course.code)}</div>
      <div class="relationship-arrow">→</div>
      <div class="relationship-column">${next.length ? next.slice(0,5).map((item) => `<button class="relationship-node" data-catalog-id-link="${escapeHtml(item.id)}">${escapeHtml(item.code)}</button>`).join("") : `<div class="relationship-node">No linked next courses</div>`}</div>
    </div>

    <div class="detail-section">
      <div class="fulfillment-box">
        <label><input type="checkbox" data-catalog-panel="fulfilled" data-code="${escapeHtml(course.code)}" ${isFulfilled(course.code) ? "checked" : ""}> Already fulfilled</label>
        <select data-catalog-panel="source" data-code="${escapeHtml(course.code)}" ${manualFulfilled ? "" : "disabled"}>
          ${["Completed UW course","AP / IB credit","Running Start / college credit","Transfer or equivalent credit","Other approved fulfillment"].map((value) => `<option ${source === value ? "selected" : ""}>${value}</option>`).join("")}
        </select>
        ${externalSources.length ? `<div class="external-source-list">${externalSources.map((entry) => `<span>${escapeHtml(entry.label)}</span>`).join("")}</div><button class="text-button credit-manage-link" type="button" data-catalog-panel="open-credits">Manage outside credit →</button>` : ""}
      </div>
    </div>

    <div class="detail-section">
      <h3>Add to four-year plan</h3>
      <div class="plan-add-row">
        <select data-catalog-quarter>${QUARTERS.map((quarter) => `<option value="${quarter.id}" ${planQuarter === quarter.id ? "selected" : ""}>Y${quarter.year} ${quarter.season}</option>`).join("")}</select>
        <button class="button primary" data-catalog-panel="add" data-code="${escapeHtml(course.code)}">${planQuarter ? "Move" : "Add"}</button>
      </div>
    </div>

    <div class="detail-section">
      <h3>Prerequisite text</h3>
      <p class="detail-description">${escapeHtml(course.prerequisiteText || "No prerequisite text listed.")}</p>
      ${course.sourceType !== "official-live" ? `<p class="requirement-note">Offline relationship data may be incomplete or old. Use the sync command before relying on it for registration.</p>` : ""}
      ${course.sourceUrl ? `<a class="source-link" href="${escapeHtml(course.sourceUrl)}" target="_blank" rel="noreferrer">Open official department catalog page ↗</a>` : ""}
    </div>`;
}

function handleCatalogPanelClick(event) {
  const idLink = event.target.closest("[data-catalog-id-link]");
  if (idLink) {
    app.selectedCatalogId = idLink.dataset.catalogIdLink;
    renderCatalog();
    return;
  }
  const codeLink = event.target.closest("[data-catalog-code-link]");
  if (codeLink) {
    const linked = getCatalogCourse(codeLink.dataset.catalogCodeLink);
    if (linked) app.selectedCatalogId = linked.id;
    renderCatalog();
    return;
  }
  const action = event.target.closest("[data-catalog-panel]");
  if (action?.dataset.catalogPanel === "add") {
    const quarter = $("[data-catalog-quarter]", $("#catalog-panel")).value;
    addCourseToPlan(action.dataset.code, quarter);
  }
  if (action?.dataset.catalogPanel === "open-credits") switchView("credits");
}

function handleCatalogPanelChange(event) {
  const action = event.target.dataset.catalogPanel;
  if (action === "fulfilled") setFulfilled(event.target.dataset.code, event.target.checked);
  if (action === "source") {
    app.progress.fulfillmentSources[normalizeCode(event.target.dataset.code)] = event.target.value;
    saveProgress();
  }
}

async function resetAll() {
  const ok = await confirmAction("Reset this major? This removes all fulfilled courses, transfer/AP selections, requirement overrides, and planned quarters.", "Reset everything");
  if (!ok) return;
  app.progress = createDefaultProgress();
  app.selectedCode = null;
  app.selectedCatalogId = null;
  saveProgress();
  renderAll();
  showToast("Everything has been reset. Nothing is fulfilled or planned.");
}

function exportProgress() {
  const payload = {
    app: "UW Degree Mapper",
    exportedAt: new Date().toISOString(),
    majorId: app.major.id,
    majorName: app.major.name,
    progress: app.progress
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `uw-degree-plan-${new Date().toISOString().slice(0,10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

async function importProgress(event) {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) return;
  try {
    const parsed = JSON.parse(await file.text());
    if (!parsed.progress || parsed.majorId !== app.major.id) throw new Error(`This file is not a ${app.major.name} plan export from this website.`);
    const ok = await confirmAction("Import this plan and replace the currently saved progress?", "Import plan");
    if (!ok) return;
    const defaults = createDefaultProgress();
    app.progress = {
      ...defaults,
      ...parsed.progress,
      fulfilled: { ...defaults.fulfilled, ...(parsed.progress.fulfilled || {}) },
      plan: { ...defaults.plan, ...(parsed.progress.plan || {}) },
      requirementOverrides: { ...defaults.requirementOverrides, ...(parsed.progress.requirementOverrides || {}) },
      manualCredits: { ...defaults.manualCredits, ...(parsed.progress.manualCredits || {}) },
      fulfillmentSources: { ...defaults.fulfillmentSources, ...(parsed.progress.fulfillmentSources || {}) },
      apSelections: { ...defaults.apSelections, ...(parsed.progress.apSelections || {}) },
      transferCourses: { ...defaults.transferCourses, ...(parsed.progress.transferCourses || {}) }
    };
    saveProgress();
    renderAll();
    showToast("Plan imported.");
  } catch (error) {
    showToast(error.message || "Could not import that file.");
  }
}

function openDataModal() {
  const metadata = app.catalogPayload.metadata || {};
  const isLive = metadata.sourceType === "official-live";
  $("#data-modal-content").innerHTML = `<div class="data-detail">
    <p><strong>Current source:</strong> ${isLive ? "Official UW public course-description pages" : "Bundled offline fallback catalog"}</p>
    <p><strong>Courses loaded:</strong> ${Number(metadata.courseCount || app.courses.length).toLocaleString()}</p>
    ${metadata.syncedAt ? `<p><strong>Synced:</strong> ${escapeHtml(new Date(metadata.syncedAt).toLocaleString())}</p>` : ""}
    <p>${escapeHtml(metadata.notice || (isLive ? "The local catalog was generated from the public UW Seattle, Bothell, and Tacoma course-description pages." : "The offline catalog makes the site usable immediately, but current official data should be synced before registration planning."))}</p>
    <p>To download all current official UW course descriptions, stop the server and run this command in the VS Code terminal:</p>
    <div class="code-block">py server.py --sync</div>
    <p>The sync uses only Python's standard library. After it finishes, the website starts automatically with the new catalog.</p>
  </div>`;
  $("#data-modal").hidden = false;
}

function confirmAction(message, title = "Confirm") {
  $("#confirm-title").textContent = title;
  $("#confirm-message").textContent = message;
  $("#confirm-modal").hidden = false;
  return new Promise((resolve) => { app.confirmResolver = resolve; });
}

function resolveConfirm(value) {
  $("#confirm-modal").hidden = true;
  app.confirmResolver?.(value);
  app.confirmResolver = null;
}

let toastTimer = null;
function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

initialize();
