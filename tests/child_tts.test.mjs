// Zero-dependency tests for the issue #15 child-facing speech pack.
//
// Runs the real inline <script> from index.html inside a minimal DOM shim
// (same approach as meal_picker.test.mjs: this repo is a zero-dependency
// static site, so no jsdom). The Audio stub records every src assignment so
// tests can assert exactly which frozen clip is requested at each moment.
//
// Run: node --test tests/child_tts.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync, mkdtempSync, rmSync, cpSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { join } from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(path.join(ROOT, "index.html"), "utf-8");

// ---------------------------------------------------------------------------
// Minimal DOM (same shape as meal_picker.test.mjs)
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

parsedBody.parentNode = document;

// ---------------------------------------------------------------------------
// Speech-recording Audio stub
// ---------------------------------------------------------------------------

const played = [];

class AudioStub {
  constructor() {
    this._src = "";
    this.preload = "";
    this.volume = 1;
    this.currentTime = 0;
  }
  set src(v) {
    this._src = v;
    played.push(v);
  }
  get src() {
    return this._src;
  }
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

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, "inline <script> found in index.html");
vm.runInContext(scriptMatch[1], sandbox);

const playedSince = () => played.slice(marker);
let marker = 0;
const resetLog = () => {
  marker = played.length;
};
const lastClip = () => played[played.length - 1];

function click(el) {
  el.dispatchEvent({ type: "click", bubbles: true, target: null, preventDefault() {} });
}

function mealButton(key) {
  return document
    .querySelectorAll("#mealGrid .meal-option")
    .find((b) => b.dataset.meal === key);
}

// ---------------------------------------------------------------------------
// Static checks: pack wiring
// ---------------------------------------------------------------------------


test("picker group headings are decorative and hints do not invent extra copy", () => {
  const labels = [...html.matchAll(/class="picker-group-label"([^>]*)>([^<]+)</g)];
  assert.ok(labels.length >= 3, "group labels present");
  for (const [, attrs, label] of labels) {
    assert.match(attrs, /aria-hidden="true"/, `${label} is aria-hidden`);
  }
  assert.equal(html.includes("niet meer."), false, "deselect hint does not invent extra copy");
});

