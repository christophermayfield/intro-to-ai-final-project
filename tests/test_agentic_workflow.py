import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentic_workflow import (
    ACTION_SPECS,
    AgentAction,
    AgentConfig,
    AgentOrchestrator,
    AgentToolRouter,
    BaseModelAdapter,
    validate_action_payload,
)
from pawpal_system import Owner, Pet, Scheduler, Task


class StubModel(BaseModelAdapter):
    def __init__(self, outputs):
        self.outputs = outputs
        self.idx = 0

    def next_action(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> str:
        if self.idx >= len(self.outputs):
            return json.dumps(
                {
                    "action": "respond",
                    "arguments": {"message": "No more model outputs."},
                    "thought": "fallback",
                }
            )
        value = self.outputs[self.idx]
        self.idx += 1
        return value


@pytest.fixture
def scheduler_context():
    owner = Owner("Tester", 120)
    pet = Pet("Milo", "dog", 4, "medium")
    scheduler = Scheduler(owner, pet)
    task = Task("Walk", "walk", 30, 7)
    scheduler.add_task(task)
    return owner, pet, scheduler, task


def test_action_schema_contains_expected_actions():
    assert "read_context" in ACTION_SPECS
    assert "generate_schedule" in ACTION_SPECS
    assert "propose_task_update" in ACTION_SPECS
    assert "complete_task" in ACTION_SPECS
    assert "respond" in ACTION_SPECS


def test_validate_action_payload_accepts_valid_payload():
    action = validate_action_payload(
        {"action": "respond", "arguments": {"message": "done"}, "thought": "finished"}
    )
    assert action.action == "respond"
    assert action.arguments["message"] == "done"


def test_validate_action_payload_rejects_unknown_fields():
    with pytest.raises(ValueError):
        validate_action_payload(
            {"action": "generate_schedule", "arguments": {"unexpected": True}}
        )


def test_mutating_action_rejected_when_approval_denied(scheduler_context):
    owner, pet, scheduler, task = scheduler_context
    router = AgentToolRouter(
        owner=owner,
        pet=pet,
        scheduler=scheduler,
        approval_callback=lambda _message: False,
    )
    result = router.execute(
        AgentAction(
            action="propose_task_update",
            arguments={"task_id": task.get_task_id(), "updates": {"priority": 9}},
        )
    )
    assert result.success is False
    assert result.output["status"] == "rejected_by_user"
    assert task.get_priority() == 7


def test_mutating_action_applies_when_approved(scheduler_context):
    owner, pet, scheduler, task = scheduler_context
    router = AgentToolRouter(
        owner=owner,
        pet=pet,
        scheduler=scheduler,
        approval_callback=lambda _message: True,
    )
    result = router.execute(
        AgentAction(
            action="propose_task_update",
            arguments={
                "task_id": task.get_task_id(),
                "updates": {"priority": 9, "description": "Evening walk"},
            },
        )
    )
    assert result.success is True
    assert task.get_priority() == 9
    assert task.get_description() == "Evening walk"


def test_orchestrator_happy_path_generates_schedule_then_responds(tmp_path, scheduler_context):
    owner, pet, scheduler, _task = scheduler_context
    router = AgentToolRouter(
        owner=owner,
        pet=pet,
        scheduler=scheduler,
        approval_callback=lambda _message: True,
    )
    model = StubModel(
        outputs=[
            json.dumps(
                {
                    "action": "generate_schedule",
                    "arguments": {},
                    "thought": "Build deterministic schedule first",
                }
            ),
            json.dumps(
                {
                    "action": "respond",
                    "arguments": {"message": "Your schedule is ready."},
                    "thought": "Return summary",
                }
            ),
        ]
    )
    config = AgentConfig(max_steps=4, transcript_dir=str(tmp_path))
    orchestrator = AgentOrchestrator(model_adapter=model, tool_router=router, config=config)
    session = orchestrator.run_session(goal="Plan today's pet care")

    assert session["final_message"] == "Your schedule is ready."
    assert len(session["trace"]) == 2
    assert (tmp_path / f"{session['session_id']}.json").exists()


def test_orchestrator_handles_invalid_model_json_and_recovers(tmp_path, scheduler_context):
    owner, pet, scheduler, _task = scheduler_context
    router = AgentToolRouter(
        owner=owner,
        pet=pet,
        scheduler=scheduler,
        approval_callback=lambda _message: True,
    )
    model = StubModel(
        outputs=[
            "not-json",
            json.dumps(
                {
                    "action": "respond",
                    "arguments": {"message": "Recovered after invalid output."},
                    "thought": "valid now",
                }
            ),
        ]
    )
    config = AgentConfig(max_steps=3, transcript_dir=str(tmp_path))
    orchestrator = AgentOrchestrator(model_adapter=model, tool_router=router, config=config)
    session = orchestrator.run_session(goal="Do something useful")

    assert session["final_message"] == "Recovered after invalid output."
    assert "validation_error" in session["trace"][0]["error"]
