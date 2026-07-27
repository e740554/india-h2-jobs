'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const PROJECT_ROOT = path.join(__dirname, '..');
const webTemplatePath = path.join(PROJECT_ROOT, 'web', 'main.js.template');

function loadRuntime() {
  const source = fs.readFileSync(webTemplatePath, 'utf8');
  const sandbox = {
    console,
    module: { exports: {} },
    exports: {},
    setTimeout,
    clearTimeout,
    URL,
  };
  sandbox.globalThis = sandbox;
  vm.runInNewContext(source, sandbox, { filename: webTemplatePath });
  return sandbox.module.exports || sandbox.H2AtlasRuntime;
}

const runtime = loadRuntime();

function run() {
  const raw = process.argv[2] || '{}';
  const input = JSON.parse(raw);
  const output = runtime.buildBriefingModel(input);
  process.stdout.write(JSON.stringify(output, null, 2));
}

run();
