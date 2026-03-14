#!/usr/bin/env python3
"""
component_scaffold.py - SaaS Component Scaffolder

Generates a complete, production-ready component with ALL states:
default, hover, focus, error, loading, empty, disabled.

Framework-agnostic: outputs semantic HTML+CSS by default,
or specify --framework for framework-specific output.

Usage:
    python component_scaffold.py --component button
    python component_scaffold.py --component input --framework react
    python component_scaffold.py --component data-table --framework svelte
    python component_scaffold.py --component stat-card --theme dark-terminal
    python component_scaffold.py --list

Components:
    button          Primary, secondary, ghost, destructive variants + all states
    input           Text/email/password input with label, helper, error
    form-field      Full field with label, input, validation, helper text
    stat-card       KPI card with value, label, delta trend
    data-table      Sortable table with selection, hover, empty state
    empty-state     First-run, zero-result, and error empty states
    toast           Success, error, warning, info notification
    badge           Status badge in all semantic variants
    nav-item        Sidebar navigation item with all states
    modal           Dialog with header, body, footer + focus trap
    skeleton        Loading skeleton for card, list, table
    command-palette Cmd+K search interface
"""

import argparse
import sys
from typing import Optional


COMPONENTS = {
    "button": "Primary, secondary, ghost, destructive + all interaction states",
    "input": "Form input with label, placeholder, helper, error, loading states",
    "form-field": "Complete field: label + input + validation + helper text",
    "stat-card": "KPI metric card: value, label, trend delta",
    "data-table": "Sortable table: column headers, rows, selection, empty state",
    "empty-state": "First-run, zero-result, and error empty state variants",
    "toast": "Toast notifications: success, error, warning, info",
    "badge": "Status badge: success, error, warning, info, neutral variants",
    "nav-item": "Sidebar nav item: default, hover, active, disabled states",
    "modal": "Dialog with header, body, footer, focus trap, close behavior",
    "skeleton": "Shimmer loading placeholders for card, list, and table",
    "command-palette": "Cmd+K search interface with keyboard navigation",
}


# ─────────────────────────────────────────
# HTML+CSS scaffolds
# ─────────────────────────────────────────

