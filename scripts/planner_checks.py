from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
APP = ROOT / "src" / "app.js"
STYLES = ROOT / "src" / "styles.css"


def backup(path: Path) -> None:
    target = path.with_name(path.name + ".before-plan-map-navigation")
    if not target.exists():
        shutil.copy2(path, target)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Could not find {label}")
    return text.replace(old, new, 1)


def replace_function(text: str, name: str, replacement: str) -> str:
    pattern = re.compile(
        rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{.*?\n\}}(?=\n\nfunction\s|\n\nasync function\s|\n\nconst\s|\Z)",
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Could not find function {name} in src/app.js")
    return text[: match.start()] + replacement.rstrip() + text[match.end() :]


def patch_index(text: str) -> str:
    if 'id="pan-map-button"' not in text:
        old = '<button id="fit-map-button" class="button secondary" type="button">Fit map</button>'
        new = old + '\n        <button id="pan-map-button" class="button secondary" type="button" aria-pressed="false">Pan map: off</button>'
        text = replace_once(text, old, new, "Fit map button")

    if 'class="map-scroll-stack"' not in text:
        old = '''      <div class="map-layout">
        <div id="map-scroll" class="map-scroll card-surface">
          <div id="map-stage" class="map-stage">
            <svg id="map-edges" class="map-edges" aria-hidden="true"></svg>
            <div id="map-columns" class="map-columns"></div>
          </div>
        </div>
        <aside id="course-panel" class="course-panel card-surface" aria-live="polite"></aside>
      </div>'''
        new = '''      <div class="map-layout">
        <div class="map-scroll-stack">
          <div id="map-scroll-top" class="map-scroll-top card-surface" aria-label="Horizontal map scrollbar">
            <div id="map-scroll-top-content" class="map-scroll-top-content"></div>
          </div>
          <div id="map-scroll" class="map-scroll card-surface">
            <div id="map-stage" class="map-stage">
              <svg id="map-edges" class="map-edges" aria-hidden="true"></svg>
              <div id="map-columns" class="map-columns"></div>
            </div>
          </div>
        </div>
        <aside id="course-panel" class="course-panel card-surface" aria-live="polite"></aside>
      </div>'''
        text = replace_once(text, old, new, "degree-map layout")

    return text


VALIDATION_HELPERS = r'''
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
'''


PAN_HELPERS = r'''
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
'''


