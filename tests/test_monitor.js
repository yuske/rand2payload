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
}

test("monitor logs Math.random invocations from different call sites", async () => {
  const envSnapshot = {
    log: process.env.MATH_RANDOM_LOG,
    verbose: process.env.MATH_RANDOM_VERBOSE,
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
