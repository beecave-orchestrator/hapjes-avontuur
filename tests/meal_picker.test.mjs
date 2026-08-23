// Zero-dependency tests for the issue #6 meal picker.
//
// Runs the real inline <script> from index.html inside a minimal DOM shim
// (this repo is a zero-dependency static site, so no jsdom). The shim
// implements exactly the DOM surface the game uses: element tree, classList,
// dataset, hidden, style, focus/activeElement, bubbling keydown/click
// events (up to document), and a small selector engine.
//
// Run: node --test tests/
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(path.join(ROOT, "index.html"), "utf-8");

// ---------------------------------------------------------------------------
// Minimal DOM
// ---------------------------------------------------------------------------

const VOID_TAGS = new Set(["meta", "br", "hr", "img", "input", "link", "source"]);

class ClassList {
  constructor(el) {
    this.el = el;
  }
  _set() {
    return new Set((this.el._attrs.class || "").split(/\s+/).filter(Boolean));
  }
  _write(set) {
    this.el._attrs.class = [...set].join(" ");
  }
  add(...names) {
    const s = this._set();
    names.forEach((n) => s.add(n));
    this._write(s);
  }
  remove(...names) {
    const s = this._set();
    names.forEach((n) => s.delete(n));
    this._write(s);
  }
  toggle(name, force) {
    const s = this._set();
    const target = force === undefined ? !s.has(name) : force;
    if (target) s.add(name);
    else s.delete(name);
    this._write(s);
    return target;
  }
  contains(name) {
    return this._set().has(name);
  }
}

