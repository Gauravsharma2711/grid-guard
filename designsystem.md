# Grid-Guard — Design System

**Status:** Approved implementation baseline for the React migration  
**Design direction:** Calm Proof Flow  
**Product:** Grid-Guard electricity meter risk analysis and inspection prioritization  
**Use this document for:** Every Grid-Guard frontend screen, component, state, responsive implementation, chart, table, and interaction.

> **Design premise:** Grid-Guard is a calm, credible operational analytics product—not a noisy AI command center. It helps utility analysts inspect risk, understand evidence, and prioritize financially justified field inspections. Every screen should make the current task clear, keep evidence close to the claim it supports, and reveal technical detail progressively.

The visual language must retain the supplied Web-Slinger design system’s exact palette, typography, spacing scale, geometry, interaction timing, and restrained visual style. Only product terminology, information architecture, data components, and task flows are adapted to Grid-Guard.

---

## 1. Design Personality

| Attribute | Implementation meaning |
|---|---|
| **Calm** | Generous whitespace, measured density, concise copy, no visual urgency unless a decision is blocked or a system is unhealthy. |
| **Credible** | Display real model outputs, financial assumptions, time ranges, and evidence. Distinguish estimates from observed outcomes. |
| **Analyst-native** | Precise data typography, readable tables, code/technical metadata only when useful, meaningful chart axes, and reproducible model metadata. |
| **Human-owned** | Recommendations support analyst review and field verification. A model flag is not proof of physical tampering and must never be presented as a final accusation. |
| **Restrained** | One chartreuse signal color, violet reserved for model evidence, semantic status colors, no generic SaaS decoration. |
| **Financially clear** | Probability, estimated recoverable revenue, dispatch cost, and Expected Net Value are distinct quantities and must never be visually conflated. |

### Non-negotiable rules

1. Do not use a permanent left sidebar. Use a quiet horizontal header/navigation pattern with a clear active state.
2. Keep one dominant task per view and one visually dominant primary action. Secondary actions must remain quiet.
3. Do not use gradients, glassmorphism, floating blobs, particles, or decorative motion.
4. Do not use lorem ipsum, fake analytics, fake testimonials, or fake system activity.
5. Do not expose source data, verbose model metadata, or internal diagnostics by default. Use progressive disclosure.
6. Preserve the calm, lightly textured canvas and evidence-first visual language from the source system.
7. Prefer a single readable task area over a wall of equally weighted cards. Use compact KPI groupings only when they answer the same operational question.
8. Never style a model prediction as confirmed theft. Use “risk,” “flagged,” “signature,” “recommended inspection,” and “field verification.”
9. Label modeled and expected financial outputs as **estimated** or **expected**. Do not label estimates as actual recovered revenue.
10. The UI must consume backend/API outputs. Do not reimplement model, threshold, ENV, ranking, or SHAP calculations in the frontend.

---

## 2. Foundation Tokens

### 2.1 Color

**Preserve these values exactly. Do not introduce a new primary palette.**

| Token | Value | Use | Do not use for |
|---|---|---|---|
| `--gg-canvas` | `#FBFBF7` | Default page background | Dark code areas |
| `--gg-surface` | `#FFFFFF` | Inputs, table surfaces, small elevated surfaces, drawer/modal surfaces | Whole-page background by default |
| `--gg-ink` | `#121512` | Headings, primary buttons, critical text | Muted metadata |
| `--gg-ink-soft` | `#344038` | Body emphasis, labels, table values | Disabled states |
| `--gg-muted` | `#737B74` | Supporting copy, timestamps, helper text, inactive UI | Headings or important actions |
| `--gg-rule` | `#E1E5DD` | 1px dividers and quiet control borders | Heavy boxed card outlines |
| `--gg-signal` | `#D9FF4A` | Selected filter chips, one confirmed completion state, rare positive-ENV emphasis | General decoration or every primary button |
| `--gg-signal-ink` | `#3F4B08` | Text/icons on chartreuse | Normal body text |
| `--gg-evidence` | `#7D6DB2` | SHAP/model evidence, attribution markers, evidence references | Generic action color, navigation, or financial-positive status |
| `--gg-safe` | `#3F8B61` | Confirmed healthy service state and accessible positive status | Generic success marketing copy or proof of no theft |
| `--gg-warning` | `#B88418` | Needs review, uncertainty, incomplete data, verification required | Decorative emphasis |
| `--gg-danger` | `#C45646` | Blocked or failed state, validation error, operational failure | Default destructive hover or generic high-risk styling |
| `--gg-code` | `#151A16` | Code/diff/technical payload surfaces only | Page canvas |
| `--gg-code-ink` | `#E7EEE7` | Code and structured technical snippets | Light surfaces |

