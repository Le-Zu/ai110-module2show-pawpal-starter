from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from itertools import combinations


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskType(Enum):
    FEEDING = "feeding"
    GROOMING = "grooming"
    MEDICATION = "medication"
    VET_VISIT = "vet_visit"
    EXERCISE = "exercise"


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ---------------------------------------------------------------------------
# Dataclasses  (pure data objects)
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: int
    title: str
    description: str
    type: TaskType
    due_date: datetime
    frequency: Frequency
    pet_id: int
    is_completed: bool = False

    def complete(self) -> None:
        """Mark this task as done."""
        self.is_completed = True

    def reschedule(self, new_date: datetime) -> None:
        """Move the task to a new due date and reopen it if it was completed."""
        self.due_date = new_date
        self.is_completed = False

    def get_details(self) -> str:
        """Return a human-readable summary of the task."""
        status = "Done" if self.is_completed else "Pending"
        return (
            f"[{status}] {self.title} ({self.type.value}) — "
            f"due {self.due_date.strftime('%Y-%m-%d %H:%M')}, "
            f"repeats {self.frequency.value}"
        )


@dataclass
class Pet:
    id: int
    name: str
    species: str
    breed: str
    age: int
    weight: float
    owner_id: int

    def get_info(self) -> str:
        """Return a human-readable summary of the pet."""
        return (
            f"{self.name} ({self.species} / {self.breed}) — "
            f"age {self.age}, {self.weight} kg"
        )

    def update_info(self, **kwargs) -> None:
        """Update any Pet attribute by keyword. Ignores unknown keys."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# ---------------------------------------------------------------------------
# Regular classes  (behaviour-heavy objects)
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        phone: str,
        address: str,
    ) -> None:
        """Initialize an owner with contact details and an empty pet list."""
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def remove_pet(self, pet_id: int) -> None:
        """Remove a pet by ID. No-op if the pet is not found."""
        self._pets = [p for p in self._pets if p.id != pet_id]

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return list(self._pets)

    def update_profile(self, **kwargs) -> None:
        """Update any Owner attribute by keyword. Ignores unknown keys."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class Scheduler:
    """
    Central coordinator for all pet care tasks.

    Holds a flat list of Tasks and provides queries by pet, owner, and date.
    Neither Owner nor Pet need a reference to the Scheduler — the pet_id
    foreign key on Task is the only bridge between the two sides.
    """

    def __init__(self, reminders_enabled: bool = True) -> None:
        """Initialize the scheduler with an empty task list."""
        self.reminders_enabled = reminders_enabled
        self._tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the schedule."""
        self._tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove a task by ID. No-op if not found."""
        self._tasks = [t for t in self._tasks if t.id != task_id]

    def get_tasks_for_pet(self, pet_id: int) -> list[Task]:
        """Return all tasks assigned to a specific pet."""
        return [t for t in self._tasks if t.pet_id == pet_id]

    def get_tasks_for_owner(self, owner: Owner) -> list[Task]:
        """Return all tasks across every pet belonging to the given owner."""
        pet_ids = {pet.id for pet in owner.get_pets()}
        return [t for t in self._tasks if t.pet_id in pet_ids]

    def get_tasks_for_date(self, date: datetime) -> list[Task]:
        """Return all tasks whose due date falls on the given calendar day."""
        return [
            t for t in self._tasks
            if t.due_date.date() == date.date()
        ]

    def send_reminder(self, task: Task) -> None:
        """Print a reminder for a task (placeholder for notification logic)."""
        if self.reminders_enabled and not task.is_completed:
            print(f"Reminder: {task.get_details()}")

    def generate_schedule(self) -> dict[int, list[Task]]:
        """Return all tasks grouped by pet_id and sorted by due date."""
        schedule: dict[int, list[Task]] = {}
        for task in self._tasks:
            schedule.setdefault(task.pet_id, []).append(task)
        for tasks in schedule.values():
            tasks.sort(key=lambda t: t.due_date)
        return schedule

    # ------------------------------------------------------------------
    # Sorting
    # ------------------------------------------------------------------

    def sort_tasks_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return a new list of tasks sorted ascending by due time (HH:MM)."""
        return sorted(tasks, key=lambda t: t.due_date.strftime("%H:%M"))

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return all tasks whose completion status matches the given flag."""
        return [t for t in self._tasks if t.is_completed == completed]

    def filter_by_pet_name(self, pet_name: str, owner: Owner) -> list[Task]:
        """Return tasks assigned to the pet with the given name (case-insensitive)."""
        matching_ids = {
            p.id for p in owner.get_pets()
            if p.name.lower() == pet_name.lower()
        }
        return [t for t in self._tasks if t.pet_id in matching_ids]

    # ------------------------------------------------------------------
    # Recurring task automation
    # ------------------------------------------------------------------

    def mark_task_complete(self, task_id: int) -> Task | None:
        """Mark a task done and auto-schedule the next occurrence based on its frequency; returns None for ONCE tasks."""
        task = next((t for t in self._tasks if t.id == task_id), None)
        if task is None:
            return None

        task.complete()

        delta_map = {
            Frequency.DAILY:   timedelta(days=1),
            Frequency.WEEKLY:  timedelta(weeks=1),
            Frequency.MONTHLY: timedelta(days=30),
        }
        delta = delta_map.get(task.frequency)
        if delta is None:                          # ONCE — nothing to schedule
            return None

        next_id   = max(t.id for t in self._tasks) + 1
        next_task = replace(task,
                            id=next_id,
                            due_date=task.due_date + delta,
                            is_completed=False)
        self._tasks.append(next_task)
        return next_task

    # ------------------------------------------------------------------
    # Recurring task projection
    # ------------------------------------------------------------------

    def expand_recurring(self, target_date: datetime) -> list[Task]:
        """Return a new list of tasks projected onto target_date according to each task's frequency rule."""
        results: list[Task] = []
        for task in self._tasks:
            origin = task.due_date
            projected = origin.replace(
                year=target_date.year,
                month=target_date.month,
                day=target_date.day,
            )
            include = False
            if task.frequency == Frequency.DAILY:
                include = True
            elif task.frequency == Frequency.WEEKLY:
                include = origin.weekday() == target_date.weekday()
            elif task.frequency == Frequency.MONTHLY:
                include = origin.day == target_date.day
            elif task.frequency == Frequency.ONCE:
                include = origin.date() == target_date.date()

            if include:
                results.append(replace(task, due_date=projected))

        return results

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self,
                         window_minutes: int = 30,
                         same_pet_only: bool = False) -> list[str]:
        """Return warning strings for any two tasks scheduled within window_minutes of each other."""
        warnings: list[str] = []
        for a, b in combinations(self._tasks, 2):
            if same_pet_only and a.pet_id != b.pet_id:
                continue
            gap_min = abs((a.due_date - b.due_date).total_seconds()) / 60
            if gap_min <= window_minutes:
                scope = "same pet" if a.pet_id == b.pet_id else "cross-pet"
                warnings.append(
                    f"⚠  [{scope}]  '{a.title}' @ {a.due_date.strftime('%I:%M %p')}"
                    f"  ←→  '{b.title}' @ {b.due_date.strftime('%I:%M %p')}"
                    f"  ({int(gap_min)} min apart)"
                )
        return warnings