def scaffold_button(theme: str, framework: str) -> str:
    return '''\
<!-- ══════════════════════════════════════════════
     BUTTON COMPONENT — All Variants & States
     Tokens: see design-tokens.md
     ══════════════════════════════════════════════ -->

<!-- HTML Structure -->
<div class="btn-demo-grid">
  <!-- PRIMARY -->
  <button class="btn btn-primary btn-md">
    Save changes
  </button>
  <button class="btn btn-primary btn-md" data-loading aria-busy="true" aria-label="Saving…">
    <span class="btn-spinner" aria-hidden="true"></span>
    <span class="btn-label">Save changes</span>
  </button>
  <button class="btn btn-primary btn-md" disabled aria-disabled="true" title="Fix validation errors to continue">
    Save changes
  </button>

  <!-- SECONDARY -->
  <button class="btn btn-secondary btn-md">Cancel</button>

  <!-- GHOST -->
  <button class="btn btn-ghost btn-md">View details</button>

  <!-- DESTRUCTIVE -->
  <button class="btn btn-danger btn-md">Delete project</button>

  <!-- ICON-ONLY (always needs aria-label) -->
  <button class="btn btn-icon btn-ghost btn-md" aria-label="More options">
    <svg width="16" height="16" fill="currentColor" aria-hidden="true">
      <circle cx="4" cy="8" r="1.5"/><circle cx="8" cy="8" r="1.5"/><circle cx="12" cy="8" r="1.5"/>
    </svg>
  </button>

  <!-- SIZES -->
  <button class="btn btn-primary btn-sm">Small</button>
  <button class="btn btn-primary btn-md">Medium</button>
  <button class="btn btn-primary btn-lg">Large</button>
</div>

<style>
/* ── Base Button ──────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: var(--font-sans);
  font-weight: 500;
  line-height: 1;
  border: 1px solid transparent;
  border-radius: var(--btn-radius, var(--radius-md));
  cursor: pointer;
  transition:
    background-color var(--transition-hover),
    box-shadow       var(--transition-hover),
    border-color     var(--transition-hover),
    transform        var(--duration-instant, 80ms) ease;
  outline: none;
  text-decoration: none;
  white-space: nowrap;
  user-select: none;
}

/* ── Sizes ────────────────────────────────────── */
.btn-sm { padding: 5px 10px; font-size: 13px; height: 30px; }
.btn-md { padding: 7px 14px; font-size: 14px; height: 36px; }
.btn-lg { padding: 9px 18px; font-size: 15px; height: 42px; }
.btn-icon { padding: 0; aspect-ratio: 1; }
.btn-icon.btn-sm { width: 30px; }
.btn-icon.btn-md { width: 36px; }
.btn-icon.btn-lg { width: 42px; }

/* ── Variants ─────────────────────────────────── */
.btn-primary {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
}
.btn-primary:hover:not(:disabled):not([data-loading]) {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

.btn-secondary {
  background: var(--color-bg-subtle);
  color: var(--color-text-primary);
  border-color: var(--color-border);
}
.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-muted);
  border-color: var(--color-border-strong);
}

.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
}
.btn-ghost:hover:not(:disabled) {
  background: var(--color-bg-subtle);
  color: var(--color-text-primary);
}

.btn-danger {
  background: var(--color-error);
  color: #fff;
  border-color: var(--color-error);
}
.btn-danger:hover:not(:disabled) {
  filter: brightness(0.9);
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

/* ── States ───────────────────────────────────── */
.btn:active:not(:disabled):not([data-loading]) {
  transform: translateY(1px);
  box-shadow: none !important;
}

/* Focus — NEVER remove this */
.btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
.btn-danger:focus-visible {
  box-shadow: 0 0 0 3px var(--color-error)33;
}

.btn:disabled,
.btn[aria-disabled="true"] {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Loading state */
.btn[data-loading] {
  cursor: default;
  pointer-events: none;
  position: relative;
  color: transparent !important;
}
.btn[data-loading] .btn-label { opacity: 0; }
.btn-spinner {
  position: absolute;
  width: 14px; height: 14px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  opacity: 1;
  color: #fff;  /* matches primary button text */
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .btn { transition: none; }
  .btn-spinner { animation: none; opacity: 0.7; }
}
</style>
'''


