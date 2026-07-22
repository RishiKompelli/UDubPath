from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app.js"
CSS = ROOT / "src" / "styles.css"
HTML = ROOT / "index.html"
MAJOR_DIR = ROOT / "data" / "majors"
MARKER = "DOUBLE_MAJOR_DUAL_DEGREE_MODE_V1"


def backup(path: Path) -> None:
    backup_path = path.with_name(path.name + ".before-degree-combinations")
    if path.exists() and not backup_path.exists():
        backup_path.write_bytes(path.read_bytes())


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Could not patch {label}: expected one match, found {count}.")
    return text.replace(old, new, 1)


def update_major_metadata() -> int:
    explicit = {
        "uw-seattle-me": ("BSME", "engineering"),
        "uw-seattle-mse": ("BSMSE", "engineering"),
        "uw-seattle-aa": ("BSAAE", "engineering"),
        "uw-seattle-bioe": ("BSBIOE", "engineering"),
        "uw-seattle-cheme": ("BSCHE", "engineering"),
        "uw-seattle-cive": ("BSCE", "engineering"),
        "uw-seattle-ece": ("BSECE", "engineering"),
        "uw-seattle-enve": ("BSENVE", "engineering"),
        "uw-seattle-hcde": ("BSHCDE", "engineering"),
        "uw-seattle-ise": ("BSIE", "engineering"),
        "uw-seattle-cs": ("BS", "arts-sciences"),
        "uw-seattle-math-bs": ("BS", "arts-sciences"),
        "uw-seattle-biology-bs": ("BS", "arts-sciences"),
        "uw-seattle-biology-ba": ("BA", "arts-sciences"),
        "uw-seattle-biochemistry-bs": ("BS", "arts-sciences"),
        "uw-seattle-biochemistry-ba": ("BA", "arts-sciences"),
        "uw-seattle-lsj": ("BA", "arts-sciences"),
    }

    changed = 0
    for path in MAJOR_DIR.glob("*.json"):
        if path.name == "index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or not data.get("id"):
            continue

        major_id = str(data.get("id"))
        name = str(data.get("name", "")).lower()
        degree = str(data.get("degree", "")).lower()

        award, college = explicit.get(major_id, (None, None))
        if not award:
            if "computer science" in name:
                award, college = "BS", "arts-sciences"
            elif "mathematics" in name and "bs" in (name + " " + degree):
                award, college = "BS", "arts-sciences"
            elif "biology" in name and ("ba" in name or "bachelor of arts" in degree):
                award, college = "BA", "arts-sciences"
            elif "biology" in name:
                award, college = "BS", "arts-sciences"
            elif "law, societies" in name or "law societies" in name:
                award, college = "BA", "arts-sciences"
            elif "engineering" in name or "engineering" in degree:
                award, college = "NAMED-" + re.sub(r"[^A-Z0-9]+", "-", major_id.upper()).strip("-"), "engineering"
            elif "bachelor of arts" in degree:
                award, college = "BA", "arts-sciences"
            elif "bachelor of science" in degree:
                # College of Arts & Sciences majors with a Bachelor of Science
                # share the BS degree name even when the catalog spells out
                # "Bachelor of Science with/in a major in ...".
                award, college = "BS", "arts-sciences"
            else:
                award, college = "UNKNOWN-" + major_id, "unknown"

        before = json.dumps(data, sort_keys=True)
        data.setdefault("degreeAwardId", award)
        data.setdefault("collegeId", college)
        data.setdefault("minimumDegreeCredits", int(data.get("totalCredits") or 180))
        if json.dumps(data, sort_keys=True) != before:
            backup(path)
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            changed += 1
    return changed


