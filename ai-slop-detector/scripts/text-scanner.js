#!/usr/bin/env node
/**
 * text-scanner.js — AI Slop Text Scanner
 *
 * Usage:
 *   node text-scanner.js <file.txt>
 *   echo "some text" | node text-scanner.js
 *   node text-scanner.js --json <file.txt>
 */

const fs = require('fs');

const TIER1 = ['delve','delving','tapestry','testament','meticulous','meticulously',
  'pivotal','underscore','underscores','intricate','intricacies','vibrant','garner',
  'garnered','bolster','bolstered','robust','leverage','leveraging','revolutionize',
  'transformative','groundbreaking','comprehensive','multifaceted','nuanced',
  'synergy','synergize','spearhead','harness','empower','foster'];

const TIER2 = ['furthermore','moreover','additionally','consequently','notably',
  'indeed','thus','thereby','hence'];

const TIER3 = ['crucial','essential','significant','enhance','optimize',
  'innovative','impactful','actionable','scalable','seamless','streamline'];

const PHRASES = [
  { re: /in today.s fast[- ]paced/gi, name: 'Grandiose opener: "fast-paced world"', tier: 1 },
  { re: /in (the )?(ever[- ])?(evolving|changing|shifting) (landscape|world|era)/gi, name: 'Evolving landscape opener', tier: 1 },
  { re: /at the (fore)?front of/gi, name: '"At the forefront of"', tier: 1 },
  { re: /not just .{1,30}, but/gi, name: 'AI contrast: "not just X, but Y"', tier: 1 },
  { re: /more than just/gi, name: 'AI contrast: "more than just"', tier: 1 },
  { re: /it.s (important|crucial|essential|worth noting|worth mentioning)/gi, name: 'Over-hedge: "it\'s important/worth noting"', tier: 1 },
  { re: /that being said/gi, name: 'AI filler: "that being said"', tier: 2 },
  { re: /in (summary|conclusion)[,:]/gi, name: 'AI structure: "in summary/conclusion"', tier: 2 },
  { re: /unlock (the )?(full |true )?(power|potential)/gi, name: 'AI marketing: "unlock potential"', tier: 1 },
  { re: /harness the power of/gi, name: 'AI marketing: "harness the power"', tier: 1 },
  { re: /embark on a (journey|path)/gi, name: 'AI marketing: "embark on a journey"', tier: 1 },
  { re: /pave the way/gi, name: 'AI marketing: "pave the way"', tier: 1 },
  { re: /navigate (the )?complexit/gi, name: 'AI marketing: "navigate complexities"', tier: 1 },
  { re: /active social media presence/gi, name: 'AI filler: "active social media presence"', tier: 1 },
  { re: /revolutionize the way/gi, name: 'AI hyperbole: "revolutionize the way"', tier: 1 },
  { re: /game[- ]chang(er|ing)/gi, name: 'AI hyperbole: "game-changer"', tier: 1 },
  { re: /world[- ]class/gi, name: 'Hollow superlative: "world-class"', tier: 2 },
  { re: /best[- ]in[- ]class/gi, name: 'Hollow superlative: "best-in-class"', tier: 2 },
  { re: /industry[- ]leading/gi, name: 'Hollow superlative: "industry-leading"', tier: 2 },
  { re: /unparalleled/gi, name: 'Hollow superlative: "unparalleled"', tier: 2 },
  { re: /cutting[- ]edge/gi, name: 'AI cliché: "cutting-edge"', tier: 1 },
  { re: /at the intersection of/gi, name: 'AI phrase: "at the intersection of"', tier: 2 },
];

