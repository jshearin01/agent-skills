# Chrome Extensions Manifest V3 — Complete Reference

## Table of Contents
1. [Manifest Structure](#1-manifest-structure)
2. [Permissions Reference](#2-permissions-reference)
3. [Service Worker Patterns](#3-service-worker-patterns)
4. [Storage API Comparison](#4-storage-api-comparison)
5. [Content Scripts](#5-content-scripts)
6. [Message Passing](#6-message-passing)
7. [Offscreen Documents](#7-offscreen-documents)
8. [declarativeNetRequest](#8-declarativenetrequest)
9. [Native Messaging](#9-native-messaging)
10. [Side Panel API](#10-side-panel-api)
11. [Extension Service Worker Lifecycle](#11-extension-service-worker-lifecycle)
12. [Content Security Policy](#12-content-security-policy)
13. [Testing Extensions](#13-testing-extensions)
14. [Chrome Web Store Publishing](#14-chrome-web-store-publishing)

---

## 1. Manifest Structure

### Complete Manifest V3 Template

```json
{
  "manifest_version": 3,
  "name": "Extension Name",
  "version": "1.0.0",
  "description": "Extension description (max 132 chars)",
  "minimum_chrome_version": "116",

  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },

  "permissions": [
    "storage",
    "alarms",
    "tabs",
    "activeTab",
    "scripting",
    "offscreen",
    "sidePanel",
    "contextMenus",
    "notifications",
    "identity"
  ],

  "host_permissions": [
    "https://*.example.com/*",
    "<all_urls>"
  ],

  "optional_permissions": ["bookmarks", "history"],
  "optional_host_permissions": ["https://*/*"],

  "background": {
    "service_worker": "background.js",
    "type": "module"
  },

  "content_scripts": [
    {
      "matches": ["https://*.example.com/*"],
      "js": ["content.js"],
      "css": ["content.css"],
      "run_at": "document_idle",
      "all_frames": false,
      "world": "ISOLATED"
    }
  ],

  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png"
    },
    "default_title": "Click to open"
  },

  "options_page": "options.html",

  "side_panel": {
    "default_path": "sidepanel.html"
  },

  "declarative_net_request": {
    "rule_resources": [{
      "id": "ruleset_1",
      "enabled": true,
      "path": "rules.json"
    }]
  },

  "web_accessible_resources": [{
    "resources": ["images/*.png", "fonts/*.woff2"],
    "matches": ["<all_urls>"]
  }],

  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

---

## 2. Permissions Reference

### API Permissions (declare in `"permissions"`)

| Permission | Grants Access To |
|-----------|-----------------|
| `storage` | `chrome.storage.*` |
| `alarms` | `chrome.alarms.*` |
| `tabs` | Full tab URL/title access; `chrome.tabs.*` |
| `activeTab` | Temporary access to the active tab (triggered by user gesture) |
| `scripting` | `chrome.scripting.executeScript()` |
| `offscreen` | `chrome.offscreen.*` |
| `sidePanel` | `chrome.sidePanel.*` |
| `contextMenus` | `chrome.contextMenus.*` |
| `notifications` | `chrome.notifications.*` |
| `identity` | `chrome.identity.*` (OAuth) |
| `webNavigation` | `chrome.webNavigation.*` |
| `cookies` | `chrome.cookies.*` |
| `bookmarks` | `chrome.bookmarks.*` |
| `history` | `chrome.history.*` |
| `downloads` | `chrome.downloads.*` |
| `management` | `chrome.management.*` (other extensions) |
| `nativeMessaging` | `chrome.runtime.connectNative()` |
| `debugger` | `chrome.debugger.*` (also keeps SW alive) |
| `declarativeNetRequest` | Modify/block network requests |
| `declarativeNetRequestFeedback` | Debug DNR matching |

### Warning-Level Permissions (shown to users)

Avoid these unless required:
- `tabs` — "Read your browsing history"
- `<all_urls>` — "Read and change all your data on all websites"
- `webRequest` — "Read and change all your data on the websites you visit"
- `history` — "Read and change your browsing history"

### Using `activeTab` Instead of `tabs`

`activeTab` is granted temporarily when user interacts with the extension (clicks action button, uses context menu). No warning shown. Prefer over `tabs` when you only need the current page:

```js
chrome.action.onClicked.addListener(async (tab) => {
  // tab.url is available without "tabs" permission
  const result = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.title
  });
});
```

---

## 3. Service Worker Patterns

### Module Pattern (recommended for MV3)

```js
// background.js
import { handleMessage } from './handlers.js';
import { setupContextMenus } from './context-menus.js';

// ✅ Register all listeners at top level (synchronously)
chrome.runtime.onInstalled.addListener(onInstalled);
chrome.runtime.onMessage.addListener(handleMessage);
chrome.alarms.onAlarm.addListener(onAlarm);
chrome.tabs.onUpdated.addListener(onTabUpdated);

async function onInstalled({ reason }) {
  if (reason === 'install') {
    await chrome.storage.local.set({ version: '1.0', initialized: true });
    setupContextMenus();
  }
}

function onAlarm({ name }) {
  if (name === 'sync') performSync();
}
```

### Keeping the Service Worker Alive

```js
// Method 1: Periodic alarm (minimum 30s interval)
chrome.alarms.create('keepalive', { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(({ name }) => {
  if (name === 'keepalive') chrome.storage.local.set({ lastPing: Date.now() });
});

// Method 2: WebSocket connection (Chrome 116+)
let socket;
function connectWebSocket() {
  socket = new WebSocket('wss://your-server.com');
  socket.onclose = () => setTimeout(connectWebSocket, 5000);
}

// Method 3: Native messaging port
const port = chrome.runtime.connectNative('com.your.app');
port.onDisconnect.addListener(() => reconnect());
```

### Persisting State Across Restarts

```js
// State manager pattern
class ExtensionState {
  static async get(key) {
    const data = await chrome.storage.local.get(key);
    return data[key];
  }

  static async set(key, value) {
    await chrome.storage.local.set({ [key]: value });
  }

  static async update(key, updater) {
    const current = await this.get(key) ?? {};
    await this.set(key, updater(current));
  }
}

// Usage
await ExtensionState.set('userPrefs', { theme: 'dark', lang: 'en' });
const prefs = await ExtensionState.get('userPrefs');
```

---

## 4. Storage API Comparison

| Storage | Sync across devices | Quota | Persistence | Notes |
|---------|---------------------|-------|-------------|-------|
| `chrome.storage.local` | ❌ | 5MB (extendable to 10MB with `unlimitedStorage`) | Until cleared | Fast, recommended default |
| `chrome.storage.sync` | ✅ Chrome account | 100KB total, 8KB/item | Until cleared | Throttled writes (1800/hr) |
| `chrome.storage.session` | ❌ | 10MB | Session only | In-memory, fast |
| `chrome.storage.managed` | N/A | Enterprise policy | Read-only | Set by admins |
| `IndexedDB` | ❌ | Large (disk-based) | Until cleared | Only in popup/options/offscreen |

```js
// Storage change listener
chrome.storage.onChanged.addListener((changes, area) => {
  for (const [key, { oldValue, newValue }] of Object.entries(changes)) {
    console.log(`${area}.${key}: ${oldValue} → ${newValue}`);
  }
});

// Batch reads/writes
const { counter, user, settings } = await chrome.storage.local.get({
  counter: 0,       // default values
  user: null,
  settings: {}
});
await chrome.storage.local.set({ counter: counter + 1, lastSeen: Date.now() });
```

---

## 5. Content Scripts

### Injecting Scripts Dynamically

```js
// From background service worker
await chrome.scripting.executeScript({
  target: { tabId: tab.id, allFrames: false },
  func: (config) => {
    // This function runs in the page context
    window.__myExtConfig = config;
    document.querySelectorAll('button').forEach(btn => {
      btn.style.border = '2px solid red';
    });
  },
  args: [{ debug: true }]  // JSON-serializable only
});

// Inject CSS
await chrome.scripting.insertCSS({
  target: { tabId: tab.id },
  css: 'body { filter: invert(1); }'
});
```

### MAIN world vs ISOLATED world

```json
// manifest.json — default is ISOLATED (secure)
{
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"],
    "world": "ISOLATED"   // or "MAIN" to access page's JS globals
  }]
}
```

```js
// MAIN world — can access page's window, libraries, etc.
// ISOLATED world — separate JS context, cannot read page variables
// Use MAIN only when you need to call page's functions
```

### Content Script ↔ Page Communication

```js
// content.js (ISOLATED world) — relay messages between page and extension
window.addEventListener('message', (event) => {
  if (event.source !== window) return;
  if (event.data.source !== 'myExtension') return;
  chrome.runtime.sendMessage(event.data.payload);
});

// page.js — send to content script
window.postMessage({ source: 'myExtension', payload: { action: 'getData' } }, '*');
```

---

## 6. Message Passing

### One-time Messages

```js
// Send from content script / popup
const response = await chrome.runtime.sendMessage({ action: 'fetchData', url });

// Send to specific tab
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
await chrome.tabs.sendMessage(tab.id, { action: 'highlight', selector: '.btn' });

// Background handler (must return true for async)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'fetchData') {
    fetch(message.url)
      .then(r => r.json())
      .then(data => sendResponse({ success: true, data }))
      .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // ← CRITICAL: keeps channel open for async response
  }
});
```

### Long-lived Ports

```js
// Content script
const port = chrome.runtime.connect({ name: 'data-stream' });
port.postMessage({ type: 'subscribe', topic: 'updates' });
port.onMessage.addListener(({ type, payload }) => {
  if (type === 'update') renderUpdate(payload);
});
port.onDisconnect.addListener(() => console.log('Port disconnected'));

// Background
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== 'data-stream') return;
  
  const interval = setInterval(() => {
    port.postMessage({ type: 'update', payload: getLatestData() });
  }, 1000);
  
  port.onDisconnect.addListener(() => clearInterval(interval));
});
```

---

## 7. Offscreen Documents

### All Available Reasons

```js
const OFFSCREEN_REASONS = {
  'AUDIO_PLAYBACK': 'Play audio in background',
  'CLIPBOARD': 'Access clipboard APIs',
  'DOM_PARSER': 'Use DOMParser API',
  'DOM_SCRAPING': 'Parse/scrape HTML content',
  'IFRAME_SCRIPTING': 'Interact with iframes',
  'LOCAL_STORAGE': 'Access localStorage API',
  'MATCH_MEDIA': 'Use window.matchMedia',
  'WORKERS': 'Spawn Web Workers or SharedWorkers',
  'GEOLOCATION': 'Access navigator.geolocation',
  'BATTERY_STATUS': 'Access navigator.getBattery',
};
```

### Robust Offscreen Document Manager

```js
// offscreen-manager.js
let creating = null;

export async function ensureOffscreenDocument(path, reasons, justification) {
  const offscreenUrl = chrome.runtime.getURL(path);
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [offscreenUrl]
  });
  
  if (contexts.length > 0) return;
  
  if (creating) {
    await creating;
    return;
  }
  
  creating = chrome.offscreen.createDocument({ url: path, reasons, justification });
  await creating;
  creating = null;
}

export async function sendToOffscreen(message) {
  await ensureOffscreenDocument(
    'offscreen.html',
    ['DOM_SCRAPING'],
    'Process HTML content'
  );
  return chrome.runtime.sendMessage({ target: 'offscreen', ...message });
}
```

```js
// offscreen.js — must filter messages targeting offscreen doc
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.target !== 'offscreen') return;
  
  if (msg.action === 'parseHTML') {
    const parser = new DOMParser();
    const doc = parser.parseFromString(msg.html, 'text/html');
    const links = [...doc.querySelectorAll('a')].map(a => a.href);
    sendResponse({ links });
  }
  
  return true;
});
```

---

## 8. declarativeNetRequest

### Static Rules (bundled in extension)

```json
// rules.json
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "||ads.doubleclick.net^",
      "resourceTypes": ["script", "xmlhttprequest", "image"]
    }
  },
  {
    "id": 2,
    "priority": 2,
    "action": {
      "type": "modifyHeaders",
      "responseHeaders": [
        { "header": "X-Frame-Options", "operation": "remove" }
      ]
    },
    "condition": {
      "urlFilter": "https://example.com/*",
      "resourceTypes": ["main_frame"]
    }
  },
  {
    "id": 3,
    "priority": 1,
    "action": {
      "type": "redirect",
      "redirect": { "regexSubstitution": "https://safe.\\1" }
    },
    "condition": {
      "regexFilter": "https://unsafe\\.(.*)",
      "resourceTypes": ["main_frame"]
    }
  }
]
```

### Dynamic Rules (updated at runtime)

```js
// Add rules at runtime (max 5000 dynamic rules)
await chrome.declarativeNetRequest.updateDynamicRules({
  addRules: [
    {
      id: 1001,
      priority: 1,
      action: { type: 'block' },
      condition: {
        domains: ['tracker.example.com'],
        resourceTypes: ['xmlhttprequest']
      }
    }
  ],
  removeRuleIds: [999]  // remove old rules by ID
});

