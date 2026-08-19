// Verify the issue #5 quiet savings loop (Schatkist) by stubbing the DOM and
// running the game's script logic extracted from index.html.
//
// Product boundaries under test (from issue #5):
//   - every registered hap gives exactly 1 muntje (no combo escalation)
//   - one savings goal at a time with visible progress
//   - cosmetics unlock visibly, permanently, and without munt deduction
//   - no negative balance is possible
//   - "Opnieuw" (adventure reset) never touches the spaarpot
//   - the spaar-reset is explicit, confirmed, and keeps unlocked items
//   - no timers, streaks, quotas, speed/amount/plate-empty or comparison copy
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error('NO SCRIPT FOUND'); process.exit(1); }
const code = m[1];

// --- Minimal DOM stub with persistent focusable controls ---
const elements = {};
const documentListeners = {};
let dynCounter = 0;

function makeEl(id, tag) {
  const el = {
    id,
    tagName: String(tag || 'div').toUpperCase(),
    textContent: '',
    _innerHTML: '',
    className: '',
    hidden: false,
    disabled: false,
    style: {},
    children: [],
    listeners: {},
    classList: {
      _set: new Set(),
      add(c) { this._set.add(c); },
      remove(c) { this._set.delete(c); },
      contains(c) { return this._set.has(c); },
      toggle(c, force) {
        if (force === undefined) {
          if (this._set.has(c)) this._set.delete(c); else this._set.add(c);
        } else if (force) {
          this._set.add(c);
        } else {
          this._set.delete(c);
        }
      },
    },
    focus() { global.document.activeElement = this; },
    appendChild(child) { this.children.push(child); return child; },
    setAttribute(k, v) { this['attr_' + k] = v; },
    addEventListener(type, fn) { this.listeners[type] = fn; },
    closest(sel) { return null; },
    offsetWidth: 100,
  };
  Object.defineProperty(el, 'innerHTML', {
    get() { return this._innerHTML; },
    set(v) {
      this._innerHTML = String(v);
      if (v === '') this.children = [];
    },
  });
  return el;
}

const ids = [
  'food', 'counter', 'message', 'levelName', 'progressText', 'progressFill',
  'coins', 'level', 'hapButton', 'reward', 'rewardEmoji', 'rewardTitle',
  'rewardText', 'end', 'endEmoji', 'endTitle', 'endText', 'endNote',
  'endPrimary', 'endBonus', 'badge-1', 'badge-2', 'badge-3', 'badge-4', 'badge-5',
  'soundButton', 'plate', 'vriendje', 'strijkje', 'feestKnop',
  'goalName', 'goalText', 'goalTrack', 'goalFill', 'goalRemaining', 'goalButton',
  'schatkist', 'schatkistText', 'schatkistList', 'schatkistClose',
  'spaarReset', 'spaarResetBtn', 'spaarResetJa', 'spaarResetNee',
];
for (const id of ids) elements[id] = makeEl(id);

elements.schatkistClose.tagName = 'BUTTON';
elements.spaarResetBtn.tagName = 'BUTTON';
elements.spaarResetJa.tagName = 'BUTTON';
elements.spaarResetNee.tagName = 'BUTTON';
elements.spaarReset.classList._set = new Set();
elements.spaarReset.textContent =
  'Opnieuw sparen? Je spaarpot wordt dan leeg. Je ontgrendelde dingen mag je houden.';
elements.spaarResetJa.closest = (sel) => (sel === '.spaar-reset' || !sel ? elements.spaarReset : null);
elements.spaarResetNee.closest = (sel) => (sel === '.spaar-reset' || !sel ? elements.spaarReset : null);
elements.schatkist.children = [
  elements.schatkistList,
  elements.schatkistClose,
  elements.spaarResetBtn,
  elements.spaarReset,
];
elements.spaarReset.children = [elements.spaarResetJa, elements.spaarResetNee];