def patch_html(text: str) -> str:
    if MARKER in text:
        return text

    text = replace_once(
        text,
        '<span>Major</span>\n        <select id="major-select"></select>',
        '<span>Primary major</span>\n        <select id="major-select"></select>',
        "primary major label",
    )

    old = '''      <label class="select-field">\n        <span>Degree path</span>\n        <select id="track-select"></select>\n      </label>\n      <button id="data-status"'''
    new = '''      <label class="select-field">\n        <span>Primary degree path</span>\n        <select id="track-select"></select>\n      </label>\n      <button id="add-second-major-button" class="button secondary combination-add-button" type="button">＋ Add second major</button>\n      <label id="secondary-major-field" class="select-field combination-control" hidden>\n        <span>Second major</span>\n        <select id="secondary-major-select"><option value="">Choose a second major…</option></select>\n      </label>\n      <label id="secondary-track-field" class="select-field combination-control" hidden>\n        <span>Second degree path</span>\n        <select id="secondary-track-select"></select>\n      </label>\n      <button id="remove-second-major-button" class="button danger-ghost combination-control" type="button" hidden>Remove second major</button>\n      <button id="data-status"'''
    text = replace_once(text, old, new, "second-major controls")

    old_tab = '    <button class="tab" data-view="planner" type="button"><span class="tab-icon">▦</span>Four-year plan</button>\n'
    new_tab = old_tab + '    <button id="combination-tab" class="tab" data-view="combination" type="button" hidden><span class="tab-icon">⇉</span>Combined degrees</button>\n'
    text = replace_once(text, old_tab, new_tab, "combined tab")

    text = replace_once(
        text,
        '  <main>\n',
        '''  <section id="degree-combination-banner" class="degree-combination-banner" hidden></section>\n\n  <main>\n''',
        "combination banner",
    )

    planner_button = '          <button id="clear-plan-button" class="button secondary" type="button">Clear plan</button>\n'
    planner_button_new = planner_button + '          <button id="toggle-year5-button" class="button secondary" type="button">＋ Add Year 5</button>\n'
    text = replace_once(text, planner_button, planner_button_new, "year 5 button")

    credits_anchor = '    <section id="view-credits" class="view">\n'
    combination_section = '''    <section id="view-combination" class="view">\n      <div class="view-heading">\n        <div>\n          <div class="eyebrow">ONE SHARED PLAN · TWO DEGREE AUDITS</div>\n          <h1>Combined degree plan</h1>\n          <p>Compare shared courses, requirements unique to each major, the minimum credit target, and how your current plan applies to both programs.</p>\n        </div>\n      </div>\n      <div id="combination-summary" class="metric-grid"></div>\n      <div id="combination-alert" class="combination-alert card-surface"></div>\n      <div id="combination-course-grid" class="combination-course-grid"></div>\n      <div id="combination-audits" class="combination-audits"></div>\n    </section>\n\n'''
    text = replace_once(text, credits_anchor, combination_section + credits_anchor, "combined view")

    return text.replace("</body>", f"  <!-- {MARKER} -->\n</body>", 1)


def patch_css(text: str) -> str:
    if MARKER in text:
        return text
    addition = r'''

/* DOUBLE_MAJOR_DUAL_DEGREE_MODE_V1 */
.combination-add-button { white-space: nowrap; }
.combination-control[hidden], #combination-tab[hidden], #degree-combination-banner[hidden] { display: none !important; }
.degree-combination-banner {
  margin: 14px 24px 0;
  padding: 13px 16px;
  border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--line));
  border-radius: var(--radius);
  background: color-mix(in srgb, var(--accent-soft) 72%, var(--surface));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  box-shadow: var(--shadow);
}
.degree-combination-banner strong { display: block; font-size: 1rem; }
.degree-combination-banner span { color: var(--muted); font-size: .9rem; }
.degree-combination-banner .combination-banner-copy { min-width: 0; }
.degree-combination-banner .combination-banner-actions { display: flex; gap: 8px; flex-shrink: 0; }
.combination-alert { padding: 16px 18px; margin-bottom: 18px; }
.combination-alert.valid { border-color: color-mix(in srgb, var(--success) 55%, var(--line)); }
.combination-alert.warning { border-color: color-mix(in srgb, #b7791f 55%, var(--line)); }
.combination-alert h2 { margin: 0 0 7px; font-size: 1rem; }
.combination-alert p { margin: 5px 0 0; color: var(--muted); line-height: 1.45; }
.combination-course-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 16px; margin-bottom: 18px; }
.combination-course-card { padding: 16px; min-width: 0; }
.combination-course-card h2 { margin: 0 0 5px; font-size: 1rem; }
.combination-course-card > p { margin: 0 0 12px; color: var(--muted); font-size: .88rem; }
.combination-course-chips { display: flex; flex-wrap: wrap; gap: 7px; max-height: 280px; overflow: auto; }
.combination-course-chip {
  border: 1px solid var(--line);
  background: var(--surface-2);
  border-radius: 999px;
  padding: 6px 9px;
  font: inherit;
  font-size: .78rem;
  color: var(--text);
}
.combination-course-chip.in-plan { border-color: var(--accent); background: var(--accent-soft); }
.combination-course-empty { color: var(--muted); font-size: .86rem; }
.combination-audits { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 16px; }
.combination-audit { padding: 18px; }
.combination-audit-head { display: flex; justify-content: space-between; gap: 14px; align-items: start; margin-bottom: 12px; }
.combination-audit-head h2 { margin: 0; font-size: 1.08rem; }
.combination-audit-head span { color: var(--muted); font-size: .82rem; text-align: right; }
.combination-requirement-list { display: grid; gap: 8px; }
.combination-requirement-row {
  display: grid;
  grid-template-columns: minmax(0,1fr) auto;
  gap: 10px;
  padding: 10px 11px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-2);
}
.combination-requirement-row strong { font-size: .86rem; }
.combination-requirement-row span { color: var(--muted); font-size: .78rem; text-align: right; }
.combination-requirement-row.fulfilled { border-color: color-mix(in srgb, var(--success) 50%, var(--line)); }
.combination-requirement-row.planned { border-color: color-mix(in srgb, var(--accent) 50%, var(--line)); }
.combination-status-pill { display: inline-flex; border-radius: 999px; padding: 4px 8px; font-size: .75rem; font-weight: 700; }
.combination-status-pill.double-major { background: var(--accent-soft); color: var(--accent); }
.combination-status-pill.dual-degree { background: #fff3cd; color: #7a4d00; }

@media (max-width: 980px) {
  .combination-course-grid, .combination-audits { grid-template-columns: 1fr; }
  .degree-combination-banner { margin: 10px 12px 0; align-items: flex-start; flex-direction: column; }
}
'''
    return text + addition


