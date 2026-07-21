from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
APP = ROOT / "src" / "app.js"
STYLES = ROOT / "src" / "styles.css"


def backup(path: Path) -> None:
    target = path.with_name(path.name + ".before-search-dropdown")
    if not target.exists():
        shutil.copy2(path, target)


def patch_index(text: str) -> str:
    old = '''        <label class="search-box grow">
          <span aria-hidden="true">＋</span>
          <input id="planner-add-search" type="search" placeholder="Search a course to add to your plan">
        </label>
        <select id="planner-add-results" aria-label="Matching courses"><option value="">Choose a matching course…</option></select>'''

    new = '''        <div class="planner-course-combobox grow">
          <div class="search-box planner-search-field">
            <span aria-hidden="true">＋</span>
            <input
              id="planner-add-search"
              type="search"
              placeholder="Search a course to add to your plan"
              autocomplete="off"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="planner-add-menu"
              aria-expanded="false"
              aria-label="Search and choose a course"
            >
            <button
              id="planner-course-toggle"
              class="planner-course-toggle"
              type="button"
              aria-label="Show course choices"
              aria-controls="planner-add-menu"
              aria-expanded="false"
            >⌄</button>
          </div>
          <div id="planner-add-menu" class="planner-course-menu" role="listbox" hidden></div>
        </div>'''

    if old in text:
        return text.replace(old, new, 1)

    pattern = re.compile(
        r'''\s*<label class="search-box grow">\s*'''
        r'''<span aria-hidden="true">＋</span>\s*'''
        r'''<input id="planner-add-search"[^>]*>\s*'''
        r'''</label>\s*'''
        r'''<select id="planner-add-results"[^>]*>.*?</select>''',
        re.S,
    )
    if not pattern.search(text):
        if "planner-course-combobox" in text:
            return text
        raise RuntimeError("Could not find the planner search/select block in index.html")
    return pattern.sub("\n" + new, text, count=1)


def patch_app(text: str) -> str:
    if "function selectPlannerCourse(code)" in text:
        return text

    old_binding = '  $("#planner-add-search").addEventListener("input", debounce(updatePlannerSearchResults, 100));'
    new_binding = '''  const plannerSearch = $("#planner-add-search");
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
  document.addEventListener("click", handlePlannerOutsideClick);'''

    if old_binding not in text:
        raise RuntimeError("Could not find the planner search event binding in src/app.js")
    text = text.replace(old_binding, new_binding, 1)

    text = text.replace(
        "function beginFillPlanSlot(item, quarterId) {\n  app.pendingPlanSlot = { item, quarterId };",
        "function beginFillPlanSlot(item, quarterId) {\n  app.pendingPlanSlot = { item, quarterId };\n  app.plannerSelectedCourseCode = null;",
        1,
    )

    replacement = r'''function plannerCourseDisplay(course) {
  return `${course.code} — ${course.title}`;
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
  const course = app.catalogByCode.get(normalized) || getCourse(normalized);
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
  const exactCourse = app.catalogByCode.get(rawCode)
    || app.courses.find((course) => plannerCourseDisplay(course).toLowerCase() === raw.toLowerCase());
  const code = app.plannerSelectedCourseCode || exactCourse?.code;
  const quarter = $("#planner-add-quarter").value;

  if (!code) {
    openPlannerCourseMenu();
    return showToast("Choose a course from the search dropdown first.");
  }

  app.plannerSelectedCourseCode = null;
  if (input) input.value = "";
  closePlannerCourseMenu();

  if (app.pendingPlanSlot) {
    const { item, quarterId } = app.pendingPlanSlot;
    app.progress.plan[quarterId] = (app.progress.plan[quarterId] || []).filter((entry) => entry !== item);
    clearPendingPlanSlot();
    addCourseToPlan(code, quarterId);
    return;
  }

  addCourseToPlan(code, quarter);
}'''

    pattern = re.compile(
        r"function updatePlannerSearchResults\(\) \{.*?\n\}\n\nfunction addPlannerSearchCourse\(\) \{.*?\n\}",
        re.S,
    )
    if not pattern.search(text):
        raise RuntimeError("Could not find planner search functions in src/app.js")
    text = pattern.sub(replacement, text, count=1)
    return text


def patch_styles(text: str) -> str:
    if ".planner-course-combobox" in text:
        return text

    block = r'''

/* Searchable course dropdown in the four-year planner */
.planner-course-combobox {
  position: relative;
  min-width: min(620px, 100%);
}

.planner-search-field {
  width: 100%;
  padding-right: 7px;
}

.planner-search-field input {
  min-width: 0;
  font-size: 14px;
}

.planner-course-toggle {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: var(--uw-purple);
  cursor: pointer;
  font-size: 21px;
  line-height: 1;
  transition: background .15s ease, transform .15s ease;
}

.planner-course-toggle:hover,
.planner-course-toggle[aria-expanded="true"] {
  background: rgba(75, 46, 131, .09);
}

.planner-course-toggle[aria-expanded="true"] {
  transform: rotate(180deg);
}

.planner-course-menu {
  position: absolute;
  z-index: 80;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  max-height: 330px;
  overflow-y: auto;
  padding: 7px;
  border: 1px solid var(--line);
  border-radius: 15px;
  background: white;
  box-shadow: 0 18px 45px rgba(27, 19, 45, .18);
}

.planner-course-menu[hidden] {
  display: none;
}

.planner-course-option {
  display: grid;
  grid-template-columns: minmax(78px, auto) minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 11px 12px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}

.planner-course-option:hover,
.planner-course-option.active {
  background: rgba(75, 46, 131, .09);
}

.planner-option-code {
  color: var(--uw-purple);
  font-size: 12px;
  font-weight: 850;
  white-space: nowrap;
}

.planner-option-title {
  min-width: 0;
  overflow: hidden;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.planner-option-credits {
  color: var(--muted);
  font-size: 11px;
  font-weight: 750;
  white-space: nowrap;
}

.planner-course-empty {
  padding: 18px 14px;
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}

@media (max-width: 760px) {
  .planner-course-combobox {
    width: 100%;
    min-width: 0;
  }

  .planner-course-option {
    grid-template-columns: 1fr auto;
  }

  .planner-option-title {
    grid-column: 1 / -1;
    white-space: normal;
  }
}
'''
    return text.rstrip() + block + "\n"


def main() -> None:
    for path in (INDEX, APP, STYLES):
        if not path.exists():
            raise SystemExit(f"Missing expected file: {path}")
        backup(path)

    INDEX.write_text(patch_index(INDEX.read_text(encoding="utf-8")), encoding="utf-8")
    APP.write_text(patch_app(APP.read_text(encoding="utf-8")), encoding="utf-8")
    STYLES.write_text(patch_styles(STYLES.read_text(encoding="utf-8")), encoding="utf-8")

    print("Replaced the separate course dropdown with a searchable dropdown inside the search box.")
    print("Updated index.html, src/app.js, and src/styles.css.")
    print("Backups use the suffix .before-search-dropdown")


if __name__ == "__main__":
    main()