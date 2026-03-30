# India H2 Workforce Atlas -- Design System

**Based on:** HyGOAT Brand Design, Dieter Rams' principles, WCAG 2.2 AA
**Source of truth:** `web/style.css` (tokens), this file (decisions)

---

## Brand Identity

The India H2 Workforce Atlas is a **data visualization tool** for hydrogen workforce planning. It complements [h2hubs.in](https://h2hubs.in) (infrastructure maps) with occupation-level workforce depth.

Visual identity follows the **HyGOAT brand**: green for hydrogen, orange for energy/action, clean typography for a policy audience.

---

## Color Palette

### Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-hy` | `#00994C` | Primary brand green. Atlas mode accent, active states, positive outcomes |
| `--color-hy-dark` | `#007A3D` | Hover state for primary |
| `--color-emerald` | `#50C878` | Secondary green. Score band 7-8, treemap mid-tier |
| `--color-goat` | `#ff8a00` | Brand orange. Scenario mode accent, CTAs, forward navigation |
| `--color-goat-dark` | `#E67300` | Hover state for orange |

### Semantic Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#f9fafb` (gray-50) | Page background |
| `--surface` | `#ffffff` | Cards, sidebar, panels |
| `--text` | `#111827` (gray-900) | Primary text |
| `--text-muted` | `#6b7280` (gray-500) | Secondary text, labels, empty states |
| `--border` | `#e5e7eb` (gray-200) | Borders, dividers |
| `--accent` | = `--color-hy` | Default accent (green) |
| `--nav-bg` | `#0a1320` | Navigation bar background (dark slate) |
| `--nav-text` | `#f8fafc` | Navigation bar text (off-white) |

### Mode-Specific Color Language

The treemap's color scheme changes by mode. This is the product's core visual language:

**Atlas Mode (green = static data):**

| Token | Hex | Meaning |
|-------|-----|---------|
| `--score-9` | `#00994C` | Core H2 occupations (score 9-10) |
| `--score-7` | `#50C878` | Strong adjacency (score 7-8) |
| `--score-5` | `#86efac` | Adjacent occupations (score 5-6) |
| `--score-3` | `#ff8a00` | Transferable (score 3-4) |
| `--score-1` | `#dc2626` | Low relevance (score 1-2) |
| `--score-null` | `#374151` | Unscored / N/A |

**Scenario Mode (demand magnitude):**

| Hex | Meaning |
|-----|---------|
| `#00994C` | Critical demand (>= 1000 workers) |
| `#50C878` | High demand (500-999) |
| `#86efac` | Moderate demand (100-499) |
| `#ff8a00` | Low demand (10-99) |
| `#dc2626` | Minimal demand (1-9) |
| `#374151` | No demand |

**Gap Mode (shortage/surplus diverging):**

| Hex | Meaning |
|-----|---------|
| `#991b1b` | Severe shortage |
| `#ef4444` | Moderate shortage |
| `#fca5a5` | Mild shortage |
| `#f3f4f6` | Balanced |
| `#bbf7d0` | Mild surplus |
| `#22c55e` | Large surplus |

**Phase Colors (Timeline Mode -- Phase 3):**

| Token | Hex | Meaning |
|-------|-----|---------|
| `--phase-construction` | `#3b82f6` | Construction workforce (temporary, building) |
| `--phase-commissioning` | `#8b5cf6` | Commissioning workforce (short peak, testing) |
| `--phase-operations` | `#0d9488` | Operations workforce (sustained, long-term) |
| `--phase-mixed` | `#6b7280` | No dominant phase (< 50% any single phase) |

Phase colors are intentionally distinct from all other mode palettes (no green, no orange, no red) to signal "you are viewing a time snapshot."

**Pathway Overlap Bar Colors (Phase 3):**

| Token | Hex | Range | Meaning |
|-------|-----|-------|---------|
| `--overlap-high` | `#0d9488` | >= 70% | High skill transferability |
| `--overlap-medium` | `#f59e0b` | 40-69% | Moderate transferability |
| `--overlap-low` | `#ef4444` | < 40% | Low transferability |

### Gray Scale

Full gray scale from Tailwind/HyGOAT tokens, used for backgrounds, borders, and text:

`--gray-50` through `--gray-900` (see `style.css :root` for all values).

---

## Typography

### Font

**Mukta** (Google Fonts) -- weights 300, 400, 500, 600, 700, 800.
Fallbacks: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

Mukta was chosen for excellent Devanagari support alongside Latin glyphs, important for a tool serving Indian policy audiences.

### Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Summary bar metric value | `2rem` | 700 | 1.2 |
| Nav logo | `1.1rem` | 700 | 1.5 |
| Sidebar h2 (occupation title) | `1.1rem` | 600 | 1.5 |
| Nav title | `0.95rem` | 500 | 1.5 |
| Body text, stats | `1rem` / `0.85rem` | 400 | 1.5 |
| Controls, labels | `0.85rem` | 500 | 1.5 |
| Pills, tooltips | `0.8rem` | 400 | 1.4 |
| Legend items | `0.75rem` | 600 | 1.5 |
| Score rationale | `0.72rem` | 400 | 1.4 |
| Treemap cell labels | `10px` | 400 | -- (SVG) |

### Scientific Notation

Always use Unicode subscripts for chemical formulas: H₂, CO₂, NH₃, CH₄. Never HTML entities.

---

## Spacing

No formal spacing scale token set. Common values used throughout:

| Size | Usage |
|------|-------|
| 2px | Mode toggle gap, minimal separation |
| 4px | Badge padding, tight gaps |
| 6px | Score bar margin, metadata gap |
| 8px | Nav gap, tooltip padding, score bar track height |
| 12px | Control gap, nav padding vertical, control bar padding |
| 14px | Pill horizontal padding |
| 16px | Sidebar section margin, footer padding |
| 20px | Sidebar padding, summary bar vertical padding |
| 24px | Nav horizontal padding, summary bar horizontal padding |
| 48px | Summary bar metric gap (desktop) |

---

## Component Patterns

### Buttons

**Pill button** (`.pill`): Primary interactive control pattern.
- `padding: 6px 14px`, `border-radius: 999px`, `border: 1px solid var(--border)`
- Active: `background: var(--accent)`, `color: white`, `border-color: var(--accent)`
- Hover: `border-color: var(--color-goat)`, `color: var(--color-goat)`

**Mode button** (`.mode-btn`): Nav-embedded toggle.
- `padding: 4px 12px`, `border-radius: 999px`, transparent background
- Active color varies by mode: green (Atlas), orange (Scenario), red (Gap)

**Download button** (`.btn-download`): Transparent border style, hover fills.

### Score Bars

Horizontal bar visualization for 0-10 scores:
- Track: `height: 8px`, `background: var(--gray-100)`, `border-radius: 4px`
- Fill: colored by score range, `transition: width 0.3s`
- Label: 110px fixed width. Value: 32px right-aligned.

### Sidebar

- Width: `320px` (desktop), full width (mobile)
- Padding: `20px`
- Sections stack vertically with `16px` margin between
- Metadata badges: `background: var(--gray-100)`, `padding: 4px 8px`, `border-radius: 6px`

**Phase 3 addition: Sidebar tabs** (`.sidebar-tabs`)
- Uses `.pill` pattern for tab buttons
- Tab badge (`.tab-badge`): 16px circle, orange when count > 0
- `role="tablist"` / `role="tab"` / `role="tabpanel"` for a11y

### Dropdown Menu

- `border-radius: 12px`, `box-shadow: 0 4px 16px rgba(0,0,0,0.12)`
- `min-width: 220px`, absolute positioned below trigger
- Items: full-width, `padding: 10px 16px`, hover background

### Slider

- `accent-color: var(--color-goat)`, `height: 6px`, `max-width: 300px`
- Native `<input type="range">` for keyboard/screen reader support

### Treemap

- SVG-based D3 treemap
- Cells: `stroke: var(--surface)` (white separators), `stroke-width: 1`
- Labels: `fill: white`, `font-size: 10px`, `text-shadow: 0 1px 2px rgba(0,0,0,0.5)`
- Hover: `opacity: 0.85`
- Selected cell: pulse animation (3 iterations, 0.8s)

### Tooltip

- `background: var(--nav-bg)`, `color: var(--nav-text)`
- `padding: 8px 12px`, `border-radius: 8px`, `max-width: 250px`
- `pointer-events: none`, `z-index: 50`

### Phase 3 Components

| Component | Class | Derives From |
|-----------|-------|-------------|
| Sidebar tab bar | `.sidebar-tabs` | New (flex, gap: 2px) |
| Tab badge | `.tab-badge` | New (16px circle) |
| Pathway card | `.pathway-card` | `.upskill-item` separator |
| Overlap bar | `.overlap-track` / `.overlap-fill` | `.score-bar-*` |
| Phase legend (inline) | `.phase-legend` | New (flex, gap: 12px) |
| Cluster dropdown | `.cluster-select` | `.scenario-select` |
| Year slider | `.year-slider` | `.mt-slider` |
| Treemap empty state | `.treemap-empty` | New (centered, muted) |

---

## Layout

### Page Structure

```
.atlas-nav          Fixed top, dark background
.summary-bar        Centered metrics, light background
.controls           Filter pills row
.scenario-bar       Scenario/Gap mode controls (conditional)
.atlas-main         Flex row: treemap (flex:1) + sidebar (320px)
.legend             Color legend, centered
.atlas-footer       Attribution
```

### Responsive Breakpoint

**Single breakpoint: 768px.**

| Property | Desktop (> 768px) | Mobile (<= 768px) |
|----------|-------------------|-------------------|
| `.atlas-main` | Flex row | Flex column |
| `.sidebar` | 320px right panel | Full width below treemap, max-h: 50vh |
| `.treemap-container` | Flex: 1 | min-h: 350px, max-h: 50vh |
| Summary bar gap | 48px | 16px |
| Metric value size | 2rem | 1.5rem |
| Pill button size | 0.8rem, 6px 14px | 0.7rem, 4px 10px |
| Scenario controls | Inline row | `flex-wrap: wrap` |

---

## Accessibility

Following WCAG 2.2 AA standards (aligned with HyGOAT Pilot `UI_UX.md`):

### Contrast Ratios

- Normal text: minimum 4.5:1
- Large text (18px+ or 14px+ bold): minimum 3:1
- Focus indicators: visible in light mode (no dark mode in this tool)

### Keyboard Navigation

- All interactive elements reachable via `Tab`
- Focus ring: `outline: 2px solid #3b82f6; outline-offset: 2px`
- Sliders: `←→` for step, `Home`/`End` for min/max (native behavior)
- Dropdowns: `Enter`/`Space` to open, `↑↓` to navigate, `Esc` to close
- No keyboard traps

### Touch Targets

- Minimum 44px for all interactive elements on mobile
- Applies to: dropdown triggers, slider thumbs, tab buttons, pathway card expand triggers

### ARIA Patterns

- Dynamic content updates: `aria-live="polite"` on summary bar
- Tabs: `role="tablist"` / `role="tab"` / `role="tabpanel"` with `aria-selected`
- Expandable sections: `aria-expanded` on trigger elements
- Export progress: `role="progressbar"` with `aria-live="assertive"`

### Scientific Text

Unicode subscripts only (H₂, CO₂). No HTML entities. Ensures screen readers pronounce correctly.