def scaffold_input(theme: str, framework: str) -> str:
    return '''\
<!-- ══════════════════════════════════════════════
     INPUT COMPONENT — All States
     ══════════════════════════════════════════════ -->

<!-- Default + Hover + Focus + Error + Disabled -->
<div class="fields-demo">

  <!-- Standard text input -->
  <div class="field">
    <label class="field-label" for="name-input">
      Full name
      <span class="field-required" aria-hidden="true">*</span>
    </label>
    <input
      class="input"
      id="name-input"
      type="text"
      placeholder="Sarah Johnson"
      aria-required="true"
      aria-describedby="name-helper"
      autocomplete="name"
    />
    <p class="field-helper" id="name-helper">
      As it appears on your ID document.
    </p>
  </div>

  <!-- Error state -->
  <div class="field is-error">
    <label class="field-label" for="email-input">Email address</label>
    <input
      class="input"
      id="email-input"
      type="email"
      value="not-an-email"
      aria-invalid="true"
      aria-describedby="email-error"
    />
    <p class="field-error" id="email-error" role="alert">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
        <path d="M6 0C2.69 0 0 2.69 0 6s2.69 6 6 6 6-2.69 6-6S9.31 0 6 0zm.75 9H5.25V7.5h1.5V9zm0-3H5.25V3h1.5v3z"/>
      </svg>
      Please enter a valid email address.
    </p>
  </div>

  <!-- Password with show/hide -->
  <div class="field">
    <label class="field-label" for="password-input">Password</label>
    <div class="input-wrapper">
      <input
        class="input input-with-suffix"
        id="password-input"
        type="password"
        placeholder="At least 8 characters"
        aria-describedby="password-helper"
        autocomplete="new-password"
      />
      <button
        class="input-suffix-btn"
        type="button"
        aria-label="Show password"
        aria-controls="password-input"
        onclick="togglePassword(this)"
      >
        <!-- Eye icon SVG -->
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7z"/>
          <circle cx="12" cy="12" r="3"/>
        </svg>
      </button>
    </div>
    <p class="field-helper" id="password-helper">Min 8 characters with one uppercase and one number.</p>
  </div>

  <!-- Disabled -->
  <div class="field">
    <label class="field-label" for="disabled-input">Organization</label>
    <input
      class="input"
      id="disabled-input"
      type="text"
      value="Acme Corporation"
      disabled
      aria-disabled="true"
      title="Contact your admin to change organization name"
    />
    <p class="field-helper">Contact your admin to change this. <a href="/support">Get help</a></p>
  </div>

</div>

<style>
/* ── Field wrapper ──────────────────────────────── */
.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  line-height: 1.4;
}
.field-required { color: var(--color-error); margin-left: 2px; font-weight: 400; }
.field-helper {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
}
.field-error {
  font-size: 12px;
  color: var(--color-error);
  display: flex;
  align-items: center;
  gap: 4px;
  line-height: 1.4;
}

/* ── Input base ─────────────────────────────────── */
.input {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  font-family: var(--font-sans);
  color: var(--color-text-primary);
  background: var(--color-bg-base);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  outline: none;
  transition:
    border-color var(--transition-hover),
    box-shadow   var(--transition-hover),
    background   var(--transition-hover);
  -webkit-appearance: none;
}
.input::placeholder { color: var(--color-text-tertiary); }

/* Hover (not focused, not disabled) */
.input:hover:not(:focus):not(:disabled) {
  border-color: var(--color-border-strong);
  background: var(--color-bg-subtle);
}

/* Focus */
.input:focus {
  border-color: var(--color-border-focus);
  box-shadow: var(--shadow-focus);
}

/* Error state */
.field.is-error .input,
.input[aria-invalid="true"] {
  border-color: var(--color-error);
  background: var(--color-error-subtle);
}
.field.is-error .input:focus,
.input[aria-invalid="true"]:focus {
  box-shadow: var(--shadow-focus-error);
}

/* Disabled */
.input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-bg-muted);
}

/* ── Input with suffix (password toggle) ──────── */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-suffix { padding-right: 40px; }
.input-suffix-btn {
  position: absolute;
  right: 8px;
  padding: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-tertiary);
  border-radius: var(--radius-sm);
  transition: color var(--transition-hover);
  display: flex;
}
.input-suffix-btn:hover { color: var(--color-text-secondary); }
.input-suffix-btn:focus-visible {
  outline: none;
  box-shadow: var(--shadow-focus);
}
</style>

<script>
function togglePassword(btn) {
  const input = document.getElementById(btn.getAttribute('aria-controls'));
  const isHidden = input.type === 'password';
  input.type = isHidden ? 'text' : 'password';
  btn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
}
</script>
'''


