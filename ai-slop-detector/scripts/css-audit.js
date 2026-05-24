#!/usr/bin/env node
/**
 * css-audit.js — AI Slop UI/CSS Pattern Detector
 *
 * Usage:
 *   node css-audit.js <file.css|.html|.jsx|.tsx>
 *   node css-audit.js --dir ./src
 *   node css-audit.js --json <file>
 */

const fs = require('fs');
const path = require('path');

const RULES = [
  // Colors
  { re: /#6366f1|indigo-500|rgb\(99,?\s*102,?\s*241/gi, cat:'Color', sev:'critical', name:'Tailwind indigo-500 (the purple AI default)', fix:'Define brand-specific primary color. This is the #1 AI UI tell.' },
  { re: /#7c3aed|violet-600|#8b5cf6|violet-500/gi, cat:'Color', sev:'critical', name:'Tailwind violet (AI button default)', fix:'Replace with a brand-specific accent color.' },
  { re: /from-indigo-\d+.{0,10}to-(purple|violet)-\d+/gi, cat:'Color', sev:'critical', name:'Indigo-to-purple gradient (most recognizable AI pattern)', fix:'The #1 visual AI fingerprint. Replace with brand colors.' },
  { re: /linear-gradient\([^)]*(?:#6366f1|#8b5cf6|#7c3aed)[^)]*\)/gi, cat:'Color', sev:'critical', name:'Purple gradient in linear-gradient()', fix:'Use a brand-appropriate gradient or flat color.' },
  { re: /bg-clip-text.*text-transparent|background-clip:\s*text/gi, cat:'Color', sev:'medium', name:'Gradient headline text (overused AI hero pattern)', fix:'Gradient text is a 2022-era trend. Use typographic weight/size for hierarchy instead.' },

  // Typography
  { re: /font-family:\s*['"]?Inter['"]?/gi, cat:'Typography', sev:'high', name:'Inter font (AI default — 80%+ of AI UIs use this)', fix:'Choose a distinctive font appropriate to brand context. See references/ui-slop.md §3.' },
  { re: /font-family:\s*['"]?Roboto['"]?/gi, cat:'Typography', sev:'high', name:'Roboto font (AI default)', fix:'Use a more distinctive typeface.' },
  { re: /font-family:\s*['"]?(?:Open Sans|DM Sans)['"]?/gi, cat:'Typography', sev:'medium', name:'Open Sans / DM Sans (common AI defaults)', fix:'Choose context-appropriate, distinctive typography.' },
  { re: /system-ui,\s*-apple-system|BlinkMacSystemFont/gi, cat:'Typography', sev:'medium', name:'System UI font stack (pure AI default — no brand)', fix:'Import a web font that reflects your brand identity.' },
  { re: /'Inter',?\s*sans-serif/gi, cat:'Typography', sev:'high', name:'Inter as sans-serif fallback', fix:'Replace with a brand font from Google Fonts or a type foundry.' },

  // Layout
  { re: /grid-cols-3|grid-template-columns:\s*repeat\(\s*3/gi, cat:'Layout', sev:'medium', name:'3-column equal grid (the AI feature card layout)', fix:'Use asymmetric layouts: one primary cell (7/12) + two secondary (5/12).' },
  { re: /rounded-2xl|rounded-3xl|border-radius:\s*(?:1\.5|2)rem/gi, cat:'Layout', sev:'low', name:'Excessive rounding (rounded-2xl/3xl on everything)', fix:'Pick one consistent radius. Sharp corners can signal precision; full pill only for brand.' },
  { re: /items-center.*text-center|text-center.*items-center/gi, cat:'Layout', sev:'low', name:'Centered hero layout (AI landing page default)', fix:'Left-aligned or off-center layouts feel more intentional and human.' },
  { re: /flex-col.*items-center.*py-\d{2}/gi, cat:'Layout', sev:'medium', name:'Centered flex column hero section pattern', fix:'Consider asymmetric layout: headline left, visual right.' },

  // CSS Quality
  { re: /transition:\s*all\s+[\d.]+s/gi, cat:'CSS Quality', sev:'medium', name:'transition: all (causes perf issues, animates unexpected properties)', fix:'Be specific: transition: background-color 150ms ease, transform 200ms ease' },
  { re: /className=\{[^}]+\}\s+style=\{|style=\{[^}]+\}\s+className=/g, cat:'CSS Quality', sev:'medium', name:'Mixing Tailwind classes + inline styles (AI copout)', fix:'Pick one system. Use CSS custom properties for dynamic values with Tailwind.' },
  { re: /shadow-(?:sm|md|lg|xl|2xl)[^\s"']*.*shadow-(?:sm|md|lg|xl|2xl)/g, cat:'CSS Quality', sev:'medium', name:'Inconsistent shadow scale across components', fix:'Define 3 shadow levels as CSS custom properties and apply consistently.' },
  { re: /@keyframes\s+fadeIn/gi, cat:'Animation', sev:'low', name:'Generic fadeIn animation (applied to everything)', fix:'Animations need a purpose. One coordinated page entrance > 20 scattered fades.' },
  { re: /\bstyle=\{\{[^}]*backgroundColor:\s*['"]#(?:6366f1|7c3aed|8b5cf6)/gi, cat:'Color', sev:'high', name:'Purple color hardcoded in inline style', fix:'Use design tokens / CSS variables. Replace with brand color.' },

  // Missing states (heuristic — flag if no loading/error patterns found in component)
];

const MISSING_STATE_CHECKS = [
  { pattern: /loading|isLoading|skeleton|Skeleton/i, name: 'Loading state' },
  { pattern: /error|isError|catch|Error/i, name: 'Error state' },
  { pattern: /empty|isEmpty|EmptyState|no items|no data/i, name: 'Empty state' },
  { pattern: /:focus|onFocus|focus-visible/i, name: 'Focus/accessibility state' },
];

function scanFile(content, filename) {
  const issues = [];
  for (const rule of RULES) {
    const m = content.match(rule.re) || [];
    if (m.length) issues.push({ ...rule, count: m.length, examples: m.slice(0,2) });
  }

  // Check for missing states in interactive component files
  if (/\.(jsx|tsx|html)$/.test(filename)) {
    const hasInteraction = /onClick|onChange|onSubmit|fetch\(|useQuery|useMutation|useForm/.test(content);
    if (hasInteraction) {
      for (const { pattern, name } of MISSING_STATE_CHECKS) {
        if (!pattern.test(content)) {
          issues.push({ cat: 'Missing States', sev: 'medium', name: `Missing: ${name}`, fix: `Add ${name.toLowerCase()} to handle all component states.`, count: 1 });
        }
      }
    }
  }

  const SEV = { critical: 10, high: 5, medium: 2, low: 1 };
  const score = issues.reduce((s, i) => s + (SEV[i.sev] || 1) * Math.min(i.count, 5), 0);
  const density = score === 0 ? 'Clean' : score < 8 ? 'Low' : score < 20 ? 'Medium' : score < 45 ? 'High' : 'Severe';

  return { filename, issues, score, density };
}

function report(r) {
  const R='\x1b[0m',RED='\x1b[31m',YEL='\x1b[33m',GRN='\x1b[32m',B='\x1b[1m',D='\x1b[2m',C='\x1b[36m';
  const dc={Clean:GRN,Low:GRN,Medium:YEL,High:RED,Severe:RED+B}[r.density];
  let o = `\n${B}═══ UI Slop Audit: ${r.filename} ═══${R}\n`;
  o += `${r.issues.length} issues | Score: ${r.score} | Density: ${dc}${r.density}${R}\n\n`;
  const byCat = {};
  for (const i of r.issues) { (byCat[i.cat] = byCat[i.cat] || []).push(i); }
  const icon = { critical:'🚨', high:'🔴', medium:'🟡', low:'🟢' };
  const sevOrd = ['critical','high','medium','low'];
  for (const [cat, items] of Object.entries(byCat)) {
    o += `${C}${B}${cat}${R}\n`;
    for (const i of items.sort((a,b)=>sevOrd.indexOf(a.sev)-sevOrd.indexOf(b.sev))) {
      o += `  ${icon[i.sev]||'•'} ${i.name}${i.count>1?` ×${i.count}`:''}\n`;
      if (i.examples?.length) o += `    ${D}Found: ${i.examples.map(e=>`"${e}"`).join(', ')}${R}\n`;
      o += `    ${D}→ ${i.fix}${R}\n`;
    }
    o += '\n';
  }
  const top = r.issues.sort((a,b)=>sevOrd.indexOf(a.sev)-sevOrd.indexOf(b.sev)).slice(0,3);
  if (top.length) { o+=`${B}Priority Fixes:${R}\n`; top.forEach((f,i)=>o+=`  ${i+1}. [${f.sev}] ${f.name}\n     ${D}${f.fix}${R}\n`); }
  return o;
}

function walk(dir, exts=['.css','.html','.jsx','.tsx','.js','.ts','.vue','.svelte']) {
  const files=[];
  for (const e of fs.readdirSync(dir,{withFileTypes:true})) {
    if (e.isDirectory()&&!['node_modules','.git','dist','build','.next'].includes(e.name)) walk(path.join(dir,e.name),exts).forEach(f=>files.push(f));
    else if (e.isFile()&&exts.some(x=>e.name.endsWith(x))) files.push(path.join(dir,e.name));
  }
  return files;
}

function main() {
  const args = process.argv.slice(2);
  const json = args.includes('--json');
  const dir = args.includes('--dir');
  const target = args.find(a=>!a.startsWith('--'));
  if (!target) { console.error('Usage: node css-audit.js <file>  OR  node css-audit.js --dir ./src'); process.exit(1); }
  const files = dir ? walk(target) : [target];
  const results = files.map(f => { try { return scanFile(fs.readFileSync(f,'utf8'),f); } catch(e) { return null; } }).filter(Boolean);
  if (json) { console.log(JSON.stringify(results,null,2)); }
  else {
    for (const r of results.filter(r=>r.issues.length)) console.log(report(r));
    if (dir) {
      const total=results.reduce((s,r)=>s+r.issues.length,0), hi=results.filter(r=>['High','Severe'].includes(r.density)).length;
      console.log(`\n\x1b[1mSummary: ${files.length} files | ${total} issues | ${hi} high/severe\x1b[0m`);
    }
  }
  process.exit(results.some(r=>['High','Severe'].includes(r.density))?1:0);
}
main();
