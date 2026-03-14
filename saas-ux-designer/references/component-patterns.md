# SaaS Component Patterns Reference

Detailed specs for the most common SaaS UI components. Each component includes all required states, interaction specs, and accessibility requirements. Read this file when implementing specific components or auditing existing ones.

## Table of Contents
1. [Button System](#button-system)
2. [Input / Form Elements](#input--form-elements)
3. [Navigation Sidebar](#navigation-sidebar)
4. [Data Table](#data-table)
5. [KPI / Stat Card](#kpi--stat-card)
6. [Empty States](#empty-states)
7. [Toast Notifications](#toast-notifications)
8. [Command Palette](#command-palette)
9. [Skeleton Loading States](#skeleton-loading-states)
10. [Status Badges](#status-badges)

---

## Button System

### States Required
Every button variant must have: default, hover, active (pressed), focus, disabled, loading

### Variants
```
Primary     — Main action, use once per section max
Secondary   — Subordinate actions, paired with primary
Ghost       — Tertiary, contextual actions (table row actions)
Destructive — Delete, remove, disable (always requires confirmation)
Link        — Inline navigation, not actions
Icon-only   — With tooltip on hover (required for accessibility)
```

### Size System
```
sm:  height 30px, padding 0 10px, font 13px
md:  height 36px, padding 0 14px, font 14px  (default)
lg:  height 42px, padding 0 18px, font 15px
xl:  height 48px, padding 0 22px, font 16px  (hero CTAs only)
```

### CSS Interaction Spec
```css
/* Default + Hover + Active */
.btn-primary {
  background: var(--btn-primary-bg);
  transition: background var(--transition-hover), 
              box-shadow var(--transition-hover),
              transform var(--duration-instant) ease;
}
.btn-primary:hover {
  background: var(--btn-primary-bg-hover);
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}
.btn-primary:active {
  transform: translateY(1px);
  box-shadow: none;
}

/* Focus (never remove) */
.btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}

/* Disabled */
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;  /* NOT pointer-events: none if you need tooltip */
}

/* Loading state — spinner replaces or precedes label */
.btn[data-loading] {
  cursor: default;
  position: relative;
  color: transparent;  /* hide text */
}
.btn[data-loading]::after {
  content: '';
  position: absolute;
  width: 14px; height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
```

### Accessibility Notes
- Icon-only buttons MUST have `aria-label`
- Loading state MUST update `aria-label` to include "loading" or use `aria-busy`
- Disabled buttons SHOULD have `title` or `aria-describedby` explaining why
- Destructive actions MUST have a confirmation step before execution

---

## Input / Form Elements

### Input States
```
Default      — border: var(--input-border)
Hover        — border: var(--color-border-strong)
Focus        — border: var(--color-border-focus) + focus shadow
Filled       — same as default
Error        — border: var(--color-error) + error shadow + error text below
Disabled     — opacity 0.5, cursor not-allowed, background --bg-muted
Read-only    — no border, background --bg-subtle
```

### Full Input CSS Pattern
```css
.input {
  width: 100%;
  padding: var(--input-padding);
  font-size: var(--input-font-size);
  font-family: var(--font-sans);
  color: var(--input-text);
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--input-border-radius);
  transition: border-color var(--transition-hover), 
              box-shadow var(--transition-hover);
  outline: none;
}

.input:hover:not(:disabled):not(:focus) {
  border-color: var(--color-border-strong);
}

.input:focus {
  border-color: var(--input-border-focus);
  box-shadow: var(--shadow-focus);
}

.input.is-error {
  border-color: var(--input-border-error);
  box-shadow: var(--shadow-focus-error);
}

.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-bg-muted);
}
```

### Label + Input + Helper Text Stack
```html
<div class="field">
  <label class="field-label" for="email">
    Email address
    <span class="field-required" aria-hidden="true">*</span>
  </label>
  <input 
    class="input" 
    id="email" 
    type="email" 
    aria-required="true"
    aria-describedby="email-helper email-error"
  />
  <p class="field-helper" id="email-helper">
    We'll send confirmation to this address.
  </p>
  <p class="field-error" id="email-error" role="alert" hidden>
    <!-- Error shown here on validation -->
  </p>
</div>
```

```css
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 13px; font-weight: 500; color: var(--color-text-secondary); }
.field-required { color: var(--color-error); margin-left: 2px; }
.field-helper { font-size: 12px; color: var(--color-text-tertiary); }
.field-error { font-size: 12px; color: var(--color-error); display: flex; align-items: center; gap: 4px; }
```

### Validation Timing
- **Validate on blur** (not on keystroke — too aggressive)
- **Re-validate on keystroke** only after the first error has appeared (so it clears in real time)
- **Never validate on submit only** — user must know which field is wrong
- Error messages must be specific: "Password must be at least 8 characters" not "Invalid password"

---

## Navigation Sidebar

### Layout Structure
```
┌──────────────────────────┐
│ [Logo]   [CollapseToggle]│
├──────────────────────────┤
│ [Search]                 │
├──────────────────────────┤
│ PRIMARY SECTION          │
│ ◆ Dashboard              │ ← active item
│   Projects               │
│   Reports                │
├──────────────────────────┤
│ SECONDARY SECTION        │
│   Integrations           │
│   Team                   │
│   Billing                │
├──────────────────────────┤  ← pushes to bottom
│   Settings               │
│   Help                   │
│ ┌────────────────────┐   │
│ │ User Avatar  Name  │   │
│ └────────────────────┘   │
└──────────────────────────┘
```

### Active Item Styling
```css
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: var(--nav-item-padding);
  border-radius: var(--nav-item-radius);
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 400;
  text-decoration: none;
  transition: background var(--transition-hover), color var(--transition-hover);
}

.nav-item:hover {
  background: var(--nav-item-hover-bg);
  color: var(--color-text-primary);
}

.nav-item.is-active {
  background: var(--nav-item-active-bg);
  color: var(--nav-item-active-text);
  font-weight: 500;
  /* Left border accent — the signature active indicator */
  box-shadow: inset 2px 0 0 var(--nav-item-active-border);
}
```

### Collapsed State
- Width: 64px, show icons only
- Tooltip on hover with full label (required for accessibility)
- Section headers collapse to horizontal rules
- User avatar shows without name

---

## Data Table

### Column Alignment Rules
- **Numbers**: Right-align, use tabular-nums (`font-variant-numeric: tabular-nums`)
- **Dates**: Right-align or center, relative time preferred
- **Status badges**: Center-align
- **Text content**: Left-align
- **Actions**: Right-align, appears on row hover

### Row Interaction Pattern
```css
.table-row {
  transition: background var(--transition-hover);
}
.table-row:hover {
  background: var(--table-row-hover-bg);
}
.table-row:hover .row-actions {
  opacity: 1;
  pointer-events: auto;
}
.row-actions {
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-hover);
}
```

### Sort Header Pattern
```html
<th aria-sort="ascending">
  <button class="sort-btn">
    Name <span class="sort-icon" aria-hidden="true">↑</span>
  </button>
</th>
```

### Bulk Selection Pattern
- Checkbox in header: indeterminate state when partial selection
- Selected count banner appears above table (not floating)
- Banner contains: "N rows selected" + bulk action buttons + "Deselect all"
- Row checkbox appears on hover OR always visible if any row is selected

---

## KPI / Stat Card

### Anatomy
```
┌──────────────────────────────┐
│ Label          [Icon/Badge]  │
│                              │
│ Value                        │
│                              │
│ △ +12.5% vs last period      │
└──────────────────────────────┘
```

### Implementation Pattern
```css
.stat-card {
  padding: 20px 24px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-border-radius);
}

.stat-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: none;  /* avoid all-caps */
  letter-spacing: 0;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  margin-bottom: 8px;
}

.stat-delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
}
.stat-delta.positive { color: var(--color-success); }
.stat-delta.negative { color: var(--color-error); }
.stat-delta.neutral  { color: var(--color-text-tertiary); }
```

### Critical Notes
- The trend indicator MUST use both color AND an icon/text (not color alone — colorblind)
- Never use red/green without also indicating direction with an arrow or text
- Large numbers should use `Intl.NumberFormat` for locale-aware formatting

---

## Empty States

### Three Types (all different)

**1. First-Run Empty State** (no data has ever existed)
- Encourages action, explains value
- Has a clear CTA
- Can use illustration
- Copy: "Create your first [thing]" + benefit statement

**2. Zero-Result Empty State** (filtered/searched, no matches)
- Helps user understand why
- Offers an escape hatch (clear filters, change search)
- Copy: "No [things] match your search" + "Clear filters" link

**3. Error Empty State** (data should exist but failed to load)
- Explains what went wrong briefly
- Offers retry action
- Copy: "We couldn't load [things]" + "Try again" button

### HTML Structure
```html
<div class="empty-state" role="status">
  <!-- Optional: inline SVG illustration, max 200px wide -->
  <div class="empty-state-icon" aria-hidden="true"><!-- SVG --></div>
  
  <h3 class="empty-state-title">No projects yet</h3>
  <p class="empty-state-description">
    Projects keep your work organized in one place.
  </p>
  <button class="btn btn-primary">Create your first project</button>
</div>
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  gap: 12px;
}
.empty-state-title { font-size: 18px; font-weight: 600; }
.empty-state-description { font-size: 14px; color: var(--color-text-secondary); max-width: 320px; }
```

---

## Toast Notifications

### Rules
- **Success/Info**: auto-dismiss after 4-5 seconds
- **Warning/Error**: require explicit dismiss (don't auto-close)
- Maximum 3 visible at once (queue additional ones)
- Position: bottom-right for desktop; bottom-center for mobile
- NEVER use toast for critical errors — use inline error or a dedicated error page

### State Types
```
success  — green accent, checkmark icon
error    — red accent, × icon  
warning  — amber accent, ⚠ icon
info     — blue accent, ℹ icon
loading  — spinner, no auto-dismiss
```

### Animation
```css
/* Enter: slide up + fade */
@keyframes toast-enter {
  from { transform: translateY(100%); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
/* Exit: slide down + fade */
@keyframes toast-exit {
  from { transform: translateY(0);    opacity: 1; }
  to   { transform: translateY(100%); opacity: 0; }
}
```

---

## Command Palette

### Triggered by: Cmd/Ctrl + K

### Structure
```
┌─────────────────────────────────────────┐
│ 🔍 Search...                            │
├─────────────────────────────────────────┤
│ RECENT                                  │
│  ↗ Project Alpha                        │
│  ↗ Q3 Report                            │
├─────────────────────────────────────────┤
│ NAVIGATION                              │
│  □ Dashboard         Ctrl+H             │
│  □ Projects                             │
├─────────────────────────────────────────┤
│ ACTIONS                                 │
│  ✦ Create project    Ctrl+Shift+P       │
│  ✦ Invite member                        │
└─────────────────────────────────────────┘
```

### Keyboard Navigation
- Arrow keys: move between items
- Enter: execute selected item  
- Escape: close without action
- Type: filter results in real-time (fuzzy match)
- Tab: navigate between categories

### Accessibility
- `role="dialog"` on overlay, `aria-modal="true"`
- `role="combobox"` on input, `aria-controls` pointing to result list
- `role="listbox"` on result list, `role="option"` on items
- Focus trapped inside palette while open

---

## Skeleton Loading States

### Rule: Skeleton should match the shape of the content it replaces exactly.

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-muted) 25%,
    var(--color-bg-subtle) 50%,
    var(--color-bg-muted) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

/* Common skeleton shapes */
.skeleton-text  { height: 14px; border-radius: 4px; }
.skeleton-title { height: 24px; border-radius: 4px; }
.skeleton-avatar { border-radius: 50%; }
.skeleton-card  { height: 100%; border-radius: var(--card-border-radius); }
```

### Staggered Loading
```css
/* Stagger skeleton items for a more natural feel */
.skeleton-item:nth-child(1) { animation-delay: 0ms; }
.skeleton-item:nth-child(2) { animation-delay: 100ms; }
.skeleton-item:nth-child(3) { animation-delay: 200ms; }
```

---

## Status Badges

### Required: Color + Text (never color alone)

```
● Active    (green dot + text)
● Inactive  (gray dot + text)  
● Pending   (amber dot + text)
● Error     (red dot + text)
● Draft     (gray outline + text)
● Archived  (gray strikethrough + text)
```

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: var(--badge-padding);
  border-radius: var(--badge-border-radius);
  font-size: var(--badge-font-size);
  font-weight: var(--badge-font-weight);
  line-height: 1.4;
}

.badge-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.badge-success { background: var(--color-success-subtle); color: var(--color-success); }
.badge-success .badge-dot { background: var(--color-success); }

.badge-error   { background: var(--color-error-subtle);   color: var(--color-error); }
.badge-warning { background: var(--color-warning-subtle); color: var(--color-warning); }
.badge-info    { background: var(--color-info-subtle);    color: var(--color-info); }
.badge-neutral { background: var(--color-bg-muted);       color: var(--color-text-secondary); }
```
