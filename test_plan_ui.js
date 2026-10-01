const test = require('node:test');
const assert = require('node:assert/strict');
const {planBulletPoints} = require('./web/app.js');
const source = require('./fc27_interpreted.json');

function scenario(ids, completed = false) {
  const groups = source.groups.filter(group => ids.includes(group.id));
  return {groups, view: {selected_groups: groups.map(group => ({
    group_id: group.id, availability: 'active',
    tasks: group.tasks.map(task => ({id: task.id, progress: completed ? {count: 99, completed: true} : null})),
  }))}};
}

test('Weekly Objectives and Ted Lasso show four actionable bullets', () => {
  const bullets = planBulletPoints(scenario(['65', '98'])).map(item => item.text);
  assert.deepEqual(bullets, [
    'Score 10 goals with an English starter.',
    'Build 20+ chemistry.',
    'Score 5 goals with 1 Premier League starter and 1 Women’s Super League starter in your starting XI.',
    'Play 3 matches with 2 USA starters.',
  ]);
});

test('adding Mito states the Japanese and LM scoring conditions', () => {
  const bullets = planBulletPoints(scenario(['65', '98', '113'])).map(item => item.text);
  assert.equal(bullets.length, 7);
  assert.ok(bullets.includes('Score in 4 matches with a Japanese starter.'));
  assert.ok(bullets.includes('Score in 3 matches with a starter whose preferred position is LM.'));
  assert.ok(bullets.includes('Win 3 matches with 2 Eredivisie starters.'));
  assert.ok(!bullets.some(text => /^Play [34] matches\.$/.test(text)));
});

test('old saved progress does not change the static plan', () => {
  assert.deepEqual(planBulletPoints(scenario(['65', '98'], true)),
    planBulletPoints(scenario(['65', '98'])));
});
