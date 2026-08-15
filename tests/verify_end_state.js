// Verify the issue #7 end-state flow by stubbing the DOM and running the
// game's script logic extracted from index.html.
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

// Extract the <script> body (the last <script> block).
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('NO SCRIPT FOUND'); process.exit(1); }
let code = m[1];

// --- Minimal DOM stub ---
const elements = {};
const documentListeners = {};
function makeEl(id) {
  return {
    id,
    textContent: '',
    className: '',
    style: {},
    classList: {
      _set: new Set(),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      contains(c) { return this._set.has(c); },
    },
    focus() { this._focused = true; },
    offsetWidth: 100,
  };
}
const ids = [
  'food','counter','message','levelName','progressText','progressFill',
  'combo','coins','level','hapButton','reward','rewardEmoji','rewardTitle',
  'rewardText','end','endEmoji','endTitle','endText','endNote',
  'badge-1','badge-2','badge-3','badge-4','badge-5','soundButton'
];
for (const id of ids) elements[id] = makeEl(id);

global.document = {
  getElementById(id) { return elements[id] || makeEl(id); },
  querySelector(sel) {
    if (sel === '#end .main-btn') return elements['end'] ? { focus() { this._focused = true; } } : null;
    return null;
  },
  querySelectorAll(sel) {
    if (sel === '.badge') return ids.filter(i => i.startsWith('badge')).map(i => elements[i]);
    return [];
  },
  createElement() { return makeEl('confetti'); },
  addEventListener(type, handler) { documentListeners[type] = handler; },
  body: { appendChild() {} },
};
global.window = { AudioContext: null, webkitAudioContext: null };
global.Audio = function () { return { play() { return Promise.resolve(); }, pause() { return Promise.resolve(); }, set src(v) {}, set preload(v) {}, set volume(v) {}, set currentTime(v) {} }; };
global.setTimeout = (fn) => { /* no-op timers */ };
global.console = console;

// Run the game script.
eval(code);

// --- Simulate 20 hapjes ---
for (let i = 0; i < 20; i++) hapGenomen();

const results = {
  counter: elements['counter'].textContent,
  endShown: elements['end'].classList.contains('show'),
  endTitle: elements['endTitle'].textContent,
  endText: elements['endText'].textContent,
  endNote: elements['endNote'].textContent,
  rewardShown: elements['reward'].classList.contains('show'),
  adventureDone: typeof adventureDone !== 'undefined' ? adventureDone : 'n/a',
};

console.log('=== END-STATE FLOW ===');
console.log(JSON.stringify(results, null, 2));

// --- After Klaar met eten, hap button should reopen end, not continue ---
klaarMetEten();
const afterDone = {
  endShown: elements['end'].classList.contains('show'),
  message: elements['message'].textContent,
};
console.log('=== AFTER KLAAR MET ETEN ===');
console.log(JSON.stringify(afterDone, null, 2));

// Click hap again -> should reopen end, counter unchanged
const before = elements['counter'].textContent;
hapGenomen();
const after = elements['counter'].textContent;
const hapAfterDoneEndShown = elements['end'].classList.contains('show');
console.log('=== HAP AFTER DONE ===');
console.log(JSON.stringify({ counterBefore: before, counterAfter: after, endShown: hapAfterDoneEndShown }, null, 2));

// --- Bonus mode: hap continues at own pace, no re-trigger of end ---
bonusAvontuur();
const bBefore = elements['counter'].textContent;
hapGenomen();
const bAfter = elements['counter'].textContent;
const bonusEndShown = elements['end'].classList.contains('show');
console.log('=== BONUS MODE ===');
console.log(JSON.stringify({ counterBefore: bBefore, counterAfter: bAfter, endShown: bonusEndShown, message: elements['message'].textContent }, null, 2));

// --- Reset clears everything ---
resetGame();
const resetCounter = elements['counter'].textContent;
const resetEndShown = elements['end'].classList.contains('show');
console.log('=== RESET ===');
console.log(JSON.stringify({ counter: resetCounter, endShown: resetEndShown }, null, 2));

// --- Escape key closes end dialog ---
// Re-reach end
for (let i = 0; i < 20; i++) hapGenomen();
const escShown = elements['end'].classList.contains('show');
// Dispatch the real registered Escape handler.
if (documentListeners.keydown) documentListeners.keydown({ key: 'Escape' });
console.log('=== ESCAPE ===');
console.log(JSON.stringify({ endShownBeforeEsc: escShown, endShownAfterEsc: elements['end'].classList.contains('show') }, null, 2));

// Assertions
let pass = true;
function check(name, cond) { if (!cond) { pass = false; console.error('FAIL:', name); } else { console.log('PASS:', name); } }
const S = v => String(v);
check('counter reaches 20', S(results.counter) === '20');
check('end dialog shown at boundary', results.endShown === true);
check('end title is positive', results.endTitle === 'Avontuur klaar!');
check('end text mentions coins', /muntjes/.test(results.endText));
check('end note is pressure-free', /niet nodig/.test(results.endNote));
check('reward modal superseded', results.rewardShown === false);
check('hap after done reopens end, no counter change', S(after) === S(before) && hapAfterDoneEndShown);
check('bonus mode continues without re-triggering end', S(bAfter) !== S(bBefore) && bonusEndShown === false);
check('reset clears counter', S(resetCounter) === '0');
check('escape closes end', elements['end'].classList.contains('show') === false);

console.log(pass ? '\nALL CHECKS PASSED' : '\nSOME CHECKS FAILED');
process.exit(pass ? 0 : 1);
