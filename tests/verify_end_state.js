// Verify the issue #7 end-state flow by stubbing the DOM and running the
// game's script logic extracted from index.html.
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('NO SCRIPT FOUND'); process.exit(1); }
const code = m[1];

// --- Minimal DOM stub with persistent focusable controls ---
const elements = {};
const documentListeners = {};
function makeEl(id) {
  return {
    id,
    textContent: '',
    className: '',
    style: {},
    disabled: false,
    setAttribute(k, v) { this['attr_' + k] = v; },
    classList: {
      _set: new Set(),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      contains(c) { return this._set.has(c); },
    },
    focus() { global.document.activeElement = this; },
    addEventListener() {},
    offsetWidth: 100,
  };
}
const ids = [
  'food','counter','message','levelName','progressText','progressFill',
  'combo','coins','level','hapButton','reward','rewardEmoji','rewardTitle',
  'rewardText','end','endEmoji','endTitle','endText','endNote',
  'endPrimary','endBonus','badge-1','badge-2','badge-3','badge-4','badge-5','soundButton'
];
for (const id of ids) elements[id] = makeEl(id);
elements.mealPickerBox = makeEl('mealPickerBox');

global.document = {
  activeElement: null,
  getElementById(id) { return elements[id] || makeEl(id); },
  querySelector(sel) {
    if (sel === '#end .main-btn') return elements.endPrimary;
    // The meal picker's static markup exists in the page; expose its box so
    // the picker's keydown bindings from the merged script still attach.
    if (sel === '#mealPicker .picker-box') return elements.mealPickerBox;
    return null;
  },
  querySelectorAll(sel) {
    if (sel === '#end button') return [elements.endPrimary, elements.endBonus];
    if (sel === '.badge') return ids.filter(i => i.startsWith('badge')).map(i => elements[i]);
    if (sel === '#mealGrid .meal-option' || sel === '#extraGrid .meal-option') return [];
    return [];
  },
  createElement() { return makeEl('confetti'); },
  addEventListener(type, handler) { documentListeners[type] = handler; },
  body: { appendChild() {} },
};
global.window = { AudioContext: null, webkitAudioContext: null };
global.Audio = function () { return { play() { return Promise.resolve(); }, pause() { return Promise.resolve(); }, set src(v) {}, set preload(v) {}, set volume(v) {}, set currentTime(v) {} }; };
global.setTimeout = () => {};
global.console = console;

function dispatchKey(key, shiftKey = false) {
  let prevented = false;
  documentListeners.keydown({ key, shiftKey, preventDefault() { prevented = true; } });
  return prevented;
}

// Run the game script.
eval(code);

// --- Simulate 20 hapjes ---
elements.hapButton.focus();
for (let i = 0; i < 20; i++) hapGenomen();
const results = {
  counter: elements.counter.textContent,
  endShown: elements.end.classList.contains('show'),
  endTitle: elements.endTitle.textContent,
  endText: elements.endText.textContent,
  endNote: elements.endNote.textContent,
  rewardShown: elements.reward.classList.contains('show'),
  adventureDone: typeof adventureDone !== 'undefined' ? adventureDone : 'n/a',
  initialFocus: document.activeElement,
};

// --- Modal keyboard behavior ---
const tabToBonusPrevented = dispatchKey('Tab');
const focusAfterTab = document.activeElement;
const tabWrapPrevented = dispatchKey('Tab');
const focusAfterTabWrap = document.activeElement;
const shiftTabPrevented = dispatchKey('Tab', true);
const focusAfterShiftTab = document.activeElement;

// --- After Klaar met eten, hap button should reopen end, not continue ---
klaarMetEten();
const focusAfterDoneClose = document.activeElement;
const afterDone = {
  endShown: elements.end.classList.contains('show'),
  message: elements.message.textContent,
};

// Click hap again -> should reopen end, counter unchanged
const before = elements.counter.textContent;
hapGenomen();
const after = elements.counter.textContent;
const hapAfterDoneEndShown = elements.end.classList.contains('show');

// --- Bonus mode: hap continues at own pace, no re-trigger of end ---
bonusAvontuur();
const focusAfterBonusClose = document.activeElement;
const bBefore = elements.counter.textContent;
hapGenomen();
const bAfter = elements.counter.textContent;
const bonusEndShown = elements.end.classList.contains('show');

// --- Reset closes an open dialog, restores focus, and clears everything ---
elements.hapButton.focus();
resetGame();
for (let i = 0; i < 20; i++) hapGenomen();
const resetStartedWithEndOpen = elements.end.classList.contains('show');
resetGame();
const resetCounter = elements.counter.textContent;
const resetEndShown = elements.end.classList.contains('show');
const focusAfterResetClose = document.activeElement;

// --- Escape closes end dialog and restores invoking focus ---
elements.hapButton.focus();
for (let i = 0; i < 20; i++) hapGenomen();
const escShown = elements.end.classList.contains('show');
dispatchKey('Escape');
const focusAfterEscape = document.activeElement;

// Assertions
let pass = true;
function check(name, cond) { if (!cond) { pass = false; console.error('FAIL:', name); } else { console.log('PASS:', name); } }
const S = v => String(v);
check('counter reaches 20', S(results.counter) === '20');
check('end dialog shown at boundary', results.endShown === true);
check('end dialog describes its explanatory text', /aria-describedby="endText endNote"/.test(html));
check('end title is positive', results.endTitle === 'Avontuur klaar!');
check('end text mentions coins', /muntjes/.test(results.endText));
check('end note is pressure-free', /niet nodig/.test(results.endNote));
check('reward modal superseded', results.rewardShown === false);
check('focus enters the dialog on its primary action', results.initialFocus === elements.endPrimary);
check('Tab advances focus to bonus action inside dialog', tabToBonusPrevented && focusAfterTab === elements.endBonus);
check('Tab wraps focus within dialog controls', tabWrapPrevented && focusAfterTabWrap === elements.endPrimary);
check('Shift+Tab wraps focus within dialog controls', shiftTabPrevented && focusAfterShiftTab === elements.endBonus);
check('Klaar met eten closes dialog and restores invoking focus', !afterDone.endShown && focusAfterDoneClose === elements.hapButton);
check('hap after done reopens end, no counter change', S(after) === S(before) && hapAfterDoneEndShown);
check('bonus mode continues without re-triggering end', S(bAfter) !== S(bBefore) && bonusEndShown === false);
check('Bonusavontuur closes dialog and restores invoking focus', focusAfterBonusClose === elements.hapButton);
check('reset closes an open dialog, restores invoking focus, and clears counter', resetStartedWithEndOpen && !resetEndShown && focusAfterResetClose === elements.hapButton && S(resetCounter) === '0');
check('Escape closes end and restores invoking focus', escShown && !elements.end.classList.contains('show') && focusAfterEscape === elements.hapButton);

console.log(pass ? '\nALL CHECKS PASSED' : '\nSOME CHECKS FAILED');
process.exit(pass ? 0 : 1);