def patch_app(text: str) -> str:
    if "const OFFICIAL_COURSE_OVERLAP_GROUPS" not in text:
        marker = "];\n\nconst app = {"
        if marker not in text:
            raise RuntimeError("Could not find the end of QUARTERS in src/app.js")
        text = text.replace(marker, "];\n\n" + VALIDATION_HELPERS.strip() + "\n\nconst app = {", 1)

    old_state = "  mapRenderToken: 0,\n  pendingPlanSlot: null"
    new_state = "  mapRenderToken: 0,\n  pendingPlanSlot: null,\n  plannerSelectedCourseCode: null,\n  plannerSearchMatches: [],\n  plannerSearchIndex: -1,\n  mapPanEnabled: false,\n  mapPanState: null,\n  mapDidPan: false,\n  mapScrollSyncing: false"
    if old_state in text:
        text = text.replace(old_state, new_state, 1)

    old_map_bindings = '''  $("#show-all-connections").addEventListener("change", drawMapEdges);
  $("#fit-map-button").addEventListener("click", () => $("#map-scroll").scrollTo({ left: 0, top: 0, behavior: "smooth" }));
  $("#map-columns").addEventListener("click", handleMapClick);'''
    new_map_bindings = '''  $("#show-all-connections").addEventListener("change", drawMapEdges);
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
  updatePanButton();'''
    if old_map_bindings in text:
        text = text.replace(old_map_bindings, new_map_bindings, 1)
    elif '$("#pan-map-button").addEventListener("click", toggleMapPan);' not in text:
        raise RuntimeError("Could not find degree-map event bindings in src/app.js")

    if "function updateMapTopScrollbar()" not in text:
        marker = "function renderMap() {"
        if marker not in text:
            raise RuntimeError("Could not find renderMap in src/app.js")
        text = text.replace(marker, PAN_HELPERS.strip() + "\n\n" + marker, 1)

    # Keep the mirrored top scrollbar sized after every map redraw.
    old_svg_end = '''  </defs>${paths.join("")}`;
}'''
    new_svg_end = '''  </defs>${paths.join("")}`;
  updateMapTopScrollbar();
}'''
    if old_svg_end in text and "updateMapTopScrollbar();\n}" not in text[text.find("function drawMapEdges"):text.find("function handleMapClick")]:
        text = text.replace(old_svg_end, new_svg_end, 1)

    # Clicking blank map space clears the selected course; panning never selects.
    old_handle_end = '''  const node = event.target.closest(".course-node");
  if (!node) return;
  app.selectedCode = node.dataset.courseCode;
  renderMap();
}'''
    new_handle_end = '''  if (app.mapDidPan) {
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
}'''
    if old_handle_end in text:
        text = text.replace(old_handle_end, new_handle_end, 1)

    text = replace_function(text, "plannerCourseDisplay", r'''function plannerCourseDisplay(courseOrCode) {
  const course = typeof courseOrCode === "string" ? getCourse(courseOrCode) : courseOrCode;
  const code = normalizeCode(course?.code || courseOrCode || "");
  const title = course?.title || getCourse(code).title || "Course information unavailable";
  return `${code} — ${title}`;
}''')

    text = replace_function(text, "selectPlannerCourse", r'''function selectPlannerCourse(code) {
  const normalized = normalizeCode(code);
  const course = getCourse(normalized);
  const input = $("#planner-add-search");
  app.plannerSelectedCourseCode = normalized;
  if (input) input.value = plannerCourseDisplay(course);
  closePlannerCourseMenu();
}''')

    text = replace_function(text, "addPlannerSearchCourse", r'''function addPlannerSearchCourse() {
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
}''')

    text = replace_function(text, "addCourseToPlan", r'''function addCourseToPlan(code, quarterId, options = {}) {
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
}''')

    text = replace_function(text, "removePlanItem", r'''function removePlanItem(item, quarterId) {
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
}''')

    text = replace_function(text, "validatePlan", r'''function validatePlan() {
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
}''')

    return text


STYLE_BLOCK = r'''

/* Easier degree-map scrolling and panning */
.map-scroll-stack {
  min-width: 0;
}

.map-scroll-top {
  height: 20px;
  margin-bottom: 7px;
  overflow-x: scroll;
  overflow-y: hidden;
  border-radius: 9px;
  scrollbar-gutter: stable;
}

.map-scroll-top-content {
  height: 1px;
  pointer-events: none;
}

.map-scroll.pan-enabled,
.map-scroll.panning {
  cursor: grab;
}

.map-scroll.panning {
  cursor: grabbing;
  user-select: none;
}

.map-scroll.panning * {
  cursor: grabbing !important;
}

#pan-map-button[aria-pressed="true"] {
  border-color: var(--uw-purple);
  background: var(--uw-purple-soft);
  color: var(--uw-purple);
}

.course-node,
.map-requirement-node,
.map-plan-slot-node {
  cursor: pointer;
}

@media (max-width: 980px) {
  .map-scroll-stack {
    width: 100%;
  }
}
'''


def patch_styles(text: str) -> str:
    if "/* Easier degree-map scrolling and panning */" not in text:
        text = text.rstrip() + STYLE_BLOCK + "\n"
    return text


def main() -> None:
    for path in (INDEX, APP, STYLES):
        if not path.exists():
            raise SystemExit(f"Missing expected file: {path}")
        backup(path)

    INDEX.write_text(patch_index(INDEX.read_text(encoding="utf-8")), encoding="utf-8")
    APP.write_text(patch_app(APP.read_text(encoding="utf-8")), encoding="utf-8")
    STYLES.write_text(patch_styles(STYLES.read_text(encoding="utf-8")), encoding="utf-8")

    print("Added strict prerequisite ordering and same-quarter overlap checks.")
    print("Added a top scrollbar, toggleable left-drag pan mode, and right-drag panning.")
    print("Clicking blank map space now clears the selected course.")
    print("Fixed the planner search selection showing undefined values.")
    print("Updated index.html, src/app.js, and src/styles.css.")
    print("Backups use the suffix .before-plan-map-navigation")


if __name__ == "__main__":
    main()