// Query matched rules (requires declarativeNetRequestFeedback permission)
const matchedRules = await chrome.declarativeNetRequest.getMatchedRules();
```

---

## 9. Native Messaging

Allows extensions to communicate with installed desktop applications.

```js
// background.js
const port = chrome.runtime.connectNative('com.mycompany.myapp');

port.onMessage.addListener((message) => {
  console.log('Native app says:', message);
});

port.onDisconnect.addListener(() => {
  if (chrome.runtime.lastError) {
    console.error('Native app disconnected:', chrome.runtime.lastError);
  }
});

port.postMessage({ action: 'readFile', path: '/home/user/data.txt' });
```

```json
// Native host manifest (installed on OS)
// macOS: ~/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.mycompany.myapp.json
{
  "name": "com.mycompany.myapp",
  "description": "My Native Messaging Host",
  "path": "/usr/local/bin/myapp",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://YOUR_EXTENSION_ID/"
  ]
}
```

---

## 10. Side Panel API

```js
// background.js
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

// Open side panel programmatically
chrome.action.onClicked.addListener(async (tab) => {
  await chrome.sidePanel.open({ tabId: tab.id });
});

// Different panel per tab
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (!tab.url) return;
  const isGithub = tab.url.startsWith('https://github.com');
  await chrome.sidePanel.setOptions({
    tabId,
    path: isGithub ? 'github-panel.html' : 'default-panel.html',
    enabled: true
  });
});
```

---

## 11. Extension Service Worker Lifecycle

### Timeline

```
Extension installed/updated
  → Service worker registered
    → SW activates (runs top-level code)
      → Browser event fires (tab opened, message received, alarm)
        → SW wakes up (if dormant)
          → Event handler runs
            → SW idles → terminates after ~30s