function scanText(text) {
  const words = text.toLowerCase().split(/\W+/);
  const wordCount = words.length;
  const results = { tier1: [], tier2: [], tier3: [], phrases: [], structural: [], score: 0 };

  for (const w of TIER1) {
    const m = text.match(new RegExp(`\\b${w}s?\\b`, 'gi')) || [];
    if (m.length) { results.tier1.push({ word: w, count: m.length }); results.score += m.length * 3; }
  }
  for (const w of TIER2) {
    const m = text.match(new RegExp(`\\b${w}\\b`, 'gi')) || [];
    if (m.length) { results.tier2.push({ word: w, count: m.length }); results.score += m.length * 2; }
  }
  for (const w of TIER3) {
    const m = text.match(new RegExp(`\\b${w}\\b`, 'gi')) || [];
    if (m.length > 1) { results.tier3.push({ word: w, count: m.length }); results.score += m.length; }
  }
  for (const { re, name, tier } of PHRASES) {
    const m = text.match(re) || [];
    if (m.length) { results.phrases.push({ name, count: m.length, tier, examples: m.slice(0, 2) }); results.score += m.length * (tier === 1 ? 4 : 2); }
  }

  // Structural: passive voice density
  const passive = (text.match(/\b(is|are|was|were|been)\s+\w+ed\b/gi) || []).length;
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 10).length;
  if (passive / Math.max(sentences, 1) > 1.5) {
    results.structural.push({ name: 'High passive voice density', detail: `~${passive} passive constructions` });
    results.score += 5;
  }

  // Low burstiness
  const sentLengths = text.split(/[.!?]+/).filter(s => s.trim().length > 10).map(s => s.trim().split(/\s+/).length);
  if (sentLengths.length > 8) {
    const avg = sentLengths.reduce((a, b) => a + b, 0) / sentLengths.length;
    const sd = Math.sqrt(sentLengths.reduce((s, l) => s + (l - avg) ** 2, 0) / sentLengths.length);
    if (sd < 5) { results.structural.push({ name: 'Low sentence burstiness (uniform length)', detail: `StdDev: ${sd.toFixed(1)} words` }); results.score += 4; }
    if (!sentLengths.some(l => l < 8)) { results.structural.push({ name: 'No short sentences found', detail: 'Human writing includes punchy short sentences' }); results.score += 3; }
  }

  const normalized = (results.score / wordCount) * 500;
  let density;
  if (normalized < 5) density = 'Low';
  else if (normalized < 15) density = 'Medium';
  else if (normalized < 30) density = 'High';
  else density = 'Severe';

  return { ...results, wordCount, normalizedScore: Math.round(normalized), density };
}

function report(r) {
  const R='\x1b[0m',RED='\x1b[31m',YEL='\x1b[33m',GRN='\x1b[32m',B='\x1b[1m',D='\x1b[2m';
  const dc = {Low:GRN,Medium:YEL,High:RED,Severe:RED+B}[r.density];
  let o = `\n${B}═══ AI Slop Text Report ═══${R}\n`;
  o += `${r.wordCount} words | Score: ${r.normalizedScore}/norm | Density: ${dc}${r.density}${R}\n\n`;
  if (r.tier1.length) { o += `${RED}${B}🔴 Tier 1 — High Confidence AI Words${R}\n`; for (const {word,count} of r.tier1) o += `  • "${word}" ×${count}\n`; o+='\n'; }
  if (r.tier2.length) { o += `${YEL}${B}🟡 Tier 2 — Overused Transitions${R}\n`; for (const {word,count} of r.tier2) o += `  • "${word}" ×${count}\n`; o+='\n'; }
  if (r.phrases.length) {
    o += `${RED}${B}🔴 AI Phrase Patterns${R}\n`;
    for (const {name,count,tier,examples} of r.phrases) {
      o += `  ${tier===1?RED:YEL}• ${name} ×${count}${R}\n`;
      for (const ex of examples) o += `    ${D}→ "${ex.trim()}"${R}\n`;
    }
    o += '\n';
  }
  if (r.structural.length) { o += `${YEL}${B}🟡 Structural Tells${R}\n`; for (const {name,detail} of r.structural) o += `  • ${name}\n    ${D}${detail}${R}\n`; o+='\n'; }
  const fixes = [...r.tier1.map(w=>({name:`Remove "${w.word}"`,priority:1})),...r.phrases.filter(p=>p.tier===1).map(p=>({name:p.name,priority:1}))].slice(0,3);
  if (fixes.length) { o += `${B}Top Fixes:${R}\n`; fixes.forEach((f,i)=>o+=`  ${i+1}. ${f.name}\n`); }
  return o;
}

async function main() {
  const args = process.argv.slice(2);
  const json = args.includes('--json');
  const file = args.find(a => !a.startsWith('--'));
  let text = '';
  if (file) { try { text = fs.readFileSync(file, 'utf8'); } catch(e) { console.error(e.message); process.exit(1); } }
  else if (!process.stdin.isTTY) { const c=[]; process.stdin.on('data',d=>c.push(d)); await new Promise(r=>process.stdin.on('end',r)); text=Buffer.concat(c).toString(); }
  else { console.error('Usage: node text-scanner.js <file.txt>'); process.exit(1); }
  const r = scanText(text);
  json ? console.log(JSON.stringify(r,null,2)) : console.log(report(r));
  process.exit(['High','Severe'].includes(r.density) ? 1 : 0);
}
main().catch(e=>{console.error(e);process.exit(1);});