Use the `--gg-` prefix for Grid-Guard CSS tokens. Preserve every listed color value exactly. Grid-Guard-specific semantic aliases may refer to these tokens but must not redefine their values.

```css
:root {
  --gg-canvas: #fbfbf7;
  --gg-surface: #ffffff;
  --gg-ink: #121512;
  --gg-ink-soft: #344038;
  --gg-muted: #737b74;
  --gg-rule: #e1e5dd;
  --gg-signal: #d9ff4a;
  --gg-signal-ink: #3f4b08;
  --gg-evidence: #7d6db2;
  --gg-safe: #3f8b61;
  --gg-warning: #b88418;
  --gg-danger: #c45646;
  --gg-code: #1b211cff;
  --gg-code-ink: #e7eee7;
}
```

### 2.2 Semantic Color Rules

- **Risk probability:** Show as a number/percentage first. Use neutral ink for ordinary risk values; use warning/danger only when the applicable, documented operational threshold or status warrants it. Never invent risk bands in the frontend.
- **Expected Net Value (ENV):** Show the currency value with an explicit sign. Positive ENV may use restrained chartreuse or safe-green emphasis, but it must remain readable without color. Negative ENV uses neutral or warning styling based on context, not a bright alarm panel.
- **Dispatch cost:** Neutral ink. It is a cost component, not an alert state.
- **Estimated recovery:** Neutral ink with “Estimated” or “Expected” context.
- **SHAP contribution:** Violet (`--gg-evidence`) is for model attribution/evidence only. Positive and negative contribution direction must also be stated with text and/or a sign.
- **API/system health:** Green for healthy, amber for degraded/needs attention, red for failed/unavailable. Always include a textual label or icon.
- **Confirmed user action:** Chartreuse is used sparingly for a completed/selected state, not as a permanent page highlight.

Never depend on color alone to explain an alert, financial value, or decision.

### 2.3 Dark Mode

Dark mode may invert the primary canvas, surface, and text hierarchy, but the semantic colors must remain recognizable. Do not introduce new neon hues, gradients, or glass surfaces. The code surface remains near-black in either theme. If dark mode is not already implemented, do not make it a prerequisite for the React migration.

---

## 3. Typography

Preserve the original type families and hierarchy.

| Role | Family | Size | Line height | Weight | Use |
|---|---|---:|---:|---:|---|
| Display | Space Grotesk | 48–64px | 0.98 | 600 | Main page question/title; maximum two desktop lines |
| Section title | Space Grotesk | 28–36px | 1.05 | 600 | Major screen section |
| Record / issue title | Space Grotesk | 16–20px | 1.2 | 600 | Meter ID display, ticket title, selected record heading |
| Body | Inter | 14–16px | 1.55 | 400 | Explanations, context, descriptions |
| Interface label | Inter | 12–13px | 1.3 | 600 | Buttons, fields, table labels, selected tags |
| System metadata | IBM Plex Mono | 9–11px | 1.4 | 500–700 | Timestamps, model/version IDs, stage labels, compact statuses |
| Code / structured technical data | IBM Plex Mono | 12–13px | 1.55 | 400 | JSON excerpts, code, feature names, diagnostic snippets |
| Dense table values | Inter; IBM Plex Mono only for IDs/technical values | 12–14px | 1.4 | 400–500 | Inspection queue and metrics |

### Type rules

- Use all caps only for short operational metadata, such as `MODEL READY`, `EVALUATION PERIOD`, or `PHASE 6 MODEL`.
- Never use a text size smaller than 12px for essential controls or body information. The original 9–11px metadata scale is reserved for non-essential compact metadata only.
- Keep prose blocks within a 60–68 character line measure where practical.
- Do not use Inter as the only font; Space Grotesk provides the product’s primary editorial character.
- Tabular numeric fields should align consistently. Keep units and currency visible.
- Use concise numbers: for example `78.4%`, `₹8,200`, and `1,245 kWh`. Do not round values before the backend decision has been made.
- Avoid using oversized display type for every dashboard section. Reserve it for the primary screen title and occasional hero KPI when useful.