```

### Events that Wake the Service Worker

- `chrome.runtime.onMessage`
- `chrome.alarms.onAlarm`
- `chrome.tabs.onUpdated / onCreated / onRemoved`
- `chrome.webNavigation.*`
- `chrome.webRequest.*` (observe-only in MV3)
- `chrome.declarativeNetRequest.onRuleMatchedDebug`
- `chrome.contextMenus.onClicked`
- `chrome.action.onClicked`
- `chrome.runtime.onInstalled / onStartup`
- `chrome.notifications.onClicked`

### Service Worker Lifetime Improvements by Chrome Version

| Chrome | Improvement |
|--------|-------------|
| 110 | 5-minute keepalive for long tasks |
| 116 | WebSockets reset idle timer |
| 116 | Messages from offscreen docs reset timer |
| 120 | Active debugger sessions prevent termination |
| 120+ | Alarms minimum interval: 30 seconds |

---

## 12. Content Security Policy

```json
// Strict CSP for extension pages
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; style-src 'self' 'unsafe-inline';"
  }
}
```

**Note:** `unsafe-eval` is NOT allowed in MV3 extension pages. This means:
- No `eval()`, `new Function()`, or `setTimeout(string)`
- No remotely-hosted scripts
- All scripts must be in the extension package

For content scripts injected into pages, the page's CSP applies.

---

## 13. Testing Extensions

### With Puppeteer

```js
import puppeteer from 'puppeteer';
import path from 'path';