test("SPEECH_MAP mirrors the frozen inventory in speech_inventory.py", () => {
  const block = html.match(/const SPEECH_MAP = \{(.*?)\};/s);
  assert.ok(block, "SPEECH_MAP present");
  const mapKeys = [...block[1].matchAll(/([A-Za-z0-9_]+):\s*"[^"]+"/g)].map((m) => m[1]);

  const inventorySrc = readFileSync(path.join(ROOT, "scripts", "speech_inventory.py"), "utf-8");
  const invIds = [...inventorySrc.matchAll(/"id": "([a-z0-9_]+)"/g)].map((m) => m[1]);

  assert.deepEqual([...mapKeys].sort(), [...invIds].sort());
  assert.equal(mapKeys.length, invIds.length);
});

test("every SPEECH_MAP clip exists on disk and in the manifest", () => {
  const manifest = JSON.parse(readFileSync(path.join(ROOT, "audio", "manifest.json"), "utf-8"));
  const block = html.match(/const SPEECH_MAP = \{(.*?)\};/s);
  const entries = [...block[1].matchAll(/([A-Za-z0-9_]+):\s*"([^"]+)"/g)];
  for (const [, id, file] of entries) {
    assert.ok(manifest.clips[id], `manifest has ${id}`);
    assert.equal(manifest.clips[id].file, file);
    assert.ok(
      existsSync(path.join(ROOT, "audio", file)),
      `${file} on disk`
    );
  }
});

test("validator fails when a child-facing clip is missing", () => {
  // Non-destructive: copy the repo to a temp dir, remove one clip, and run
  // the real validator there. The manifest still lists the clip, so the
  // "missing file / missing on disk" checks must fail.
  const tmp = mkdtempSync(join(tmpdir(), "hapjes-tts-"));
  cpSync(ROOT, tmp, { recursive: true });
  const victim = path.join(tmp, "audio", "chip_eat_pasta.mp3");
  assert.ok(existsSync(victim));
  rmSync(victim);
  let failed = false;
  let stderr = "";
  try {
    execFileSync("python3", [path.join(tmp, "scripts", "validate_audio_assets.py")], {
      stdio: ["ignore", "pipe", "pipe"],
    });
  } catch (err) {
    failed = true;
    stderr = String(err.stdout || err.stderr || "");
  }
  assert.ok(failed, "validator exits non-zero on a missing child clip");
  assert.match(stderr, /chip_eat_pasta/, "validator names the missing clip");
  rmSync(tmp, { recursive: true, force: true });
});

// ---------------------------------------------------------------------------
// Behaviour: which clip plays when
// ---------------------------------------------------------------------------

test("picker step titles are spoken as one title+note clip per step", () => {
  resetLog();
  sandbox.openMealPicker();
  assert.equal(lastClip(), "audio/picker_title_1.mp3");
  sandbox.confirmMealStep(); // advance to step 2
  assert.equal(lastClip(), "audio/picker_title_2.mp3");
  sandbox.closeMealPicker();
});

test("selecting a meal speaks the chosen meal name", () => {
  sandbox.openMealPicker();
  resetLog();
  click(mealButton("pasta"));
  assert.equal(lastClip(), "audio/meal_pasta.mp3");
  click(mealButton("pannenkoeken"));
  assert.equal(lastClip(), "audio/meal_pannenkoeken.mp3");
  sandbox.closeMealPicker();
});

test("selecting an extra speaks the chosen extra name", () => {
  sandbox.openMealPicker();
  sandbox.confirmMealStep();
  resetLog();
  const groente = document
    .querySelectorAll("#extraGrid .meal-option")
    .find((b) => b.dataset.extra === "groente");
  click(groente);
  assert.equal(lastClip(), "audio/extra_groente.mp3");
  sandbox.closeMealPicker();
});

test("first confirmed meal plays the start clip once, later closes speak the chip line", () => {
  // A meal is already selected from earlier tests; reset the session flag by
  // simulating the real first-start path: resetGame keeps the meal, so the
  // first-start flag is what matters. Fresh start happens once per session;
  // the earlier tests already consumed it, so assert the chip behaviour and
  // that start is never replayed on later closes.
  sandbox.openMealPicker();
  resetLog();
  sandbox.closeMealPicker();
  assert.equal(lastClip(), "audio/chip_eat_pannenkoeken.mp3");
  const starts = playedSince().filter((s) => s === "audio/start.mp3");
  assert.equal(starts.length, 0, "start clip not replayed on later picker closes");
});

test("start clip plays on the true first close and not while the play area is hidden", () => {
  // Fresh script context for a pristine first-start path.
  const fresh = makeFreshSandbox();
  assert.ok(fresh.document.getElementById("playArea").hidden);
  // Opening the picker alone never speaks the start line.
  fresh.sandbox.openMealPicker();
  const startsBefore = fresh.played.filter((s) => s === "audio/start.mp3").length;
  assert.equal(startsBefore, 0, "start never plays while the start line is hidden");
  // Choose a meal: play area becomes visible inside the picker.
  fresh.clickMeal("pasta");
  assert.ok(!fresh.document.getElementById("playArea").hidden);
  // Close: the start line is now the visible message; the start clip plays.
  fresh.sandbox.closeMealPicker();
  assert.equal(fresh.lastClip(), "audio/start.mp3");
});

test("reset speaks the start line clip", () => {
  resetLog();
  sandbox.resetGame();
  assert.equal(lastClip(), "audio/start.mp3");
});

test("schatkist open speaks title + standing question, not the pot count", () => {
  resetLog();
  sandbox.openSchatkist();
  assert.equal(lastClip(), "audio/schatkist_intro.mp3");
  const after = playedSince();
  assert.equal(after.length, 1, "exactly one clip plays on open; no numeric pot clip");
  sandbox.sluitSchatkist();
});

test("choosing a goal speaks the active-status clip; affordable unlock speaks Van jou!", () => {
  sandbox.openSchatkist();
  resetLog();
  // panda costs 8; pot is 0 after the spaar reset in earlier tests only if
  // that test ran. Drive to a known state instead: pick the cheapest active
  // goal path by using kiesDoel directly on a not-yet-unlocked item.
  // After resetGame the pot persists (Opnieuw keeps the spaarpot), so take
  // the panda: whatever happens, the spoken clip must match the row status.
  sandbox.kiesDoel("panda");
  const row = sandbox.document.getElementById("schatkistList").children.find((li) => {
    const info = li.children[1];
    return info && info.children[0] && info.children[0].textContent === "Dierenvriendje";
  });
  const status = row && row.children[2] ? row.children[2].textContent : "";
  if (status.includes("Van jou")) {
    assert.equal(lastClip(), "audio/schatkist_vrij.mp3");
  } else {
    assert.equal(lastClip(), "audio/schatkist_actief.mp3");
  }
  sandbox.sluitSchatkist();
});

test("spaar reset question and confirmation are spoken", () => {
  sandbox.openSchatkist();
  resetLog();
  sandbox.bevestigSpaarReset();
  assert.equal(lastClip(), "audio/spaar_reset_vraag.mp3");
  sandbox.spaarResetBevestig();
  assert.equal(lastClip(), "audio/spaar_reset_nieuw.mp3");
  sandbox.sluitSchatkist();
});

test("goal unlock during play speaks the Gefeliciteerd line for that item", () => {
  // confetti costs 3: empty pot (previous test reset it), choose it, take
  // three hapjes -> unlock_confetti must be spoken.
  sandbox.openSchatkist();
  sandbox.kiesDoel("confetti");
  sandbox.sluitSchatkist();
  resetLog();
  sandbox.hapGenomen();
  sandbox.hapGenomen();
  sandbox.hapGenomen();
  assert.ok(
    playedSince().includes("audio/unlock_confetti.mp3"),
    `unlock_confetti spoken; got ${JSON.stringify(playedSince())}`
  );
  assert.match(
    sandbox.document.getElementById("message").textContent,
    /Gefeliciteerd! Feestconfetti is nu van jou!/
  );
});

test("oudermenu copy is never spoken: no clips exist for parent lines", () => {
  const oudermenu = document.getElementById("oudermenu");
  assert.ok(oudermenu);
  const text = collectText(oudermenu);
  for (const line of [
    "De gesproken teksten zijn met AI gegenereerd.",
    "Spelen stopt vanzelf.",
    "Opnieuw beginnen",
  ]) {
    assert.ok(text.includes(line), `oudermenu still shows ${line}`);
  }
  const manifest = JSON.parse(readFileSync(path.join(ROOT, "audio", "manifest.json"), "utf-8"));
  for (const clip of Object.values(manifest.clips)) {
    assert.ok(
      !clip.text.includes("AI gegenereerd"),
      "no oudermenu copy frozen as a clip"
    );
  }
});

function collectText(el) {
  let out = el.textContent || "";
  for (const c of el.children) out += collectText(c);
  return out;
}

// Fresh-context helper for the pristine first-start test.
function makeFreshSandbox() {
  const body = parseHtml(html);
  const doc = {
    body,
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
      return collect(body, []).find((el) => el._attrs.id === id) || null;
    },
    querySelector(sel) {
      return this.querySelectorAll(sel)[0] || null;
    },
    querySelectorAll(sel) {
      return collect(body, []).filter((el) => el._matchesSelector(sel));
    },
    createElement(tag) {
      return new Element(tag);
    },
  };
  body.parentNode = doc;
  const freshPlayed = [];
  class FreshAudio {
    constructor() {
      this._src = "";
    }
    set src(v) {
      this._src = v;
      freshPlayed.push(v);
    }
    get src() {
      return this._src;
    }
    play() {
      return { catch() {} };
    }
    pause() {
      return { catch() {} };
    }
  }
  const sb = {
    document: doc,
    Audio: FreshAudio,
    Math,
    setTimeout: (fn) => fn(),
  };
  sb.window = sb;
  vm.createContext(sb);
  vm.runInContext(scriptMatch[1], sb);
  return {
    sandbox: sb,
    document: doc,
    played: freshPlayed,
    lastClip: () => freshPlayed[freshPlayed.length - 1],
    clickMeal(key) {
      const btn = doc
        .querySelectorAll("#mealGrid .meal-option")
        .find((b) => b.dataset.meal === key);
      btn.dispatchEvent({ type: "click", bubbles: true, target: null, preventDefault() {} });
    },
  };
}