global.document = {
  activeElement: null,
  getElementById(id) { return elements[id] || makeEl(id); },
  querySelector(sel) {
    if (sel === '#end .main-btn') return elements.endPrimary;
    return null;
  },
  querySelectorAll(sel) {
    if (sel === '#end button') return [elements.endPrimary, elements.endBonus];
    if (sel === '#schatkist button') {
      const buttons = [];
      function walk(node) {
        if (!node) return;
        if (node.tagName === 'BUTTON') buttons.push(node);
        (node.children || []).forEach(walk);
      }
      walk(elements.schatkist);
      return buttons;
    }
    if (sel === '.badge') return ids.filter(i => i.startsWith('badge')).map(i => elements[i]);
    return [];
  },
  createElement(tag) { dynCounter += 1; return makeEl('dyn-' + dynCounter, tag); },
  addEventListener(type, handler) { documentListeners[type] = handler; },
  body: makeEl('body'),
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

function latestKiesKnopVoor(doelId) {
  // renderSchatkist appends rows in schatkistItems order; the "kies" button
  // for an item is the dynamically created button whose data-doel matches.
  const rows = elements.schatkistList.children;
  for (const row of rows) {
    for (const child of [row.children[2]]) {
      const knop = child.children[0];
      if (knop && knop.listeners && knop['attr_data-doel'] === doelId) return knop;
    }
  }
  return null;
}

let pass = true;
function check(name, cond) { if (!cond) { pass = false; console.error('FAIL:', name); } else { console.log('PASS:', name); } }
const S = v => String(v);

// ── 1. Exactly one muntje per hap; combo escalation removed ──────────────
for (let i = 0; i < 3; i++) hapGenomen();
check('each hap gives exactly 1 muntje (3 hapjes -> 3 muntjes)', S(elements.coins.textContent) === '3');
check('combo stat removed from the UI', !/id="combo"/.test(html));
check('no combo variable in the script', !/\bcombo\s*[+\-]/.test(code));

// ── 2. Schatkist: goal choice and progress line ───────────────────────────
openSchatkist();
check('schatkist opens as a named, modal dialog', /id="schatkist"\s+role="dialog"\s+aria-modal="true"/.test(html));
const firstItemButton = latestKiesKnopVoor('confetti');
check('schatkist focus starts on the first item button', document.activeElement === firstItemButton);
check('pot line shows the quiet rule', /Elke hap geeft er \u00e9\u00e9n/.test(elements.schatkistText.textContent));

const kiesPanda = latestKiesKnopVoor('panda');
check('panda is offered as a goal', !!kiesPanda);
kiesPanda.listeners.click();
check('goal card shows progress "3 van 8"', S(elements.goalText.textContent) === '3 van 8');
check('goal line matches the issue example shape', S(elements.goalRemaining.textContent) === '\u{1FA99} nog 5 muntjes tot de panda');
sluitSchatkist();

// ── 3. The exact issue example: 4 of 8, nog 4 tot de panda ────────────────
hapGenomen();
check('issue example: 4 van 8', S(elements.goalText.textContent) === '4 van 8');
check('issue example: nog 4 tot de panda', S(elements.goalRemaining.textContent) === '\u{1FA99} nog 4 muntjes tot de panda');

// ── 4. Unlock at the threshold: visible, permanent, no deduction ─────────
for (let i = 4; i < 8; i++) hapGenomen();
const pandaOntgrendeldZichtbaar = elements.vriendje.classList.contains('zichtbaar');
check('panda unlocks when the pot reaches the price', pandaOntgrendeldZichtbaar);
check('unlock is visible immediately (vriendje shown)', pandaOntgrendeldZichtbaar);
check('unlock does not deduct muntjes (pot stays 8)', S(elements.coins.textContent) === '8');
check('quiet unlock announces via the message card', /Dierenvriendje is nu van jou!/.test(elements.message.textContent));

// ── 5. Switching goals never loses muntjes; affordable items unlock at once
openSchatkist();
const kiesBord = latestKiesKnopVoor('bord');
check('bord is offered as a goal', !!kiesBord);
kiesBord.listeners.click();
check('already-affordable item unlocks immediately', elements.plate.classList.contains('feest-bord'));
check('goal switch keeps the pot (still 8)', S(elements.coins.textContent) === '8');
check('feestbord cosmetic applied to the plate', elements.plate.classList.contains('feest-bord'));
check('unlocked row is marked "Van jou!"', elements.schatkistList.children.some(r => /Van jou!/.test(r.children[2].textContent || '')));
sluitSchatkist();

// ── 6. Focus trap and Escape in the Schatkist dialog ──────────────────────
elements.hapButton.focus();
openSchatkist();
const tabPrevented = dispatchKey('Tab');
const focusAfterTab = document.activeElement;
dispatchKey('Tab');
const focusAfterTabWrap = document.activeElement;
const shiftTabPrevented = dispatchKey('Tab', true);
const focusAfterShiftTab = document.activeElement;
const schatkistButtons = document.querySelectorAll('#schatkist button');
check('Tab stays inside the Schatkist dialog', tabPrevented && schatkistButtons.includes(focusAfterTab));
check('Tab wraps within the Schatkist dialog', schatkistButtons.includes(focusAfterTabWrap));
check('Shift+Tab wraps within the Schatkist dialog', shiftTabPrevented && schatkistButtons.includes(focusAfterShiftTab));
dispatchKey('Escape');
check('Escape closes the Schatkist and restores invoking focus', !elements.schatkist.classList.contains('show') && document.activeElement === elements.hapButton);

// ── 7. End state stays honest (per-adventure count) and pressure-free ─────
for (let i = 8; i < 20; i++) hapGenomen();
check('end dialog opens at the safe boundary', elements.end.classList.contains('show'));
check('end text counts muntjes found this adventure', S(elements.endText.textContent) === 'Je hebt vandaag 20 muntjes gevonden.');
check('end note stays pressure-free', /niet nodig/.test(elements.endNote.textContent));
dispatchKey('Escape');

// ── 8. "Opnieuw" resets the adventure but never the spaarpot ──────────────
resetGame();
check('Opnieuw resets hapjes to 0', S(elements.counter.textContent) === '0');
check('Opnieuw keeps the spaarpot (20 muntjes)', S(elements.coins.textContent) === '20');
check('Opnieuw keeps unlocked cosmetics visible', elements.vriendje.classList.contains('zichtbaar') && elements.plate.classList.contains('feest-bord'));
const potVoorReset = S(elements.coins.textContent);

// ── 9. Spaar-reset: explicit, confirmed, child-friendly, keeps unlocks ────
openSchatkist();
bevestigSpaarReset();
check('spaar-reset asks before clearing', elements.spaarReset.classList.contains('open'));
check('spaar-reset explains what is kept', /ontgrendelde dingen mag je houden/.test(elements.spaarReset.textContent));
spaarResetAnnuleer();
check('cancelling keeps the pot intact', S(elements.coins.textContent) === potVoorReset && !elements.spaarReset.classList.contains('open'));
bevestigSpaarReset();
spaarResetBevestig();
check('confirmed reset empties the pot to exactly 0', S(elements.coins.textContent) === '0');
check('confirmed reset keeps unlocked items', elements.vriendje.classList.contains('zichtbaar') && elements.plate.classList.contains('feest-bord'));
check('confirmed reset keeps cosmetics visible', elements.vriendje.classList.contains('zichtbaar'));
check('after reset a new goal can be chosen', S(elements.goalName.textContent) === 'Spaardoel kiezen');
sluitSchatkist();

// ── 10. Balance can never go negative ─────────────────────────────────────
check('no code path subtracts from the pot', !/coins\s*-=/.test(code) && !/coins\s*=\s*coins\s*-/.test(code));
const potZeroWrites = (code.match(/(?<!let )coins = 0/g) || []).length;
check('only the confirmed spaar-reset writes the pot to 0', potZeroWrites === 1);

// ── 11. Static product-boundary checks on the shipped copy ────────────────
// Scan user-visible copy only: strip HTML and JS comments first.
const visibleHtml = html.replace(/<!--[\s\S]*?-->/g, '').replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '');
const forbidden = [
  'snoep', 'toetje', 'dessert', 'sneller', 'snelste', 'streak', 'timer',
  'minstens', 'minimum', 'quotum', 'quota', 'ranking', 'ranglijst',
  'bord wordt leeg', 'bord is leeg', 'bord leeg', 'leeg eten', 'nog_eentje',
  'Nog eentje', 'vergil', 'beter dan', 'het beste van',
];
for (const term of forbidden) {
  check('copy free of pressure term: ' + term, !visibleHtml.includes(term));
}
check('goal card uses a real progressbar role', /role="progressbar"[^>]*aria-label="Voortgang naar spaardoel"/.test(html));
check('decorative cosmetics are aria-hidden', /class="vriendje"[^>]*aria-hidden="true"/.test(html));

console.log(pass ? '\nALL CHECKS PASSED' : '\nSOME CHECKS FAILED');
process.exit(pass ? 0 : 1);
