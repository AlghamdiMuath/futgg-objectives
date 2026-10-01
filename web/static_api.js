"use strict";

// Public data comes from the daily Pages build. Private progress never leaves this browser.
const PRIVATE_KEY = 'futgg-objectives-private-v1';
const PYTHON_FILES = ['interpret_objectives.py', 'user_objectives.py',
  'optimize_matches.py', 'plan_objectives.py', 'prize_summary.py', 'daily_game_planner.py', 'browser_api.py'];

function privateData() {
  const saved = localStorage.getItem(PRIVATE_KEY);
  return saved ? JSON.parse(saved) : {state: null, settings: null};
}

async function initializePython() {
  const pyodide = await loadPyodide();
  const files = await Promise.all(PYTHON_FILES.map(async name => {
    const response = await fetch(`./${name}`, {cache: 'no-store'});
    if (!response.ok) throw Error(`Could not load ${name}`);
    return [name, await response.text()];
  }));
  for (const [name, contents] of files) pyodide.FS.writeFile(`/home/pyodide/${name}`, contents);
  pyodide.runPython("import sys, json; sys.path.insert(0, '/home/pyodide'); import browser_api");
  const response = await fetch('./fc27_interpreted.json', {cache: 'no-store'});
  if (!response.ok) throw Error('Could not load objective data');
  pyodide.globals.set('_source_json', await response.text());
  pyodide.runPython('browser_api.initialize(_source_json)');
  return pyodide;
}

const ready = initializePython();
async function callPython(expression, args) {
  const pyodide = await ready;
  pyodide.globals.set('_browser_args', JSON.stringify(args));
  return JSON.parse(pyodide.runPython(`browser_api.${expression}(*json.loads(_browser_args))`));
}

window.objectiveApi = {
  ready,
  async snapshot() {
    const {state, settings} = privateData();
    const result = await callPython('snapshot_json', [state, settings, new Date().toISOString()]);
    if (result.private_state || result.private_settings) {
      localStorage.setItem(PRIVATE_KEY, JSON.stringify({state: result.private_state ? JSON.stringify(result.private_state) : state,
        settings: result.private_settings ? JSON.stringify(result.private_settings) : settings}));
      delete result.private_state;delete result.private_settings;
    }
    return result;
  },
  async update(action, data) {
    const {state, settings} = privateData();
    const result = await callPython('update_json', [action, JSON.stringify(data),
      state, settings, new Date().toISOString()]);
    localStorage.setItem(PRIVATE_KEY, JSON.stringify({state: JSON.stringify(result.state),
      settings: JSON.stringify(result.settings)}));
    return result.snapshot;
  },
  exportPrivate() {
    return localStorage.getItem(PRIVATE_KEY);
  },
  async importPrivate(value) {
    const parsed = JSON.parse(value);
    if (typeof parsed.state !== 'string' || typeof parsed.settings !== 'string')
      throw Error('Invalid backup');
    await callPython('snapshot_json', [parsed.state, parsed.settings, new Date().toISOString()]);
    localStorage.setItem(PRIVATE_KEY, JSON.stringify(parsed));
  },
};
