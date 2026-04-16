# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Agentic Workflow (Local CLI)

PawPal+ now includes a semi-autonomous agent runtime in `agentic_workflow.py` that can:

- Read owner/pet/task context
- Generate deterministic schedules using `Scheduler`
- Propose task updates with a required human approval gate
- Complete tasks (including recurrence) with approval
- Return explainable outcomes plus a tool-call trace

### Architecture Notes

- **LLM decides actions**, but does not directly implement scheduling logic
- **Tool router executes deterministic operations** against existing domain classes
- **Mutating actions require approval** through a CLI confirmation prompt
- **Bounded loop** (`max_steps`) prevents runaway tool-calling sessions
- **Session transcript logging** writes JSON traces to `agent_runs/` by default

### Run the Agent Workflow

1. Start your local open-source model runtime (for example, Ollama).
2. Run an agent session from CLI:

```bash
python main.py agent --goal "Plan today's care and explain priorities"
```

Optional flags:

```bash
python main.py agent \
  --goal "Prioritize medication tasks for Luna" \
  --pet luna \
  --model llama3.1:8b \
  --endpoint http://localhost:11434 \
  --temperature 0.2 \
  --max-tokens 512 \
  --max-steps 8 \
  --transcript-dir agent_runs
```

To run the classic deterministic demo:

```bash
python main.py demo
```

### Testing

Run agent workflow tests:

```bash
pytest -q tests/test_agentic_workflow.py
```

### Troubleshooting

- **Model endpoint errors:** ensure your local model server is running and endpoint/model flags are correct.
- **Invalid JSON from model:** the orchestrator records validation failures in the trace and retries within `max_steps`.
- **Approval loops:** mutating actions are rejected unless explicitly approved in CLI.
