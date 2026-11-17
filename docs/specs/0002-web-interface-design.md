# Web interface design

## Scope

Daymark is a display name for the existing single-owner Project Supervision application. This slice redesigns the working Phase 1 screens: login, today, project list and creation, and project detail and editing. It implements presentation for R2, R3, R9 and R7 without changing any rule or endpoint.

The repository requires English copy. There is no registration or password-reset flow because the corresponding APIs do not exist. The frontend neither computes business dates nor invents streaks, misses, logs, completion rates or schedule data.

## Source of truth

`docs/interface-preview.html` is **normative**. It is not a mood board and not an approximation: it is the rendering the implementation must reproduce. Open it in a browser next to the running application and compare.

"Exactly the same" means, in order of importance:

1. **Structure** — the same regions in the same places: fixed sidebar, workspace header with breadcrumb and privacy label, page heading with eyebrow, content grid, footer with timezone line.
2. **Copy** — the same strings, including headings, helper text, empty states and the two footer notices. Copy in the preview is final; rewriting it is a visual regression, not an improvement.
3. **Tokens** — the same palette, radius and type scale, consumed through the shared CSS variables below rather than re-typed per component.
4. **Components** — the same button hierarchy, panel treatment, status pills, swatches, field structure, availability notices and timeline empty state.
5. **Icons** — inline SVG on a 24×24 viewBox, `stroke-width: 1.65`, round caps and joins. No icon package, no emoji as an icon, no filled glyphs.
6. **Rhythm** — the same spacing and border weight; panels are 1px `--line` on `--surface`, not shadowed cards.

Where the preview shows a state, that state is required. Where the preview is silent — an error message, a 404, a loading skeleton — extend it using the values in this document rather than inventing a new visual language, and prefer plain text over a new component.

### Design tokens

```css
:root {
  color-scheme: light;
  --paper: #faf9f6;
  --surface: #ffffff;
  --ink: #292d29;
  --muted: #697069;
  --line: #e4e5de;
  --accent: #b84c25;
  --accent-soft: #f8ebe3;
  --green: #39705a;
  --green-soft: #edf3ed;
  --danger: #b03232;
  --radius: 14px;
}
```

Type: `"Segoe UI", Arial, sans-serif` at 15px / 1.6 for everything operative; `Georgia, serif` only for the login statement and the welcome panel heading. No webfont is downloaded — the system stack is deliberate, and on the owner's machine it resolves to Segoe UI.

Chrome: sidebar 238px fixed, background `#f1f1ea`, 1px `--line` on its right edge. Brand mark 39×43 with `--ink` fill and an asymmetric corner (`11px 11px 11px 3px`). Focus is `3px solid var(--accent)` at `4px` offset, never a browser default outline. Transitions are colour and border only, 160ms; they are removed under `prefers-reduced-motion`.

### Component inventory

| Component | Classes in the preview | Notes |
| --- | --- | --- |
| App shell | `app-frame`, `sidebar`, `workspace`, `workspace-top`, `page-content`, `workspace-footer` | Shared by every authenticated screen |
| Brand | `brand`, `brand-mark`, `brand-caption` | Book-and-mark glyph; caption "A little proof, every day." |
| Navigation | `main-nav`, `sidebar-label`, `sidebar-note`, `note-line` | Current item carries `aria-current="page"` and a trailing arrow |
| Buttons | `button` (primary), `button secondary`, `button subtle`, `icon-button` | Primary is `--ink` on white text; secondary is outlined |
| Panels | `panel`, `panel-heading`, `detail-panel`, `timeline-panel`, `create-panel` | 1px border, `--surface`, 14px radius |
| Headings | `eyebrow`, `page-heading`, `page-description`, `section-heading`, `count`, `section-note` | Eyebrow is uppercase, letter-spaced, `--muted` |
| Forms | `form`, `field`, `optional`, `helper`, `form-actions`, `color-options`, `swatch` | Label above control; helper below; no placeholder-only labels |
| Status | `status-pill`, `status-pill.active` | Neutral pill; green variant for active |
| Notices | `availability`, `private-label`, `tiny-label` | Inline, icon plus text, never a modal |
| Timeline | `timeline-empty`, `project-symbol` | Empty state is a sentence, not a spinner |
| Login | `login-*` panels | Serif statement, password visibility toggle, inline error |