---

## 4. Spacing, Geometry, and Layout

### 4.1 Spacing Scale

| Token | Value | Typical use |
|---|---:|---|
| `--gg-space-1` | 4px | Hairline inline correction |
| `--gg-space-2` | 8px | Icon/label gaps |
| `--gg-space-3` | 12px | Compact padding |
| `--gg-space-4` | 16px | Default control padding |
| `--gg-space-6` | 24px | Small section gap |
| `--gg-space-8` | 32px | Main grouped-content gap |
| `--gg-space-12` | 48px | Page title to main task distance |
| `--gg-space-16` | 64px | Large screen whitespace |
| `--gg-space-20` | 80px | Desktop page breathing room |

### 4.2 Geometry Tokens

| Token | Value | Use |
|---|---:|---|
| `--gg-radius-xs` | 4px | Tags, compact status items |
| `--gg-radius-sm` | 6px | Inputs, buttons, quiet content blocks |
| `--gg-radius-lg` | 10px | Drawers, dialogs, selected detail surfaces |
| `--gg-rule-width` | 1px | Dividers and component boundaries |
| `--gg-header-height` | 56–60px | Global header height |
| `--gg-content-width` | 560–680px | Reading/detail column where a narrow measure is appropriate |
| `--gg-drawer-width` | 480px max | Evidence/details drawer on desktop |
| `--gg-control-height` | 44px min | Buttons, important inputs, action controls |
| `--gg-page-max-width` | 1440px | Wide analytics content container, where useful |

### 4.3 Grid-Guard Layout Patterns

| Pattern | When to use | Rules |
|---|---|---|
| **Decision Canvas** | Single-meter review, prediction review, confirmation, empty states | Focus one central question in a 560–680px column. Retain whitespace and one dominant action. |
| **Operations Canvas** | Overview, inspection queue, model comparison | Use a restrained full-width content area with clear hierarchy. A small row of related KPIs is allowed; avoid a wall of equal cards. |
| **Reading Canvas** | About, methodology, model details, limitations | Center readable content with a narrow measure and technical detail progressively disclosed. |
| **Inspection Workbench** | Meter detail and ticket review | Present risk and decision first, then temporal evidence, SHAP attribution, and financial detail in a deliberate reading order. Avoid three permanent equal columns. |
| **Right Drawer** | Detailed evidence, feature metadata, settings | Overlay from the right, maximum 480px on desktop, preserving the current inspection context underneath. |
| **Confirmation Modal** | Export, clear local filters/session, other irreversible actions | One decision, plain explanation, one confirm action, one cancel action. Never use for ordinary navigation. |

### 4.4 Background Texture

Entry, loading, empty, and proof/receipt states may use a faint dotted grid with an 18px rhythm and subtle circular linework. This texture is an orientation device, not decoration. Do not place it behind dense tables, charts, code, source excerpts, or long-form technical copy. Never let the texture reduce chart or table readability.

### 4.5 Whitespace and Density

- Use compact data density where it improves comparison, especially the inspection queue.
- Use generous whitespace around major decisions, meter explanations, and empty states.
- Do not make every panel a bordered card. Use spacing and dividers first; reserve surface elevation for a few meaningful focal areas.
- Table density may be increased for analyst workflows, but row labels and values must remain comfortably readable.

---

## 5. Navigation System

Navigation must be quiet, compact, and consistent. Grid-Guard needs several operational views, but that does not justify a permanent command-center sidebar.

### Header

The header contains:

- Grid-Guard mark/wordmark on the left,
- a compact current-area or system status label where useful,
- horizontal primary navigation,
- a restrained system/settings control only if it has real functionality.

Suggested navigation destinations:

1. **Overview**
2. **Inspection Queue**
3. **Meter Analysis**
4. **Model Insights**
5. **System Information**

Use the actual implemented route structure if it differs. Do not create a link to a screen that does not exist. On narrower screens, collapse navigation accessibly into a menu; do not compress all items until they are unreadable.

