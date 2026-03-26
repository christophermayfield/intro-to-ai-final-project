"""
PawPal+ System Logic Layer
This module contains the core classes for the PawPal+ pet care scheduling system.
"""

import uuid
from datetime import date
from typing import Dict, List


class Owner:
    """Represents a pet owner with time constraints and preferences."""

    def __init__(self, name: str, available_time_minutes: int):
        """
        Initialize an Owner instance.

        Args:
            name: The owner's name
            available_time_minutes: Daily available time in minutes for pet care
        """
        self._name = name
        self._available_time_minutes = available_time_minutes
        self._preferences = {}

    def get_name(self) -> str:
        """Return the owner's name."""
        return self._name

    def get_available_time(self) -> int:
        """Return the available time in minutes."""
        return self._available_time_minutes

    def set_available_time(self, minutes: int) -> None:
        """
        Set the available time for pet care.

        Args:
            minutes: Available time in minutes
        """
        self._available_time_minutes = minutes

    def add_preference(self, key: str, value) -> None:
        """
        Add or update a preference.

        Args:
            key: Preference key
            value: Preference value
        """
        self._preferences[key] = value

    def get_preferences(self) -> Dict:
        """Return all preferences as a dictionary."""
        return self._preferences


class Pet:
    """Represents a pet with characteristics that affect care needs."""

    def __init__(self, name: str, species: str, age: int, size: str):
        """
        Initialize a Pet instance.

        Args:
            name: The pet's name
            species: Type of pet (dog, cat, bird, etc.)
            age: Pet's age in years
            size: Pet's size (small, medium, large)
        """
        self._name = name
        self._species = species
        self._age = age
        self._size = size
        self._special_needs = []
        self._tasks = []

    def get_name(self) -> str:
        """Return the pet's name."""
        return self._name

    def get_species(self) -> str:
        """Return the pet's species."""
        return self._species

    def add_special_need(self, need: str) -> None:
        """
        Add a special care need for the pet.

        Args:
            need: Description of special need
        """
        self._special_needs.append(need)

    def get_special_needs(self) -> List[str]:
        """Return list of special needs."""
        return self._special_needs

    def get_age(self) -> int:
        """Return the pet's age."""
        return self._age

    def get_size(self) -> str:
        """Return the pet's size."""
        return self._size

    def add_task(self, task: "Task") -> None:
        """
        Add a task to this pet.

        Args:
            task: Task to add to the pet
        """
        self._tasks.append(task)

    def get_tasks(self) -> List["Task"]:
        """Return all tasks for this pet."""
        return self._tasks

    def get_task_count(self) -> int:
        """Return the number of tasks for this pet."""
        return len(self._tasks)


class Task:
    """Represents a pet care task with duration and priority."""

    def __init__(self, name: str, task_type: str, duration_minutes: int, priority: int):
        """
        Initialize a Task instance.

        Args:
            name: Task name
            task_type: Type of task (walk, feeding, meds, enrichment, grooming, etc.)
            duration_minutes: How long the task takes
            priority: Task priority (higher number = higher priority)
        """
        self._task_id = str(uuid.uuid4())
        self._name = name
        self._task_type = task_type
        self._duration_minutes = duration_minutes
        self._priority = priority
        self._description = ""
        self._is_mandatory = False
        self._frequency = "daily"
        self._is_completed = False

    def get_duration(self) -> int:
        """Return task duration in minutes."""
        return self._duration_minutes

    def get_priority(self) -> int:
        """Return task priority."""
        return self._priority

    def set_priority(self, priority: int) -> None:
        """
        Set task priority.

        Args:
            priority: New priority value
        """
        self._priority = priority

    def get_task_type(self) -> str:
        """Return the task type."""
        return self._task_type

    def is_mandatory(self) -> bool:
        """Return whether this task is mandatory."""
        return self._is_mandatory

    def get_task_id(self) -> str:
        """Return the task ID."""
        return self._task_id

    def get_name(self) -> str:
        """Return the task name."""
        return self._name

    def get_description(self) -> str:
        """Return the task description."""
        return self._description

    def set_mandatory(self, is_mandatory: bool) -> None:
        """
        Set whether this task is mandatory.

        Args:
            is_mandatory: True if task must be completed, False otherwise
        """
        self._is_mandatory = is_mandatory

    def set_description(self, description: str) -> None:
        """
        Set the task description.

        Args:
            description: Task description text
        """
        self._description = description

    def set_frequency(self, frequency: str) -> None:
        """
        Set the task frequency.

        Args:
            frequency: How often the task should be done (e.g., "daily", "weekly")
        """
        self._frequency = frequency

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self._is_completed = True

    def is_completed(self) -> bool:
        """Return whether this task is completed."""
        return self._is_completed

    def get_frequency(self) -> str:
        """Return the task frequency."""
        return self._frequency


