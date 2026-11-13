# Design System — FleetKit

> Category: Backend & Ops  
> Self-hosted control plane for bots, workers, cron and webhooks.  
> OpenDesign-compatible `DESIGN.md` for the `saas-landing` template.

## 1. Visual Theme & Atmosphere

FleetKit reads as a night ops console: deep slate (`#0c1219`) with a single teal signal (`#3dd6c6`). Display type is Syne — heavy, slightly condensed, architectural. Body is DM Sans. Depth comes from soft radial light, hairline borders and one full-bleed product stage in the hero — not from stacked glass cards or purple glow.

**Key Characteristics:**
- Slate void canvas with teal as the only chromatic accent
- Syne 700–800 for brand and headlines; DM Sans for UI copy
- Product mock (queue / workers) is the hero visual anchor
- Hairline borders (`rgba(139,155,176,0.22)`), radius capped at 10px
- Accent used sparingly: primary CTA + one footer band

## 2. Color Palette & Roles

### Primary
- **Signal Teal** (`#3dd6c6`): sole accent — primary CTA, brand mark span, link hover
- **Teal Deep** (`#2aa89b`): pressed / secondary accent
- **Accent Ink** (`#06201c`): text on teal buttons

### Surface & Background
- **Void** (`#0c1219`): page background
- **Panel** (`#162030`): elevated panels, code rails
- **Panel Lift** (`#1a2738`): hover / selected surface
- **Mist** (`#8b9bb0`): muted body / meta

### Neutrals & Text
- **Ink** (`#e8eef6`): primary text
- **Line** (`rgba(139, 155, 176, 0.22)`): borders and rules

### Semantic
- **Ok** (`#5ce0a0`), **Run** (`#6ec8ff`), **Warn** (`#f0b429`), **Danger** (`#ff6b6b`)

### Gradient System
- Atmosphere only: faint teal radial at top-left, cool blue at top-right, both ≤14% opacity. No purple→indigo trust gradients. No two-stop hero washes.

## 3. Typography Rules

### Font Family
- **Display / Brand**: `Syne`
- **Body**: `DM Sans`
- **Code**: `ui-monospace`, `SF Mono`, `JetBrains Mono`, `Menlo`

### Hierarchy

| Role | Font | Size | Weight | Line Height | Notes |
|------|------|------|--------|-------------|-------|
| Brand | Syne | 28–32px | 700 | 1.1 | Wordmark; `Kit` in accent |
| Display / Hero | Syne | clamp(40px, 6vw, 72px) | 800 | 0.98 | One line preferred |
| Section | Syne | 28–36px | 700 | 1.15 | |
| Body | DM Sans | 16–18px | 400–500 | 1.5 | |
| Meta / Label | DM Sans | 12–14px | 500–600 | 1.4 | Uppercase + 0.08em tracking for overlines |
| Code | Mono | 13–14px | 500 | 1.45 | |

## 4. Component Stylings

### Buttons
- **Primary**: bg Signal Teal, text Accent Ink, radius 8px, padding 12px 20px. Hover: Teal Deep. Press: translateY(1px).
- **Ghost**: transparent, 1px Line border, Ink text. Hover: Panel Lift fill.

### Cards & Containers
- Prefer open sections over cards. When a panel is needed (demo stage, code rail): Panel bg + Line border, radius 10px, no left-accent stripe, no multi-layer shadow.

### Icons
- 1.6–1.8px monoline SVG, `currentColor`. No emoji icons.

## 5. Layout Principles

- Container max: 1120px, gutters 20–28px
- Hero vertical padding: 96px desktop / 64px tablet / 48px phone
- One composition in the first viewport: brand, one headline, one support line, CTA group, full-bleed product stage
- Features: 3 columns desktop → 1 column phone; no feature-card left borders
- Skip pricing for OSS self-host; use an unconventional **ops demo** strip instead

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | none | page, text |
| Bordered | 1px Line | panels, demo stage |
| Soft | `0 24px 60px rgba(0,0,0,0.35)` | hero product stage only |

## 7. Motion

- Hero enter: 280ms opacity + 8px rise, `cubic-bezier(0.2, 0, 0, 1)`
- Queue pulse: 1.8s opacity cycle on one live row
- CTA press: 80ms translateY(1px)
- Respect `prefers-reduced-motion: reduce`

## 8. Do's and Don'ts

### Do
- Lead with the FleetKit wordmark as a hero-level brand signal
- Keep teal as the only accent; at most two strong accent surfaces per page
- Show real product language: jobs, workers, heartbeats, DLQ, API keys
- Use Syne for display; never Inter / Roboto for headlines

### Don't
- Default Tailwind indigo / violet accents
- Purple→blue hero gradients
- Emoji as icons
- Invented metrics ("10×", "99.9%")
- Lorem / Feature One / placeholder CDNs
- Rounded card + colored left border

## Agent Prompt Guide

Build with OpenDesign skill `saas-landing`. Inputs:
- `product_name`: FleetKit
- `tagline`: Один API и dashboard для флота ботов, воркеров и cron
- `has_pricing`: false
- `proof_count`: 3
- `hero_density`: 96

Replace pricing with an inline ops demo (queue rows + worker heartbeats). Copy in Russian. Output a single self-contained `index.html` with `data-od-id` on editable blocks.