| Navigation type | Rule |
|---|---|
| Primary action | One per screen; near-black fill; moves the user to the next meaningful task. |
| Secondary action | One quiet border button or text action; it cannot compete with the primary action. |
| Back navigation | Small text link, contextual label, or browser back; never a large visual control. |
| Status | Compact metadata such as `MODEL READY`; never a large provenance dashboard. |
| Footer | Product/version or documentation links when useful; no extra product controls. |

The current location should be identifiable without a bright navigation block. Use underline, restrained border, or a subtle selected state consistent with the palette.

---

## 6. Component System

### 6.1 Header

| Property | Specification |
|---|---|
| Height | 56–60px |
| Left side | Grid-Guard mark and wordmark |
| Right side | Primary navigation, compact API/model status if genuinely available, settings only if implemented |
| Border | Optional single bottom `--gg-rule` divider |
| Prohibited | Permanent sidebar, multiple competing navigation clusters, marketing CTA cluster |

### 6.2 Buttons

| Variant | Style | Use |
|---|---|---|
| Primary | `--gg-ink` fill, white label, 44px minimum height, 6px radius | One forward/submit action per view |
| Primary hover | Chartreuse surface or subtle chartreuse edge only | Affordance, not decoration |
| Secondary | Transparent, 1px `--gg-rule` border, `--gg-ink` label | One quiet alternative action |
| Text action | No border; muted/ink label; underline only on hover/focus | Back, inspect, clear filter, expand detail |
| Destructive | Text-led confirmation with `--gg-danger` only when an irreversible action is involved | Clear/discard/export-sensitive actions where applicable |

Buttons must have a visible keyboard focus ring and a 120–160ms interaction response. Disabled controls must communicate their disabled state without relying on opacity alone.

### 6.3 Inputs and Filter Chips

| Component | Behavior |
|---|---|
| Search input | Clear label and search purpose; 44px minimum height; no placeholder-only labeling. |
| Select/filter | Use when it narrows an actual supported backend dataset or client-side result. |
| Selected filter chip | `--gg-signal` fill with `--gg-signal-ink`; removable action remains accessible. |
| Numeric threshold filter | Show unit and allowed range; do not reinterpret business thresholds in the frontend. |
| Error message | One clear sentence near the input; pair color with icon/text. |
| Empty filter result | State that no records match the current filters and provide one reset action. |

Do not show every filter permanently. Reveal advanced filters progressively, especially on smaller screens.

### 6.4 KPI Group

A KPI group is allowed when every metric answers the same operational question. Keep it to a small number of items and avoid decorative mini-charts without meaning.

Each metric must include:

- an explicit label,
- a formatted value,
- a unit/currency where relevant,
- a short contextual label when the metric is estimated, expected, or model-derived.

Examples:

- `Meters evaluated`
- `Inspections recommended`
- `Expected net value`
- `Estimated recoverable revenue`

Do not show a trend arrow or percent change unless an actual comparison period exists. Do not fabricate a trend to fill space.

### 6.5 Tables and Inspection Queue

Tables are central to Grid-Guard and must remain calm rather than decorative.

- Use a clear table heading and one sentence that explains the current queue.
- Show only the columns needed for the current decision. Put additional metadata in the meter detail view or a drawer.
- Keep header typography compact but readable.
- Align numeric columns consistently.
- Right-align currency and quantitative metrics where appropriate.
- Keep meter identifiers and timestamps easy to scan.
- Use subtle row separators with `--gg-rule`; avoid heavy gridlines around every cell.
- Use one restrained selected-row state.
- Support keyboard navigation and accessible sort controls.
- Show the active ranking basis, such as “Ranked by Expected Net Value,” only if that is the actual backend ranking basis.
- Never silently re-sort a financial-priority queue by tamper probability in the frontend.
- If pagination or sorting is client-side, make that explicit and preserve the backend’s decision values.

Recommended columns, where data exists:

- Rank
- Meter ID
- Tamper probability
- Estimated recoverable revenue
- Dispatch cost
- Expected Net Value
- Decision/status
- Primary signature

Do not display columns whose values are unavailable or inferred without a reliable source.

### 6.6 Status and Risk Labels

Use small, quiet status labels rather than large colored badges.

