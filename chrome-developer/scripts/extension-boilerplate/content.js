/**
 * content.js — Content Script
 *
 * Runs in an ISOLATED JavaScript world on web pages.
 * Has DOM access but cannot read page's JS variables.
 * Use chrome.runtime.sendMessage to communicate with background.
 */

// ─────────────────────────────────────────────────────────
// INITIALIZATION
// ─────────────────────────────────────────────────────────

(async function init() {
  // Listen for messages from background
  chrome.runtime.onMessage.addListener(onBackgroundMessage);

  // Listen for messages from the page (if needed — ISOLATED ↔ MAIN world bridge)
  window.addEventListener('message', onPageMessage);

  console.log('[content] Loaded on:', window.location.hostname);
})();

// ─────────────────────────────────────────────────────────
// MESSAGE HANDLERS
// ─────────────────────────────────────────────────────────

function onBackgroundMessage(message, sender, sendResponse) {
  if (message.action === 'highlight') {
    highlightElements(message.selector);
    sendResponse({ success: true });
  }

  if (message.action === 'extractContent') {
    const content = extractPageContent();
    sendResponse({ content });
  }

  return true; // async
}

function onPageMessage(event) {
  // Security: only accept messages from the same window
  if (event.source !== window) return;
  if (!event.data?.extensionBridge) return;

  // Relay page→extension messages
  chrome.runtime.sendMessage(event.data.payload);
}

// ─────────────────────────────────────────────────────────
// DOM UTILITIES
// ─────────────────────────────────────────────────────────

function highlightElements(selector) {
  document.querySelectorAll(selector).forEach((el) => {
    el.style.outline = '2px solid #4285f4';
    el.style.outlineOffset = '2px';
  });
}

function extractPageContent() {
  return {
    title: document.title,
    url: window.location.href,
    text: document.body.innerText.slice(0, 10000),
    metaDescription: document.querySelector('meta[name="description"]')?.content,
    h1s: [...document.querySelectorAll('h1')].map((el) => el.textContent.trim()),
  };
}

// ─────────────────────────────────────────────────────────
// EXAMPLE: SEND PAGE CONTENT TO BACKGROUND FOR AI PROCESSING
// ─────────────────────────────────────────────────────────

async function processCurrentPage() {
  const content = extractPageContent();

  const result = await chrome.runtime.sendMessage({
    action: 'processText',
    text: content.text,
  });

  return result;
}
