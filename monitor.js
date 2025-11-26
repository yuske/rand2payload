// Monitor all Math.random() calls in Node and capture stack traces.
//
// Usage (instrument your whole app):
//   node -r ./monitor.js app.js
//
// Quick self-test (runs some sample calls if you run this file directly):
//   node monitor.js
//
// Env vars:
//   MATH_RANDOM_LOG=/path/to/file.log   (default: ./math-random-traces.log)
//   MATH_RANDOM_VERBOSE=0               (silence console logging)

"use strict";

const fs = require("fs");
const path = require("path");

const LOG_FILE =
  process.env.MATH_RANDOM_LOG ||
  path.join(process.cwd(), "math-random-traces.log");
const LOG_TO_CONSOLE = process.env.MATH_RANDOM_VERBOSE !== "0";

function installMonitor() {
  // Guard: don’t install twice
  if (global.__MATH_RANDOM_MONITOR_INSTALLED__) return;
  global.__MATH_RANDOM_MONITOR_INSTALLED__ = true;

  const original = Math.random;

  // Our wrapper: logs a trimmed stack, then calls the original
  function monitoredRandom() {
    const err = new Error("Math.random()");
    // Drop this wrapper from the stack:
    if (Error.captureStackTrace) {
      Error.captureStackTrace(err, monitoredRandom);
    }
    const now = new Date().toISOString();
    monitoredRandom.__count = (monitoredRandom.__count || 0) + 1;

    const stack = (err.stack || "")
      .split("\n")
      .filter(Boolean)
      .slice(1) // remove "Error: …" header line
      .join("\n");

    const entry =
      `[${now}] Math.random() #${monitoredRandom.__count}\n` + stack + "\n\n";

    try {
      fs.appendFileSync(LOG_FILE, entry);
    } catch (e) {
      // Fallback to console if file write fails
      console.warn("Failed to write Math.random log file:", e.message);
      console.warn(entry);
    }

    if (LOG_TO_CONSOLE) {
      // Console echo for immediate visibility
      console.warn(entry);
    }

    // Call through to the original
    return Reflect.apply(original, Math, []);
  }

  // Keep a handle to unpatch if needed
  monitoredRandom.__original = original;

  // Patch Math.random
  Object.defineProperty(Math, "random", {
    value: monitoredRandom,
    configurable: true,
    writable: true,
    enumerable: false,
  });

  // Optional: expose unpatch on global for convenience
  global.unmonitorMathRandom = function unmonitorMathRandom() {
    const current = Math.random;
    if (current && current.__original) {
      Object.defineProperty(Math, "random", {
        value: current.__original,
        configurable: true,
        writable: true,
        enumerable: false,
      });
      delete global.__MATH_RANDOM_MONITOR_INSTALLED__;
      return true;
    }
    return false;
  };
}

installMonitor();