class ScheduledTask:
    """Represents a task scheduled at a specific time in a plan."""

    def __init__(self, task: Task, start_time: str, end_time: str, order: int):
        """
        Initialize a ScheduledTask instance.

        Args:
            task: The Task to schedule
            start_time: Start time (e.g., "08:00")
            end_time: End time (e.g., "08:30")
            order: Order in the schedule (1st, 2nd, 3rd, etc.)
        """
        self._task = task
        self._start_time = start_time
        self._end_time = end_time
        self._order = order

    def get_task(self) -> Task:
        """Return the associated Task."""
        return self._task

    def get_start_time(self) -> str:
        """Return the start time."""
        return self._start_time

    def get_end_time(self) -> str:
        """Return the end time."""
        return self._end_time

    def get_order(self) -> int:
        """Return the order in the schedule."""
        return self._order


class Plan:
    """Represents a daily care plan with scheduled tasks and explanations."""

    def __init__(self):
        """Initialize a Plan instance."""
        self._scheduled_tasks = []
        self._total_time_minutes = 0
        self._explanation = ""
        self._plan_date = date.today()
        self._excluded_tasks = []

    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """
        Add a scheduled task to the plan.

        Args:
            scheduled_task: ScheduledTask to add
        """
        self._scheduled_tasks.append(scheduled_task)
        self._total_time_minutes += scheduled_task.get_task().get_duration()

    def get_scheduled_tasks(self) -> List[ScheduledTask]:
        """Return all scheduled tasks."""
        return self._scheduled_tasks

    def get_total_time(self) -> int:
        """Return total time of all scheduled tasks in minutes."""
        return self._total_time_minutes

    def set_explanation(self, explanation: str) -> None:
        """
        Set the explanation for the plan.

        Args:
            explanation: Text explaining scheduling decisions
        """
        self._explanation = explanation

    def get_explanation(self) -> str:
        """Return the plan explanation."""
        return self._explanation

    def get_excluded_tasks(self) -> List[Task]:
        """Return tasks that couldn't be scheduled."""
        return self._excluded_tasks

    def add_excluded_task(self, task: Task) -> None:
        """
        Add a task that couldn't be scheduled.

        Args:
            task: Task that was excluded from the plan
        """
        self._excluded_tasks.append(task)

    def get_plan_date(self) -> date:
        """Return the date for this plan."""
        return self._plan_date