JS_BLOCK = r'''

// DOUBLE_MAJOR_DUAL_DEGREE_MODE_V1
function completedMajorDefinitions() {
  return (app.majorIndex?.majors || []).filter((entry) => entry.status === "complete" && entry.file);
}

function majorHasAlternateDegreePaths(major) {
  return Array.isArray(major?.tracks) && major.tracks.length > 1;
}

function majorAwardId(major) {
  return String(major?.degreeAwardId || major?.degree || major?.id || "unknown").trim();
}

function majorCollegeId(major) {
  return String(major?.collegeId || "unknown").trim();
}

function majorMinimumCredits(major) {
  return Number(major?.minimumDegreeCredits || major?.totalCredits || 180);
}

function combinationPairKey(first, second) {
  return [first?.id, second?.id].filter(Boolean).sort().join("|");
}

function combinationRestriction(primary, secondary) {
  if (!primary || !secondary) return "";
  if (primary.id === secondary.id) return "Choose two different majors.";

  const pair = combinationPairKey(primary, secondary);
  const primaryCollege = majorCollegeId(primary);
  const secondaryCollege = majorCollegeId(secondary);

  if (primaryCollege === "engineering" && secondaryCollege === "engineering") {
    return "UW permits only one undergraduate degree from the College of Engineering.";
  }

  const csIds = new Set(["uw-seattle-cs"]);
  const eceIds = new Set(["uw-seattle-ece", "uw-seattle-computer-engineering"]);
  if ([...csIds].some((id) => pair.includes(id)) && [...eceIds].some((id) => pair.includes(id))) {
    return "The Allen School does not permit this CS/Computer Engineering or CS/ECE degree combination.";
  }

  if (pair.includes("uw-seattle-cs") && /acms/i.test(pair)) {
    return "The Allen School does not permit a CS/ACMS double major or double degree.";
  }

  const hcde = [primary, secondary].find((major) => /human centered design|hcde/i.test(`${major.id} ${major.name}`));
  const other = hcde === primary ? secondary : hcde === secondary ? primary : null;
  if (hcde && other && (
    majorCollegeId(other) === "engineering"
    || /informatics|interaction design/i.test(`${other.id} ${other.name}`)
  )) {
    return "HCDE does not permit this second-major combination.";
  }

  return "";
}

function getDegreeCombination() {
  if (!app.secondaryMajor) return null;
  const primary = app.major;
  const secondary = app.secondaryMajor;
  const error = combinationRestriction(primary, secondary);
  const sameAward = majorAwardId(primary) === majorAwardId(secondary);
  const type = sameAward ? "double-major" : "dual-degree";
  const minimumCredits = sameAward
    ? Math.max(majorMinimumCredits(primary), majorMinimumCredits(secondary))
    : Math.min(majorMinimumCredits(primary), majorMinimumCredits(secondary)) + 45;

  const warnings = [];
  if (type === "dual-degree") {
    warnings.push("Two UW degrees normally require at least 45 credits beyond the smaller degree and at least 90 matriculated UW residence credits.");
  } else {
    warnings.push("The 180-credit minimum does not guarantee that every requirement for both majors will fit within 180 credits.");
  }
  if (majorCollegeId(primary) !== majorCollegeId(secondary)) {
    warnings.push("Because the programs are in different colleges, both colleges’ general-education requirements must be completed where they do not overlap.");
  }
  if ((majorCollegeId(primary) === "engineering" || majorCollegeId(secondary) === "engineering")
      && (primary.id === "uw-seattle-cs" || secondary.id === "uw-seattle-cs")) {
    warnings.push("CS plus an Engineering degree requires department approval and may be allowed only as a rare exception; CS plus ECE is prohibited.");
  }
  warnings.push("Course overlap between two majors is an estimate here; the departments decide which core courses may count toward both programs.");

  return {
    primary,
    secondary,
    type,
    label: type === "double-major" ? "Double major" : "Dual degree",
    minimumCredits,
    error,
    warnings
  };
}

function plannerDegreeTarget() {
  return getDegreeCombination()?.minimumCredits || Number(app.major.totalCredits || 180);
}

function plannerYears() {
  const showYear5 = Boolean(app.progress.year5Enabled || getDegreeCombination()?.type === "dual-degree");
  return showYear5 ? [1, 2, 3, 4, 5] : [1, 2, 3, 4];
}

function maxVisiblePlannerYear() {
  return Math.max(...plannerYears());
}

async function restoreSecondaryMajor() {
  app.secondaryMajor = null;
  const id = app.progress?.secondaryMajorId;
  if (!id || id === app.major?.id) return;
  const definition = completedMajorDefinitions().find((entry) => entry.id === id);
  if (!definition) {
    app.progress.secondaryMajorId = "";
    app.progress.secondaryTrack = "";
    return;
  }
  try {
    const secondary = await fetchJson(`data/majors/${definition.file}`);
    if (combinationRestriction(app.major, secondary)) {
      app.progress.secondaryMajorId = "";
      app.progress.secondaryTrack = "";
      return;
    }
    app.secondaryMajor = secondary;
    const tracks = secondary.tracks || [];
    if (!tracks.some((track) => track.id === app.progress.secondaryTrack)) {
      app.progress.secondaryTrack = tracks[0]?.id || "standard";
    }
  } catch (error) {
    console.warn("Could not restore second major", error);
    app.progress.secondaryMajorId = "";
    app.progress.secondaryTrack = "";
  }
}

function populateCombinationControls() {
  const addButton = $("#add-second-major-button");
  const majorField = $("#secondary-major-field");
  const trackField = $("#secondary-track-field");
  const removeButton = $("#remove-second-major-button");
  const majorSelect = $("#secondary-major-select");
  const trackSelect = $("#secondary-track-select");
  const tab = $("#combination-tab");

  if (!addButton || !majorField || !majorSelect) return;
  const active = Boolean(app.secondaryMajor || app.progress.secondaryMajorId);
  addButton.hidden = active;
  majorField.hidden = !active;
  removeButton.hidden = !active;
  trackField.hidden = !app.secondaryMajor || !majorHasAlternateDegreePaths(app.secondaryMajor);
  tab.hidden = !app.secondaryMajor;

  majorSelect.innerHTML = `<option value="">Choose a second major…</option>${completedMajorDefinitions()
    .filter((entry) => entry.id !== app.major.id)
    .map((entry) => `<option value="${escapeHtml(entry.id)}">${escapeHtml(entry.name)}</option>`)
    .join("")}`;
  majorSelect.value = app.progress.secondaryMajorId || "";

  if (app.secondaryMajor) {
    const tracks = app.secondaryMajor.tracks || [];
    const selectedTrack = app.progress.secondaryTrack || tracks[0]?.id || "standard";
    app.progress.secondaryTrack = selectedTrack;

    if (majorHasAlternateDegreePaths(app.secondaryMajor)) {
      trackSelect.disabled = false;
      trackSelect.innerHTML = tracks.map((track) => `<option value="${escapeHtml(track.id)}">${escapeHtml(track.name)}</option>`).join("");
      trackSelect.value = selectedTrack;
    } else {
      trackSelect.innerHTML = "";
      trackSelect.value = "";
      trackSelect.disabled = true;
    }
  } else {
    trackSelect.innerHTML = "";
    trackSelect.disabled = true;
  }
}

function showSecondMajorChooser() {
  app.progress.secondaryMajorId = app.progress.secondaryMajorId || "";
  populateCombinationControls();
  $("#add-second-major-button").hidden = true;
  $("#secondary-major-field").hidden = false;
  $("#remove-second-major-button").hidden = false;
  $("#secondary-major-select").focus();
}

async function changeSecondaryMajor(majorId) {
  if (!majorId) {
    app.secondaryMajor = null;
    app.progress.secondaryMajorId = "";
    app.progress.secondaryTrack = "";
    saveProgress();
    renderAll();
    return;
  }
  const definition = completedMajorDefinitions().find((entry) => entry.id === majorId);
  if (!definition) return showToast("That major definition is not available yet.");

  try {
    const secondary = await fetchJson(`data/majors/${definition.file}`);
    const error = combinationRestriction(app.major, secondary);
    if (error) {
      $("#secondary-major-select").value = app.progress.secondaryMajorId || "";
      return showToast(error);
    }
    app.secondaryMajor = secondary;
    app.progress.secondaryMajorId = secondary.id;
    app.progress.secondaryTrack = secondary.tracks?.[0]?.id || "standard";
    if (getDegreeCombination()?.type === "dual-degree") app.progress.year5Enabled = true;
    saveProgress();
    renderAll();
    showToast(`${secondary.name} added to the shared plan.`);
  } catch (error) {
    showToast(`Could not load that major: ${error.message}`);
  }
}

function removeSecondaryMajor() {
  app.secondaryMajor = null;
  app.progress.secondaryMajorId = "";
  app.progress.secondaryTrack = "";
  saveProgress();
  if (app.activeView === "combination") switchView("map");
  renderAll();
  showToast("Second major removed. Your shared course plan was kept.");
}

function toggleYear5() {
  const year5HasContent = QUARTERS.some((quarter) => quarter.year === 5 && (app.progress.plan?.[quarter.id] || []).length);
  if (app.progress.year5Enabled && year5HasContent) {
    return showToast("Move or remove Year 5 courses before hiding Year 5.");
  }
  app.progress.year5Enabled = !app.progress.year5Enabled;
  saveProgress();
  renderPlanner();
}

function updateYear5Button() {
  const button = $("#toggle-year5-button");
  if (!button) return;
  const forced = getDegreeCombination()?.type === "dual-degree";
  const shown = plannerYears().includes(5);
  button.textContent = forced ? "Year 5 included for dual degree" : shown ? "− Hide Year 5" : "＋ Add Year 5";
  button.disabled = forced;
}

function withMajorContext(major, trackId, callback) {
  const originalMajor = app.major;
  const originalTrack = app.progress.track;
  app.major = major;
  app.progress.track = trackId || major.tracks?.[0]?.id || "standard";
  try {
    return callback();
  } finally {
    app.major = originalMajor;
    app.progress.track = originalTrack;
  }
}

function visibleCodesForMajor(major, trackId) {
  return withMajorContext(major, trackId, () => new Set(
    getVisibleMapGroups().flatMap((group) => group.courses || []).map(normalizeCode)
  ));
}

function requirementRowsForMajor(major, trackId) {
  return withMajorContext(major, trackId, () => getActiveRequirements().map((requirement) => {
    const evaluation = evaluateRequirement(requirement);
    const planned = requirementHasPlannedCourses(requirement);
    return { requirement, evaluation, planned };
  }));
}

function renderCombinationCourseCard(title, subtitle, codes) {
  const represented = new Set([
    ...fulfilledCourseCodes(),
    ...Object.values(app.progress.plan || {}).flat().filter((item) => !isPlanSlot(item)).map(normalizeCode)
  ]);
  const sorted = [...codes].sort();
  const preview = sorted.slice(0, 120);
  return `<article class="combination-course-card card-surface">
    <h2>${escapeHtml(title)}</h2>
    <p>${escapeHtml(subtitle)} · ${sorted.length} course${sorted.length === 1 ? "" : "s"}</p>
    <div class="combination-course-chips">${preview.length
      ? preview.map((code) => `<span class="combination-course-chip ${represented.has(code) ? "in-plan" : ""}" title="${escapeHtml(getCourse(code).title)}">${escapeHtml(code)}</span>`).join("")
      : `<span class="combination-course-empty">No courses in this category.</span>`}
      ${sorted.length > preview.length ? `<span class="combination-course-empty">+ ${sorted.length - preview.length} more</span>` : ""}
    </div>
  </article>`;
}

function renderCombinationAudit(major, trackId) {
  const rows = requirementRowsForMajor(major, trackId);
  const completed = rows.filter((row) => row.evaluation.satisfied).length;
  const track = major.tracks?.find((entry) => entry.id === trackId)?.name || trackId;
  const trackSummary = majorHasAlternateDegreePaths(major) ? track : "";
  return `<article class="combination-audit card-surface">
    <div class="combination-audit-head">
      <div><h2>${escapeHtml(major.name)}</h2><span>${escapeHtml(major.degree || "")}</span></div>
      <span>${completed}/${rows.length} sections fulfilled${trackSummary ? `<br>${escapeHtml(trackSummary)}` : ""}</span>
    </div>
    <div class="combination-requirement-list">${rows.map(({ requirement, evaluation, planned }) => {
      const state = evaluation.satisfied ? "fulfilled" : planned ? "planned" : "";
      const status = evaluation.satisfied ? `✓ ${evaluation.label}` : planned ? `Planned · ${evaluation.label}` : evaluation.label;
      return `<div class="combination-requirement-row ${state}"><strong>${escapeHtml(requirement.title)}</strong><span>${escapeHtml(status)}</span></div>`;
    }).join("")}</div>
  </article>`;
}

function renderCombinationBanner() {
  const banner = $("#degree-combination-banner");
  if (!banner) return;
  const info = getDegreeCombination();
  if (!info) {
    banner.hidden = true;
    return;
  }
  banner.hidden = false;
  banner.innerHTML = `<div class="combination-banner-copy">
    <strong>${escapeHtml(info.primary.name)} + ${escapeHtml(info.secondary.name)} · ${escapeHtml(info.label)}</strong>
    <span>${escapeHtml(majorAwardId(info.primary))} + ${escapeHtml(majorAwardId(info.secondary))} · minimum ${formatNumber(info.minimumCredits)} credits · ${formatNumber(plannedCredits())} currently represented</span>
  </div>
  <div class="combination-banner-actions"><button id="open-combination-button" class="button primary" type="button">View combined plan</button></div>`;
  $("#open-combination-button")?.addEventListener("click", () => switchView("combination"));
}

function renderCombination() {
  const summary = $("#combination-summary");
  if (!summary) return;
  const info = getDegreeCombination();
  if (!info) {
    summary.innerHTML = "";
    $("#combination-alert").innerHTML = "<h2>Add a second major</h2><p>Use the button in the header to compare two programs.</p>";
    $("#combination-course-grid").innerHTML = "";
    $("#combination-audits").innerHTML = "";
    return;
  }

  const primaryCodes = visibleCodesForMajor(info.primary, app.progress.track);
  const secondaryCodes = visibleCodesForMajor(info.secondary, app.progress.secondaryTrack);
  const shared = new Set([...primaryCodes].filter((code) => secondaryCodes.has(code)));
  const primaryOnly = new Set([...primaryCodes].filter((code) => !secondaryCodes.has(code)));
  const secondaryOnly = new Set([...secondaryCodes].filter((code) => !primaryCodes.has(code)));
  const planned = plannedCredits();
  const remaining = Math.max(0, info.minimumCredits - planned);

  summary.innerHTML = [
    metricCard("Combination", info.label, 0, `${majorAwardId(info.primary)} + ${majorAwardId(info.secondary)}`),
    metricCard("Minimum credits", formatNumber(info.minimumCredits), 0, info.type === "dual-degree" ? "Usually 45 beyond the smaller degree" : "The actual course total may be higher"),
    metricCard("Plan represented", `${formatNumber(planned)} / ${formatNumber(info.minimumCredits)}`, planned / info.minimumCredits, `${formatNumber(remaining)} credits remaining to the minimum`),
    metricCard("Shared listed courses", shared.size, 0, "Potential overlap; department approval controls core overlap")
  ].join("");

  const alert = $("#combination-alert");
  alert.className = `combination-alert card-surface ${info.error ? "warning" : "valid"}`;
  alert.innerHTML = `<h2>${info.error ? "This combination is not permitted" : `${escapeHtml(info.label)} planning estimate`}</h2>
    ${info.error ? `<p>${escapeHtml(info.error)}</p>` : info.warnings.map((warning) => `<p>• ${escapeHtml(warning)}</p>`).join("")}`;

  $("#combination-course-grid").innerHTML = [
    renderCombinationCourseCard("Shared courses", "Listed by both selected degree paths", shared),
    renderCombinationCourseCard(info.primary.name, "Courses unique to the primary degree map", primaryOnly),
    renderCombinationCourseCard(info.secondary.name, "Courses unique to the second degree map", secondaryOnly)
  ].join("");

  $("#combination-audits").innerHTML = [
    renderCombinationAudit(info.primary, app.progress.track),
    renderCombinationAudit(info.secondary, app.progress.secondaryTrack)
  ].join("");
}
'''