Examples:

- `Inspection recommended`
- `Review required`
- `Not recommended`
- `Data incomplete`
- `Model unavailable`
- `API degraded`

Status rules:

- Status text must reflect the actual API response or documented state.
- Do not invent labels such as “Critical theft” unless the backend explicitly defines them and the label is appropriate.
- Never identify a consumer as a thief based on a prediction.
- Pair status colors with text and, where useful, a small icon.

### 6.7 Financial Summary

Financial details must clearly separate:

- **Tamper probability:** the model's prediction score/probability.
- **Estimated recoverable revenue:** a derived or assumed financial estimate.
- **Expected gross recovery:** model probability multiplied by estimated recoverable revenue, when that is the configured formula.
- **Dispatch cost:** the configured/observed inspection expense.
- **Expected Net Value (ENV):** expected gross recovery minus dispatch cost, under the project's configured formula.
- **Realized recovery:** actual recovery after field inspection, only if real outcomes exist.

Never use one color or one label to merge these separate quantities. Use a small “How this is calculated” disclosure for equations/assumptions rather than adding explanatory paragraphs to every KPI.

### 6.8 Meter Detail / Inspection Workbench

The meter detail view should follow a deliberate sequence:

1. Meter identity and evaluation period.
2. Prediction and inspection recommendation.
3. ENV and financial components.
4. Consumption history and relevant baseline.
5. Primary evidence/signatures.
6. SHAP contributions and counter-evidence.
7. Data quality and technical metadata, progressively disclosed.

Do not show all metadata in the first viewport. The primary decision and main evidence must be understandable before the user expands technical detail.

### 6.9 Evidence and SHAP

| Component | Specification |
|---|---|
| SHAP attribution | Use `--gg-evidence` for attribution/evidence markers only. |
| Positive contribution | Show direction with a textual label/sign and use restrained evidence color. |
| Negative contribution | Explicitly label as counter-evidence; do not hide it. |
| Feature label | Use a human-readable feature name; preserve the raw feature name in expandable technical details if useful. |
| Source window | Show the actual start/end period supplied by the feature/explanation mapping. Never infer an unsupported date range. |
| Explanation statement | State the observed pattern and the model contribution separately where necessary. |
| Explanation caveat | Explain that a model signal requires verification and does not prove physical tampering. |

Never claim a SHAP contribution proves causality or a physical mechanism such as a bypass wire or magnet.

### 6.10 Charts

Charts must answer a clear question. Use the original palette without creating a new chart palette.

- **Consumption history:** ink line for observed consumption; restrained muted/reference line for a baseline; evidence color for attribution/marked evidence only; warning color for a genuinely documented review interval.
- **Model comparison:** use consistent styling across phases and label the metric and evaluation split.
- **ENV distribution:** use a readable zero reference line and correctly label currency.
- **Precision-recall curves:** label model version and evaluation split; use clearly distinguishable line styles in addition to color.
- **Feature contributions:** horizontal bars are preferred for readable feature names; clearly distinguish positive contribution from negative contribution.
- **Axes:** always include meaningful units and readable labels. Do not hide a relevant zero baseline to exaggerate differences.
- **Tooltips:** show precise values and units. Do not rely on tooltips for essential information.
- **Empty chart:** explain why the chart has no data and provide one sensible recovery action.

Do not generate decorative charts, fake trend lines, or fabricated data. Demo-only synthetic data must be explicitly labelled as such.

### 6.11 Source / Detail Drawer

A right drawer is appropriate for feature definitions, threshold formulas, model metadata, API diagnostics, and detailed evidence.

- Maximum width: 480px on desktop.
- Preserve the current record/page state beneath the drawer.
- Provide a clear close control.
- Support Escape and correct focus restoration.
- On mobile, use a full-height sheet with clear close/back behavior.

### 6.12 System Health

Health is compact by default. Display one factual state, such as `API available`, `Model not ready`, or `Data quality needs review`. Expand technical details only when requested.

Do not use an oversized status panel or continually animated activity indicator. Health checks must reflect actual `/health`, `/ready`, or metadata responses.

### 6.13 Code / JSON / Technical Data

Use `--gg-code` background and `--gg-code-ink` text for code/JSON excerpts only. Use IBM Plex Mono at 12–13px, with readable line height. Do not use the code surface for ordinary dashboard cards or the entire page background.