class Scheduler:
    """Core scheduling logic that generates optimized daily plans."""

    def __init__(self, owner: Owner, pet: Pet):
        """
        Initialize a Scheduler instance.

        Args:
            owner: The Owner for whom to schedule
            pet: The Pet requiring care
        """
        self._tasks = []
        self._owner = owner
        self._pet = pet
        self._constraints = {}

    def add_task(self, task: Task) -> None:
        """
        Add a task to the scheduler.

        Args:
            task: Task to add
        """
        self._tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """
        Remove a task by ID.

        Args:
            task_id: UUID of the task to remove
        """
        self._tasks = [t for t in self._tasks if t.get_task_id() != task_id]

    def get_tasks(self) -> List[Task]:
        """Return all tasks."""
        return self._tasks

    def generate_plan(self) -> Plan:
        """
        Generate an optimized daily plan based on tasks and constraints.

        Returns:
            A Plan object with scheduled tasks and explanation
        """
        plan = Plan()

        if not self._tasks:
            plan.set_explanation("No tasks to schedule.")
            return plan

        # Step 1: Prioritize tasks (mandatory first, then by priority)
        prioritized_tasks = self._prioritize_tasks()

        # Step 2: Optimize the order of tasks
        optimized_tasks = self._optimize_schedule(prioritized_tasks)

        # Step 3: Schedule tasks within time constraints
        available_time = self._owner.get_available_time()
        current_time = 480  # Start at 8:00 AM (480 minutes from midnight)
        scheduled_count = 0
        excluded_count = 0

        explanation_parts = []
        explanation_parts.append(
            f"Scheduling plan for {self._pet.get_name()} ({self._pet.get_species()})."
        )
        explanation_parts.append(
            f"Owner: {self._owner.get_name()}, Available time: {available_time} minutes."
        )

        for task in optimized_tasks:
            task_duration = task.get_duration()

            # Check if we have enough time left
            if plan.get_total_time() + task_duration <= available_time:
                # Calculate start and end times
                start_hour = current_time // 60
                start_min = current_time % 60
                start_time = f"{start_hour:02d}:{start_min:02d}"

                current_time += task_duration
                end_hour = current_time // 60
                end_min = current_time % 60
                end_time = f"{end_hour:02d}:{end_min:02d}"

                # Create scheduled task
                scheduled_task = ScheduledTask(
                    task, start_time, end_time, scheduled_count + 1
                )
                plan.add_scheduled_task(scheduled_task)
                scheduled_count += 1
            else:
                # Task doesn't fit
                plan.add_excluded_task(task)
                excluded_count += 1

        # Build explanation
        explanation_parts.append(
            f"\nScheduled {scheduled_count} task(s) totaling {plan.get_total_time()} minutes."
        )

        if scheduled_count > 0:
            explanation_parts.append("\nPrioritization strategy:")
            explanation_parts.append("1. Mandatory tasks scheduled first")
            explanation_parts.append(
                "2. Remaining tasks sorted by priority (highest first)"
            )
            explanation_parts.append("3. Tasks optimized for logical flow")

        if excluded_count > 0:
            explanation_parts.append(
                f"\n{excluded_count} task(s) could not fit within available time:"
            )
            for task in plan.get_excluded_tasks():
                explanation_parts.append(
                    f"  - {task.get_name()} ({task.get_duration()} min, priority {task.get_priority()})"
                )

        plan.set_explanation("\n".join(explanation_parts))
        return plan

    def _prioritize_tasks(self) -> List[Task]:
        """
        Sort tasks by priority (private helper method).

        Returns:
            Sorted list of tasks
        """
        # Sort by: mandatory first, then by priority (descending), then by duration (ascending)
        return sorted(
            self._tasks,
            key=lambda t: (not t.is_mandatory(), -t.get_priority(), t.get_duration()),
        )

    def _check_time_constraints(self, tasks: List[Task]) -> bool:
        """
        Check if tasks fit within available time (private helper method).

        Args:
            tasks: List of tasks to check

        Returns:
            True if tasks fit, False otherwise
        """
        total_duration = sum(task.get_duration() for task in tasks)
        return total_duration <= self._owner.get_available_time()

    def _optimize_schedule(self, tasks: List[Task]) -> List[Task]:
        """
        Optimize the order of tasks (private helper method).

        Args:
            tasks: List of tasks to optimize

        Returns:
            Optimized list of tasks
        """
        # Create a copy to avoid modifying the original
        optimized = tasks.copy()

        # Define task type ordering for logical flow
        task_order = {
            "feeding": 1,
            "meds": 2,
            "walk": 3,
            "enrichment": 4,
            "grooming": 5,
            "training": 6,
            "playtime": 7,
        }

        # Group by mandatory status and priority, then order by task type
        optimized.sort(
            key=lambda t: (
                not t.is_mandatory(),
                -t.get_priority(),
                task_order.get(t.get_task_type().lower(), 99),
            )
        )

        return optimized