def scaffold_stat_card(theme: str, framework: str) -> str:
    return '''\
<!-- ══════════════════════════════════════════════
     STAT CARD (KPI) COMPONENT
     Includes: value, label, trend delta, sparkline
     ══════════════════════════════════════════════ -->

<div class="stat-cards">

  <!-- Positive trend -->
  <div class="stat-card">
    <div class="stat-header">
      <span class="stat-label">Monthly Revenue</span>
      <div class="stat-badge stat-badge-positive">+12.4%</div>
    </div>
    <div class="stat-value">$84,291</div>
    <div class="stat-delta stat-delta-positive" aria-label="Up 12.4% vs last month">
      <svg class="stat-delta-icon" width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
        <path d="M7 2L12 9H2L7 2Z"/>
      </svg>
      <span>+$9,312 vs last month</span>
    </div>
  </div>

  <!-- Negative trend -->
  <div class="stat-card">
    <div class="stat-header">
      <span class="stat-label">Churn Rate</span>
    </div>
    <div class="stat-value">2.8%</div>
    <div class="stat-delta stat-delta-negative" aria-label="Up 0.3 points vs last month. Negative trend.">
      <svg class="stat-delta-icon" width="14" height="14" viewBox="0 0 14 14" fill="currentColor" aria-hidden="true">
        <path d="M7 12L2 5H12L7 12Z"/>
      </svg>
      <span>+0.3pts vs last month</span>
    </div>
  </div>

  <!-- Neutral / loading -->
  <div class="stat-card stat-card-loading" aria-busy="true" aria-label="Loading active users">
    <div class="stat-header">
      <span class="stat-label">Active Users</span>
    </div>
    <div class="skeleton skeleton-title" style="width: 120px;"></div>
    <div class="skeleton skeleton-text" style="width: 160px; margin-top: 8px;"></div>
  </div>

</div>

<style>
/* ── Stat Card ──────────────────────────────────── */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

.stat-card {
  padding: 20px 24px;
  background: var(--card-bg, var(--color-bg-base));
  border: 1px solid var(--card-border, var(--color-border));
  border-radius: var(--card-radius, var(--radius-lg));
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.stat-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  line-height: 1.3;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.1;
  /* ALWAYS use tabular nums for financial/metric data */
  font-variant-numeric: tabular-nums;
  font-family: var(--font-mono, var(--font-sans));
}

/* Delta (trend indicator) */
.stat-delta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.3;
}
/* CRITICAL: Use color AND icon/text for colorblind accessibility */
.stat-delta-positive { color: var(--color-success); }
.stat-delta-negative { color: var(--color-error); }
.stat-delta-neutral  { color: var(--color-text-tertiary); }

.stat-delta-icon { flex-shrink: 0; }

/* Badge in header */
.stat-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}
.stat-badge-positive {
  background: var(--color-success-subtle);
  color: var(--color-success);
}
.stat-badge-negative {
  background: var(--color-error-subtle);
  color: var(--color-error);
}

/* Loading skeleton */
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
.skeleton-title { height: 32px; }
.skeleton-text  { height: 14px; }

@keyframes skeleton-shimmer {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}
@media (prefers-reduced-motion: reduce) {
  .skeleton { animation: none; }
}
</style>
'''


def scaffold_empty_state(theme: str, framework: str) -> str:
    return '''\
<!-- ══════════════════════════════════════════════
     EMPTY STATES — All Three Variants
     1. First-run (no data has ever existed)
     2. Zero results (filtered/searched)
     3. Error (failed to load)
     ══════════════════════════════════════════════ -->

<!-- 1. FIRST-RUN empty state -->
<div class="empty-state" role="status">
  <!-- Replace SVG with your product-relevant illustration -->
  <div class="empty-state-icon" aria-hidden="true">
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      <rect width="64" height="64" rx="16" fill="var(--color-accent-subtle)"/>
      <rect x="16" y="20" width="32" height="4" rx="2" fill="var(--color-accent)" opacity="0.4"/>
      <rect x="16" y="28" width="24" height="4" rx="2" fill="var(--color-accent)" opacity="0.3"/>
      <rect x="16" y="36" width="28" height="4" rx="2" fill="var(--color-accent)" opacity="0.2"/>
      <circle cx="48" cy="46" r="10" fill="var(--color-accent)"/>
      <path d="M44 46H52M48 42V50" stroke="white" stroke-width="2" stroke-linecap="round"/>
    </svg>
  </div>
  <h3 class="empty-state-title">Create your first project</h3>
  <p class="empty-state-description">
    Projects keep your work organized. Add tasks, collaborate with your team, and track progress in one place.
  </p>
  <div class="empty-state-actions">
    <button class="btn btn-primary btn-md">Create project</button>
    <a class="btn btn-ghost btn-md" href="/templates">Browse templates</a>
  </div>
</div>

<!-- 2. ZERO RESULTS empty state -->
<div class="empty-state" role="status">
  <div class="empty-state-icon" aria-hidden="true">
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      <circle cx="32" cy="28" r="16" stroke="var(--color-border-strong)" stroke-width="2" fill="none"/>
      <circle cx="32" cy="28" r="10" stroke="var(--color-border)" stroke-width="1.5" fill="none"/>
      <line x1="44" y1="40" x2="52" y2="50" stroke="var(--color-border-strong)" stroke-width="2" stroke-linecap="round"/>
    </svg>
  </div>
  <h3 class="empty-state-title">No results for "acme corp"</h3>
  <p class="empty-state-description">
    Try different keywords or check for typos.
  </p>
  <div class="empty-state-actions">
    <button class="btn btn-secondary btn-md" onclick="clearSearch()">Clear search</button>
    <button class="btn btn-ghost btn-md" onclick="clearFilters()">Remove all filters</button>
  </div>
</div>

<!-- 3. ERROR empty state -->
<div class="empty-state" role="alert">
  <div class="empty-state-icon empty-state-icon-error" aria-hidden="true">
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
      <circle cx="32" cy="32" r="28" stroke="var(--color-error)" stroke-width="2" fill="var(--color-error-subtle)"/>
      <path d="M32 20v14M32 40v4" stroke="var(--color-error)" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
  </div>
  <h3 class="empty-state-title">Couldn't load projects</h3>
  <p class="empty-state-description">
    There was a problem loading your data. Your work is safe — this is a temporary issue.
  </p>
  <div class="empty-state-actions">
    <button class="btn btn-primary btn-md" onclick="retry()">Try again</button>
    <a class="btn btn-ghost btn-md" href="/support">Get help</a>
  </div>
</div>

<style>
/* ── Empty State ────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 64px 24px;
  gap: 12px;
  max-width: 420px;
  margin: 0 auto;
}

.empty-state-icon {
  margin-bottom: 4px;
}

.empty-state-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.3;
  margin: 0;
}

.empty-state-description {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.55;
  max-width: 320px;
  margin: 0;
}

.empty-state-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 4px;
}
</style>
'''