def patch_js(text: str) -> str:
    if MARKER in text:
        return text

    # Add a fifth year to the data model. It stays hidden until requested, or is
    # shown automatically for a dual degree.
    text = replace_once(
        text,
        '  { id: "y4-summer", year: 4, season: "Summer" }\n];',
        '  { id: "y4-summer", year: 4, season: "Summer" },\n  { id: "y5-autumn", year: 5, season: "Autumn" },\n  { id: "y5-winter", year: 5, season: "Winter" },\n  { id: "y5-spring", year: 5, season: "Spring" },\n  { id: "y5-summer", year: 5, season: "Summer" }\n];',
        "Year 5 quarter definitions",
    )

    text = replace_once(text, '  major: null,\n', '  major: null,\n  secondaryMajor: null,\n', "secondary app state")

    text = replace_once(
        text,
        '    track: "standard",\n    fulfilled: {},',
        '    track: "standard",\n    secondaryMajorId: "",\n    secondaryTrack: "",\n    year5Enabled: false,\n    fulfilled: {},',
        "combination progress fields",
    )

    text = replace_once(
        text,
        '    app.progress = loadProgress();\n    migrateLegacyPlanSlots();',
        '    app.progress = loadProgress();\n    await restoreSecondaryMajor();\n    migrateLegacyPlanSlots();',
        "restore secondary major at startup",
    )

    # Insert the new feature functions before the normal global controls.
    text = replace_once(text, '\nfunction populateGlobalControls() {', JS_BLOCK + '\n\nfunction populateGlobalControls() {', "combination functions")

    if "populateCombinationControls();" not in text:
        text = replace_once(
            text,
            "  populateQuarterSelects();",
            "  populateCombinationControls();\n\n  populateQuarterSelects();",
            "populate combination controls",
        )

    text = replace_once(
        text,
        'function plannerSelectableQuarters(extraQuarterId = null) {\n  return QUARTERS.filter((quarter) => (\n    quarter.season !== "Summer"\n    || summerQuarterExpanded(quarter.year)\n    || quarter.id === extraQuarterId\n  ));\n}',
        'function plannerSelectableQuarters(extraQuarterId = null) {\n  return QUARTERS.filter((quarter) => (\n    quarter.year <= maxVisiblePlannerYear()\n    && (\n      quarter.season !== "Summer"\n      || summerQuarterExpanded(quarter.year)\n      || quarter.id === extraQuarterId\n    )\n  ));\n}',
        "visible planner quarters",
    )

    text = replace_once(
        text,
        '  for (const [standard, substitutes] of Object.entries(app.major.prerequisiteSubstitutions || {})) {\n    for (const substitute of substitutes || []) {\n      groups.push([normalizeCode(standard), normalizeCode(substitute)]);\n    }\n  }',
        '  for (const major of [app.major, app.secondaryMajor].filter(Boolean)) {\n    for (const [standard, substitutes] of Object.entries(major.prerequisiteSubstitutions || {})) {\n      for (const substitute of substitutes || []) {\n        groups.push([normalizeCode(standard), normalizeCode(substitute)]);\n      }\n    }\n  }',
        "overlap substitutions for both majors",
    )

    text = replace_once(
        text,
        '  const override = app.major.courseOverrides?.[normalized] || {};',
        '  const override = {\n    ...(app.secondaryMajor?.courseOverrides?.[normalized] || {}),\n    ...(app.major.courseOverrides?.[normalized] || {})\n  };',
        "course overrides for both majors",
    )

    text = replace_once(
        text,
        'function prerequisiteSubstitutes(code) {\n  return (app.major.prerequisiteSubstitutions?.[normalizeCode(code)] || []).map(normalizeCode);\n}',
        'function prerequisiteSubstitutes(code) {\n  const normalized = normalizeCode(code);\n  return [...new Set([\n    ...(app.major.prerequisiteSubstitutions?.[normalized] || []),\n    ...(app.secondaryMajor?.prerequisiteSubstitutions?.[normalized] || [])\n  ].map(normalizeCode))];\n}',
        "prerequisite substitutions for both majors",
    )

    text = replace_once(
        text,
        'function allMajorCodes() {\n  return [...new Set(app.major.mapGroups.flatMap((group) => group.courses).map(normalizeCode))];\n}',
        'function allMajorCodes() {\n  const majors = [app.major, app.secondaryMajor].filter(Boolean);\n  return [...new Set(majors.flatMap((major) => major.mapGroups.flatMap((group) => group.courses || [])).map(normalizeCode))];\n}',
        "all codes from both majors",
    )

    # Use either major's curated rule for status detection.
    text = replace_once(
        text,
        '  const override = app.major.courseOverrides?.[normalized];',
        '  const override = app.major.courseOverrides?.[normalized] || app.secondaryMajor?.courseOverrides?.[normalized];',
        "secondary status overrides",
    )

    # Add event handlers.
    text = replace_once(
        text,
        '  $("#major-select").addEventListener("change", (event) => changeMajor(event.target.value));\n',
        '  $("#major-select").addEventListener("change", (event) => changeMajor(event.target.value));\n  $("#add-second-major-button").addEventListener("click", showSecondMajorChooser);\n  $("#secondary-major-select").addEventListener("change", (event) => changeSecondaryMajor(event.target.value));\n  $("#secondary-track-select").addEventListener("change", (event) => {\n    app.progress.secondaryTrack = event.target.value;\n    saveProgress();\n    renderAll();\n  });\n  $("#remove-second-major-button").addEventListener("click", removeSecondaryMajor);\n  $("#toggle-year5-button").addEventListener("click", toggleYear5);\n',
        "combination event handlers",
    )

    # Restore any saved second major when changing the primary major.
    text = replace_once(
        text,
        '    app.major = major;\n    app.progress = loadProgress();\n    app.selectedCode = null;',
        '    app.major = major;\n    app.secondaryMajor = null;\n    app.progress = loadProgress();\n    await restoreSecondaryMajor();\n    app.selectedCode = null;',
        "primary-major change restoration",
    )

    text = replace_once(
        text,
        '  if (view === "catalog") renderCatalog();\n  if (view === "credits") renderCredits();',
        '  if (view === "catalog") renderCatalog();\n  if (view === "credits") renderCredits();\n  if (view === "combination") renderCombination();',
        "combined view render",
    )

    text = replace_once(
        text,
        '  renderPlanner();\n  renderCredits();',
        '  renderPlanner();\n  populateCombinationControls();\n  renderCombinationBanner();\n  renderCombination();\n  updateYear5Button();\n  renderCredits();',
        "render combined mode",
    )

    text = replace_once(
        text,
        '  $("#planner-grid").innerHTML = [1, 2, 3, 4].map((year) => {',
        '  $("#planner-grid").innerHTML = plannerYears().map((year) => {',
        "dynamic planner years",
    )

    text = replace_once(
        text,
        '  const totals = QUARTERS\n    .filter((quarter) => (\n      quarter.season !== "Summer"',
        '  const visibleYears = new Set(plannerYears());\n  const totals = QUARTERS\n    .filter((quarter) => (\n      visibleYears.has(quarter.year)\n      && (quarter.season !== "Summer"',
        "planner insight visible years",
    )
    # The previous replacement opened one extra parenthesis. Close it after the
    # existing summer conditions.
    text = replace_once(
        text,
        '      || quarterCredits(quarter.id) > 0\n    ))\n    .map((quarter)',
        '      || quarterCredits(quarter.id) > 0)\n    ))\n    .map((quarter)',
        "planner insight filter parentheses",
    )

    text = replace_once(
        text,
        '<p class="requirement-note"><strong>${formatNumber(plannedCredits())} / ${app.major.totalCredits}</strong> credits are represented.',
        '<p class="requirement-note"><strong>${formatNumber(plannedCredits())} / ${plannerDegreeTarget()}</strong> credits are represented.',
        "combined planner target",
    )

    return text


def main() -> None:
    for path in (APP, CSS, HTML):
        if not path.exists():
            raise SystemExit(f"Missing expected file: {path}")
        backup(path)

    html = patch_html(HTML.read_text(encoding="utf-8"))
    css = patch_css(CSS.read_text(encoding="utf-8"))
    js = patch_js(APP.read_text(encoding="utf-8"))

    HTML.write_text(html, encoding="utf-8")
    CSS.write_text(css, encoding="utf-8")
    APP.write_text(js, encoding="utf-8")
    count = update_major_metadata()

    print("Added optional second-major selection and a Combined degrees view.")
    print("Added double-major versus dual-degree classification and UW combination restrictions.")
    print("The planner is shared by both majors and uses the correct combined credit target.")
    print("Added an optional Year 5; dual degrees show it automatically.")
    print(f"Added degree metadata to {count} major file(s).")
    print("Backups use the suffix .before-degree-combinations")


if __name__ == "__main__":
    main()