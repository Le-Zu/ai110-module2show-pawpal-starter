from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