def scaffold_toast(theme: str, framework: str) -> str:
    return '''\
<!-- ══════════════════════════════════════════════
     TOAST NOTIFICATION COMPONENT
     Auto-dismiss: success/info (4s), warning/error: manual
     ══════════════════════════════════════════════ -->

<div class="toast-container" role="region" aria-label="Notifications" aria-live="polite">

  <!-- Success -->
  <div class="toast toast-success" role="status">
    <div class="toast-icon" aria-hidden="true">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path fill-rule="evenodd" d="M8 1a7 7 0 100 14A7 7 0 008 1zM6.5 10.5l-2-2L5.6 7.4 6.5 8.3l3.4-3.4 1.1 1.1L6.5 10.5z"/>
      </svg>
    </div>
    <div class="toast-content">
      <p class="toast-title">Project saved</p>
      <p class="toast-description">All changes saved successfully.</p>
    </div>
    <button class="toast-close" aria-label="Dismiss notification">×</button>
  </div>

  <!-- Error (requires manual dismiss) -->
  <div class="toast toast-error" role="alert">
    <div class="toast-icon" aria-hidden="true">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path fill-rule="evenodd" d="M8 1a7 7 0 100 14A7 7 0 008 1zM7.25 4.5h1.5v5h-1.5v-5zm0 6.5h1.5v1.5h-1.5V11z"/>
      </svg>
    </div>
    <div class="toast-content">
      <p class="toast-title">Failed to save</p>
      <p class="toast-description">Check your connection and try again.</p>
    </div>
    <button class="toast-close" aria-label="Dismiss notification">×</button>
    <button class="toast-action">Retry</button>
  </div>

  <!-- Warning -->
  <div class="toast toast-warning" role="status">
    <div class="toast-icon" aria-hidden="true">⚠</div>
    <div class="toast-content">
      <p class="toast-title">Storage almost full</p>
    </div>
    <button class="toast-close" aria-label="Dismiss">×</button>
    <a class="toast-action" href="/billing">Upgrade</a>
  </div>

  <!-- Info -->
  <div class="toast toast-info" role="status">
    <div class="toast-icon" aria-hidden="true">ℹ</div>
    <div class="toast-content">
      <p class="toast-title">New version available</p>
      <p class="toast-description">Refresh to get the latest features.</p>
    </div>
    <button class="toast-action">Refresh</button>
    <button class="toast-close" aria-label="Dismiss">×</button>
  </div>

</div>

<style>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: var(--z-toast, 500);
  max-width: 360px;
  width: 100%;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  background: var(--color-bg-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  animation: toast-enter var(--duration-slow) var(--ease-expo-out) both;
}

.toast.toast-exit {
  animation: toast-exit var(--duration-normal) var(--ease-back) both;
}

.toast-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
  font-size: 13px;
}

.toast-success .toast-icon { color: var(--color-success); }
.toast-error   .toast-icon { color: var(--color-error); }
.toast-warning .toast-icon { color: var(--color-warning); }
.toast-info    .toast-icon { color: var(--color-info); }

.toast-content { flex: 1; min-width: 0; }
.toast-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin: 0;
  line-height: 1.4;
}
.toast-description {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 2px 0 0;
  line-height: 1.4;
}

.toast-close {
  flex-shrink: 0;
  padding: 2px 4px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: var(--color-text-tertiary);
  border-radius: var(--radius-sm);
  line-height: 1;
  margin-top: -1px;
  transition: color var(--transition-hover);
}
.toast-close:hover { color: var(--color-text-primary); }
.toast-close:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 1px; }

.toast-action {
  flex-shrink: 0;
  padding: 4px 10px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  text-decoration: none;
  transition: background var(--transition-hover), color var(--transition-hover);
  display: inline-flex;
  align-items: center;
}
.toast-action:hover { background: var(--color-bg-subtle); color: var(--color-text-primary); }

@keyframes toast-enter {
  from { transform: translateY(16px) scale(0.95); opacity: 0; }
  to   { transform: translateY(0)     scale(1);    opacity: 1; }
}
@keyframes toast-exit {
  from { transform: translateY(0);   opacity: 1; max-height: 200px; }
  to   { transform: translateY(8px); opacity: 0; max-height: 0; padding: 0; margin: 0; }
}

@media (max-width: 480px) {
  .toast-container { left: 12px; right: 12px; bottom: 12px; max-width: none; }
}
@media (prefers-reduced-motion: reduce) {
  .toast, .toast.toast-exit { animation: none; }
}
</style>
'''


