# Configuring use cases: packs and tasks

SHIFTTRACE is no longer tied to one story. What the agent knows and what it is asked to do are configuration:

| Layer | File | Sets |
|---|---|---|
| **Pack** (a site or a use case) | `demo_data/packs/<id>/pack.json` + manual `.md` files | Machines, manuals, parts, work orders, previous sessions, evidence, handoffs, per-machine safety notes, the simulated panel |
| **Task** (what this session is for) | `demo_data/tasks.json` (or a `"tasks"` list in a pack) | The agent's goal and procedure, the greeting, and optionally which tools it may use |

The technician picks the machine on **Machines**, then the task in the **Start session** dialog. The task is stored on the session, shown in the live session header, written into the handoff, and changes the agent's system prompt, greeting and tool allowlist.

## Packs that ship

| Pack | Machine | Story | Default task |
|---|---|---|---|
| `compressor_house` | C-204 rotary screw compressor (KS-75), P-117 pump | A-17 alarm recurs after a sensor swap; DE vibration; bearing suspected | Troubleshoot a fault |
| `packaging_line` | CV-310 belt conveyor (TL-600) | Belt drift after over-adjustment, F-12 overload trips; monthly PM due | Preventive maintenance |
| `building_hvac` | AHU-3 air handling unit (NB-AH20) | Bag filter pressure near change limit, belt squeal | Inspection round |

All machines, people, suppliers and manuals are fictional.

Choose which packs load with `SHIFTTRACE_PACKS` in `backend/.env` (comma-separated ids; default all), then reset the data (`POST /api/demo/reset` or *Reset demo data*). Example for a single-scenario demo: `SHIFTTRACE_PACKS=packaging_line`.

## Tasks that ship

| Task | What the agent does | Tools |
|---|---|---|
| `troubleshoot` | Briefs from the handoff, reads the panel, checks the manual, treats causes as hypotheses, handles parts with approval | all 15 |
| `preventive_maintenance` | Finds the PM checklist in the manual, reads one step at a time, records each step and finding, refuses to skip the safety step, reserves consumables on request | all 15 |
| `inspection_round` | Asks for each reading, records it, compares it with the manual limit, logs out-of-limit readings as open items, does not order or change anything unless asked | all 15 |
| `shift_briefing` | Answers "what happened and what is open" from stored records; can capture a note; cannot order, reserve, change or escalate | 8 (read tools + `record_observation`, `record_reading`) |

A restricted task also changes the prompt: action instructions for tools it lacks are removed, and the agent is told never to offer them. (Live, before this, a briefing agent offered to draft an order it had no tool for.) A task's `tools` list is enforced twice: Agora only offers those tools to the LLM (`allowed_tools`), and the MCP server rejects any other tool for that session (`not_available_in_task`), so a model that tries anyway gets an error and nothing changes.

## Add a machine or site

1. Create `demo_data/packs/<id>/pack.json`. Copy an existing pack as a template. Keys:
   - `id`, `name`, `description`
   - `manuals`: `[{"model": "XY-10", "prefix": "XY10", "file": "XY-10_manual.md"}]`. The manual is Markdown with sections written `## 4.1 Title`. Section ids become `XY10-4.1`, and the agent cites "section 4.1".
   - `assets`: the `assets` table columns plus `metadata`:
     - `tasks`: the task ids offered for this machine. The first one is the default.
     - `safety_notes`: sentences the agent must remind the technician about and never help bypass.
     - `limits` (optional): reading limits used by `record_reading`, e.g. `{"label": "fan motor current", "aliases": ["motor current", "amps"], "unit": "A", "normal": [10, 13], "limit_high": 13.5, "section": "3.1", "note": "...", "action_high": "..."}`. The agent never compares numbers itself. The tool returns `normal`, `outside_normal`, `out_of_limit`, `unit_mismatch` or `no_limit_configured`, and logs out-of-limit readings as open items. The longest matching alias wins, so give specific readings ("pre filter pressure") longer aliases than general ones ("filter").
     - `panel` (optional): `title`, `subtitle`, `lamps` [{key, label, color}], `lit`, `alarms`, `readings` [{key, label, unit, value, step, min, max, decimals}]. It is served at `/panel/<asset_id>`.
   - `parts`, `work_orders`, `work_order_log`, `sessions` (with `task_id`), `evidence`, `handoffs` (with a full `report`).
