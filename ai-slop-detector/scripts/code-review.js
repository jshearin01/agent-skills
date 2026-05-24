#!/usr/bin/env node
/**
 * code-review.js — AI Slop Code Pattern Detector (React / TS / Backend)
 *
 * Usage:
 *   node code-review.js <file.ts|.tsx|.js|.jsx>
 *   node code-review.js --dir ./src
 *   node code-review.js --json <file>
 *
 * Exit codes: 0=clean/low, 1=high, 2=critical
 */

const fs = require('fs');
const path = require('path');

const RULES = [
  // ── React ─────────────────────────────────────────────────────────────
  { cat:'React', sev:'high',     re:/key=\{index\}/g,          name:'Array index as key', fix:'Use stable unique IDs: key={item.id}' },
  { cat:'React', sev:'high',     re:/\bfunction\b[\s\S]{0,200}const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*</g, name:'Component defined inside component', fix:'Move child component to module scope. Inner components recreate on every render.' },
  { cat:'React', sev:'medium',   re:/\.\.\.\s*props\s*\/>/g,  name:'Spreading all props onto element', fix:'Destructure and forward only valid HTML/component props.' },
  { cat:'React', sev:'high',     re:/ErrorBoundary/,           name:'No ErrorBoundary found', fix:'Wrap feature sections with ErrorBoundary. One uncaught error crashes the whole app.', absent:true, context:'jsx|tsx' },

  // ── Hooks ──────────────────────────────────────────────────────────────
  { cat:'Hooks', sev:'high',
    re:/useState\([^)]*\);\s*\n\s*useEffect\s*\(\s*\(\)\s*=>\s*\{\s*\n\s*set\w+\(`/g,
    name:'Derived state via useState + useEffect (string interpolation)',
    fix:'Compute derived values directly during render — no useState + useEffect needed.' },
  { cat:'Hooks', sev:'critical',
    re:/useEffect\s*\([^)]*\)\s*\{[\s\S]*?addEventListener[\s\S]*?\}\s*,\s*\[[^\]]*\]\s*\)(?![\s\S]*return)/g,
    name:'Event listener in useEffect without cleanup',
    fix:'Return cleanup: return () => element.removeEventListener(...)' },
  { cat:'Hooks', sev:'critical',
    re:/useEffect\s*\([^)]*\)\s*\{[\s\S]*?setInterval[\s\S]*?\}\s*,\s*\[[^\]]*\]\s*\)(?![\s\S]{0,50}return)/g,
    name:'setInterval in useEffect without cleanup',
    fix:'Return cleanup: return () => clearInterval(id)' },
  { cat:'Hooks', sev:'high',
    re:/useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]*fetch\([^}]*\}[^,)]*,\s*\[[^\]]*\]\s*\)/g,
    name:'Raw fetch() in useEffect (no cleanup/AbortController)',
    fix:'Use React Query/SWR, or add AbortController with cleanup.' },
  { cat:'Hooks', sev:'high',
    re:/if\s*\([^)]+\)\s*\{[^}]*\}\s*\n[\s\S]{0,100}const\s+\[\w+,\s*set\w+\]\s*=\s*useState/g,
    name:'Possible hook after conditional block (Rules of Hooks)',
    fix:'All hooks must appear before any conditional returns.' },
  { cat:'Hooks', sev:'low',
    re:/useMemo\s*\(\s*\(\)\s*=>\s*`[^`]*\$\{[^}]+\}[^`]*`,/g,
    name:'useMemo on string interpolation (unnecessary)',
    fix:'String template literals do not need memoization.' },
  { cat:'Hooks', sev:'low',
    re:/useMemo\s*\(\s*\(\)\s*=>\s*[\d\s+\-*/]+,\s*\[\s*\]\s*\)/g,
    name:'useMemo on constant arithmetic (unnecessary)',
    fix:'Move constant computations outside the component.' },

  // ── State ──────────────────────────────────────────────────────────────
  { cat:'State', sev:'medium',
    re:/const\s+\[loading[^;]+;\s*const\s+\[(?:data|error)[^;]+;\s*const\s+\[(?:data|error)/g,
    name:'Parallel boolean flags (impossible state machine)',
    fix:'Use useReducer with discriminated union: {status: "idle"|"loading"|"success"|"error"}' },
  { cat:'State', sev:'low',
    re:/createContext\(\)/g,
    name:'Context created without type annotation',
    fix:'createContext<MyType | null>(null) — always type your contexts.' },

  // ── Backend / API ───────────────────────────────────────────────────────
  { cat:'Backend', sev:'critical',
    re:/req\.body(?!\.\w+\s*=)(?![^;]*safeParse|[^;]*validate|[^;]*schema)/g,
    name:'Unvalidated req.body used directly',
    fix:'Validate all input with Zod/Joi before using. Never trust raw request body.' },
  { cat:'Backend', sev:'critical',
    re:/`[^`]*\$\{req\.(body|params|query)\.\w+\}[^`]*`/g,
    name:'User input in template literal (injection risk)',
    fix:'Use parameterized queries. Never interpolate user input into SQL or commands.' },
  { cat:'Backend', sev:'high',
    re:/findMany\(\s*\)(?![^;]*take|[^;]*limit)/g,
    name:'Unbounded findMany() — no pagination',
    fix:'Add take/limit: findMany({ take: Math.min(limit, 100) }). All records = DoS risk.' },
  { cat:'Backend', sev:'high',
    re:/for\s*\((?:const|let)\s+\w+\s+of\s+\w+\)[\s\S]{0,200}await\s+(?:prisma|db|mongoose)\.\w+\./g,
    name:'Database query inside loop (N+1 problem)',
    fix:'Batch queries: use include/populate or collect IDs then query once.' },
  { cat:'Backend', sev:'medium',
    re:/'[Ss]omething went wrong'|"[Ss]omething went wrong"/g,
    name:'Generic error message ("something went wrong")',
    fix:'Log the real error server-side. Return a request ID to aid debugging.' },
  { cat:'Backend', sev:'high',
    re:/async\s*\(req,\s*res\)\s*=>\s*\{(?![\s\S]{0,20}try)/g,
    name:'Async route handler without try/catch',
    fix:'Use an asyncHandler wrapper or global error middleware.' },

  // ── Security 🚨 ─────────────────────────────────────────────────────────
  { cat:'Security 🚨', sev:'critical',
    re:/sk-(?:proj-)?[a-zA-Z0-9]{20,}/g,
    name:'HARDCODED API KEY (OpenAI/Anthropic pattern)',
    fix:'Move to environment variable IMMEDIATELY. This key may be compromised.' },
  { cat:'Security 🚨', sev:'critical',
    re:/['"](?:pk_live_|sk_live_)[a-zA-Z0-9]{20,}['"]/g,
    name:'HARDCODED STRIPE LIVE KEY',
    fix:'Move to environment variable. Never commit live keys.' },
  { cat:'Security 🚨', sev:'critical',
    re:/(?:password|secret|apiKey)\s*[=:]\s*['"][^'"]{6,}['"]/gi,
    name:'Possible hardcoded credential',
    fix:'Move to environment variables. Validate env vars at startup with Zod.' },
  { cat:'Security 🚨', sev:'critical',
    re:/`SELECT.+WHERE.+\$\{/gi,
    name:'SQL query with template literal interpolation',
    fix:'Use parameterized queries: db.query("SELECT ... WHERE id = $1", [id])' },

  // ── TypeScript ─────────────────────────────────────────────────────────
  { cat:'TypeScript', sev:'medium', re:/:\s*any\b/g,  name:'`any` type (defeats type safety)', fix:'Use specific types, unknown, or a union type.' },
  { cat:'TypeScript', sev:'medium', re:/as\s+any\b/g, name:'`as any` cast',  fix:'Use `as unknown as TargetType` or fix the underlying type.' },
  { cat:'TypeScript', sev:'medium', re:/!\.\w+/g,     name:'Non-null assertion (!.) — potential runtime crash', fix:'Handle null explicitly with optional chaining (?.) and a fallback.' },
  { cat:'TypeScript', sev:'medium', re:/\[key:\s*string\]:\s*any/g, name:'Index signature with `any` value type', fix:'Use Record<string, KnownType> or a discriminated union.' },

  // ── Code Quality ───────────────────────────────────────────────────────
  { cat:'Code Quality', sev:'low',
    re:/\/\/\s*(Initialize|Set|Get|Return|Declare|Define|Call|Create)\s+\w+/gi,
    name:'Comments that restate the code',
    fix:'Comments explain WHY, not WHAT. Delete comments that mirror the code.' },
  { cat:'Code Quality', sev:'low',
    re:/\/\/\s*TODO:\s*(handle|add|fix|improve)\s+edge\s+cases?/gi,
    name:'Vague TODO: "handle edge cases"',
    fix:'Name the specific edge case. File a tracked issue instead of a comment.' },
  { cat:'Code Quality', sev:'low',
    re:/\/\/\s*Note:\s*(This|In production|For production|This is just)/gi,
    name:'AI disclaimer comment ("Note: This is simplified...")',
    fix:'Remove disclaimers. Either implement properly or create a tracked issue.' },
  { cat:'Code Quality', sev:'low',
    re:/\/\/\s*This is just for (demonstration|example|testing)/gi,
    name:'AI demo comment ("just for demonstration")',
    fix:'If demo code, delete it. If real code, remove the disclaimer.' },

  // ── Tests ──────────────────────────────────────────────────────────────
  { cat:'Tests', sev:'medium',
    re:/it\(['"](?:should\s+)?\w+\s+successfully['"]/gi,
    name:'Test covers happy path only ("should X successfully")',
    fix:'Add failure cases: invalid input, network errors, auth failures, edge cases.' },
  { cat:'Tests', sev:'medium',
    re:/toHaveBeenCalledWith|calls\s+set\w+/g,
    name:'Test verifies implementation details (not behavior)',
    fix:'Test what the user sees/experiences, not internal function calls.' },
];

function scanFile(content, filename) {
  const ext = path.extname(filename).slice(1);
  const issues = [];
  const lineCount = content.split('\n').length;

  // File size signal
  if (lineCount > 250 && /jsx|tsx/.test(ext)) {
    issues.push({ cat:'Component Size', sev:'high', name:`Large component file (${lineCount} lines)`, fix:'Components over 150 lines usually mix concerns. Extract hooks and sub-components.', count:1 });
  }

  for (const rule of RULES) {
    // Skip absent-checks for wrong file types
    if (rule.absent) {
      if (rule.context && !rule.context.split('|').includes(ext)) continue;
      if (!rule.re.test(content)) {
        // Only flag if there's interactivity suggesting a component
        if (/useState|useEffect|onClick/.test(content)) {
          issues.push({ ...rule, count: 1 });
        }
      }
      continue;
    }
    const m = content.match(rule.re) || [];
    if (m.length) issues.push({ ...rule, count: m.length, examples: m.slice(0,1).map(s=>s.slice(0,80)) });
  }

  const SEV = { critical:15, high:8, medium:3, low:1 };
  const score = issues.reduce((s,i)=>s+(SEV[i.sev]||1)*Math.min(i.count,5),0);
  const density = score===0?'Clean':score<10?'Low':score<25?'Medium':score<60?'High':'Severe';
  const criticals = issues.filter(i=>i.sev==='critical').length;

  return { filename, issues, score, density, lineCount, criticals };
}

function report(r) {
  const R='\x1b[0m',RED='\x1b[31m',YEL='\x1b[33m',GRN='\x1b[32m',B='\x1b[1m',D='\x1b[2m',C='\x1b[36m';
  const dc={Clean:GRN,Low:GRN,Medium:YEL,High:RED,Severe:RED+B}[r.density];
  let o=`\n${B}═══ Code Slop Audit: ${r.filename} ═══${R}\n`;
  o+=`Lines: ${r.lineCount} | Issues: ${r.issues.length} | Density: ${dc}${r.density}${R}`;
  if (r.criticals) o+=` | ${RED}${B}${r.criticals} CRITICAL${R}`;
  o+='\n\n';
  const byCat={};
  for (const i of r.issues) (byCat[i.cat]=byCat[i.cat]||[]).push(i);
  const icon={critical:'🚨',high:'🔴',medium:'🟡',low:'🟢'};
  const ord=['critical','high','medium','low'];
  for (const [cat,items] of Object.entries(byCat).sort()) {
    o+=`${C}${B}${cat}${R}\n`;
    for (const i of items.sort((a,b)=>ord.indexOf(a.sev)-ord.indexOf(b.sev))) {
      o+=`  ${icon[i.sev]||'•'} ${i.name}${i.count>1?` ×${i.count}`:''}\n`;
      if (i.examples?.length) o+=`    ${D}e.g.: ${i.examples[0]}${R}\n`;
      o+=`    ${D}→ ${i.fix}${R}\n`;
    }
    o+='\n';
  }
  const top=r.issues.sort((a,b)=>ord.indexOf(a.sev)-ord.indexOf(b.sev)).slice(0,3);
  if (top.length) { o+=`${B}Priority Fixes:${R}\n`; top.forEach((f,i)=>o+=`  ${i+1}. [${f.sev.toUpperCase()}] ${f.name}\n     ${D}${f.fix}${R}\n`); }
  return o;
}

function walk(dir) {
  const exts=['.ts','.tsx','.js','.jsx'];
  const files=[];
  for (const e of fs.readdirSync(dir,{withFileTypes:true})) {
    if (e.isDirectory()&&!['node_modules','.git','dist','build','.next','out'].includes(e.name)) walk(path.join(dir,e.name)).forEach(f=>files.push(f));
    else if (e.isFile()&&exts.some(x=>e.name.endsWith(x))) files.push(path.join(dir,e.name));
  }
  return files;
}

function main() {
  const args=process.argv.slice(2);
  const json=args.includes('--json'), dir=args.includes('--dir');
  const target=args.find(a=>!a.startsWith('--'));
  if (!target) { console.error('Usage: node code-review.js <file>  OR  node code-review.js --dir ./src'); process.exit(1); }
  const files=dir?walk(target):[target];
  const results=files.map(f=>{try{return scanFile(fs.readFileSync(f,'utf8'),f);}catch(e){return null;}}).filter(Boolean);
  if (json) { console.log(JSON.stringify(results,null,2)); return; }
  for (const r of results.filter(r=>r.issues.length)) console.log(report(r));
  if (dir) {
    const total=results.reduce((s,r)=>s+r.issues.length,0), crits=results.reduce((s,r)=>s+r.criticals,0), hi=results.filter(r=>['High','Severe'].includes(r.density)).length;
    console.log(`\n\x1b[1mSummary: ${files.length} files | ${total} issues | ${crits} critical | ${hi} high/severe\x1b[0m`);
  }
  const hasCrit=results.some(r=>r.criticals>0), hasHigh=results.some(r=>['High','Severe'].includes(r.density));
  process.exit(hasCrit?2:hasHigh?1:0);
}
main();
