// Zero-dependency tests for issue #18: the reward ("Beloning!") dialog must
// follow the same overlay recipe as the picker / Schatkist / end dialogs.
//
// Pure static checks against the CSS in index.html — no DOM shim needed,
// stacking and scrim values are declared facts in the stylesheet.
//
// Run: node --test tests/reward_overlay.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(path.join(ROOT, "index.html"), "utf-8");

// ---------------------------------------------------------------------------
// Minimal CSS rule extractor (same idea as the DOM shims: no dependencies)
// ---------------------------------------------------------------------------

function cssRule(selector) {
  const start = html.indexOf(`${selector} {`);
  assert.ok(start !== -1, `selector ${selector} not found in index.html`);
  const body = html.slice(start, html.indexOf("}", start));
  return body;
}

function declaration(rule, property) {
  const match = rule.match(new RegExp(`${property}:\\s*([^;]+);`));
  return match ? match[1].trim() : null;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test("the reward dialog stacks above the confetti layer", () => {
  const confettiZ = Number(declaration(cssRule(".confetti-piece"), "z-index"));
  const rewardZ = Number(declaration(cssRule(".reward"), "z-index"));
  assert.ok(Number.isFinite(confettiZ), "confetti z-index parses");
  assert.ok(Number.isFinite(rewardZ), "reward z-index parses");
  // Issue #18: reward was z-index 20, below confetti (30), so confetti
  // rained over the "Beloning!" card text.
  assert.ok(
    rewardZ > confettiZ,
    `.reward z-index ${rewardZ} must sit above confetti z-index ${confettiZ}`
  );
});

test("the reward scrim uses the shared overlay dimmer, not a light wash", () => {
  const scrim = declaration(cssRule(".reward"), "background");
  // Recipe value shared by picker / Schatkist / end dialogs.
  assert.equal(scrim, "rgba(45, 42, 74, 0.72)");
});

test("the reward card stays opaque white like the other dialog cards", () => {
  const boxBg = declaration(cssRule(".reward-box"), "background");
  assert.equal(boxBg, "white");
  const opacity = declaration(cssRule(".reward-box"), "opacity");
  assert.ok(
    opacity === null || Number(opacity) === 1,
    "reward card must not be translucent"
  );
});

test("the reward overlay keeps the fixed inset: 0 dialog shape", () => {
  const rule = cssRule(".reward");
  // Do not convert a working inset: 0 dialog into the oudermenu shape.
  assert.equal(declaration(rule, "position"), "fixed");
  assert.equal(declaration(rule, "inset"), "0");
});
