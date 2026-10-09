# Grid-Guard — Phase 2 Design System Implementation

## 1. Overview & Authority

This document specifies the technical implementation of the Grid-Guard Design System ("Calm Proof Flow") established in Phase 2 of the React migration.

The authoritative design specification is [/designsystem.md](file:///c:/Gaurav's%20Den/crazy-shits/grid-guard/designsystem.md). All tokens, component geometries, typography families, color constraints, and accessibility rules implemented in the React frontend strictly conform to `/designsystem.md` without deviation or competing conventions.

---

## 2. Token Architecture & CSS Implementation

The design token system is located in [`frontend/src/styles/tokens.css`](file:///c:/Gaurav's%20Den/crazy-shits/grid-guard/frontend/src/styles/tokens.css) and exposed globally through CSS custom properties on `:root`.

### 2.1 Color Tokens
| Token | Value | Semantic Intent / Usage |
| :--- | :--- | :--- |
| `--gg-canvas` | `#f4f3ef` | Warm neutral foundational background; zero pure white wash |
| `--gg-surface` | `#ffffff` | Primary content panels, cards, data tables, dialogs |
| `--gg-surface-subtle` | `#eeede8` | Table headers, secondary control backgrounds, input fills |
| `--gg-text` | `#111111` | Primary interface copy, headings, and high-contrast labels |
| `--gg-text-muted` | `#6b6a65` | Secondary metadata, timestamps, units, explanatory text |
| `--gg-border` | `#dedcd5` | Container borders, card outlines, control perimeters |
| `--gg-border-subtle` | `#e8e7e1` | Table row dividers, inner section separators |
| `--gg-signal` | `#d4e838` | Restrained chartreuse accent; active filter chips and stage badges |
| `--gg-signal-ink` | `#111111` | High-contrast dark ink on chartreuse signals |
| `--gg-evidence` | `#ede9fe` | Violet evidence wash; strictly reserved for SHAP & model explainability |
| `--gg-evidence-text` | `#5b21b6` | Violet evidence text for SHAP attribution labels |
| `--gg-code` | `#0f0f0e` | Near-black terminal surface for raw code, JSON payloads, and logs |
| `--gg-code-text` | `#f4f3ef` | Light text on code surfaces |
| `--gg-safe` | `#16a34a` | Green indicator for non-tamper/normal meters and positive revenue recovery |
| `--gg-warning` | `#d97706` | Amber indicator for degraded connectivity and data quality warnings |
| `--gg-danger` | `#dc2626` | Red indicator for high-risk meter tampering and critical system errors |
| `--gg-focus` | `#111111` | Solid high-contrast keyboard focus ring |

### 2.2 Typography Hierarchy
Configured in [`frontend/src/styles/typography.css`](file:///c:/Gaurav's%20Den/crazy-shits/grid-guard/frontend/src/styles/typography.css):
- **Display & Section Headings:** `'Space Grotesk', -apple-system, sans-serif`
  - `.gg-type-display`: 28px / line-height 34px / weight 600
  - `.gg-type-section`: 20px / line-height 26px / weight 600
  - `.gg-type-title`: 15px / line-height 20px / weight 600
- **Body & Interface Labels:** `'Inter', -apple-system, sans-serif`
  - `.gg-type-body`: 14px / line-height 20px / weight 400
  - `.gg-type-caption`: 12px / line-height 16px / weight 400
  - `.gg-type-label`: 12px / line-height 16px / weight 500 / uppercase letter-spaced
- **Technical Metadata & Code:** `'IBM Plex Mono', monospace`
  - `.gg-type-mono`: 12px / line-height 16px / weight 400
  - Used for Meter IDs (`CONS_XXXXXX`), timestamps, financial numbers, SHA hashes, and probabilities.

### 2.3 Geometry & Layout Dimensions
- `--gg-radius-sm`: `4px` (Chips, badges, inner tags)
- `--gg-radius-md`: `6px` (Standard inputs, buttons, table containers)
- `--gg-radius-lg`: `8px` (Main cards, drawers, dialogs)
- `--gg-header-height`: `52px` (Sticky application header)
- `--gg-control-height`: `44px` (Accessible minimum touch/click target for buttons and inputs)
- `--gg-control-height-compact`: `32px` (Table action buttons and inline filters)
- `--gg-max-decision-canvas`: `680px` (Focused single-meter triage and decision canvas)
- `--gg-max-ops-canvas`: `1440px` (Operations dashboard, inspection queue, and analytics)
- `--gg-drawer-max-width`: `480px` (Right-side slide-out inspection drawer)

---

## 3. Reusable Component Library

The frontend architecture implements focused, reusable primitives in `frontend/src/components/`:

### 3.1 Button (`components/ui/Button/`)
- **Variants:**
  - `primary`: High-contrast near-black background (`#111111`) with white text.
  - `secondary`: Subtle surface fill (`#ffffff`) with border (`--gg-border`).
  - `text`: Bare link-style button with restrained hover line.
  - `destructive`: Muted red border and text for risky confirmations.
- **Sizes:** Standard (`44px`) and `compact` (`32px`).
- **States:** Hover, active, disabled (`opacity: 0.5`), and `isLoading` (replaces label with inline SVG spinner).

### 3.2 Form Controls & Inputs (`components/ui/Input/`)
- `FormField`: Accessible wrapper handling label association (`htmlFor`), optional badge, hint text, and inline error messages with `role="alert"`.
- `TextInput`: Standard text input with optional `mono` styling for meter identifiers and custom prefixes/suffixes.
- `NumberInput`: Tabular numeric input supporting min/max constraints, step sizing, and currency/unit suffixes (e.g. `₹/kWh`, `₹`).
- `Select`: Restrained native `<select>` styling with standardized height and focus outline.

### 3.3 Filter Chips (`components/ui/FilterChip/`)
- Compact clickable chips for inspection queue filtering (e.g. "High Risk", "Positive ENV").
- Selected state uses chartreuse signal fill (`--gg-signal`) and dark ink (`--gg-signal-ink`).
- Includes count badge and accessible removal button (`×`).

### 3.4 Status & Evidence Badges (`components/ui/Status/`)
- `StatusBadge`: Four semantic variants (`safe`, `warning`, `danger`, `neutral`) using discrete colored status dots and high-contrast text. Never relies on color alone.
- `EvidenceBadge`: Reserved strictly for SHAP feature attributions. Employs light violet wash (`--gg-evidence`) and violet text (`--gg-evidence-text`) with directional indicator (`+ Risk` / `- Counter`).
- `TechnicalMetadata`: Key-value pair with monospace value formatting.
- `DataQualityWarning`: Alert callout for missing consumption intervals or telemetry gaps.

### 3.5 Surfaces & Dividers (`components/ui/Surface/`)
- `Surface`: Main content container with quiet border (`--gg-border`) and subtle shadow.
- `Divider`: Quiet 1px horizontal separator (`--gg-border-subtle`).
- `CodeSurface`: Terminal-like container (`--gg-code`) for JSON previews and technical logs.

### 3.6 Data Table (`components/ui/Table/`)
- Generic typed `DataTable<T>` component with:
  - Header row with uppercase tracking labels.
  - Right-aligned numeric columns.
  - Monospace meter identifiers.
  - Keyboard accessible row selection (`Enter` / `Space`).
  - Integrated loading skeleton and empty state fallback.

### 3.7 Financial Presentation Primitives (`components/ui/Financial/`)
- Pure presentation formatting only — **never calculates financial metrics in the browser**.
- `CurrencyValue`: Formats amounts in Indian Rupee (`₹`) with grouping and tabular numerals.
- `EnvMetric`: Highlights positive Expected Net Value (`+₹XX`) with green pill or negative value with neutral pill.
- `ProbabilityMetric`: Displays calibrated tamper probability (`0.0% – 100.0%`).
- `FinancialSummaryBlock`: Structured multi-column breakdown comparing Estimated Recovery vs Dispatch Cost.

### 3.8 Chart Container (`components/ui/Chart/`)
- Standardized container frame for future Plotly/canvas time-series visualizers.
- Includes header with title, subtitle, evaluation date range badge, series legend, and hidden accessible `<details>` summary for screen readers.

### 3.9 Feedback States (`components/ui/Feedback/`)
- `LoadingState`: Calm loading indicator with spinner and descriptive message.
- `EmptyState`: Contextual empty message with title, description, and primary recovery action.
- `ErrorState`: Clear error description and retry button without exposing stack traces.
- `DegradedBanner`: Non-blocking warning banner when the FastAPI inference backend is unavailable.

### 3.10 Accessible Overlays (`components/ui/Overlay/`)
- `Drawer`: Right-side slide-out panel (max 480px) for meter detail inspections.
  - Traps focus inside the drawer while open.
  - Restores focus to the triggering element upon close.
  - Closes on `Escape` key press or backdrop click.
  - Supports `prefers-reduced-motion`.
- `ConfirmationModal`: Center-aligned modal for dispatch confirmation and high-impact actions.

---

## 4. Application Shell & Navigation

- **Header (`AppHeader`):** Sticky top bar at 52px height.
  - Electric bolt brand mark and `"GRID-GUARD"` title.
  - Subtitle: `"NTL Detection Platform"`.
  - Phase 2 stage pill (`"PHASE 2"`).
  - Navigation tabs: Overview, Component Showcase (Dev), Inspection Queue, Meter Analysis, Model Insights, and System Info.
  - Real-time API connection probe badge (`API ONLINE` or `API DISCONNECTED`).
- **Shell (`AppShell`):** Wraps header, main application area, and quiet bottom footer.
- **Layouts (`LayoutPrimitives`):**
  - `DecisionCanvas`: Centered layout constrained to 560–680px for high-focus decisioning.
  - `OperationsCanvas`: Full-width layout up to 1440px for data tables and multi-series charts.

---

## 5. Typed API Client Architecture

Located in [`frontend/src/services/apiClient.ts`](file:///c:/Gaurav's%20Den/crazy-shits/grid-guard/frontend/src/services/apiClient.ts) and contracts in [`frontend/src/types/api.ts`](file:///c:/Gaurav's%20Den/crazy-shits/grid-guard/frontend/src/types/api.ts):

- **Strict Contracts:** Models all 8 FastAPI routes:
  1. `GET /api/v1/health`
  2. `GET /api/v1/ready`
  3. `GET /api/v1/model/info`
  4. `POST /api/v1/predict`
  5. `POST /api/v1/predict/explain`
  6. `POST /api/v1/predict/batch`
  7. `POST /api/v1/inspection/ticket`
  8. `POST /api/v1/inspection/queue`
- **Client Features:**
  - Configurable base URL via `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).
  - Strict timeout handling (defaults to 10,000ms) with `AbortController`.
  - Structured error mapping via `ApiClientError` with status code, endpoint, and detail payload.

---

## 6. Verification & Automated Testing

### 6.1 Test Suites Executed
1. **Frontend Unit & Component Tests:**
   - Command: `npm run test` (Vitest)
   - Results: **15 test files passed, 61 tests passed, 0 failures**.
   - Verified: Token definitions, Button states, Form inputs, Filter chips, Status & Evidence semantics, Financial formatting, Table keyboard accessibility, Drawer focus/escape handling, API client timeout/error handling, and Shell routing.
2. **TypeScript Compilation:**
   - Command: `npm run typecheck` (`tsc --noEmit`)
   - Results: **0 errors**. Strict type checking compliant.
3. **Frontend Linting:**
   - Command: `npm run lint` (`eslint .`)
   - Results: **0 warnings, 0 errors**.
4. **Vite Production Build:**
   - Command: `npm run build` (`tsc && vite build`)
   - Results: Successfully bundled 61 modules into `dist/assets/` (gzip CSS: 5.12 kB, JS: 56.43 kB).
5. **Backend Regression Test Suite:**
   - Command: `uv run pytest -q`
   - Results: **162 tests passed (100%)**.
6. **Backend Code Quality:**
   - Command: `uv run ruff check .`
   - Results: **All checks passed!**
7. **Visual & Browser Audit:**
   - Executed autonomous browser session inspecting `http://localhost:3000/` and `http://localhost:3000/#showcase`.
   - Verified token compliance, typography hierarchy, 44px control heights, tablet responsiveness at 768px, and right drawer interaction.
