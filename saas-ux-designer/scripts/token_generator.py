#!/usr/bin/env python3
"""
token_generator.py - Design Token System Generator

Generates a complete CSS custom property token system from a brief aesthetic description.
Outputs production-ready CSS, or optionally a JSON token file (Style Dictionary format).

Usage:
    python token_generator.py --aesthetic "warm editorial"
    python token_generator.py --aesthetic "dark terminal developer" --accent "#00dc82"
    python token_generator.py --aesthetic "neo-brutalist" --format json
    python token_generator.py --aesthetic "clinical precision fintech" --output tokens.css
    python token_generator.py --list   # show available aesthetics

Aesthetic presets:
    warm-editorial        editorial, serif, terracotta
    dark-terminal         developer, monospace, green accent
    neo-brutalist         bold, thick borders, hot accent
    refined-minimal       quiet, one-family, monochrome
    clinical-precision    fintech, cool grays, blue accent
    soft-computational    AI-native, glass, violet or cyan
    premium-enterprise    dark luxe, indigo + gold
    bold-brand-led        strong personality, brand-dominant
"""

import argparse
import json
import sys
from typing import Optional


# ─────────────────────────────────────────
# Aesthetic presets
# ─────────────────────────────────────────

AESTHETICS = {
    "warm-editorial": {
        "description": "Warm, approachable editorial — parchment backgrounds, serif display, terracotta accent",
        "aliases": ["warm", "editorial", "content", "blog", "notion", "craft"],
        "bg_base": "#faf8f4",
        "bg_subtle": "#f2efe9",
        "bg_muted": "#e8e3da",
        "border": "#d6cfc4",
        "border_strong": "#b8ad9f",
        "text_primary": "#1a1714",
        "text_secondary": "#6b6159",
        "text_tertiary": "#9c9087",
        "accent": "#c9622f",
        "accent_dark": "#a84e25",
        "accent_subtle_light": "#fff3ed",
        "success": "#3d7a4a",
        "warning": "#b07d2c",
        "error": "#b83333",
        "font_display": "'Instrument Serif', 'Playfair Display', Georgia, serif",
        "font_sans": "'DM Sans', 'Plus Jakarta Sans', system-ui, sans-serif",
        "font_mono": "'DM Mono', 'IBM Plex Mono', monospace",
        "border_radius_base": "6px",
        "dark_bg_base": "#14110e",
        "dark_bg_subtle": "#1c1915",
        "dark_bg_muted": "#28231d",
        "dark_border": "#3a3228",
        "dark_text_primary": "#f0ece6",
        "dark_text_secondary": "#a09080",
        "dark_accent": "#e8885c",
    },

    "dark-terminal": {
        "description": "Developer-grade dark UI — monospace-first, near-black, green or blue accent",
        "aliases": ["terminal", "developer", "dev", "vercel", "resend", "cli", "code"],
        "bg_base": "#0a0a0a",
        "bg_subtle": "#111111",
        "bg_muted": "#1a1a1a",
        "border": "#232323",
        "border_strong": "#3a3a3a",
        "text_primary": "#ededed",
        "text_secondary": "#a1a1a1",
        "text_tertiary": "#616161",
        "accent": "#00dc82",
        "accent_dark": "#00b368",
        "accent_subtle_light": "#00dc8215",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "font_display": "'Geist', 'Sohne', system-ui, sans-serif",
        "font_sans": "'Geist', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', 'Geist Mono', 'Fira Code', monospace",
        "border_radius_base": "4px",
        "dark_bg_base": "#0a0a0a",
        "dark_bg_subtle": "#111111",
        "dark_bg_muted": "#1a1a1a",
        "dark_border": "#232323",
        "dark_text_primary": "#ededed",
        "dark_text_secondary": "#a1a1a1",
        "dark_accent": "#00dc82",
        "notes": "This aesthetic is dark-first. Light mode uses reversed values.",
    },

    "neo-brutalist": {
        "description": "Bold, high-contrast, anti-corporate — thick borders, hot accent, hard shadows",
        "aliases": ["brutalist", "bold", "anti-design", "rebellious", "raw"],
        "bg_base": "#fffbe6",
        "bg_subtle": "#fff5cc",
        "bg_muted": "#ffe98a",
        "border": "#111111",
        "border_strong": "#000000",
        "text_primary": "#0a0a0a",
        "text_secondary": "#333333",
        "text_tertiary": "#666666",
        "accent": "#ff3b00",
        "accent_dark": "#cc2f00",
        "accent_subtle_light": "#ff3b0015",
        "success": "#1a7a2e",
        "warning": "#cc7700",
        "error": "#cc0000",
        "font_display": "'Unbounded', 'Archivo Black', 'Space Grotesk', system-ui, sans-serif",
        "font_sans": "'Space Grotesk', 'Archivo', system-ui, sans-serif",
        "font_mono": "'Space Mono', 'Courier New', monospace",
        "border_radius_base": "0px",
        "dark_bg_base": "#0f0f0f",
        "dark_bg_subtle": "#1a1a1a",
        "dark_bg_muted": "#262626",
        "dark_border": "#f5f5f5",
        "dark_text_primary": "#f5f5f5",
        "dark_text_secondary": "#d0d0d0",
        "dark_accent": "#ccff00",
        "notes": "Use 2-3px borders everywhere. Hard box-shadows: 4px 4px 0 #000.",
    },

    "refined-minimal": {
        "description": "Quiet confidence, restrained, Japanese-influenced — generous whitespace, minimal accent",
        "aliases": ["minimal", "quiet", "japanese", "zen", "things", "bear"],
        "bg_base": "#fafafa",
        "bg_subtle": "#f4f4f5",
        "bg_muted": "#e4e4e7",
        "border": "#e4e4e7",
        "border_strong": "#a1a1aa",
        "text_primary": "#18181b",
        "text_secondary": "#52525b",
        "text_tertiary": "#a1a1aa",
        "accent": "#18181b",
        "accent_dark": "#000000",
        "accent_subtle_light": "#f4f4f5",
        "success": "#059669",
        "warning": "#d97706",
        "error": "#dc2626",
        "font_display": "'Neue Haas Grotesk', 'Cabinet Grotesk', 'Helvetica Neue', Helvetica, sans-serif",
        "font_sans": "'Neue Haas Grotesk', 'Cabinet Grotesk', system-ui, sans-serif",
        "font_mono": "'SF Mono', 'IBM Plex Mono', monospace",
        "border_radius_base": "4px",
        "dark_bg_base": "#09090b",
        "dark_bg_subtle": "#111113",
        "dark_bg_muted": "#1c1c1f",
        "dark_border": "#27272a",
        "dark_text_primary": "#fafafa",
        "dark_text_secondary": "#a1a1aa",
        "dark_accent": "#fafafa",
        "notes": "Use only weights 300, 400, 600. No heavy weights. Maximum whitespace.",
    },

    "clinical-precision": {
        "description": "Cool, precise, trustworthy — for fintech, healthcare, compliance, data tools",
        "aliases": ["fintech", "precision", "clinical", "stripe", "mercury", "finance", "medical"],
        "bg_base": "#ffffff",
        "bg_subtle": "#f8fafc",
        "bg_muted": "#f1f5f9",
        "border": "#e2e8f0",
        "border_strong": "#cbd5e1",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "text_tertiary": "#94a3b8",
        "accent": "#3b82f6",
        "accent_dark": "#2563eb",
        "accent_subtle_light": "#eff6ff",
        "success": "#059669",
        "warning": "#d97706",
        "error": "#dc2626",
        "font_display": "'IBM Plex Sans', 'Inter', system-ui, sans-serif",
        "font_sans": "'IBM Plex Sans', system-ui, sans-serif",
        "font_mono": "'IBM Plex Mono', 'SFMono-Regular', monospace",
        "border_radius_base": "6px",
        "dark_bg_base": "#0b1120",
        "dark_bg_subtle": "#111827",
        "dark_bg_muted": "#1e293b",
        "dark_border": "#334155",
        "dark_text_primary": "#f1f5f9",
        "dark_text_secondary": "#94a3b8",
        "dark_accent": "#60a5fa",
        "notes": "All numbers must use font-variant-numeric: tabular-nums. Data density is a feature.",
    },

    "soft-computational": {
        "description": "AI-native, data-rich, glass morphism done tastefully — ambient depth, computational warmth",
        "aliases": ["ai", "computational", "glass", "perplexity", "ambient", "modern"],
        "bg_base": "#f9fafb",
        "bg_subtle": "#ffffff",
        "bg_muted": "#f3f4f6",
        "border": "#e5e7eb",
        "border_strong": "#d1d5db",
        "text_primary": "#111827",
        "text_secondary": "#6b7280",
        "text_tertiary": "#9ca3af",
        "accent": "#7c3aed",
        "accent_dark": "#6d28d9",
        "accent_subtle_light": "#f5f3ff",
        "success": "#059669",
        "warning": "#d97706",
        "error": "#dc2626",
        "font_display": "'Plus Jakarta Sans', 'DM Sans', system-ui, sans-serif",
        "font_sans": "'Plus Jakarta Sans', system-ui, sans-serif",
        "font_mono": "'Geist Mono', 'Fira Code', monospace",
        "border_radius_base": "10px",
        "dark_bg_base": "#0f1117",
        "dark_bg_subtle": "#1c1e26",
        "dark_bg_muted": "#252833",
        "dark_border": "#313442",
        "dark_text_primary": "#f0f2ff",
        "dark_text_secondary": "#8b90a8",
        "dark_accent": "#a78bfa",
        "notes": "Glass effect: background rgba(255,255,255,0.7) + backdrop-filter: blur(12px). Subtle mesh gradient on bg.",
    },

    "premium-enterprise": {
        "description": "Dark luxe, serious money — deep blacks, indigo or gold accents, elevated density",
        "aliases": ["enterprise", "premium", "luxe", "dark", "serious", "palantir"],
        "bg_base": "#0d0d0f",
        "bg_subtle": "#141417",
        "bg_muted": "#1e1e24",
        "border": "#2a2a33",
        "border_strong": "#3d3d4d",
        "text_primary": "#f0f0f5",
        "text_secondary": "#8888a0",
        "text_tertiary": "#55556a",
        "accent": "#6366f1",
        "accent_dark": "#4f46e5",
        "accent_subtle_light": "#6366f11a",
        "success": "#34d399",
        "warning": "#fbbf24",
        "error": "#f87171",
        "font_display": "'Sohne', 'Neue Montreal', 'Helvetica Neue', system-ui, sans-serif",
        "font_sans": "'Sohne', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "border_radius_base": "6px",
        "dark_bg_base": "#0d0d0f",
        "dark_bg_subtle": "#141417",
        "dark_bg_muted": "#1e1e24",
        "dark_border": "#2a2a33",
        "dark_text_primary": "#f0f0f5",
        "dark_text_secondary": "#8888a0",
        "dark_accent": "#818cf8",
        "notes": "Add amber/gold (#f59e0b) as secondary accent for premium tier indicators. Cards: glow on hover.",
    },

    "bold-brand-led": {
        "description": "Strong brand identity — the product IS the brand. Used for Notion-style personality-driven SaaS",
        "aliases": ["brand", "notion", "monday", "loom", "personality", "consumer"],
        "bg_base": "#fafafa",
        "bg_subtle": "#f5f5f5",
        "bg_muted": "#ebebeb",
        "border": "#e0e0e0",
        "border_strong": "#c0c0c0",
        "text_primary": "#1a1a1a",
        "text_secondary": "#5e5e5e",
        "text_tertiary": "#9a9a9a",
        "accent": "#2f80ed",
        "accent_dark": "#1a6bd4",
        "accent_subtle_light": "#e8f1fd",
        "success": "#27ae60",
        "warning": "#f39c12",
        "error": "#e74c3c",
        "font_display": "'Bricolage Grotesque', 'Cabinet Grotesk', system-ui, sans-serif",
        "font_sans": "'Bricolage Grotesque', system-ui, sans-serif",
        "font_mono": "'Fira Code', monospace",
        "border_radius_base": "8px",
        "dark_bg_base": "#141414",
        "dark_bg_subtle": "#1e1e1e",
        "dark_bg_muted": "#2a2a2a",
        "dark_border": "#3a3a3a",
        "dark_text_primary": "#f0f0f0",
        "dark_text_secondary": "#a0a0a0",
        "dark_accent": "#5eaaf5",
        "notes": "Brand color can be used as sidebar background. Personality in microcopy is essential.",
    },
}


