"""
PawPal+ System Logic Layer
This module contains the core classes for the PawPal+ pet care scheduling system.
"""

from typing import List, Dict, Optional
from datetime import date
import uuid


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
        pass
    
    def get_available_time(self) -> int:
        """Return the available time in minutes."""
        pass
    
    def set_available_time(self, minutes: int) -> None:
        """
        Set the available time for pet care.
        
        Args:
            minutes: Available time in minutes
        """
        pass
    
    def add_preference(self, key: str, value) -> None:
        """
        Add or update a preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        pass
    
    def get_preferences(self) -> Dict:
        """Return all preferences as a dictionary."""
        pass


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
    
    def get_name(self) -> str:
        """Return the pet's name."""
        pass
    
    def get_species(self) -> str:
        """Return the pet's species."""
        pass
    
    def add_special_need(self, need: str) -> None:
        """
        Add a special care need for the pet.
        
        Args:
            need: Description of special need
        """
        pass
    
    def get_special_needs(self) -> List[str]:
        """Return list of special needs."""
        pass


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
    
    def get_duration(self) -> int:
        """Return task duration in minutes."""
        pass
    
    def get_priority(self) -> int:
        """Return task priority."""
        pass
    
    def set_priority(self, priority: int) -> None:
        """
        Set task priority.
        
        Args:
            priority: New priority value
        """
        pass
    
    def get_task_type(self) -> str:
        """Return the task type."""
        pass
    
    def is_mandatory(self) -> bool:
        """Return whether this task is mandatory."""
        pass


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
        pass
    
    def get_start_time(self) -> str:
        """Return the start time."""
        pass
    
    def get_end_time(self) -> str:
        """Return the end time."""
        pass
    
    def get_order(self) -> int:
        """Return the order in the schedule."""
        pass


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
        pass
    
    def get_scheduled_tasks(self) -> List[ScheduledTask]:
        """Return all scheduled tasks."""
        pass
    
    def get_total_time(self) -> int:
        """Return total time of all scheduled tasks in minutes."""
        pass
    
    def set_explanation(self, explanation: str) -> None:
        """
        Set the explanation for the plan.
        
        Args:
            explanation: Text explaining scheduling decisions
        """
        pass
    
    def get_explanation(self) -> str:
        """Return the plan explanation."""
        pass
    
    def get_excluded_tasks(self) -> List[Task]:
        """Return tasks that couldn't be scheduled."""
        pass


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
        pass
    
    def remove_task(self, task_id: str) -> None:
        """
        Remove a task by ID.
        
        Args:
            task_id: UUID of the task to remove
        """
        pass
    
    def get_tasks(self) -> List[Task]:
        """Return all tasks."""
        pass
    
    def generate_plan(self) -> Plan:
        """
        Generate an optimized daily plan based on tasks and constraints.
        
        Returns:
            A Plan object with scheduled tasks and explanation
        """
        pass
    
    def _prioritize_tasks(self) -> List[Task]:
        """
        Sort tasks by priority (private helper method).
        
        Returns:
            Sorted list of tasks
        """
        pass
    
    def _check_time_constraints(self, tasks: List[Task]) -> bool:
        """
        Check if tasks fit within available time (private helper method).
        
        Args:
            tasks: List of tasks to check
            
        Returns:
            True if tasks fit, False otherwise
        """
        pass
    
    def _optimize_schedule(self, tasks: List[Task]) -> List[Task]:
        """
        Optimize the order of tasks (private helper method).
        
        Args:
            tasks: List of tasks to optimize
            
        Returns:
            Optimized list of tasks
        """
        pass

