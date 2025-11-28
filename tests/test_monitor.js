"use strict";

const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const monitorPath = require.resolve(path.join(__dirname, "..", "monitor.js"));

function resetMonitor(envSnapshot) {
  if (typeof global.unmonitorMathRandom === "function") {
    global.unmonitorMathRandom();
    delete global.unmonitorMathRandom;
  }
  delete global.__MATH_RANDOM_MONITOR_INSTALLED__;
  delete require.cache[monitorPath];
  process.env.MATH_RANDOM_LOG = envSnapshot.log;
  process.env.MATH_RANDOM_VERBOSE = envSnapshot.verbose;
  process.env.MATH_RANDOM_FILTER = envSnapshot.filter;
}

test("monitor logs Math.random invocations from different call sites", async () => {
  const envSnapshot = {
    log: process.env.MATH_RANDOM_LOG,
    verbose: process.env.MATH_RANDOM_VERBOSE,
    filter: process.env.MATH_RANDOM_FILTER,
  };

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "math-random-"));
  const logFile = path.join(tmpDir, "math-random-traces.log");

  process.env.MATH_RANDOM_LOG = logFile;
  process.env.MATH_RANDOM_VERBOSE = "0";

  try {
    require(monitorPath);

    function directCall() {
      Math.random();
    }

    function destructuredCall() {
      const { random } = Math;
      random();
    }

    function aliasedCall() {
      const r = Math.random;
      r();
    }

    (function nested() {
      directCall();
      destructuredCall();
      aliasedCall();
    })();

    await new Promise((resolve) => {
      setTimeout(() => {
        Math.random(); // timer call
        resolve();
      }, 5);
    });

    const contents = fs.readFileSync(logFile, "utf8");
    const entries = contents.trim().split(/\n\n+/);
    //console.log("Log entries:", entries);

    assert.equal(entries.length, 4, "should log each Math.random call");
    entries.forEach((entry, index) => {
      assert.match(
        entry,
        new RegExp(`Math\\.random\\(\\) #${index + 1}`),
        `entry ${index + 1} should include call counter`
      );
    });
  } finally {
    resetMonitor(envSnapshot);
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("MATH_RANDOM_FILTER suppresses matching entries but still counts invocations", () => {
  const envSnapshot = {
    log: process.env.MATH_RANDOM_LOG,
    verbose: process.env.MATH_RANDOM_VERBOSE,
    filter: process.env.MATH_RANDOM_FILTER,
  };

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "math-random-filter-"));
  const logFile = path.join(tmpDir, "math-random-traces.log");

  process.env.MATH_RANDOM_LOG = logFile;
  process.env.MATH_RANDOM_VERBOSE = "0";
  process.env.MATH_RANDOM_FILTER = "hiddenCall;filteredCall";

  try {
    require(monitorPath);

    function filteredCall() {
      Math.random();
    }

    function visibleCall() {
      Math.random();
    }

    function hiddenCall() {
      Math.random();
    }

    filteredCall();
    filteredCall();
    visibleCall();
    hiddenCall()

    const contents = fs.readFileSync(logFile, "utf8");
    const entries = contents.trim().split(/\n\n+/);

    assert.equal(entries.length, 1, "should log only the visible call");
    assert.match(entries[0], /Math\.random\(\) #3/);
    assert.equal(
      Math.random.__count,
      4,
      "call counter increments even when filtered"
    );
  } finally {
    resetMonitor(envSnapshot);
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});