### 6.14 States and Feedback

| State | Required composition |
|---|---|
| Empty | One calm headline, one sentence explaining why there is no data, one recovery action. |
| Loading | One current operation and an optional compact progress/status disclosure. Avoid fake progress percentages. |
| Degraded | Honest cause, retained user context, one retry or safe alternative. |
| Error | No raw stack trace; one explanation and one recovery action. Technical details may be expanded. |
| Success | One confirmation line and the next meaningful action. |
| No matching records | State that current filters returned no records and provide one clear reset action. |
| Model unavailable | State that predictions cannot currently be generated. Do not fall back to fake results. |
| Insufficient history | Explain that the submitted history does not support one or more expected temporal features. Preserve warnings returned by the backend. |
| Stale data | Show the actual evaluation period or last-updated time. Never imply the information is live when it is not. |

---

## 7. Motion System

Preserve the supplied restrained motion rules.

| Interaction | Duration | Motion rule |
|---|---:|---|
| Button press | 120–160ms | Subtle scale/contrast response; never springy or bouncy |
| New content | 220ms | Fade + 6–8px upward movement when it improves comprehension |
| Drawer | 200–260ms | Opacity + horizontal transform from trigger side |
| Modal | 200–260ms | Fade surface and scale from 0.95, never scale from zero |
| Health recovery | One brief chartreuse scan | Only when relevant system activity is deliberately expanded |

Never use typewriter effects, looping gradients, bouncing indicators, particles, auto-playing charts, or moving background art. Respect `prefers-reduced-motion` by removing nonessential transform and scan effects. Do not animate continuously changing financial values.

---

## 8. Content and Voice

### Approved verbs

Use: **inspect, review, compare, explain, verify, filter, export, retry, view, examine**.

### Banned wording

Do not use: “unlock,” “supercharge,” “magic,” “AI-powered solution,” “get started,” “revolutionary,” generic marketing promises, or unsupported claims of certainty.

### Content rules

- Use the product name `Grid-Guard` consistently.
- Use real meter IDs and factual values from the API or clearly marked synthetic demo inputs.
- State uncertainty directly: “Estimated recovery,” “Model evidence is partial,” “Insufficient history,” or “The API could not return an explanation.”
- Do not call expected recovery “actual savings.”
- Do not call a flagged meter “confirmed theft” without an independent verified outcome.
- Keep main-screen explanatory copy to one or two sentences before asking the user to act.
- Use plain language first; place technical terminology and formulas behind a concise detail disclosure when possible.
- Include the evaluation period whenever a prediction or ranking could be mistaken for current/live data.

---

## 9. Accessibility and Responsive Behavior

| Area | Requirement |
|---|---|
| Keyboard | All controls must be reachable; focus order follows visual order. |
| Focus | Provide visible high-contrast focus treatment for links, buttons, filters, rows, drawers, and dialogs. |
| Status | Never communicate healthy, warning, positive ENV, or negative ENV using color alone. Include label/text and a sign where useful. |
| Dialogs | Trap focus, restore focus to the trigger, offer an explicit close button and Escape behavior. |
| Tap targets | Primary inputs and actions must be at least 44px high. |
| Mobile navigation | Preserve a clear destination and current location without forcing a permanent sidebar. |
| Mobile tables | Prioritize essential columns; allow a clear record-detail route instead of shrinking text into illegibility. |
| Mobile workbench | Prediction, finance, time-series evidence, and SHAP detail become full-width consecutive sections. |
| Evidence drawer | Becomes a full-height mobile sheet with clear close/back behavior. |
| Charts | Provide a textual/table alternative for important values. Do not rely on color or hover alone. |
| Reduced motion | Respect `prefers-reduced-motion`. |

Responsive behavior must be tested on desktop, tablet, and mobile sizes. Do not solve a narrow viewport by shrinking essential text below readable sizes.

---

## 10. Data Integrity and Trust

These rules are specific to Grid-Guard and are mandatory.

