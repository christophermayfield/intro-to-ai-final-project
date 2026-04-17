"""
Agentic workflow runtime for PawPal+.

This module provides:
- A strict action schema and validator
- A model adapter abstraction (with an Ollama implementation)
- A tool router that bridges agent actions to deterministic scheduling logic
- A bounded orchestrator loop with human approval for state mutations
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib import error, request

from pawpal_system import Owner, Pet, Plan, Scheduler, Task


@dataclass(frozen=True)
class ActionSpec:
    """Schema definition for a supported agent action."""

    required_fields: List[str]
    optional_fields: List[str]
    mutating: bool
    description: str


ACTION_SPECS: Dict[str, ActionSpec] = {
    "read_context": ActionSpec(
        required_fields=[],
        optional_fields=[],
        mutating=False,
        description="Read owner/pet/task context.",
    ),
    "generate_schedule": ActionSpec(
        required_fields=[],
        optional_fields=[],
        mutating=False,
        description="Generate a deterministic daily schedule from current tasks.",
    ),
    "propose_task_update": ActionSpec(
        required_fields=["task_id", "updates"],
        optional_fields=[],
        mutating=True,
        description="Propose updates to a task; requires approval to apply.",
    ),
    "complete_task": ActionSpec(
        required_fields=["task_id"],
        optional_fields=[],
        mutating=True,
        description="Mark a task complete (and recur if configured); requires approval.",
    ),
    "respond": ActionSpec(
        required_fields=["message"],
        optional_fields=[],
        mutating=False,
        description="Return the final user-facing response and stop.",
    ),
}


@dataclass
class AgentAction:
    """Validated tool/action instruction from the LLM."""

    action: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    thought: str = ""


@dataclass
class ToolResult:
    """Structured result emitted by tool/router execution."""

    action: str
    success: bool
    output: Dict[str, Any]
    requires_approval: bool = False
    approval_message: str = ""


class ActionValidationError(ValueError):
    """Raised when agent output does not match the action schema."""


def validate_action_payload(payload: Dict[str, Any]) -> AgentAction:
    """Validate raw LLM JSON payload into a strict AgentAction."""
    if not isinstance(payload, dict):
        raise ActionValidationError("Action payload must be a JSON object.")

    if "action" not in payload:
        raise ActionValidationError("Missing required field: action.")

    action = payload["action"]
    if action not in ACTION_SPECS:
        raise ActionValidationError(
            f"Unsupported action '{action}'. Allowed: {', '.join(ACTION_SPECS.keys())}."
        )

    args = payload.get("arguments", {})
    if not isinstance(args, dict):
        raise ActionValidationError("Field 'arguments' must be a JSON object.")

    spec = ACTION_SPECS[action]
    for field_name in spec.required_fields:
        if field_name not in args:
            raise ActionValidationError(
                f"Action '{action}' missing required argument '{field_name}'."
            )

    allowed_fields = set(spec.required_fields + spec.optional_fields)
    unknown_fields = [k for k in args if k not in allowed_fields]
    if unknown_fields:
        raise ActionValidationError(
            f"Action '{action}' has unknown argument(s): {', '.join(unknown_fields)}."
        )

    thought = payload.get("thought", "")
    if thought and not isinstance(thought, str):
        raise ActionValidationError("Field 'thought' must be a string.")

    return AgentAction(action=action, arguments=args, thought=thought)


class BaseModelAdapter:
    """Abstraction layer for any model backend."""

    def next_action(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> str:
        raise NotImplementedError


class OllamaModelAdapter(BaseModelAdapter):
    """Open-source local model adapter via Ollama HTTP API."""

    def __init__(self, model: str = "llama3.1:8b", endpoint: str = "http://localhost:11434"):
        self.model = model
        self.endpoint = endpoint.rstrip("/")

    def next_action(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        req = request.Request(
            f"{self.endpoint}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("response", "").strip()
        except error.URLError as exc:
            raise RuntimeError(
                "Failed to reach local model endpoint. Ensure Ollama is running."
            ) from exc


def default_approval_callback(message: str) -> Optional[bool]:
    """CLI approval prompt used for mutating actions."""
    reply = input(f"{message}\nApprove? [y/N]: ").strip().lower()
    return reply in {"y", "yes"}


class AgentToolRouter:
    """Maps validated actions to deterministic PawPal+ operations."""

    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        scheduler: Scheduler,
        approval_callback: Callable[[str], Optional[bool]] = default_approval_callback,
    ):
        self.owner = owner
        self.pet = pet
        self.scheduler = scheduler
        self.approval_callback = approval_callback

    def execute(self, action: AgentAction, approval_decision: Optional[bool] = None) -> ToolResult:
        if action.action == "read_context":
            return self._read_context()
        if action.action == "generate_schedule":
            return self._generate_schedule()
        if action.action == "propose_task_update":
            return self._propose_task_update(action.arguments, approval_decision)
        if action.action == "complete_task":
            return self._complete_task(action.arguments, approval_decision)
        if action.action == "respond":
            return ToolResult(
                action="respond",
                success=True,
                output={"message": action.arguments["message"]},
            )
        return ToolResult(
            action=action.action,
            success=False,
            output={"error": "Action not implemented."},
        )

    def _read_context(self) -> ToolResult:
        tasks = []
        for task in self.scheduler.get_tasks():
            tasks.append(
                {
                    "task_id": task.get_task_id(),
                    "name": task.get_name(),
                    "type": task.get_task_type(),
                    "duration": task.get_duration(),
                    "priority": task.get_priority(),
                    "mandatory": task.is_mandatory(),
                    "description": task.get_description(),
                }
            )
        return ToolResult(
            action="read_context",
            success=True,
            output={
                "owner": {
                    "name": self.owner.get_name(),
                    "available_time_minutes": self.owner.get_available_time(),
                    "preferences": self.owner.get_preferences(),
                },
                "pet": {
                    "name": self.pet.get_name(),
                    "species": self.pet.get_species(),
                    "age": self.pet.get_age(),
                    "size": self.pet.get_size(),
                    "special_needs": self.pet.get_special_needs(),
                },
                "tasks": tasks,
            },
        )

    def _generate_schedule(self) -> ToolResult:
        plan: Plan = self.scheduler.generate_plan()
        serialized_tasks = []
        for scheduled in plan.get_scheduled_tasks():
            task = scheduled.get_task()
            serialized_tasks.append(
                {
                    "task_id": task.get_task_id(),
                    "name": task.get_name(),
                    "start_time": scheduled.get_start_time(),
                    "end_time": scheduled.get_end_time(),
                    "priority": task.get_priority(),
                }
            )
        return ToolResult(
            action="generate_schedule",
            success=True,
            output={
                "scheduled_tasks": serialized_tasks,
                "total_time": plan.get_total_time(),
                "excluded_count": len(plan.get_excluded_tasks()),
                "explanation": plan.get_explanation(),
            },
        )

    def _propose_task_update(
        self, arguments: Dict[str, Any], approval_decision: Optional[bool] = None
    ) -> ToolResult:
        task = self._find_task(arguments["task_id"])
        if task is None:
            return ToolResult(
                action="propose_task_update",
                success=False,
                output={"error": "Task not found."},
            )
        updates = arguments["updates"]
        if not isinstance(updates, dict):
            return ToolResult(
                action="propose_task_update",
                success=False,
                output={"error": "Field 'updates' must be an object."},
            )

        allowed_update_fields = {"priority", "mandatory", "description"}
        unknown = [key for key in updates if key not in allowed_update_fields]
        if unknown:
            return ToolResult(
                action="propose_task_update",
                success=False,
                output={"error": f"Unknown update field(s): {', '.join(unknown)}."},
            )

        approval_message = (
            f"Proposed updates for task '{task.get_name()}' ({task.get_task_id()}): {updates}"
        )
        decision = self._get_approval_decision(approval_message, approval_decision)
        if decision is None:
            return ToolResult(
                action="propose_task_update",
                success=False,
                output={"status": "approval_pending"},
                requires_approval=True,
                approval_message=approval_message,
            )
        if not decision:
            return ToolResult(
                action="propose_task_update",
                success=False,
                output={"status": "rejected_by_user"},
                requires_approval=True,
                approval_message=approval_message,
            )

        if "priority" in updates:
            task.set_priority(int(updates["priority"]))
        if "mandatory" in updates:
            task.set_mandatory(bool(updates["mandatory"]))
        if "description" in updates:
            task.set_description(str(updates["description"]))

        return ToolResult(
            action="propose_task_update",
            success=True,
            output={"status": "applied", "task_id": task.get_task_id(), "updates": updates},
            requires_approval=True,
            approval_message=approval_message,
        )

    def _complete_task(
        self, arguments: Dict[str, Any], approval_decision: Optional[bool] = None
    ) -> ToolResult:
        task_id = arguments["task_id"]
        task = self._find_task(task_id)
        if task is None:
            return ToolResult(
                action="complete_task",
                success=False,
                output={"error": "Task not found."},
            )

        approval_message = f"Complete task '{task.get_name()}' ({task.get_task_id()})?"
        decision = self._get_approval_decision(approval_message, approval_decision)
        if decision is None:
            return ToolResult(
                action="complete_task",
                success=False,
                output={"status": "approval_pending"},
                requires_approval=True,
                approval_message=approval_message,
            )
        if not decision:
            return ToolResult(
                action="complete_task",
                success=False,
                output={"status": "rejected_by_user"},
                requires_approval=True,
                approval_message=approval_message,
            )

        next_task = self.scheduler.complete_task(task_id)
        output: Dict[str, Any] = {"status": "completed", "task_id": task_id}
        if next_task:
            output["next_task_id"] = next_task.get_task_id()
            output["next_occurrence"] = str(next_task.get_next_occurrence())

        return ToolResult(
            action="complete_task",
            success=True,
            output=output,
            requires_approval=True,
            approval_message=approval_message,
        )

    def _find_task(self, task_id: str) -> Optional[Task]:
        for task in self.scheduler.get_tasks():
            if task.get_task_id() == task_id:
                return task
        return None

    def _get_approval_decision(
        self, approval_message: str, decision_override: Optional[bool]
    ) -> Optional[bool]:
        if decision_override is not None:
            return decision_override
        return self.approval_callback(approval_message)


@dataclass
class AgentConfig:
    """Runtime config for orchestrator and model settings."""

    model_name: str = "llama3.1:8b"
    model_endpoint: str = "http://localhost:11434"
    temperature: float = 0.2
    max_tokens: int = 512
    max_steps: int = 8
    transcript_dir: str = "agent_runs"


class AgentOrchestrator:
    """Runs the bounded agent loop and records a trace."""

    def __init__(
        self,
        model_adapter: BaseModelAdapter,
        tool_router: AgentToolRouter,
        config: Optional[AgentConfig] = None,
    ):
        self.model_adapter = model_adapter
        self.tool_router = tool_router
        self.config = config or AgentConfig()

    def run_session(self, goal: str) -> Dict[str, Any]:
        session = self.create_session_state(goal)
        session = self.continue_session(session)
        if not session.get("completed"):
            session["final_message"] = (
                "I could not complete the request within the step limit. "
                "Please refine the goal or try again."
            )
            session["completed"] = True
        self._write_transcript(session)
        return session

    def create_session_state(self, goal: str) -> Dict[str, Any]:
        """Create a resumable orchestrator session state."""
        session_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
        return {
            "session_id": session_id,
            "goal": goal,
            "trace": [],
            "step": 1,
            "pending_action": None,
            "pending_message": "",
            "final_message": "",
            "completed": False,
        }

    def continue_session(
        self, session: Dict[str, Any], approval_decision: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Resume a session until completion, max step, or approval pause."""
        if session.get("completed"):
            return session

        pending_action = session.get("pending_action")
        if pending_action:
            action = AgentAction(
                action=pending_action["action"],
                arguments=pending_action.get("arguments", {}),
                thought=pending_action.get("thought", ""),
            )
            result = self.tool_router.execute(action, approval_decision=approval_decision)
            session["trace"].append(
                {
                    "step": session["step"],
                    "thought": action.thought,
                    "action": action.action,
                    "arguments": action.arguments,
                    "approval_decision": approval_decision,
                    "result": asdict(result),
                }
            )
            if result.output.get("status") == "approval_pending":
                session["pending_message"] = result.approval_message
                return session
            session["pending_action"] = None
            session["pending_message"] = ""
            session["step"] += 1

        while session["step"] <= self.config.max_steps:
            step = session["step"]
            prompt = self._build_prompt(goal=session["goal"], trace=session["trace"], step=step)
            raw = self.model_adapter.next_action(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            try:
                payload = json.loads(raw)
                action = validate_action_payload(payload)
            except (json.JSONDecodeError, ActionValidationError) as exc:
                session["trace"].append(
                    {
                        "step": step,
                        "raw_model_output": raw,
                        "error": f"validation_error: {exc}",
                    }
                )
                session["step"] += 1
                continue

            result = self.tool_router.execute(action)
            session["trace"].append(
                {
                    "step": step,
                    "thought": action.thought,
                    "action": action.action,
                    "arguments": action.arguments,
                    "result": asdict(result),
                }
            )

            if result.output.get("status") == "approval_pending":
                session["pending_action"] = {
                    "action": action.action,
                    "arguments": action.arguments,
                    "thought": action.thought,
                }
                session["pending_message"] = result.approval_message
                return session

            if action.action == "respond" and result.success:
                session["final_message"] = result.output["message"]
                session["completed"] = True
                return session

            session["step"] += 1

        return session

    def _build_prompt(self, goal: str, trace: List[Dict[str, Any]], step: int) -> str:
        action_rules = {
            name: {
                "required_fields": spec.required_fields,
                "optional_fields": spec.optional_fields,
                "mutating": spec.mutating,
                "description": spec.description,
            }
            for name, spec in ACTION_SPECS.items()
        }
        context_result = self.tool_router.execute(AgentAction(action="read_context"))
        prompt_payload = {
            "instruction": (
                "You are an orchestration agent for pet care planning. "
                "Return ONLY valid JSON with keys: action, arguments, thought. "
                "When finished, use action='respond' with arguments.message."
            ),
            "goal": goal,
            "step": step,
            "allowed_actions": action_rules,
            "context": context_result.output,
            "trace_so_far": trace[-4:],
        }
        return json.dumps(prompt_payload, indent=2)

    def _write_transcript(self, session_data: Dict[str, Any]) -> None:
        base = Path(self.config.transcript_dir)
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{session_data['session_id']}.json"
        path.write_text(json.dumps(session_data, indent=2), encoding="utf-8")


def run_agent_session(
    goal: str,
    owner: Owner,
    pet: Pet,
    scheduler: Scheduler,
    config: Optional[AgentConfig] = None,
    approval_callback: Callable[[str], Optional[bool]] = default_approval_callback,
    model_adapter: Optional[BaseModelAdapter] = None,
) -> Dict[str, Any]:
    """
    Convenience helper to run an agent session for one owner/pet context.
    """
    runtime_config = config or AgentConfig()
    adapter = model_adapter or OllamaModelAdapter(
        model=runtime_config.model_name, endpoint=runtime_config.model_endpoint
    )
    router = AgentToolRouter(
        owner=owner, pet=pet, scheduler=scheduler, approval_callback=approval_callback
    )
    orchestrator = AgentOrchestrator(
        model_adapter=adapter, tool_router=router, config=runtime_config
    )
    return orchestrator.run_session(goal=goal)