SCAFFOLD_MAP = {
    "button": scaffold_button,
    "input": scaffold_input,
    "form-field": scaffold_input,   # alias
    "stat-card": scaffold_stat_card,
    "empty-state": scaffold_empty_state,
    "toast": scaffold_toast,
}


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a SaaS UI component with all states"
    )
    parser.add_argument("--component", "-c", help="Component to scaffold")
    parser.add_argument("--framework", "-f",
                        choices=["html", "react", "vue", "svelte"],
                        default="html",
                        help="Framework (default: html)")
    parser.add_argument("--theme", "-t",
                        default="default",
                        help="Theme preset (e.g. dark-terminal, warm-editorial)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--list", action="store_true", help="List available components")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable components:\n")
        for name, desc in COMPONENTS.items():
            print(f"  {name:<20} — {desc}")
        print()
        return

    if not args.component:
        parser.print_help()
        sys.exit(1)

    component = args.component.lower()
    if component not in SCAFFOLD_MAP:
        print(f"Component '{component}' not found. Use --list to see available components.")
        print(f"\nRequested: {component}")
        print(f"Available: {', '.join(SCAFFOLD_MAP.keys())}")
        sys.exit(1)

    scaffold_fn = SCAFFOLD_MAP[component]
    output = scaffold_fn(args.theme, args.framework)

    # Add framework wrapper if requested
    if args.framework == "react":
        component_name = "".join(w.title() for w in component.split("-"))
        output = f"""// {component_name}.jsx — Generated by component_scaffold.py
// Convert HTML+CSS to JSX: className instead of class, htmlFor instead of for

export default function {component_name}() {{
  return (
    <>
      {/* Paste HTML here, converting attributes to JSX */}
      {/* Remember: onClick not onclick, onChange not onchange */}
    </>
  );
}}

/* ── Styles (CSS Modules or styled-components) ── */
{output}
"""

    if args.output:
        from pathlib import Path
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ {component} scaffold written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
