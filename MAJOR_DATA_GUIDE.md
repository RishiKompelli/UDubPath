# Major data guide

Each major is a JSON file in `data/majors/`. The UI reads requirements from data instead of hard-coding a particular degree.

## Main fields

```json
{
  "id": "uw-seattle-me",
  "name": "Mechanical Engineering",
  "degree": "Bachelor of Science in Mechanical Engineering",
  "totalCredits": 180,
  "tracks": [],
  "courseOverrides": {},
  "prerequisiteSubstitutions": {},
  "mapGroups": [],
  "requirements": [],
  "samplePlan": {}
}
```

### `tracks`

Use tracks for options, concentrations, or degree variants.

```json
{"id":"standard","name":"Standard option","description":"..."}
```

### `courseOverrides`

Catalog information is used automatically. Overrides are for major-specific prerequisite logic, updated credits, or an official title.

Prerequisites are an array of AND groups. Courses inside one group are alternatives joined by OR.

```json
"ME 333": {
  "title": "Introduction to Fluid Mechanics",
  "credits": "5",
  "prerequisiteGroups": [
    ["AMATH 301"],
    ["ME 323"],
    ["MATH 207", "AMATH 351"]
  ]
}
```

That means:

```text
AMATH 301
AND ME 323
AND (MATH 207 OR AMATH 351)
```


### `prerequisiteSubstitutions`

Use one-way substitutions when an honors, accelerated, or approved equivalent course satisfies a prerequisite without pretending the original course itself was completed.

```json
"prerequisiteSubstitutions": {
  "MATH 126": ["MATH 136"],
  "PHYS 121": ["PHYS 141"]
}
```

This lets an honors path unlock later courses while keeping the standard and honors course boxes separate.

### `mapGroups`

Map groups define the official degree-requirement sections shown as columns. For UW Engineering majors, use the same section names and order as the College of Engineering degree-requirements page. Prerequisite arrows connect courses across and within those sections.

```json
{"id":"core","label":"Major Core Requirements","credits":"46 cr","courses":["ME 323","ME 333"]}
```

### `requirements`

Supported rule types:

- `group`: contains multiple items.
- `path-choice`: every course in any one listed path.
- `all`: every listed course.
- `one`: one listed course.
- `count`: a minimum number of listed courses.
- `count-credit`: both a minimum course count and credit total.
- `pool`: a minimum number of credits from an approved pool.
- `bucket`: credits carrying an area such as A&H, SSc, DIV, or C.
- `additional-bucket`: credits in an area beyond a specified base, such as the extra 4 A&H/SSc credits after the first 20.
- `manual`: a requirement entered directly as completed credits.
- `total`: total degree credits.

A requirement can include a `track` field so it appears only for that selected option.

### `samplePlan`

Quarter IDs are `y1-autumn` through `y4-spring`.

```json
"samplePlan": {
  "name": "Official sample plan",
  "quarters": {
    "y1-autumn": ["MATH 124", "CHEM 142"],
    "y1-winter": ["MATH 125"]
  }
}
```

Use `SLOT:` entries for requirements that need a course choice:

```json
"SLOT:A&H / SSc / DIV"
```


### Requirement-only cards in the map

Sections such as General Education and Free Electives may not have one fixed course list. Add `requirementRefs` to a map group so those requirements still appear visually and link to the detailed Requirements tab.

```json
{
  "id": "general-education",
  "label": "General Education Requirements",
  "credits": "29–41 cr",
  "courses": [],
  "requirementRefs": [
    {"id":"english-comp","scope":"item","label":"English Composition","credits":"5 cr"},
    {"id":"div","scope":"item","label":"Diversity","credits":"5 cr · may overlap"}
  ]
}
```
