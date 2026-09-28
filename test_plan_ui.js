const test = require('node:test');
const assert = require('node:assert/strict');
const {planCoreRequirements, planGroupOrder, planIssues, planTaskText} = require('./web/app.js');

const run = {
  group_ids: ['113', '86', '98'],
  match_tasks: [
    {group_id: '86', task_id: '86:743', remaining_qualifying_matches: 5, conditions: [
      {type: 'goals', minimum_per_match: 1},
      {type: 'squad', minimum: 1, trait: 'Serie A player', slot: 'starting_11'}]},
    {group_id: '113', task_id: '113:1756', remaining_qualifying_matches: 4, conditions: [
      {type: 'goals', minimum_per_match: 1},
      {type: 'scoring_player', trait: 'Japanese', must_start: true}]},
    {group_id: '113', task_id: '113:1755', remaining_qualifying_matches: 3, conditions: [
      {type: 'result', value: 'win'},
      {type: 'squad', minimum: 2, trait: 'players from Eredivisie', slot: 'starting_11'}]},
    {group_id: '98', task_id: '98:1708', remaining_qualifying_matches: 3, conditions: [
      {type: 'squad', minimum: 2, trait: 'players from USA', slot: 'starting_11'}]},
  ],
  cumulative_targets: [{group_id: '98', task_id: '98:1709', remaining: 5,
    target: {unit: 'goals', count: 5, scope: 'cumulative'}, conditions: [
    {type: 'squad', minimum: 1, trait: 'player from any Premier League team', slot: 'starting_11'},
    {type: 'squad', minimum: 1, trait: "player from any Women's Super League team", slot: 'starting_11'}]}],
};

test('the initial lineup contains bounded-task traits, leaving bonus traits optional', () => {
  const core = planCoreRequirements(run);
  assert.deepEqual(core.squad.map(item => item.trait).sort(),
    ['Serie A player', 'players from Eredivisie', 'players from USA'].sort());
  assert.deepEqual(core.roles, [{role: 'scoring_player', trait: 'Japanese', must_start: true}]);
});

test('the soonest bounded challenge leads the shared run', () => {
  const groups = new Map([
    ['86', {effective_expires_at: '2026-10-22T06:59:59Z'}],
    ['113', {effective_expires_at: '2026-10-03T16:59:59Z'}],
    ['98', {effective_expires_at: null}],
  ]);
  assert.deepEqual(planGroupOrder(run, groups), ['113', '86', '98']);
});

test('weekly cycle tasks get one setup path while manual and cumulative work stay separate', () => {
  const plan = {unscheduled_tasks: [
    {group_id: '65', task_id: '65:474', reasons: ['group_cycle_start_required', 'progress_cycle_unknown']},
    {group_id: '65', task_id: '65:472', reasons: ['group_cycle_start_required', 'not_match_task']},
    {group_id: '113', task_id: '113:1757', reasons: ['not_match_task']},
    {group_id: '98', task_id: '98:1709', reasons: ['match_count_not_bounded']},
    {group_id: '25', task_id: '25:140', reasons: ['cumulative_vs_single_match_unclear']},
  ]};
  const issues = planIssues(plan, [run]);
  assert.equal(issues.cycle.get('65').length, 2);
  assert.deepEqual(issues.manual.map(item => item.task_id), ['113:1757']);
  assert.deepEqual(issues.blocked.map(item => item.task_id), ['25:140']);
  assert.deepEqual(issues.cumulative, []);
});

test('two scoring tasks remain distinguishable in the compact checklist', () => {
  const japanese = run.match_tasks[1];
  const lm = {...japanese, conditions: [
    {type: 'goals', minimum_per_match: 1},
    {type: 'scoring_player', trait: 'Preferred Position: LM', must_start: true}]};
  assert.match(planTaskText(japanese), /Japanese scorer/);
  assert.match(planTaskText(lm), /LM scorer/);
  assert.notEqual(planTaskText(japanese), planTaskText(lm));
  assert.match(planTaskText(run.match_tasks[2]), /2 Eredivisie starters/);
  const bonus = planTaskText(run.cumulative_targets[0], true);
  assert.match(bonus, /1 Premier League starter/);
  assert.match(bonus, /1 Women’s Super League starter/);
});
