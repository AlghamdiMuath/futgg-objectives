# Spec: Daily Game Planner

**Status:** Draft for product decisions

## Problem Statement

The current site is organized around selecting objective groups and interpreting their individual tasks. The plan emphasizes squad/scoring conditions and long-term match totals. It does not answer the more immediate question: “What should I play today to make the most useful progress across the objectives available to me?”

Users have to recognize compatible tasks themselves, decide which rewards matter, and work out what to do in each match. Long-term milestone and mastery grinds also compete for attention with objectives that can be completed today.

## Solution

Make the home screen a low-effort, ordered batch of ten match recommendations. Each recommendation describes one playable match recipe: mode and event, difficulty where relevant, starting squad traits and player roles, goal types or other actions, and the objectives and rewards it can advance. When the user marks the batch done, show the next ten recommendations.

Build recommendations automatically from currently active objectives, except Milestones and Mastery. Combine tasks only when one match can satisfy their modes, events, difficulty, and conditions. Put deliberate requirements in the recipe; show ordinary play and win counters as progress that can happen during the same match. Recalculate the remaining recommendations when the objective data, user priorities, excluded modes, or recorded progress changes.

Let users choose Packs, Coins, or Season Points as their primary reward priority, or use a balanced default. The 84+ threshold applies to direct player rewards such as a named player card, not to players inside packs. In balanced mode, compare high-rated direct player rewards first, then Packs, SP, below-84 direct player rewards, and Coins. Compare Packs by printed rating and player count using the user's relative-difference rule. Include both subtask rewards and a group's main completion reward without counting that completion reward more than once. Keep the score breakdown visible so the ordering is understandable. Ignore Milestones and Mastery completely in this planner.

## User Stories

1. As a player opening the site, I want to see today's useful match recommendations immediately, so I can choose what to play without first assembling a plan from objective groups.
2. As a player with a reward goal, I want to prioritize Packs, Coins, or Season Points, so the ten-match batch maximizes the reward type I chose.
3. As a player without a specific reward goal, I want a balanced ranking, so the site can suggest the most rewarding batch across all reward types.
4. As a player choosing a recommendation, I want to see the mode, event, difficulty, squad traits, scorer/assister traits, and goal types together, so I can set up once and pursue compatible tasks in the same match.
5. As a player, I want each recommendation to show the objectives and reward steps it advances, so I can see why that match is useful.
6. As a player finishing the ten-match batch, I want one simple action to move on to the next ten recommendations.
7. As a player whose excluded modes or available objectives cannot produce ten useful games, I want fewer recommendations with a clear explanation, rather than filler games.
8. As a player, I want uncertain or incompatible tasks identified clearly and kept out of claimed progress, so a recommendation does not promise an objective the match may not satisfy.
9. As a player focused on today's objectives, I want long-term Milestone and Mastery grinds kept out of the default list, so daily opportunities remain easy to act on.

## Acceptance Criteria

- [ ] The landing view shows an ordered batch of ten match recommendations without requiring users to select objective groups first.
- [ ] Each recommendation shows its route, relevant setup and in-match actions, and the objective steps and rewards it can advance.
- [ ] The planner combines compatible tasks across groups and does not combine different named events into one match.
- [ ] Generic Live Events tasks can combine with a named Live Event when the task rules permit it.
- [ ] A user can prioritize Packs, Coins, or Season Points, or select a balanced default; the ranking includes a human-readable reason.
- [ ] The 84+ threshold applies to direct player-card rewards, not pack contents.
- [ ] Balanced mode ranks direct player rewards rated 84+ first, then Packs, SP, below-84 direct player rewards, then Coins.
- [ ] Pack comparisons use printed minimum rating and player count, applying the agreed relative-difference rule.
- [ ] Both subtask rewards and a group's main completion reward affect the batch ranking. A completion reward is counted once if the batch completes the group; partial group-completion progress is shown separately.
- [ ] Milestones and Mastery are fully ignored by this planner.
- [ ] The planner uses recorded progress and current availability when calculating remaining objective progress.
- [ ] Repeated threshold rewards are credited at their actual thresholds; the same reward is not counted repeatedly just because multiple tasks describe cumulative totals.
- [ ] All modes are considered unless the user excludes modes; the planner does not ask the user to select available modes or rank mode preferences.
- [ ] A match recipe distinguishes conditions that must be met in that match from cumulative targets that can progress over multiple games.
- [ ] When fewer than ten qualifying recommendations exist, the site shows the available set and explains why it is shorter.
- [ ] Uncertain interpretations are not treated as confirmed objective progress. A user-confirmed interpretation can be represented as an explicit reviewed rule.
- [ ] Recommendations state that match outcomes are conditional and do not imply guaranteed wins, reward value, or play time.

## Implementation Decisions

### Architecture & Schema

- Preserve the existing fetch and interpretation layers as the source of objective wording, availability, conditions, and listed rewards.
- Add a recommendation layer that produces ranked, single-match recipes from all eligible active tasks, rather than requiring selected groups as its input.
- A recipe contains: route, difficulty, combined squad requirements, scoring/assisting roles, goal or match actions, compatible task progress, reward steps, and a concise ranking explanation.
- Keep recommendation preferences and any user-confirmed task-rule overrides in private browser settings. Do not put them in the public objective export.
- Reuse the mode exclusion setting and consider all other modes by default. Do not infer player ownership, event access, opponent strength, match win probability, or real-world reward value from objective text.

### Interfaces & Contracts