def find_aesthetic(query: str) -> Optional[tuple]:
    """Find aesthetic by name or alias."""
    query = query.lower().strip().replace(" ", "-")
    # Exact match
    if query in AESTHETICS:
        return query, AESTHETICS[query]
    # Alias match
    for key, aesthetic in AESTHETICS.items():
        if query in [a.lower() for a in aesthetic.get("aliases", [])]:
            return key, aesthetic
    # Partial match
    for key, aesthetic in AESTHETICS.items():
        if query in key:
            return key, aesthetic
    return None


# ─────────────────────────────────────────
# Token generators
# ─────────────────────────────────────────

def generate_css_tokens(key: str, a: dict, custom_accent: Optional[str] = None) -> str:
    accent = custom_accent or a["accent"]
    accent_dark = a["accent_dark"] if not custom_accent else accent  # simplified

    css = f"""/* ══════════════════════════════════════════════════
   Design Tokens — {key.replace('-', ' ').title()} Aesthetic
   Generated by token_generator.py
   
   {a['description']}
   ══════════════════════════════════════════════════ */

/* ── Fonts ──────────────────────────────────────── */
/* Import these at the top of your CSS or in <head>: */
/* @import url('https://fonts.googleapis.com/css2?...') */

:root {{
  --font-display: {a['font_display']};
  --font-sans:    {a['font_sans']};
  --font-mono:    {a['font_mono']};
}}

/* ── Light Mode Colors ──────────────────────────── */
:root,
[data-theme="light"] {{
  /* Backgrounds */
  --color-bg-base:    {a['bg_base']};
  --color-bg-subtle:  {a['bg_subtle']};
  --color-bg-muted:   {a['bg_muted']};

  /* Borders */
  --color-border:        {a['border']};
  --color-border-strong: {a['border_strong']};
  --color-border-focus:  {accent};

  /* Text */
  --color-text-primary:   {a['text_primary']};
  --color-text-secondary: {a['text_secondary']};
  --color-text-tertiary:  {a['text_tertiary']};
  --color-text-disabled:  {a['text_tertiary']}80;  /* 50% opacity */
  --color-text-inverse:   {a['dark_text_primary']};
  --color-text-link:      {accent};
  --color-text-link-hover: {accent_dark};

  /* Accent / Brand */
  --color-accent:        {accent};
  --color-accent-hover:  {accent_dark};
  --color-accent-subtle: {a['accent_subtle_light']};
  --color-accent-text:   {accent_dark};

  /* Semantic */
  --color-success: {a['success']};
  --color-warning: {a['warning']};
  --color-error:   {a['error']};
  --color-info:    {accent};

  --color-success-subtle: {a['success']}15;
  --color-warning-subtle: {a['warning']}15;
  --color-error-subtle:   {a['error']}15;
  --color-info-subtle:    {accent}15;
}}

/* ── Dark Mode Colors ───────────────────────────── */
[data-theme="dark"],
@media (prefers-color-scheme: dark) {{
  :root {{
    --color-bg-base:    {a['dark_bg_base']};
    --color-bg-subtle:  {a['dark_bg_subtle']};
    --color-bg-muted:   {a['dark_bg_muted']};

    --color-border:        {a['dark_border']};
    --color-border-strong: {a['dark_border']}cc;
    --color-border-focus:  {a['dark_accent']};

    --color-text-primary:   {a['dark_text_primary']};
    --color-text-secondary: {a['dark_text_secondary']};
    --color-text-tertiary:  {a['dark_text_secondary']}80;
    --color-text-inverse:   {a['text_primary']};
    --color-text-link:      {a['dark_accent']};
    --color-text-link-hover: {a['dark_accent']}cc;

    --color-accent:        {a['dark_accent']};
    --color-accent-hover:  {a['dark_accent']}cc;
    --color-accent-subtle: {a['dark_accent']}18;
    --color-accent-text:   {a['dark_accent']};
  }}
}}

/* ── Typography Scale ───────────────────────────── */
:root {{
  --text-xs:   12px;
  --text-sm:   13px;
  --text-base: 15px;
  --text-lg:   18px;
  --text-xl:   20px;
  --text-2xl:  24px;
  --text-3xl:  30px;
  --text-4xl:  38px;
  --text-5xl:  48px;
  --text-6xl:  64px;

  --weight-light:    300;
  --weight-normal:   400;
  --weight-medium:   500;
  --weight-semibold: 600;
  --weight-bold:     700;
  --weight-heavy:    800;
  --weight-black:    900;

  --leading-tight:   1.15;
  --leading-snug:    1.3;
  --leading-normal:  1.5;
  --leading-relaxed: 1.65;

  --tracking-tight:  -0.02em;
  --tracking-normal:  0em;
  --tracking-wide:   +0.04em;
}}

/* ── Spacing (8px base grid) ────────────────────── */
:root {{
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  --space-24: 96px;
  --space-32: 128px;
}}

/* ── Border Radius ──────────────────────────────── */
:root {{
  --radius-sm:   calc({a['border_radius_base']} - 2px);
  --radius-md:   {a['border_radius_base']};
  --radius-lg:   calc({a['border_radius_base']} + 4px);
  --radius-xl:   calc({a['border_radius_base']} + 8px);
  --radius-full: 9999px;
}}

/* ── Shadows ────────────────────────────────────── */
:root {{
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.07), 0 4px 6px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.08), 0 8px 10px rgba(0,0,0,0.04);

  /* Semantic shadows */
  --shadow-card:    var(--shadow-sm);
  --shadow-hover:   var(--shadow-md);
  --shadow-modal:   0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px var(--color-border);
  --shadow-focus:   0 0 0 3px {accent}33;
  --shadow-focus-error: 0 0 0 3px {a['error']}33;
}}

/* ── Motion ─────────────────────────────────────── */
:root {{
  --duration-fast:    120ms;
  --duration-normal:  200ms;
  --duration-slow:    300ms;
  --duration-slower:  400ms;
  --ease-out:         cubic-bezier(0, 0, 0.2, 1);
  --ease-expo-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-bounce:      cubic-bezier(0.34, 1.56, 0.64, 1);
  --transition-hover: var(--duration-fast) var(--ease-out);
  --transition-enter: var(--duration-slow) var(--ease-expo-out);
}}

@media (prefers-reduced-motion: reduce) {{
  :root {{
    --duration-fast: 0ms; --duration-normal: 0ms;
    --duration-slow: 0ms; --duration-slower: 0ms;
  }}
}}

/* ── Component Tokens ───────────────────────────── */
:root {{
  /* Buttons */
  --btn-primary-bg:    var(--color-accent);
  --btn-primary-hover: var(--color-accent-hover);
  --btn-primary-text:  #fff;
  --btn-radius:        var(--radius-md);

  /* Inputs */
  --input-border:       var(--color-border-strong);
  --input-bg:           var(--color-bg-base);
  --input-focus-border: var(--color-border-focus);
  --input-focus-shadow: var(--shadow-focus);
  --input-radius:       var(--radius-md);
  --input-padding:      8px 12px;

  /* Cards */
  --card-bg:      var(--color-bg-base);
  --card-border:  var(--color-border);
  --card-radius:  var(--radius-lg);
  --card-shadow:  var(--shadow-card);
  --card-padding: var(--space-5);

  /* Navigation */
  --nav-bg:             var(--color-bg-subtle);
  --nav-border:         var(--color-border);
  --nav-item-active-bg: var(--color-accent-subtle);
  --nav-item-active-fg: var(--color-accent-text);
  --nav-item-active-border: var(--color-accent);
}}
"""

    # Add aesthetic-specific notes
    notes = a.get("notes")
    if notes:
        css += f"\n/* ── Designer Notes ─────────────────────────────── */\n"
        css += f"/* {notes} */\n"

    return css