class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.parentNode = null;
    this._attrs = {};
    this._listeners = {};
    this.classList = new ClassList(this);
    this.textContent = "";
    this.style = {};
    this.offsetWidth = 0;
  }
  get id() {
    return this._attrs.id || "";
  }
  set id(v) {
    this._attrs.id = v;
  }
  get className() {
    return this._attrs.class || "";
  }
  set className(v) {
    this._attrs.class = v;
  }
  get dataset() {
    const ds = {};
    for (const [k, v] of Object.entries(this._attrs)) {
      if (k.startsWith("data-")) {
        const prop = k.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
        ds[prop] = v;
      }
    }
    return ds;
  }
  get hidden() {
    return this._attrs.hidden !== undefined;
  }
  set hidden(v) {
    if (v) this._attrs.hidden = "";
    else delete this._attrs.hidden;
  }
  getAttribute(name) {
    const v = this._attrs[name];
    return v === undefined ? null : v;
  }
  setAttribute(name, v) {
    this._attrs[name] = String(v);
  }
  removeAttribute(name) {
    delete this._attrs[name];
  }
  get tabIndex() {
    return Number(this._attrs.tabindex ?? -1);
  }
  set tabIndex(v) {
    this._attrs.tabindex = String(v);
  }
  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }
  remove() {
    if (!this.parentNode) return;
    const i = this.parentNode.children.indexOf(this);
    if (i >= 0) this.parentNode.children.splice(i, 1);
    this.parentNode = null;
  }
  addEventListener(type, fn) {
    (this._listeners[type] ||= []).push(fn);
  }
  dispatchEvent(evt) {
    evt.target ||= this;
    let node = this;
    while (node) {
      for (const fn of (node._listeners[evt.type] || []).slice()) fn(evt);
      node = evt.bubbles === false ? null : node.parentNode;
    }
  }
  focus() {
    document._activeElement = this;
  }
  _matchesCompound(token) {
    token = token.trim();
    if (!token) return false;
    const attrValue = token.match(/^\[([\w-]+)="([^"]*)"\]$/);
    if (attrValue) return this._attrs[attrValue[1]] === attrValue[2];
    const attr = token.match(/^\[([a-zA-Z-]+)\]$/);
    if (attr) return this._attrs[attr[1]] !== undefined;
    const id = token.match(/^#([\w-]+)$/);
    if (id) return this._attrs.id === id[1];
    const cls = token.match(/^\.([\w-]+)$/);
    if (cls) return this.classList.contains(cls[1]);
    const m = token.match(/^([a-zA-Z][\w-]*)((?:[.#][\w-]+)*)$/);
    if (m) {
      if (this.tagName !== m[1].toUpperCase()) return false;
      for (const extra of m[2].match(/[.#][\w-]+/g) || []) {
        if (extra.startsWith("#") && this._attrs.id !== extra.slice(1))
          return false;
        if (extra.startsWith(".") && !this.classList.contains(extra.slice(1)))
          return false;
      }
      return true;
    }
    return false;
  }
  _matchesSelector(sel) {
    const parts = sel.trim().split(/\s+/);
    let node = this;
    for (let i = parts.length - 1; i >= 0; i--) {
      if (!node || typeof node._matchesCompound !== "function") return false;
      if (!node._matchesCompound(parts[i])) return false;
      node = node.parentNode;
    }
    return true;
  }
  closest(sel) {
    let node = this;
    while (node) {
      if (typeof node._matchesSelector === "function" && node._matchesSelector(sel))
        return node;
      node = node.parentNode;
    }
    return null;
  }
  querySelector(sel) {
    return this.querySelectorAll(sel)[0] || null;
  }
  querySelectorAll(sel) {
    return collect(this, []).filter((el) => el._matchesSelector(sel));
  }
}

function parseHtml(source) {
  const body = new Element("body");
  const stack = [body];
  const tagRe = /<\/?([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>/g;
  let last = 0;
  let match;
  while ((match = tagRe.exec(source))) {
    const text = source.slice(last, match.index).trim();
    if (text) stack[stack.length - 1].textContent += text;
    const [full, tag, attrText] = match;
    if (full.startsWith("</")) {
      for (let i = stack.length - 1; i > 0; i--) {
        if (stack[i].tagName === tag.toUpperCase()) {
          stack.length = i;
          break;
        }
      }
    } else {
      const el = new Element(tag);
      const attrRe = /([a-zA-Z][\w-]*)="([^"]*)"/g;
      let am;
      while ((am = attrRe.exec(attrText))) el._attrs[am[1]] = am[2];
      stack[stack.length - 1].appendChild(el);
      if (!VOID_TAGS.has(tag.toLowerCase()) && !full.endsWith("/>")) {
        stack.push(el);
      }
    }
    last = tagRe.lastIndex;
  }
  return body;
}

function collect(root, out) {
  for (const child of root.children) {
    out.push(child);
    collect(child, out);
  }
  return out;
}

const parsedBody = parseHtml(html);

const document = {
  body: parsedBody,
  parentNode: null,
  _activeElement: null,
  _listeners: {},
  _matchesCompound: () => false,
  _matchesSelector: () => false,
  addEventListener(type, fn) {
    (this._listeners[type] ||= []).push(fn);
  },
  get activeElement() {
    return this._activeElement;
  },
  getElementById(id) {
    return collect(parsedBody, []).find((el) => el._attrs.id === id) || null;
  },
  querySelector(sel) {
    return this.querySelectorAll(sel)[0] || null;
  },
  querySelectorAll(sel) {
    return collect(parsedBody, []).filter((el) => el._matchesSelector(sel));
  },
  createElement(tag) {
    return new Element(tag);
  },
};

// Events bubble from elements up through body to document-level listeners.
parsedBody.parentNode = document;

// ---------------------------------------------------------------------------
// Execute the game's inline script in this DOM
// ---------------------------------------------------------------------------

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, "inline <script> found in index.html");

class AudioStub {
  play() {
    return { catch() {} };
  }
  pause() {
    return { catch() {} };
  }
}

const sandbox = {
  document,
  Audio: AudioStub,
  Math,
  setTimeout: (fn) => fn(),
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(scriptMatch[1], sandbox);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeEvent(type, props = {}) {
  return {
    type,
    bubbles: true,
    target: null,
    preventDefault() {},
    stopPropagation() {},
    ...props,
  };
}

function mealButton(key) {
  return document
    .querySelectorAll("#mealGrid .meal-option")
    .find((b) => b.dataset.meal === key);
}

function extraButton(key) {
  return document
    .querySelectorAll("#extraGrid .meal-option")
    .find((b) => b.dataset.extra === key);
}

function click(el) {
  el.dispatchEvent(makeEvent("click"));
}

function pressKey(el, key, shiftKey = false) {
  el.dispatchEvent(makeEvent("keydown", { key, shiftKey }));
}

// ---------------------------------------------------------------------------
// Static source checks: carousel gone, labels carry meaning
// ---------------------------------------------------------------------------

test("index.html no longer contains the automatic emoji rotation", () => {
  assert.ok(!html.includes("veranderEten"), "veranderEten removed");
  assert.ok(!html.includes("const foods"), "foods rotation array removed");
  assert.ok(!html.includes("setInterval"), "no automatic rotation timers");
  assert.ok(!html.includes(">Ander eten<"), "old 'Ander eten' button removed");
});

test("all required labelled meals and extras exist with text names", () => {
  for (const name of [
    "Aardappels",
    "Rijst of noedels",
    "Pasta",
    "Yoghurt, kwark of pap",
    "Boterhammen",
    "Pannenkoeken",
    "Mijn eigen eten",
  ]) {
    assert.ok(html.includes(`>${name}</span>`), `meal label present: ${name}`);
  }
  for (const name of [
    "Groente of fruit",
    "Vlees of vis",
    "Ei, kaas of iets vegetarisch",
    "Saus",
  ]) {
    assert.ok(html.includes(`>${name}</span>`), `extra label present: ${name}`);
  }
  // Issue #19 review: broad categories replace the specific dish tiles.
  assert.ok(!html.includes("Weet ik niet"), "weetniet is not a food tile");
  assert.ok(!html.includes(">Stamppot<"), "stamppot is not its own tile");
  assert.ok(!html.includes(">Soep<"), "soep is not its own tile");
  assert.ok(!html.includes("AVG"), "AVG abbreviation is not shown to a child");
});

test("meal options are semantic radios with decorative emoji", () => {
  const grid = document.getElementById("mealGrid");
  const options = document.querySelectorAll("#mealGrid .meal-option");

  assert.equal(grid.getAttribute("role"), "radiogroup");
  assert.equal(options.length, 7, "six categories + mijn eigen eten");
  for (const btn of options) {
    assert.equal(btn.getAttribute("role"), "radio");
    assert.equal(btn.tagName, "BUTTON");
    const emoji = btn.querySelector(".meal-emoji");
    assert.ok(emoji, "emoji span present");
    assert.equal(emoji.getAttribute("aria-hidden"), "true");
    assert.ok(btn.querySelector(".meal-name").textContent.length > 0);
  }
});

test("first screen is a 3x2 category grid with a full-width neutral tile", () => {
  const options = document.querySelectorAll("#mealGrid .meal-option");
  assert.equal(options.length, 7, "seven first-screen tiles");
  // Six category tiles + the full-width "Mijn eigen eten" tile.
  const breed = document.querySelectorAll("#mealGrid .meal-option--breed");
  assert.equal(breed.length, 1, "exactly one full-width tile");
  assert.equal(breed[0].dataset.meal, "eigen", "the full-width tile is mijn eigen eten");
  // Category order follows the review: aardappels, rijst of noedels, pasta,
  // yoghurt/kwark/pap, boterhammen, pannenkoeken.
  const order = options.map((b) => b.dataset.meal);
  assert.deepEqual(order, [
    "aardappels",
    "rijst_of_noedels",
    "pasta",
    "yoghurt_kwark_pap",
    "boterhammen",
    "pannenkoeken",
    "eigen",
  ]);
  assert.ok(html.includes("#mealGrid"), "3-column grid CSS targets #mealGrid");
  assert.ok(
    html.includes("repeat(3, 1fr)"),
    "first screen uses a three-column grid"
  );
  assert.ok(
    html.includes(".meal-option--breed"),
    "full-width tile CSS exists"
  );
});

test("step 2 is a checkbox group, not a radiogroup", () => {
  const grid = document.getElementById("extraGrid");
  assert.equal(grid.getAttribute("role"), "group");
  for (const btn of document.querySelectorAll("#extraGrid .meal-option")) {
    assert.equal(btn.getAttribute("role"), "checkbox");
  }
});

test("picker dialog has dialog semantics and a visible focus style", () => {
  const picker = document.getElementById("mealPicker");
  assert.equal(picker.getAttribute("role"), "dialog");
  assert.equal(picker.getAttribute("aria-modal"), "true");
  assert.equal(picker.getAttribute("aria-labelledby"), "pickerTitle");
  assert.ok(html.includes(".meal-option:focus-visible"), "visible focus style");
});

// ---------------------------------------------------------------------------
// Behaviour: selection, persistence, change, skip, keyboard
// ---------------------------------------------------------------------------

test("initial state shows a meal-choice button and hides the play area", () => {
  const chip = document.getElementById("mealChip");
  assert.equal(chip.tagName, "BUTTON");
  assert.equal(
    document.getElementById("mealChipText").textContent,
    "Kies je eten"
  );
  assert.equal(document.getElementById("food").textContent, "🍽️");
  assert.ok(!chip.classList.contains("chosen"));
  assert.ok(document.getElementById("playArea").hidden);
});

test("selecting a meal updates chip, plate, and radio state", () => {
  sandbox.openMealPicker();
  click(mealButton("pasta"));

  assert.equal(
    document.getElementById("mealChipText").textContent,
    "Je eet nu: Pasta"
  );
  assert.equal(document.getElementById("mealChipEmoji").textContent, "🍝");
  assert.equal(document.getElementById("food").textContent, "🍝");
  assert.equal(mealButton("pasta").getAttribute("aria-checked"), "true");
  assert.equal(mealButton("boterhammen").getAttribute("aria-checked"), "false");
  assert.ok(mealButton("pasta").classList.contains("selected"));
  assert.ok(document.getElementById("mealChip").classList.contains("chosen"));
  assert.ok(!document.getElementById("playArea").hidden);
});

test("meal choice persists in the session and can be changed deliberately", () => {
  // Close and reopen: the earlier choice must survive outside the dialog.
  sandbox.closeMealPicker();
  assert.ok(!document.getElementById("mealPicker").classList.contains("show"));
  sandbox.openMealPicker();

  assert.equal(mealButton("pasta").getAttribute("aria-checked"), "true");
  assert.equal(document.activeElement, mealButton("pasta"));
  assert.equal(
    document.getElementById("mealChipText").textContent,
    "Je eet nu: Pasta"
  );

  // Deliberate change to Boterhammen.
  click(mealButton("boterhammen"));
  sandbox.closeMealPicker();

  assert.equal(
    document.getElementById("mealChipText").textContent,
    "Je eet nu: Boterhammen"
  );
  assert.equal(mealButton("pasta").getAttribute("aria-checked"), "false");
  assert.equal(mealButton("boterhammen").getAttribute("aria-checked"), "true");
});

test("step 2 is optional, multi-select, and skippable without pressure", () => {
  sandbox.openMealPicker();
  click(mealButton("rijst_of_noedels"));

  sandbox.confirmMealStep();
  assert.equal(document.getElementById("pickerStep1").hidden, true);
  assert.equal(document.getElementById("pickerStep2").hidden, false);
  assert.equal(
    extraButton("rijst_of_noedels").getAttribute("aria-checked"),
    "true",
    "preset preselects rijst of noedels"
  );

  click(extraButton("groente"));
  click(extraButton("vlees"));
  assert.equal(extraButton("groente").getAttribute("aria-checked"), "true");
  assert.equal(extraButton("vlees").getAttribute("aria-checked"), "true");
  assert.equal(
    extraButton("rijst_of_noedels").getAttribute("aria-checked"),
    "true",
    "multi-select keeps the starch tile"
  );

  sandbox.skipMealStep();
  assert.ok(!document.getElementById("mealPicker").classList.contains("show"));
  assert.equal(
    extraButton("rijst_of_noedels").getAttribute("aria-checked"),
    "true",
    "skip restores the preset preselect"
  );
  assert.equal(extraButton("groente").getAttribute("aria-checked"), "false");
  assert.equal(
    document.getElementById("mealChipText").textContent,
    "Je eet nu: Rijst of noedels"
  );
});

test("aardappels, rijst of noedels, and pasta preselect their basis tile", () => {
  sandbox.openMealPicker();
  click(mealButton("pasta"));
  sandbox.confirmMealStep();
  assert.equal(extraButton("pasta").getAttribute("aria-checked"), "true");
  assert.equal(
    document.getElementById("pickerTitle2").textContent,
    "Wat ligt er op je bord?"
  );
  sandbox.closeMealPicker();

  sandbox.openMealPicker();
  click(mealButton("aardappels"));
  sandbox.confirmMealStep();
  assert.equal(extraButton("aardappels").getAttribute("aria-checked"), "true");
  sandbox.closeMealPicker();

  sandbox.openMealPicker();
  click(mealButton("rijst_of_noedels"));
  sandbox.confirmMealStep();
  assert.equal(
    extraButton("rijst_of_noedels").getAttribute("aria-checked"),
    "true"
  );
  sandbox.closeMealPicker();
});

test("yoghurt, boterhammen, and pannenkoeken skip step 2 and start the game", () => {
  for (const key of ["yoghurt_kwark_pap", "boterhammen", "pannenkoeken"]) {
    sandbox.openMealPicker();
    click(mealButton(key));
    sandbox.confirmMealStep();
    assert.ok(
      !document.getElementById("mealPicker").classList.contains("show"),
      `${key} closes the picker instead of opening the plate step`
    );
    assert.equal(document.getElementById("pickerStep2").hidden, true);
    assert.ok(!document.getElementById("playArea").hidden);
  }
});

test("eigen eten still opens step 2 with no basis preselect", () => {
  sandbox.openMealPicker();
  click(mealButton("eigen"));
  sandbox.confirmMealStep();
  assert.equal(document.getElementById("pickerStep1").hidden, true);
  assert.equal(document.getElementById("pickerStep2").hidden, false);
  for (const basis of ["aardappels", "pasta", "rijst_of_noedels"]) {
    assert.equal(
      extraButton(basis).getAttribute("aria-checked"),
      "false",
      `eigen preselects nothing (${basis} stayed off)`
    );
  }
  click(extraButton("groente"));
  assert.equal(extraButton("groente").getAttribute("aria-checked"), "true");
  sandbox.closeMealPicker();
});

test("confirming extras keeps multi-select for the session", () => {
  sandbox.openMealPicker();
  click(mealButton("pasta"));
  sandbox.confirmMealStep();
  click(extraButton("vegetarisch"));
  sandbox.confirmMealStep();

  assert.ok(!document.getElementById("mealPicker").classList.contains("show"));
  assert.equal(extraButton("pasta").getAttribute("aria-checked"), "true");
  assert.equal(extraButton("vegetarisch").getAttribute("aria-checked"), "true");
});

test("arrow keys move and select inside the meal radiogroup with roving tabindex", () => {
  sandbox.openMealPicker();
  const buttons = document.querySelectorAll("#mealGrid .meal-option");
  const pasta = mealButton("pasta");
  click(pasta);
  assert.equal(document.activeElement, pasta);
  assert.equal(pasta.tabIndex, 0, "selected option is the tab stop");
  for (const b of buttons) {
    if (b !== pasta)
      assert.equal(b.tabIndex, -1, "others removed from tab order");
  }

  pressKey(pasta, "ArrowRight");
  const yoghurt = mealButton("yoghurt_kwark_pap");

  assert.equal(document.activeElement, yoghurt);
  assert.equal(yoghurt.getAttribute("aria-checked"), "true");
  assert.equal(pasta.getAttribute("aria-checked"), "false");
  assert.equal(
    document.getElementById("mealChipText").textContent,
    "Je eet nu: Yoghurt, kwark of pap"
  );

  pressKey(yoghurt, "ArrowLeft");
  assert.equal(document.activeElement, pasta);
  assert.equal(pasta.getAttribute("aria-checked"), "true");

  const eerst = mealButton("aardappels");
  eerst.focus();
  pressKey(eerst, "ArrowUp");
  assert.equal(document.activeElement, mealButton("eigen"));
});

test("step 2 arrows move focus only and do not toggle checkboxes", () => {
  sandbox.openMealPicker();
  click(mealButton("eigen"));
  sandbox.confirmMealStep();
  const first = extraOptionButtonsWait();
  function extraOptionButtonsWait() {
    return document.querySelectorAll("#extraGrid .meal-option");
  }
  const start = extraOptionButtonsWait()[0];
  start.focus();
  const startChecked = start.getAttribute("aria-checked");
  pressKey(start, "ArrowDown");
  const active = document.activeElement;
  assert.notEqual(active, start);
  assert.equal(start.getAttribute("aria-checked"), startChecked);
  assert.equal(active.getAttribute("role"), "checkbox");
  sandbox.closeMealPicker();
});

test("Tab is trapped inside the open dialog and Escape closes it", () => {
  sandbox.openMealPicker();
  const box = document.querySelector("#mealPicker .picker-box");

  const focusables = box
    .querySelectorAll("button")
    .filter((b) => b.closest("[hidden]") === null);
  const last = focusables[focusables.length - 1];
  const first = focusables[0];
  last.focus();
  pressKey(last, "Tab");
  assert.equal(document.activeElement, first, "Tab wraps to first control");

  pressKey(document.getElementById("mealPicker"), "Escape");
  assert.ok(
    !document.getElementById("mealPicker").classList.contains("show"),
    "picker closed on Escape"
  );
  assert.equal(
    document.activeElement,
    document.getElementById("mealChip"),
    "focus returns to the meal chip opener"
  );
});

test("step transition moves focus into the visible step", () => {
  sandbox.openMealPicker();
  sandbox.confirmMealStep();
  const step2Buttons = document.querySelectorAll("#extraGrid .meal-option");
  assert.ok(
    step2Buttons.includes(document.activeElement),
    "focus lands on a step-2 option"
  );
  sandbox.closeMealPicker();
});