1. The React UI is a presentation/client layer. FastAPI and the existing Grid-Guard domain code remain the source of truth.
2. Do not recalculate ENV, cost thresholds, leakage estimates, or rankings in JavaScript/TypeScript. Display values returned by the backend.
3. Preserve the difference between raw model score, calibrated probability, threshold, ENV, expected recovery, and realized outcome.
4. Do not manufacture values for missing tariff, bill, recovery, label, meter history, feeder metadata, or evaluation metrics.
5. Do not replace API errors with invented/demo data. Demo data must be explicitly selected and visibly marked.
6. If a field is unavailable, show `Not available` or a similarly clear state rather than silently omitting context that changes interpretation.
7. Do not treat correlation or SHAP attribution as proof of causation or physical tampering.
8. Do not claim that a model decision alone authorizes enforcement. The UI supports analyst review and field verification.
9. Do not show a ranking basis unless it matches the actual backend decision rule and response.
10. Preserve timestamps, currency, measurement units, model version, feature version, and evaluation period when supplied by the API.
11. Avoid logging or storing raw meter histories in browser storage unless a documented requirement explicitly calls for it.
12. Never expose secrets, local filesystem paths, environment variables, or credentials in the UI.

---

## 11. React Implementation Rules

### Stack

Use the existing repository stack where established. For a new React frontend, prefer:

- React
- TypeScript with strict checking
- Vite
- CSS variables sourced from this design system
- a small reusable component system
- the existing FastAPI backend

Choose routing, charting, and data-fetching libraries only where they solve an actual need. Do not add several overlapping libraries for the same job.

### Design tokens

- Implement the exact palette and type tokens above as CSS custom properties.
- Preserve the existing token names where possible.
- Do not redefine values locally in individual components.
- Do not introduce a parallel palette or one-off hex values where an existing semantic token applies.
- Use CSS variables for spacing, radii, header height, and control height.

### Components

Create reusable components for the patterns that recur in the actual product, such as:

- `AppHeader`
- `PageHeading`
- `StatusLabel`
- `MetricValue`
- `FilterBar`
- `InspectionTable`
- `InspectionDecision`
- `FinancialSummary`
- `ConsumptionChart`
- `ShapContributionList`
- `SignatureList`
- `EvidenceDrawer`
- `EmptyState`
- `LoadingState`
- `ErrorState`

These are suggested names, not a demand to create components that have no use. Reuse actual project conventions where reasonable.

### API client

- Centralize the API base URL in environment configuration.
- Use typed request/response interfaces based on the actual FastAPI/OpenAPI contract.
- Create one reusable API client/service layer.
- Handle loading, timeout, validation, not-ready, and server-error states honestly.
- Do not duplicate backend business formulas in frontend utilities.
- Do not silently change API field names to fit UI preferences; add a clear adapter at the boundary if needed.

### State and caching

- Avoid repeating expensive prediction/SHAP calls when React rerenders.
- Cache only where behavior is explicit and safe.
- Do not persist sensitive meter histories in local storage by default.
- Do not display stale response data as fresh without an evaluation timestamp/status.

### Quality

- Use semantic HTML and accessible labels.
- Keep UI components focused.
- Avoid monolithic page components.
- Do not ship debug prints, unused components, placeholder metrics, or fake activity.
- Test critical flows and API contract assumptions.

---

## 12. Screen Specifications

### 12.1 Overview

**Central question:** What requires attention in the current evaluation period?

Show a restrained group of relevant operational metrics only when the backend provides them:

- meters evaluated,
- inspections recommended,
- estimated recoverable revenue,
- estimated dispatch cost,
- aggregate expected net value.

Below the summary, show one meaningful operational view such as the highest-priority inspection candidates or a concise ENV distribution. Avoid a wall of cards and charts. Include an explicit evaluation period and a compact API/model state when available.

Primary action: open/review the inspection queue.

### 12.2 Inspection Queue

**Central question:** Which meters should be reviewed first under the active decision policy?

Show a table ranked according to the backend's actual ranking. State the active ranking basis and evaluation period. Provide search and only supported filters. Clicking a row opens its meter details. Keep secondary metadata in the details view/drawer.

Primary action: inspect a selected meter.

### 12.3 Meter Analysis

**Central question:** What evidence explains this meter's risk and decision?

Show meter identity, evaluation period, probability, inspection decision, ENV, and major financial components. Display consumption and historical baseline where available, with real evidence intervals. Follow with top positive and negative SHAP contributors, detected signatures, counter-evidence, and a clear verification caveat.