## Visual direction

Warm paper surfaces, charcoal type, terracotta emphasis and sage supporting surfaces create a quiet, personal workspace. Shared CSS variables own the palette. System sans-serif type handles controls and body copy; an editorial serif is reserved for the login statement and welcome panel. Icons share one vector stroke style. Decorative illustrations have no business meaning and are hidden from assistive technology.

UI UX Pro Max searches informed the flat product-interface direction, restrained motion, visible focus, labels and responsive hierarchy. Its marketing-pattern recommendations were off-target for an authenticated workspace and were not applied. Its Next.js 16.2 Server Actions recommendation does not apply to the locked Next.js 15 / FastAPI / TanStack Query stack.

## Current screens

| Screen | Primary action | Supporting content |
| --- | --- | --- |
| Login | Sign in | Password visibility, inline authentication error, private-owner explanation |
| Today | Create the first project / open a project | Active projects, truthful not-recorded state, short product rules |
| Projects | Create project | Status groups, editable project links, accessible up/down ordering |
| Project detail | Save changes | Name, optional note, colour, immutable start information, empty log timeline |

Creation remains inline on the project list to preserve the working API flow. Account requests use TanStack Query, and successful sign-out clears cached private data. Failed sign-out stays on the screen and reports an error. Background detail refetches do not overwrite unsaved form values.

## Screens after their blocking tickets land

| Route / surface | Design intent | Dependency |
| --- | --- | --- |
| Today supervision | Yesterday's misses above today's project rows; distinct logged, not recorded and rest states | 06–09, 15, 25 |
| Quick log | Project selector and body only as required fields; save immediately without confirmation | 06–07 |
| Project timeline | Most recent logs first, readable body, business day and backfill marker | 07, 12–13 |
| Backfill | Past-seven-business-day selector supplied by API; explicit notice that streaks do not repair | 17 |
| Calendar | Month grid; neutral rest days, text/icon plus colour for misses, day-detail panel | 15–16 |
| Settings | Email/account, global rest days, read-only Madrid timezone and 21:00 alert time | 10, 25–29 |
| Statistics | Four API-owned metrics; null values shown as a dash | 23–24 |

The current screen does not show calendar placeholders, fabricated streaks, disabled navigation to missing routes or forms that pretend to save logs. Future quick-log placement takes precedence over the introductory welcome panel once recording works.

## Interaction and accessibility

- Desktop: persistent left navigation, restrained breadcrumb header, two-column workspace.
- Tablet: supporting panels stack below primary content.
- Phone: compact top navigation, single column, visible sign-out, 16px inputs.
- Forms have visible labels, native required/date validation, pending labels and inline errors.
- Buttons expose disabled, pressed and selected semantics where applicable.
- Every screen has meaningful heading structure and a keyboard skip link.
- Motion is restricted to short colour transitions and removed under reduced motion.
- Empty, loading, network error, not-found, save success and reorder failure states are explicit.
- Light appearance is deliberate; no unverified dark theme is claimed.

## Verification

Use the repository commands `make lint` and `make test`. Then, with the Docker development stack running, open `docs/interface-preview.html` and the live routes side by side at desktop (≈1440px) and phone (≈390px) widths and confirm structure, copy, tokens, components and rhythm match. The preview file is static: its links drive view switching with JavaScript and its forms never submit, so anything that changes data is checked against the running application instead.

No new dependencies or backend behaviour are introduced in this slice. Adding one — an icon package, a component library, a webfont — requires an ADR, because it would break the "same as the preview" constraint by construction.
