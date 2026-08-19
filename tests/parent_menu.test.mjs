// Zero-dependency tests for the issue #8 parent/info menu (oudermenu).
//
// Runs the real inline <script> from index.html inside the same minimal DOM
// shim style as tests/meal_picker.test.mjs (this repo is a zero-dependency
// static site, so no jsdom).
//
// Run: node --test tests/parent_menu.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(path.join(ROOT, "index.html"), "utf-8");

// ---------------------------------------------------------------------------
// Minimal DOM (same subset as meal_picker.test.mjs)
// ---------------------------------------------------------------------------

const VOID_TAGS = new Set(["meta", "br", "hr", "img", "input", "link", "source"]);

class Classlist {
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
    this.classList = new Classlist(this);
    this._textContent = "";
    this.style = {};
    this.offsetWidth = 0;
  }
  get textContent() {
    let out = this._textContent;
    for (const child of this.children) out += child.textContent;
    return out;
  }
  set textContent(v) {
    this._textContent = String(v);
    this.children = [];
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
    const m = token.match(/^([a-zA-Z][\w-]*)([.#][\w-]+)*$/);
    if (m) {
      if (this.tagName !== m[1].toUpperCase()) return false;
      for (const extra of (m[2] ? m[2].match(/[.#][\w-]+/g) : []) || []) {
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
    if (!this._matchesCompound(parts[parts.length - 1])) return false;
    // Descendant combinator: each earlier part matches some strict
    // ancestor, consumed in order walking upward (greedy, CSS-like).
    let node = this.parentNode;
    let idx = parts.length - 2;
    while (idx >= 0 && node) {
      if (typeof node._matchesCompound === "function" && node._matchesCompound(parts[idx])) {
        idx--;
      }
      node = node.parentNode;
    }
    return idx < 0;
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
    if (text) stack[stack.length - 1]._textContent = text;
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

function pressKey(el, key, shiftKey = false) {
  el.dispatchEvent(makeEvent("keydown", { key, shiftKey }));
}

function oudermenu() {
  return document.getElementById("oudermenu");
}

// ---------------------------------------------------------------------------
// Static source checks (issue #8 scope)
// ---------------------------------------------------------------------------

test("the AI-voice disclosure moved off the main child screen", () => {
  assert.ok(
    !html.includes('<p class="speech-disclosure">'),
    "old always-visible disclosure paragraph removed"
  );
  assert.ok(
    !html.includes(".speech-disclosure"),
    "leftover disclosure style removed"
  );
});

test("oudermenu button sits next to the sound button with a clear label", () => {
  const controls = document.querySelector(".topbar-controls");
  assert.ok(controls, "topbar controls group exists");
  const ids = controls.querySelectorAll("button").map((b) => b.id);
  assert.deepEqual(ids, ["soundButton", "parentButton"]);
  const parent = document.getElementById("parentButton");
  assert.equal(
    parent.getAttribute("aria-label"),
    "Informatie voor ouders"
  );
  assert.equal(parent.getAttribute("aria-haspopup"), "dialog");
  assert.equal(parent.getAttribute("aria-expanded"), "false");
});

test("oudermenu dialog has dialog semantics and labelled content", () => {
  const menu = oudermenu();
  assert.equal(menu.getAttribute("role"), "dialog");
  assert.equal(menu.getAttribute("aria-modal"), "true");
  assert.equal(menu.getAttribute("aria-labelledby"), "oudermenuTitle");
  assert.equal(menu.getAttribute("aria-describedby"), "oudermenuInfo");

  const stem = document.getElementById("oudermenuStem");
  assert.equal(stem.textContent, "De gesproken teksten zijn met AI gegenereerd.");

  const info = document.getElementById("oudermenuInfo");
  assert.ok(info.textContent.length > 0, "described info block has text");
});

test("restart moved off the main screen actions row", () => {
  const actions = document.querySelector("section.actions");
  const labels = actions.querySelectorAll("button").map((b) => b.textContent);
  assert.ok(!labels.includes("Opnieuw"), "no bare Opnieuw on the main screen");
  const opnieuw = document.getElementById("oudermenuOpnieuw");
  assert.equal(opnieuw.textContent, "Opnieuw beginnen");
});

test("no microphone or listening claims without a verified basis", () => {
  // Verified for this change: index.html has no getUserMedia /
  // mediaDevices / SpeechRecognition / WebSocket / fetch / sendBeacon /
  // MediaRecorder / createMediaStreamSource. Claim only what the code shows.
  const forbidden = [
    /getUserMedia/,
    /mediaDevices/,
    /SpeechRecognition/,
    /WebSocket/,
    /EventSource/,
    /sendBeacon/,
    /MediaRecorder/,
    /createMediaStreamSource/,
  ];
  for (const re of forbidden) assert.ok(!re.test(html), `no ${re} in HTML`);
});

// ---------------------------------------------------------------------------
// Behaviour: open/close, focus, keyboard, restart, sound
// ---------------------------------------------------------------------------

test("opening the oudermenu traps focus, Escape returns to the opener", () => {
  const parentBtn = document.getElementById("parentButton");
  parentBtn.focus();
  sandbox.openOudermenu();

  assert.ok(oudermenu().classList.contains("show"));
  assert.equal(
    parentBtn.getAttribute("aria-expanded"),
    "true",
    "opener reflects expanded state"
  );
  assert.equal(
    document.activeElement,
    document.getElementById("oudermenuClose"),
    "focus enters the dialog on its close button"
  );

  // Tab cycles only through oudermenu buttons.
  const menuButtons = oudermenu()
    .querySelectorAll("button")
    .filter((b) => !b.disabled);
  for (let i = 0; i < menuButtons.length; i++) {
    pressKey(document.activeElement, "Tab");
  }
  assert.ok(
    menuButtons.includes(document.activeElement),
    "Tab keeps focus inside the oudermenu"
  );

  pressKey(oudermenu(), "Escape");
  assert.ok(!oudermenu().classList.contains("show"), "Escape closes");
  assert.equal(
    document.activeElement,
    parentBtn,
    "focus returns to the opener button"
  );
  assert.equal(parentBtn.getAttribute("aria-expanded"), "false");
});

test("the oudermenu sound action mirrors the shared sound state", () => {
  document.getElementById("parentButton").focus();
  sandbox.openOudermenu();
  const geluid = document.getElementById("oudermenuGeluid");

  assert.equal(geluid.textContent, "Geluid uit", "sound is on by default");
  assert.equal(geluid.getAttribute("aria-pressed"), "false");

  sandbox.toggleOuderGeluid();
  assert.equal(geluid.textContent, "Geluid aan");
  assert.equal(geluid.getAttribute("aria-pressed"), "true");
  assert.equal(
    document.getElementById("soundButton").textContent,
    "🔇",
    "topbar toggle follows the shared state"
  );

  sandbox.toggleOuderGeluid();
  assert.equal(geluid.textContent, "Geluid uit");
  assert.equal(
    document.getElementById("soundButton").textContent,
    "🔊"
  );
  sandbox.sluitOudermenu();
});

test("Opnieuw beginnen resets the adventure and closes the menu", () => {
  sandbox.selectMeal("pasta");
  sandbox.hapGenomen();
  sandbox.hapGenomen();
  sandbox.hapGenomen();
  assert.equal(document.getElementById("counter").textContent, "3");

  const parentBtn = document.getElementById("parentButton");
  parentBtn.focus();
  sandbox.openOudermenu();
  sandbox.opnieuwViaOudermenu();

  assert.ok(!oudermenu().classList.contains("show"), "menu closed");
  assert.equal(
    document.activeElement,
    parentBtn,
    "focus returns to the opener after restart"
  );
  assert.equal(document.getElementById("counter").textContent, "0");
  assert.equal(
    document.getElementById("message").textContent,
    "Klaar voor de eerste superhap?"
  );
});

test("resetGame closes an open oudermenu as well", () => {
  document.getElementById("parentButton").focus();
  sandbox.openOudermenu();
  assert.ok(oudermenu().classList.contains("show"));
  sandbox.resetGame();
  assert.ok(
    !oudermenu().classList.contains("show"),
    "resetGame closes the open oudermenu"
  );
});
