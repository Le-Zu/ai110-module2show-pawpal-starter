from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_task(id=1, pet_id=1) -> Task:
    return Task(
        id=id,
        title="Morning Feed",
        description="1 cup dry kibble",
        type=TaskType.FEEDING,
        due_date=datetime(2026, 3, 29, 7, 0),
        frequency=Frequency.DAILY,
        pet_id=pet_id,
    )

def make_pet(id=1) -> Pet:
    return Pet(id=id, name="Buddy", species="Dog", breed="Labrador",
               age=3, weight=28.5, owner_id=1)


# ---------------------------------------------------------------------------
# Test 1: Task completion
# ---------------------------------------------------------------------------

def test_task_complete_changes_status():
    """Calling complete() should flip is_completed from False to True."""
    task = make_task()

    assert task.is_completed is False   # starts incomplete

    task.complete()

    assert task.is_completed is True    # now marked done


# ---------------------------------------------------------------------------
# Test 2: Task addition increases pet's task count
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    """Adding a task to the Scheduler should increase that pet's task count."""
    pet       = make_pet(id=1)
    scheduler = Scheduler()

    before = len(scheduler.get_tasks_for_pet(pet.id))  # 0

    scheduler.add_task(make_task(id=1, pet_id=pet.id))
    scheduler.add_task(make_task(id=2, pet_id=pet.id))

    after = len(scheduler.get_tasks_for_pet(pet.id))   # 2

    assert after == before + 2