Primary action: review the evidence/inspection ticket.

### 12.4 Model Insights

**Central question:** How did the implemented models perform on the reported evaluation data?

Show actual Phase 4/5/6 metrics and Phase 7 policy comparisons only where reproducible artifacts exist. Label train/validation/test split and model version. Use a small set of meaningful comparisons such as PR-AUC, Precision@K, false positives/negatives, and financial outcome estimates. Avoid model-ranking labels that are not supported by a defined metric.

Primary action: view the metric definition or evaluation detail.

### 12.5 System Information

**Central question:** Is the current application ready, and which model/configuration produced these results?

Show compact, safe metadata: API readiness, model version, feature version, decision rule, explanation availability, and last-updated/evaluation timestamp where available. Expand diagnostics only when requested. Do not expose secrets or internal paths.

Primary action: retry or open diagnostic details only when the current state supports it.

### 12.6 Inspection Ticket

A ticket is a focused detail view, not a second dashboard. Include:

- meter/evaluation identity,
- tamper probability,
- estimated recoverable revenue,
- dispatch cost,
- expected gross recovery if available,
- ENV,
- active decision rule/threshold,
- primary model evidence,
- detected signatures and time windows,
- counter-evidence,
- field verification caveat.

Do not claim a real inspection has been scheduled or dispatched unless an actual integration confirms it.

---

## 13. Component and State Quality Checklist

Before accepting any screen or component, verify every relevant statement below:

1. Is the current task or question obvious?
2. Is there one visually dominant action?
3. Are nonessential technical details progressively disclosed?
4. Does the screen retain intentional whitespace without hiding necessary analytical information?
5. Are the original colors used semantically and sparingly?
6. Are probability, estimated recovery, dispatch cost, and ENV visually distinct?
7. Are claims about model evidence represented as risk/evidence rather than proof of theft?
8. Are API values shown without frontend recomputation?
9. Does each chart have meaningful labels, units, and evaluation period?
10. Does the screen show real content or clearly labelled synthetic demo data?
11. Can a keyboard-only user complete the main action?
12. Are loading, empty, degraded, and error states handled without raw stack traces?
13. Does the screen avoid a permanent sidebar, unnecessary cards, and decorative noise?
14. Does responsive behavior preserve readability and interaction?
15. Does the page feel calm, credible, and operationally useful at first glance?

If any relevant answer is “no,” the screen is not ready to ship.

---

## 14. Migration Rules: Streamlit to React

This system is the frontend design authority for the Grid-Guard React migration.

1. Read this file before implementing or styling any React screen.
2. Preserve the colors, typography, spacing, geometry, motion, and component tone exactly as specified.
3. Translate Streamlit functionality into React experiences; do not mechanically reproduce Streamlit layout quirks.
4. Preserve current FastAPI endpoints and request/response contracts unless a backward-compatible, justified change is required.
5. React must call FastAPI. It must not import or reimplement model training, feature engineering, financial logic, decision thresholds, ENV, or SHAP calculations.
6. Do not retire the Streamlit application until React feature parity and end-to-end regression validation pass.
7. Do not invent screens, controls, or data fields that the backend cannot support.
8. If a component requirement conflicts with a backend contract, inspect and document the mismatch before implementing an adapter. Do not silently change the underlying business semantics.
9. Build reusable components from the design tokens rather than hard-coding styling per screen.
10. Keep the final UI consistent across Overview, Inspection Queue, Meter Analysis, Model Insights, and System Information.

---

## 15. References and Implementation Notes

- **Authoritative visual source:** This `DesignSystem.md`.
- **Product:** Grid-Guard.
- **Frontend direction:** React + TypeScript, normally with Vite if the repository does not already establish an alternative.
- **Backend:** Existing FastAPI API and its actual OpenAPI contract.
- **Decision source of truth:** Existing Grid-Guard decision engine.
- **Explanation source of truth:** Existing Grid-Guard SHAP/explanation engine.
- **Financial source of truth:** Existing backend financial/ENV implementation.

When this document does not specify an implementation detail, choose the smallest accessible solution that maintains the stated visual language. Do not invent new colors, decorative motifs, or competing navigation systems to fill a gap.