def generate_json_tokens(key: str, a: dict, custom_accent: Optional[str] = None) -> dict:
    """Style Dictionary compatible format."""
    accent = custom_accent or a["accent"]
    return {
        "color": {
            "bg": {
                "base":   {"value": a["bg_base"],   "type": "color"},
                "subtle": {"value": a["bg_subtle"],  "type": "color"},
                "muted":  {"value": a["bg_muted"],   "type": "color"},
            },
            "text": {
                "primary":   {"value": a["text_primary"],   "type": "color"},
                "secondary": {"value": a["text_secondary"],  "type": "color"},
                "tertiary":  {"value": a["text_tertiary"],   "type": "color"},
            },
            "accent": {
                "base":   {"value": accent,             "type": "color"},
                "hover":  {"value": a["accent_dark"],   "type": "color"},
                "subtle": {"value": a["accent_subtle_light"], "type": "color"},
            },
            "border": {
                "base":   {"value": a["border"],        "type": "color"},
                "strong": {"value": a["border_strong"], "type": "color"},
            },
            "semantic": {
                "success": {"value": a["success"], "type": "color"},
                "warning": {"value": a["warning"], "type": "color"},
                "error":   {"value": a["error"],   "type": "color"},
            },
        },
        "font": {
            "display": {"value": a["font_display"], "type": "fontFamily"},
            "sans":    {"value": a["font_sans"],    "type": "fontFamily"},
            "mono":    {"value": a["font_mono"],    "type": "fontFamily"},
        },
        "borderRadius": {
            "base": {"value": a["border_radius_base"], "type": "borderRadius"},
        },
        "_meta": {
            "aesthetic": key,
            "description": a["description"],
        }
    }


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate design token CSS from an aesthetic description"
    )
    parser.add_argument("--aesthetic", "-a", help="Aesthetic name or keyword")
    parser.add_argument("--accent", help="Override accent color (hex)")
    parser.add_argument("--format", choices=["css", "json"], default="css")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--list", action="store_true", help="List available aesthetics")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable aesthetic presets:\n")
        for key, a in AESTHETICS.items():
            aliases = ", ".join(a.get("aliases", []))
            print(f"  {key:<25} — {a['description'][:60]}...")
            print(f"  {'':25}   Aliases: {aliases}\n")
        return

    if not args.aesthetic:
        parser.print_help()
        print("\nTip: Use --list to see available aesthetic presets.")
        sys.exit(1)

    result = find_aesthetic(args.aesthetic)
    if not result:
        print(f"Aesthetic '{args.aesthetic}' not found. Use --list to see options.")
        sys.exit(1)

    key, aesthetic = result

    if args.format == "json":
        output = json.dumps(generate_json_tokens(key, aesthetic, args.accent), indent=2)
    else:
        output = generate_css_tokens(key, aesthetic, args.accent)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ Tokens written to {args.output}")
        print(f"   Aesthetic: {key} — {aesthetic['description']}")
    else:
        print(output)


if __name__ == "__main__":
    main()