2. Write timestamps as `"ago:2d3h15m"`. They are resolved at reset, so the history always reads as recent.
3. Keep IDs unique across packs (asset, work order, session, handoff). Use work order numbers of 3 to 6 digits so spoken "work order 2214" resolves.
4. Run `cd backend; uv run python -m pytest -q tests/test_packs_tasks.py`. The integrity test checks that every referenced asset and part exists, that every task id is known, and that manuals have sections.

## Add a task

Add an object to `demo_data/tasks.json` (or to a pack's `"tasks"` list):

```json
{
  "id": "commissioning_check",
  "label": "Commissioning check",
  "summary": "One line for the start dialog.",
  "goal": "One or two sentences: what the agent is helping with in this session.",
  "procedure": ["Short, imperative steps the agent follows, naming tools where it matters."],
  "tools": ["get_asset_history", "search_maintenance_manual", "record_observation"],
  "greeting": "SHIFTTRACE is live on {asset_name} for the commissioning check. {first_name}, ready when you are."
}
```

Then add its id to `metadata.tasks` of the machines that should offer it. Omit `tools` to allow all 15. The greeting can use `{asset_name}`, `{asset_id}`, `{first_name}` and `{task}`.

## Warehouse, training and other workplaces
- **Persona.** `metadata.persona = {"worker": "associate", "systems": "warehouse and ERP systems"}` changes how the agent addresses the person and names the systems it acts in. The default is technician and maintenance systems.
- **Stock per location.** A part with `"locations": {"B-04-2": 2, "R-12": 40}` is stocked per location. `check_inventory` reports each location, and `create_stock_transfer` / `confirm_stock_transfer` move stock between them. A transfer is drafted first and confirmed only by the worker's spoken yes after the read-back (or a console click). It then posts an ERP document and is re-read before it is reported.
- **Shipments.** `"shipments": [...]` in a pack, each with `events`. `track_shipment` finds them by ID, carrier reference or item name. Use `"in:5h"` for future times such as ETAs.
- **Training.** `metadata.training = [{module_id, title, pass_score, questions: [{id, ask, section, key_points: [[phrasings...], ...], min_points, explain}]}]`. `record_training_answer` marks answers in code (correct, partly, incorrect) against the key points, and the model never sees the key. `finish_training_module` computes the score (unanswered questions count as zero), applies the pass mark and updates the learning record. Seed earlier results with `"learning_records"`.
- **Domain tools are opt-in.** A task without `tools` gets the 16 core tools. Warehouse and training tools are offered only to tasks that list them (see `warehouse_ops` and `onboarding` in `demo_data/tasks.json`), and the server rejects them anywhere else.
- **Follow-ups.** `schedule_follow_up` (a core tool) records what, when and who. Spoken due dates such as "tomorrow", "next shift" or "Friday" are turned into dates, and follow-ups appear in the handoff.

## Test feed (trying it without a machine)
`demo_data/testkit.json` lists **scenes** (images or videos the camera shows) and **lines** (recorded questions played as the technician's voice). Each item can have `assets` and `tasks` lists that limit where it is offered. A line's optional `scene` is shown and held before it is spoken, and a `note` explains what to expect. Media files live in `experiments/media/generated` or `experiments/media/web`, and line text comes from `utterances.json` there. For a new machine, render its panel (`/panel/<asset_id>?...`) to a PNG, record lines with `backend/scripts/make_utterances.ps1`, and list both in the test kit.

## What does not change between tasks

The invariants in `CLAUDE.md` hold for every pack and task: Murf Falcon voice, the spoken-approval gate, re-reading every write before reporting it verified, provenance on every piece of evidence, the claim guard, and the tunnel and link checks.
