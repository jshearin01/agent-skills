# Design Token Systems Reference

Complete, production-ready token systems for SaaS products. Read this file when building a design system from scratch, generating a CSS token layer, or converting hardcoded values to a token system.

## Table of Contents
1. [Token Architecture Philosophy](#token-architecture-philosophy)
2. [Base Token Layer (Primitives)](#base-token-layer-primitives)
3. [Semantic Token Layer](#semantic-token-layer)
4. [Component Token Layer](#component-token-layer)
5. [Complete Light/Dark Token System](#complete-lightdark-token-system)
6. [Typography Scale Tokens](#typography-scale-tokens)
7. [Spacing & Sizing Tokens](#spacing--sizing-tokens)
8. [Motion & Animation Tokens](#motion--animation-tokens)
9. [Shadow System](#shadow-system)

---

## Token Architecture Philosophy

Tokens exist in three layers:

```
Primitives → Semantic → Component

--blue-500              (primitive: raw value)
  └─ --color-accent     (semantic: what it means)
       └─ --btn-bg      (component: where it's used)
```

**Rules:**
- Components reference semantic tokens, never primitives
- Semantic tokens reference primitives, never raw hex values
- Primitives are defined once; everything else references them
- Dark mode flips semantic tokens, leaving components unchanged

This means dark mode is implemented at the semantic layer by changing what value `--color-bg-base` points to — not by overriding component styles.

---

## Base Token Layer (Primitives)

```css
/* ======================
   COLOR PRIMITIVES
   Neutral scale (Warm Gray)
   ====================== */
:root {
  --gray-0: #ffffff;
  --gray-50: #fafaf9;
  --gray-100: #f5f4f1;
  --gray-200: #e8e5df;
  --gray-300: #d4cfc7;
  --gray-400: #b8b0a5;
  --gray-500: #9a9088;
  --gray-600: #7a706a;
  --gray-700: #5c5450;
  --gray-800: #3d3936;
  --gray-900: #201e1c;
  --gray-950: #111110;
  --gray-1000: #080807;
  
  /* Blue scale */
  --blue-50: #eff6ff;
  --blue-100: #dbeafe;
  --blue-200: #bfdbfe;
  --blue-400: #60a5fa;
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --blue-700: #1d4ed8;
  
  /* Green scale */
  --green-50: #f0fdf4;
  --green-400: #4ade80;
  --green-500: #22c55e;
  --green-600: #16a34a;
  --green-700: #15803d;
  
  /* Red scale */
  --red-50: #fef2f2;
  --red-400: #f87171;
  --red-500: #ef4444;
  --red-600: #dc2626;
  --red-700: #b91c1c;
  
  /* Amber scale */
  --amber-50: #fffbeb;
  --amber-400: #fbbf24;
  --amber-500: #f59e0b;
  --amber-600: #d97706;
  
  /* Brand accent primitives (customize per project) */
  --brand-50: #fff7ed;
  --brand-100: #ffedd5;
  --brand-400: #fb923c;
  --brand-500: #f97316;
  --brand-600: #ea580c;
  --brand-700: #c2410c;
}
```

---

## Semantic Token Layer

```css
/* ======================
   LIGHT MODE SEMANTICS
   ====================== */
:root,
[data-theme="light"] {
  /* Backgrounds */
  --color-bg-base: var(--gray-50);
  --color-bg-subtle: var(--gray-100);
  --color-bg-muted: var(--gray-200);
  --color-bg-inverse: var(--gray-950);
  
  /* Borders */
  --color-border: var(--gray-200);
  --color-border-subtle: var(--gray-100);
  --color-border-strong: var(--gray-400);
  --color-border-focus: var(--brand-500);
  
  /* Text */
  --color-text-primary: var(--gray-950);
  --color-text-secondary: var(--gray-700);
  --color-text-tertiary: var(--gray-500);
  --color-text-disabled: var(--gray-400);
  --color-text-inverse: var(--gray-50);
  --color-text-link: var(--blue-600);
  --color-text-link-hover: var(--blue-700);
  
  /* Brand / Accent */
  --color-accent: var(--brand-500);
  --color-accent-hover: var(--brand-600);
  --color-accent-subtle: var(--brand-50);
  --color-accent-text: var(--brand-700);
  
  /* Semantic states */
  --color-success: var(--green-600);
  --color-success-subtle: var(--green-50);
  --color-success-border: var(--green-400);
  
  --color-warning: var(--amber-600);
  --color-warning-subtle: var(--amber-50);
  --color-warning-border: var(--amber-400);
  
  --color-error: var(--red-600);
  --color-error-subtle: var(--red-50);
  --color-error-border: var(--red-400);
  
  --color-info: var(--blue-600);
  --color-info-subtle: var(--blue-50);
  --color-info-border: var(--blue-200);
}

/* ======================
   DARK MODE SEMANTICS
   Only override what changes
   ====================== */
[data-theme="dark"],
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-base: #0c0c0c;
    --color-bg-subtle: #141414;
    --color-bg-muted: #1e1e1e;
    --color-bg-inverse: var(--gray-100);
    
    --color-border: #262626;
    --color-border-subtle: #1a1a1a;
    --color-border-strong: #404040;
    
    --color-text-primary: #f0f0f0;
    --color-text-secondary: #a0a0a0;
    --color-text-tertiary: #636363;
    --color-text-disabled: #404040;
    --color-text-inverse: var(--gray-950);
    --color-text-link: var(--blue-400);
    
    --color-accent: var(--brand-400);
    --color-accent-hover: var(--brand-500);
    --color-accent-subtle: #2a1a0e;  /* dark tint of brand */
    --color-accent-text: var(--brand-400);
    
    --color-success: var(--green-400);
    --color-success-subtle: #0a1f0e;
    --color-success-border: #1a4024;
    
    --color-warning: var(--amber-400);
    --color-warning-subtle: #1f160a;
    --color-warning-border: #3d2a10;
    
    --color-error: var(--red-400);
    --color-error-subtle: #1f0a0a;
    --color-error-border: #3d1414;
    
    --color-info: var(--blue-400);
    --color-info-subtle: #0a1520;
    --color-info-border: #152840;
  }
}
```

---

## Component Token Layer

```css
/* ======================
   COMPONENT TOKENS
   Reference semantic tokens only
   ====================== */
:root {
  /* --- Buttons --- */
  --btn-primary-bg: var(--color-accent);
  --btn-primary-bg-hover: var(--color-accent-hover);
  --btn-primary-text: var(--gray-0);
  --btn-primary-border: transparent;
  
  --btn-secondary-bg: var(--color-bg-subtle);
  --btn-secondary-bg-hover: var(--color-bg-muted);
  --btn-secondary-text: var(--color-text-primary);
  --btn-secondary-border: var(--color-border);
  
  --btn-ghost-bg: transparent;
  --btn-ghost-bg-hover: var(--color-bg-subtle);
  --btn-ghost-text: var(--color-text-secondary);
  
  --btn-danger-bg: var(--color-error);
  --btn-danger-bg-hover: var(--red-700);
  --btn-danger-text: var(--gray-0);
  
  --btn-border-radius: 6px;
  --btn-padding-sm: 6px 12px;
  --btn-padding-md: 8px 16px;
  --btn-padding-lg: 10px 20px;
  --btn-font-size-sm: 13px;
  --btn-font-size-md: 14px;
  --btn-font-size-lg: 15px;
  
  /* --- Inputs --- */
  --input-bg: var(--color-bg-base);
  --input-bg-hover: var(--color-bg-subtle);
  --input-border: var(--color-border-strong);
  --input-border-hover: var(--color-border-strong);
  --input-border-focus: var(--color-border-focus);
  --input-border-error: var(--color-error);
  --input-text: var(--color-text-primary);
  --input-placeholder: var(--color-text-tertiary);
  --input-border-radius: 6px;
  --input-padding: 8px 12px;
  --input-font-size: 14px;
  --input-focus-shadow: 0 0 0 3px var(--color-accent-subtle);
  
  /* --- Cards --- */
  --card-bg: var(--color-bg-base);
  --card-bg-hover: var(--color-bg-subtle);
  --card-border: var(--color-border);
  --card-border-radius: 8px;
  --card-padding: 20px;
  --card-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  
  /* --- Navigation/Sidebar --- */
  --nav-bg: var(--color-bg-subtle);
  --nav-border: var(--color-border);
  --nav-item-padding: 6px 10px;
  --nav-item-radius: 6px;
  --nav-item-active-bg: var(--color-accent-subtle);
  --nav-item-active-text: var(--color-accent-text);
  --nav-item-active-border: var(--color-accent);
  --nav-item-hover-bg: var(--color-bg-muted);
  
  /* --- Badges/Pills --- */
  --badge-border-radius: 4px;
  --badge-padding: 2px 8px;
  --badge-font-size: 12px;
  --badge-font-weight: 500;
  
  /* --- Tables --- */
  --table-header-bg: var(--color-bg-subtle);
  --table-border: var(--color-border);
  --table-row-hover-bg: var(--color-bg-subtle);
  --table-stripe-bg: var(--color-bg-subtle);
  --table-cell-padding: 10px 16px;
  
  /* --- Modals --- */
  --modal-bg: var(--color-bg-base);
  --modal-border: var(--color-border);
  --modal-border-radius: 12px;
  --modal-shadow: 0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px var(--color-border);
  --modal-overlay-bg: rgba(0,0,0,0.4);
  --modal-overlay-blur: blur(2px);
  
  /* --- Tooltips --- */
  --tooltip-bg: var(--gray-950);
  --tooltip-text: var(--gray-50);
  --tooltip-border-radius: 4px;
  --tooltip-padding: 4px 8px;
  --tooltip-font-size: 12px;
}
```

---

## Typography Scale Tokens

```css
:root {
  /* Font Families — customize per project aesthetic */
  --font-display: 'Instrument Serif', 'Playfair Display', Georgia, serif;
  --font-sans: 'DM Sans', 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Geist Mono', 'Fira Code', monospace;
  
  /* Scale (1.333 Perfect Fourth ratio) */
  --text-xs:   12px;   /* labels, captions, badges */
  --text-sm:   13px;   /* secondary labels, table cells */
  --text-base: 15px;   /* body copy */
  --text-md:   16px;   /* emphasized body */
  --text-lg:   18px;   /* subheadings, card titles */
  --text-xl:   20px;   /* section headings */
  --text-2xl:  24px;   /* page headings */
  --text-3xl:  28px;   
  --text-4xl:  36px;   /* display headings */
  --text-5xl:  48px;   /* hero headings */
  --text-6xl:  60px;   
  --text-7xl:  80px;   /* large display */
  
  /* Weights — use only these, no mid-weights */
  --weight-thin:       200;
  --weight-light:      300;
  --weight-normal:     400;
  --weight-medium:     500;
  --weight-semibold:   600;
  --weight-bold:       700;
  --weight-extrabold:  800;
  --weight-black:      900;
  
  /* Line Heights */
  --leading-none:    1;
  --leading-tight:   1.15;  /* headings */
  --leading-snug:    1.3;   /* subheadings, UI labels */
  --leading-normal:  1.5;   /* body text */
  --leading-relaxed: 1.65;  /* long-form reading content */
  
  /* Letter Spacing */
  --tracking-tighter: -0.04em;  /* very large display */
  --tracking-tight:   -0.02em;  /* headings */
  --tracking-normal:   0em;
  --tracking-wide:    +0.02em;  /* labels, caps */
  --tracking-wider:   +0.05em;  /* small caps, tags */
  
  /* Semantic typography aliases */
  --text-heading-display: var(--text-5xl);
  --text-heading-1: var(--text-4xl);
  --text-heading-2: var(--text-2xl);
  --text-heading-3: var(--text-xl);
  --text-heading-4: var(--text-lg);
  --text-body: var(--text-base);
  --text-body-small: var(--text-sm);
  --text-label: var(--text-xs);
  --text-code: var(--text-sm);
}
```

---

## Spacing & Sizing Tokens

```css
:root {
  /* Base 8px grid */
  --space-0:   0px;
  --space-0-5: 2px;
  --space-1:   4px;
  --space-1-5: 6px;
  --space-2:   8px;
  --space-3:   12px;
  --space-4:   16px;
  --space-5:   20px;
  --space-6:   24px;
  --space-7:   28px;
  --space-8:   32px;
  --space-10:  40px;
  --space-12:  48px;
  --space-16:  64px;
  --space-20:  80px;
  --space-24:  96px;
  --space-32:  128px;
  
  /* Border Radius */
  --radius-none: 0px;
  --radius-xs:   2px;
  --radius-sm:   4px;
  --radius-md:   6px;
  --radius-lg:   8px;
  --radius-xl:   12px;
  --radius-2xl:  16px;
  --radius-3xl:  24px;
  --radius-full: 9999px;
  
  /* Component sizing */
  --size-sidebar-width: 240px;
  --size-sidebar-collapsed: 64px;
  --size-topnav-height: 56px;
  --size-content-max: 1200px;
  --size-content-prose: 680px;
  --size-modal-sm: 400px;
  --size-modal-md: 520px;
  --size-modal-lg: 720px;
  --size-touch-target: 44px;
  
  /* Z-index scale */
  --z-base:      0;
  --z-raised:    10;
  --z-dropdown:  100;
  --z-sticky:    200;
  --z-overlay:   300;
  --z-modal:     400;
  --z-toast:     500;
  --z-tooltip:   600;
}
```

---

## Motion & Animation Tokens

```css
:root {
  /* Duration */
  --duration-instant:   80ms;
  --duration-fast:      120ms;
  --duration-normal:    200ms;
  --duration-slow:      300ms;
  --duration-slower:    400ms;
  --duration-slowest:   600ms;
  
  /* Easing */
  --ease-linear:        linear;
  --ease-in:            cubic-bezier(0.4, 0, 1, 1);
  --ease-out:           cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out:        cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce:        cubic-bezier(0.34, 1.56, 0.64, 1);  /* spring-like */
  --ease-expo-out:      cubic-bezier(0.16, 1, 0.3, 1);      /* entrance animations */
  --ease-back:          cubic-bezier(0.36, 0, 0.66, -0.56); /* exit animations */
  
  /* Semantic motion aliases */
  --transition-hover:   var(--duration-fast) var(--ease-out);
  --transition-expand:  var(--duration-normal) var(--ease-expo-out);
  --transition-collapse: var(--duration-fast) var(--ease-back);
  --transition-enter:   var(--duration-slow) var(--ease-expo-out);
  --transition-exit:    var(--duration-normal) var(--ease-in);
  --transition-page:    var(--duration-slower) var(--ease-expo-out);
}

/* Reduced motion: override all animations */
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-instant:  0ms;
    --duration-fast:     0ms;
    --duration-normal:   0ms;
    --duration-slow:     0ms;
    --duration-slower:   0ms;
    --duration-slowest:  0ms;
  }
}
```

---

## Shadow System

```css
:root {
  /* Elevation scale */
  --shadow-none: none;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.08), 0 8px 10px rgba(0,0,0,0.04);
  --shadow-2xl: 0 25px 50px rgba(0,0,0,0.12);
  
  /* Semantic shadow aliases */
  --shadow-card: var(--shadow-sm);
  --shadow-card-hover: var(--shadow-md);
  --shadow-dropdown: var(--shadow-lg);
  --shadow-modal: 0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px var(--color-border);
  --shadow-focus: 0 0 0 3px var(--color-accent-subtle);
  --shadow-focus-error: 0 0 0 3px var(--color-error-subtle);
  
  /* Dark mode shadows (more visible) */
  /* Override in [data-theme="dark"]: */
  /* --shadow-sm: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2); */
  
  /* Inset shadows (for inputs, wells) */
  --shadow-inset: inset 0 1px 2px rgba(0,0,0,0.05);
  --shadow-inset-error: inset 0 1px 2px rgba(220,38,38,0.1);
}
```
