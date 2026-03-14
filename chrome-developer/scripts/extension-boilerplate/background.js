/**
 * background.js — Extension Service Worker (MV3)
 *
 * Key rules:
 * 1. Register ALL listeners synchronously at top level
 * 2. Never use global variables for state (use chrome.storage)
 * 3. Use alarms for periodic work (not setInterval/setTimeout)
 * 4. Use offscreen documents for DOM APIs
 */

// ─────────────────────────────────────────────────────────
// LISTENER REGISTRATION (must be synchronous, top-level)
// ─────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(onInstalled);
chrome.runtime.onMessage.addListener(onMessage);
chrome.alarms.onAlarm.addListener(onAlarm);
chrome.contextMenus.onClicked.addListener(onContextMenuClicked);
chrome.action.onClicked.addListener(onActionClicked);

// ─────────────────────────────────────────────────────────
// INSTALLATION / UPGRADE
// ─────────────────────────────────────────────────────────

async function onInstalled({ reason, previousVersion }) {
  if (reason === 'install') {
    // First install: set defaults
    await chrome.storage.local.set({
      settings: { theme: 'light', notifications: true },
      version: chrome.runtime.getManifest().version,
      installDate: Date.now(),
    });

    // Set up context menu
    chrome.contextMenus.create({
      id: 'process-selection',
      title: 'Process with Extension',
      contexts: ['selection'],
    });

    // Set up periodic alarm (minimum 30s)
    chrome.alarms.create('sync', { periodInMinutes: 30 });

    console.log('[bg] Extension installed');
  }

  if (reason === 'update') {
    console.log(`[bg] Updated from ${previousVersion}`);
    await chrome.storage.local.set({
      version: chrome.runtime.getManifest().version,
    });
  }
}

// ─────────────────────────────────────────────────────────
// MESSAGE HANDLER
// ─────────────────────────────────────────────────────────

function onMessage(message, sender, sendResponse) {
  // Route to handler based on action
  const handlers = {
    getSettings: () => getSettings().then(sendResponse),
    processText: () => processText(message.text).then(sendResponse),
    openOffscreen: () => runInOffscreen(message.payload).then(sendResponse),
  };

  const handler = handlers[message.action];
  if (handler) {
    handler();
    return true; // Keep channel open for async response
  }

  // Ignore messages from offscreen doc meant for other targets
  if (message.target && message.target !== 'background') return;
}

// ─────────────────────────────────────────────────────────
// STORAGE HELPERS
// ─────────────────────────────────────────────────────────

async function getSettings() {
  const { settings = {} } = await chrome.storage.local.get('settings');
  return settings;
}

async function updateSettings(updates) {
  const current = await getSettings();
  await chrome.storage.local.set({ settings: { ...current, ...updates } });
}

// ─────────────────────────────────────────────────────────
// OFFSCREEN DOCUMENT
// ─────────────────────────────────────────────────────────

let creatingOffscreen = null;

async function ensureOffscreenDocument() {
  const url = chrome.runtime.getURL('offscreen.html');
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [url],
  });

  if (contexts.length > 0) return;

  if (creatingOffscreen) {
    await creatingOffscreen;
    return;
  }

  creatingOffscreen = chrome.offscreen.createDocument({
    url: 'offscreen.html',
    reasons: ['DOM_PARSER'],
    justification: 'Parse HTML content from clipboard/network',
  });
  await creatingOffscreen;
  creatingOffscreen = null;
}

async function runInOffscreen(payload) {
  await ensureOffscreenDocument();
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      { target: 'offscreen', action: 'process', payload },
      (response) => {
        if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
        else resolve(response);
      }
    );
  });
}

// ─────────────────────────────────────────────────────────
// ALARM HANDLER
// ─────────────────────────────────────────────────────────

async function onAlarm({ name }) {
  console.log(`[bg] Alarm fired: ${name}`);

  if (name === 'sync') {
    await performSync();
  }
}

async function performSync() {
  const { lastSync } = await chrome.storage.local.get('lastSync');
  const now = Date.now();

  // Only sync if more than 25 minutes have passed (alarm can fire early)
  if (lastSync && now - lastSync < 25 * 60 * 1000) return;

  try {
    // Your sync logic here
    console.log('[bg] Syncing...');
    await chrome.storage.local.set({ lastSync: now });
  } catch (error) {
    console.error('[bg] Sync failed:', error);
  }
}

// ─────────────────────────────────────────────────────────
// CONTEXT MENU
// ─────────────────────────────────────────────────────────

async function onContextMenuClicked({ menuItemId, selectionText }, tab) {
  if (menuItemId !== 'process-selection') return;
  if (!selectionText) return;

  const result = await processText(selectionText);

  // Show notification with result
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'Result',
    message: result.summary || 'Processing complete',
  });
}

// ─────────────────────────────────────────────────────────
// ACTION BUTTON
// ─────────────────────────────────────────────────────────

async function onActionClicked(tab) {
  // When action has no popup, this fires; with popup defined, popup opens instead.
  console.log('[bg] Action clicked on tab:', tab.id);
}

// ─────────────────────────────────────────────────────────
// CORE LOGIC
// ─────────────────────────────────────────────────────────

async function processText(text) {
  // Example: Use Chrome Built-in AI if available
  if ('LanguageModel' in globalThis) {
    const status = await LanguageModel.availability();
    if (status === 'available') {
      const session = await LanguageModel.create({
        systemPrompt: 'Summarize text in one sentence.',
      });
      try {
        const summary = await session.prompt(text.slice(0, 2000));
        return { summary, source: 'local-ai' };
      } finally {
        session.destroy();
      }
    }
  }

  // Fallback: simple word count
  const wordCount = text.split(/\s+/).filter(Boolean).length;
  return { summary: `${wordCount} words`, source: 'fallback' };
}