const extensionPath = path.resolve('./extension');
const browser = await puppeteer.launch({
  headless: false,  // Extensions require headed mode (or new headless)
  args: [
    `--disable-extensions-except=${extensionPath}`,
    `--load-extension=${extensionPath}`,
  ]
});

// Get extension ID
const targets = await browser.targets();
const extTarget = targets.find(t => t.type() === 'service_worker');
const extUrl = extTarget.url();
const extId = extUrl.split('/')[2];

// Open extension popup
const popupPage = await browser.newPage();
await popupPage.goto(`chrome-extension://${extId}/popup.html`);

// Interact with popup
await popupPage.click('#submit-btn');
const text = await popupPage.$eval('#result', el => el.textContent);
expect(text).toBe('Success');
```

### Service Worker Testing

```js
// Test service worker message handling
const swTarget = await browser.waitForTarget(
  t => t.url().includes('background.js')
);
const swPage = await swTarget.worker();

// Send a message to the service worker
const result = await swPage.evaluate(async () => {
  return new Promise(resolve => {
    chrome.runtime.sendMessage({ action: 'test' }, resolve);
  });
});
```

### Unit Testing with Jest (mock chrome APIs)

```js
// jest.setup.js
global.chrome = {
  storage: {
    local: {
      get: jest.fn().mockResolvedValue({}),
      set: jest.fn().mockResolvedValue(),
    }
  },
  runtime: {
    sendMessage: jest.fn(),
    onMessage: { addListener: jest.fn() }
  }
};
```

---

## 14. Chrome Web Store Publishing

### Pre-submission Checklist

- [ ] `manifest.json` has unique name and description
- [ ] All permissions justified in privacy policy
- [ ] No remotely-hosted code (CSP enforced)
- [ ] Icons: 16, 32, 48, 128px PNG
- [ ] Store listing: at least 1280×800 screenshot
- [ ] Privacy policy URL set (required for extensions that handle personal data)
- [ ] Single purpose clearly stated
- [ ] Version bumped for updates

### Packaging

```bash
# Create ZIP excluding dev files
zip -r extension.zip . \
  --exclude='.git*' \
  --exclude='node_modules/*' \
  --exclude='*.test.js' \
  --exclude='package*.json' \
  --exclude='*.md'
```

### Review Process

1. Automated scan: malware, policy violations
2. Manual review: 1-3 business days for new extensions, faster for updates
3. Common rejection reasons:
   - Requesting unnecessary permissions
   - Misleading description
   - Using `eval()` or remote code
   - Policy violations in content
