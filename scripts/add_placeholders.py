from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "scripts" else Path.cwd()
APP_JS = ROOT / "src" / "app.js"
STYLES = ROOT / "src" / "styles.css"


def backup(path: Path) -> None:
    target = path.with_suffix(path.suffix + ".before-map-placeholders")
    if path.exists() and not target.exists():
        shutil.copy2(path, target)


def patch_app_js() -> None:
    if not APP_JS.exists():
        raise SystemExit(f"Could not find {APP_JS}. Run this script from the project folder.")

    text = APP_JS.read_text(encoding="utf-8")
    backup(APP_JS)

    marker = "function getSamplePlanMapSlots() {"
    if marker not in text:
        helpers = r'''
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

'''
        text = text.replace("function getApExam(examId) {", helpers + "function getApExam(examId) {", 1)

    if "const planSlotsByGroup = getMapPlanSlotsByGroup(groups);" not in text:
        text = text.replace(
            "  const groups = getVisibleMapGroups();\n  const selected = app.selectedCode;",
            "  const groups = getVisibleMapGroups();\n  const planSlotsByGroup = getMapPlanSlotsByGroup(groups);\n  const selected = app.selectedCode;",
            1,
        )

    if "const planSlotCards = planSlots.map" not in text:
        text = text.replace(
            '    const requirementCards = (group.requirementRefs || []).map(renderMapRequirementCard).join("");\n    const itemCount = group.courses.length + (group.requirementRefs || []).length;',
            '    const requirementCards = (group.requirementRefs || []).map(renderMapRequirementCard).join("");\n    const planSlots = planSlotsByGroup.get(group.id) || [];\n    const planSlotCards = planSlots.map((slot) => renderMapPlanSlotCard(slot, rawQuery)).join("");\n    const itemCount = group.courses.length + (group.requirementRefs || []).length + planSlots.length;',
            1,
        )

    if 'map-plan-slot-list' not in text:
        text = text.replace(
            '        ${requirementCards ? `<div class="map-requirement-list">${requirementCards}</div>` : ""}\n        <div class="map-node-list">${nodes}</div>',
            '        ${requirementCards ? `<div class="map-requirement-list">${requirementCards}</div>` : ""}\n        ${planSlotCards ? `<div class="map-plan-slot-section"><div class="map-plan-slot-heading">Course placeholders</div><div class="map-plan-slot-list">${planSlotCards}</div></div>` : ""}\n        <div class="map-node-list">${nodes}</div>',
            1,
        )

    if 'data-map-plan-slot' not in re.search(r"function handleMapClick\(event\) \{.*?\n\}", text, re.S).group(0):
        text = text.replace(
            "function handleMapClick(event) {\n",
            '''function handleMapClick(event) {
  const planSlotNode = event.target.closest("[data-map-plan-slot]");
  if (planSlotNode) {
    openMapPlanSlot(planSlotNode.dataset.mapPlanSlot, planSlotNode.dataset.mapPlanQuarter);
    return;
  }
''',
            1,
        )

    APP_JS.write_text(text, encoding="utf-8")


def patch_styles() -> None:
    if not STYLES.exists():
        raise SystemExit(f"Could not find {STYLES}.")

    text = STYLES.read_text(encoding="utf-8")
    backup(STYLES)

    if ".map-plan-slot-section" not in text:
        text += r'''

.map-plan-slot-section {
  margin: 10px 10px 2px;
  padding-top: 10px;
  border-top: 1px dashed var(--line, #d5dce5);
}

.map-plan-slot-heading {
  margin: 0 2px 7px;
  color: var(--muted, #667085);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.map-plan-slot-list {
  display: grid;
  gap: 7px;
}

.map-plan-slot-node {
  width: 100%;
  border: 1.5px dashed #8b79c6;
  border-radius: 10px;
  background: color-mix(in srgb, #8b79c6 8%, white);
  color: inherit;
  padding: 9px 10px;
  text-align: left;
  cursor: pointer;
  transition: transform 120ms ease, border-color 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
}

.map-plan-slot-node:hover {
  transform: translateY(-1px);
  border-color: #654fb0;
  box-shadow: 0 4px 12px rgba(61, 46, 112, 0.12);
}

.map-plan-slot-node.dimmed {
  opacity: 0.28;
}

.map-plan-slot-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.map-plan-slot-top strong {
  font-size: 0.82rem;
  line-height: 1.25;
}

.map-plan-slot-top em {
  flex: 0 0 auto;
  color: #58458f;
  font-size: 0.72rem;
  font-style: normal;
  font-weight: 800;
}

.map-plan-slot-status {
  display: block;
  margin-top: 5px;
  color: var(--muted, #667085);
  font-size: 0.7rem;
  font-weight: 650;
}
'''

    STYLES.write_text(text, encoding="utf-8")


def main() -> None:
    patch_app_js()
    patch_styles()
    print("Added four-year-plan placeholders to the degree map.")
    print("Updated src/app.js and src/styles.css.")
    print("Backups use the suffix .before-map-placeholders")


if __name__ == "__main__":
    main()