- The recommendation engine accepts the interpreted export, current progress/availability, excluded modes, reward priority, and a fixed planning time. It returns an ordered ten-match batch with per-match objective contributions and a batch reward score breakdown.
- The UI presents the ten-game recommendation list first. Objective browsing and long-term grinds remain accessible separately.
- Each recipe links back to its source objectives and original task wording.
- The plan should make it possible to mark a completed recommendation or enter match progress using the existing private progress mechanism.

### Behavior & Interactions

- Default to a balanced recommendation mode. A user can change priority to Packs, Coins, or Season Points.
- The ten recommendations are one ordered itinerary, not ten alternatives. Completing the batch exposes the next batch.
- Include all currently active objectives except Milestones and Mastery. Use published availability at planning time; do not infer undocumented in-game reset boundaries from listing expiry.
- In a selected reward mode, maximize that reward type across the ten-match batch. In balanced mode, rank direct 84+ player rewards first, Packs second, SP third, below-84 direct player rewards fourth, and Coins fifth.
- The balanced reward profile is: (1) count/value of direct player-card rewards rated 84+, (2) combined Pack quality, (3) SP, (4) direct player-card rewards rated below 84, and (5) Coins.
- For a selected reward priority, put that reward's measure first, then use the balanced profile order for tie-breaking.
- Compare two Packs by printed minimum rating and number of players. If their rating floors differ by at least 2, the higher rating wins even when it contains fewer players. If player counts differ by at least 2 and the rating gap is less than 2, the higher player count wins. Other close comparisons use rating, then player count. For example, 2 players at 84+ outrank 5 players at 80+; 5 players at 82+ outrank 2 players at 81+. (The exact 2-point boundary is open below.) Do not invent market or coin values for Packs.
- The 84+ threshold applies to direct player-card rewards such as a named player reward. When a direct player's rating is unavailable, label it unknown and provisionally rank it in the below-84 tier rather than assuming it is 84+.
- If a Pack's rating or player count is unknown, expose that and compare only the known information; do not infer player count from a vague pack label.
- Rank the batch by incremental reward/progress from the user's current state, not reward labels already earned or goals already complete.
- Include each group's main completion reward as well as subtask rewards. Count its reward once if the batch finishes that group; use remaining group-completion progress as a separate tie-breaker, not as an already secured reward.
- Marking a ten-match batch done advances progress according to the recipes in that batch, then generates the next ten from the updated state.
- Collapse nested thresholds into progress milestones: for example, one Squad Battles win can advance 25-, 50-, and 100-win counters, but the recipe should show the next reward thresholds and difficulty needed for each.
- Split difficulty requirements when useful. A World Class requirement should apply to the number of wins that need World Class; it should not force all later Semi-Pro-eligible wins to World Class.
- A generic Live Events task may be advanced in a named event if its route allows it. Tasks for two different named events require separate recommendations.
- Group the recipe around a practical setup. For example, if three Exhibition wins require two French starters and three scoring matches require a Destined for Glory starter, recommend using both traits and scoring in those three wins, when the event route supports it.
- List natural play counters as “also advances” outcomes. Keep specific player, squad, goal-style/location, and deliberate checklist requirements prominent.
- Treat the user-confirmed “Score 20 goals in any Live Events match (or Rivals/Squad Battles)” as a cumulative total across eligible matches; retain its original wording and record the rule as reviewed.
- Ignore Milestone and Mastery groups throughout the daily planner. This does not delete their source data.
- If priority targets cannot be met by current eligible tasks, state the remaining shortfall and show the best available alternatives.

## Testing Decisions

- Test recipe compatibility across mode, event, difficulty, squad, and per-match conditions.
- Test reward scoring for nested thresholds, task progress, and each reward priority, including unavailable targets.
- Test that incompatible named events never share a recipe and that eligible generic event tasks do.
- Test the active daily recommendation flow through both the browser API and the rendered site, including fewer-than-ten and no-eligible-objective states.
- Test that private preferences and reviewed overrides survive reload and backup/restore without entering public exports.

## Out of Scope

- Estimating coin value or pack expected value from external market data: current objective labels do not provide enough information for a trustworthy estimate.
- Predicting match duration, win probability, or player-specific squad ownership: the app has no such inputs today.
- Replacing the challenge browser or removing long-term objectives: the change is to the planner's default purpose and presentation.
- Automating match completion or communicating with FUT.GG accounts: the source feed and progress tracking remain read-only/manual.

## Open Questions

- **Pack comparison at exactly two rating points:** The current draft assumes a rating difference of 2 favors rating, while player count wins only when the rating difference is below 2. Your wording also says player count may win when the rating difference is 2; confirm which rule should apply when both gaps are at least 2.

## Further Notes

The user confirmed that marking the ten-match batch done assumes its planned objectives advanced, then the planner shows the next batch. The 84+ threshold is for direct player rewards such as Mito, not pack contents. Balanced reward order is direct 84+ player rewards, Packs, SP, below-84 direct player rewards, then Coins. Packs are compared by minimum rating and player count; a rating gap of at least two overrides count, while a count gap of at least two wins when the rating gap is less than two. The exact two-point boundary needs confirmation. A selected reward type is the primary ranking target. Group completion rewards count alongside subtask rewards.

The data already contains task rewards, group completion rewards, match conditions, mode/event options, minimum difficulty, objective expiry, and current progress. The current optimizer can combine compatible tasks, but the site Plan screen does not present its shared runs as the primary experience. The main product change is a reward-ranked, ten-match batch and a UI that explains each match recipe and the batch's marginal rewards without implying that uncertain conditions are guaranteed.
