const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const html = fs.readFileSync('web/index.html', 'utf8');
const app = fs.readFileSync('web/app.js', 'utf8');
const staticApi = fs.readFileSync('web/static_api.js', 'utf8');

test('Today is the default landing screen with the daily itinerary', () => {
  assert.match(html, /<button data-tab="daily" class="active">/);
  assert.match(html, /<section id="daily" class="panel active">/);
  assert.match(app, /function renderDaily\(\)/);
  assert.match(app, /Mark this batch done/);
});

test('challenge browsing and My List remain while the old Plan screen is removed', () => {
  assert.match(html, /data-tab="browse"/);
  assert.match(html, /data-tab="selected"/);
  assert.doesNotMatch(html, /data-tab="plan"|id="plan"/);
  assert.doesNotMatch(app, /renderPlan|planBulletPoints/);
});

test('the hosted browser loads the daily recommendation engine', () => {
  assert.match(staticApi, /'daily_game_planner\.py'/);
});
