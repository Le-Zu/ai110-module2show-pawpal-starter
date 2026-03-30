from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_owner(id=1, name="Alex") -> Owner:
    return Owner(id=id, name=name, email="a@b.com", phone="555", address="123 St")

def make_pet(id=1, name="Buddy", owner_id=1) -> Pet:
    return Pet(id=id, name=name, species="Dog", breed="Lab",
               age=3, weight=28.5, owner_id=owner_id)

def make_task(id=1, pet_id=1, hour=8, minute=0,
              frequency=Frequency.DAILY, title="Feed") -> Task:
    return Task(
        id=id, title=title, description="desc",
        type=TaskType.FEEDING,
        due_date=datetime(2026, 3, 29, hour, minute),
        frequency=frequency,
        pet_id=pet_id,
    )

def fresh_scheduler(*tasks: Task) -> Scheduler:
    s = Scheduler()
    for t in tasks:
        s.add_task(t)
    return s


# ===========================================================================
# 1. TASK COMPLETION
# ===========================================================================

def test_task_complete_changes_status():
    """complete() flips is_completed from False to True."""
    task = make_task()
    assert task.is_completed is False
    task.complete()
    assert task.is_completed is True


def test_task_reschedule_reopens_task():
    """reschedule() updates due_date and resets is_completed to False."""
    task = make_task()
    task.complete()
    new_date = datetime(2026, 3, 30, 9, 0)
    task.reschedule(new_date)
    assert task.due_date == new_date
    assert task.is_completed is False


# ===========================================================================
# 2. SORTING CORRECTNESS
# ===========================================================================

def test_sort_tasks_by_time_chronological_order():
    """Tasks inserted out of order are returned in ascending time order."""
    s = fresh_scheduler(
        make_task(id=1, hour=18),   # evening — added first
        make_task(id=2, hour=7),    # morning — added second
        make_task(id=3, hour=12),   # noon    — added last
    )
    sorted_tasks = s.sort_tasks_by_time(s._tasks)
    times = [t.due_date.hour for t in sorted_tasks]
    assert times == sorted(times), f"Expected ascending hours, got {times}"


def test_sort_handles_midnight_task():
    """A task at 00:00 sorts before all other times."""
    s = fresh_scheduler(
        make_task(id=1, hour=8),
        make_task(id=2, hour=0, minute=0),   # midnight
        make_task(id=3, hour=14),
    )
    sorted_tasks = s.sort_tasks_by_time(s._tasks)
    assert sorted_tasks[0].due_date.hour == 0


def test_sort_returns_new_list_not_mutate():
    """sort_tasks_by_time returns a new list; original order is unchanged."""
    s = fresh_scheduler(
        make_task(id=1, hour=18),
        make_task(id=2, hour=7),
    )
    original_first_id = s._tasks[0].id
    s.sort_tasks_by_time(s._tasks)
    assert s._tasks[0].id == original_first_id   # insertion order untouched


# ===========================================================================
# 3. RECURRENCE LOGIC
# ===========================================================================

def test_mark_complete_daily_creates_next_day():
    """Completing a DAILY task auto-creates a new task exactly 1 day later."""
    task = make_task(id=1, frequency=Frequency.DAILY)
    s = fresh_scheduler(task)
    next_task = s.mark_task_complete(task.id)

    assert next_task is not None
    assert next_task.due_date == task.due_date + timedelta(days=1)
    assert next_task.is_completed is False


def test_mark_complete_weekly_creates_next_week():
    """Completing a WEEKLY task auto-creates a new task exactly 7 days later."""
    task = make_task(id=1, frequency=Frequency.WEEKLY)
    s = fresh_scheduler(task)
    next_task = s.mark_task_complete(task.id)

    assert next_task is not None
    assert next_task.due_date == task.due_date + timedelta(weeks=1)


def test_mark_complete_once_returns_none():
    """Completing a ONCE task returns None — no follow-up is created."""
    task = make_task(id=1, frequency=Frequency.ONCE)
    s = fresh_scheduler(task)
    result = s.mark_task_complete(task.id)

    assert result is None
    assert len(s._tasks) == 1   # no new task added


def test_mark_complete_new_task_added_to_scheduler():
    """The auto-created recurring task is appended to the scheduler's list."""
    task = make_task(id=1, frequency=Frequency.DAILY)
    s = fresh_scheduler(task)
    assert len(s._tasks) == 1
    s.mark_task_complete(task.id)
    assert len(s._tasks) == 2


def test_mark_complete_invalid_id_returns_none():
    """Calling mark_task_complete with a non-existent ID returns None safely."""
    s = fresh_scheduler(make_task(id=1))
    result = s.mark_task_complete(999)
    assert result is None


# ===========================================================================
# 4. CONFLICT DETECTION
# ===========================================================================

def test_detect_conflict_same_time_same_pet():
    """Two tasks for the same pet at exactly the same time are flagged."""
    s = fresh_scheduler(
        make_task(id=1, pet_id=1, hour=9, minute=0),
        make_task(id=2, pet_id=1, hour=9, minute=0),
    )
    warnings = s.detect_conflicts(window_minutes=30)
    assert len(warnings) == 1
    assert "same pet" in warnings[0]


def test_detect_no_conflict_outside_window():
    """Tasks more than window_minutes apart are not flagged."""
    s = fresh_scheduler(
        make_task(id=1, pet_id=1, hour=8, minute=0),
        make_task(id=2, pet_id=1, hour=9, minute=31),  # 91 min gap
    )
    warnings = s.detect_conflicts(window_minutes=30)
    assert warnings == []


def test_detect_conflict_boundary_at_window_limit():
    """Tasks exactly at window_minutes apart are still flagged (inclusive boundary)."""
    s = fresh_scheduler(
        make_task(id=1, pet_id=1, hour=9, minute=0),
        make_task(id=2, pet_id=1, hour=9, minute=30),  # exactly 30 min
    )
    warnings = s.detect_conflicts(window_minutes=30)
    assert len(warnings) == 1


def test_detect_cross_pet_conflict_flagged_by_default():
    """Tasks for different pets at the same time are flagged when same_pet_only=False."""
    s = fresh_scheduler(
        make_task(id=1, pet_id=1, hour=7),
        make_task(id=2, pet_id=2, hour=7),
    )
    warnings = s.detect_conflicts(window_minutes=30, same_pet_only=False)
    assert any("cross-pet" in w for w in warnings)


def test_detect_cross_pet_ignored_when_same_pet_only():
    """Cross-pet conflicts are not reported when same_pet_only=True."""
    s = fresh_scheduler(
        make_task(id=1, pet_id=1, hour=7),
        make_task(id=2, pet_id=2, hour=7),
    )
    warnings = s.detect_conflicts(window_minutes=30, same_pet_only=True)
    assert warnings == []


def test_detect_empty_scheduler_returns_no_warnings():
    """An empty scheduler produces no conflict warnings."""
    s = Scheduler()
    assert s.detect_conflicts() == []


# ===========================================================================
# 5. FILTERING
# ===========================================================================

def test_filter_by_status_pending():
    """filter_by_status(False) returns only incomplete tasks."""
    t1 = make_task(id=1)
    t2 = make_task(id=2)
    t2.complete()
    s = fresh_scheduler(t1, t2)

    pending = s.filter_by_status(completed=False)
    assert all(not t.is_completed for t in pending)
    assert len(pending) == 1


def test_filter_by_status_completed():
    """filter_by_status(True) returns only completed tasks."""
    t1 = make_task(id=1)
    t2 = make_task(id=2)
    t1.complete()
    s = fresh_scheduler(t1, t2)

    done = s.filter_by_status(completed=True)
    assert all(t.is_completed for t in done)
    assert len(done) == 1


def test_filter_by_pet_name_correct_pet():
    """filter_by_pet_name returns only tasks for the named pet."""
    owner = make_owner()
    buddy    = make_pet(id=1, name="Buddy",    owner_id=1)
    whiskers = make_pet(id=2, name="Whiskers", owner_id=1)
    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    s = fresh_scheduler(
        make_task(id=1, pet_id=1),   # Buddy
        make_task(id=2, pet_id=2),   # Whiskers
        make_task(id=3, pet_id=1),   # Buddy
    )
    results = s.filter_by_pet_name("Buddy", owner)
    assert len(results) == 2
    assert all(t.pet_id == buddy.id for t in results)


def test_filter_by_pet_name_unknown_returns_empty():
    """filter_by_pet_name with an unknown name returns an empty list."""
    owner = make_owner()
    owner.add_pet(make_pet(id=1, name="Buddy"))
    s = fresh_scheduler(make_task(id=1, pet_id=1))

    results = s.filter_by_pet_name("NoSuchPet", owner)
    assert results == []


# ===========================================================================
# 6. OWNER / PET RELATIONSHIP
# ===========================================================================

def test_add_task_increases_pet_task_count():
    """Adding tasks to the scheduler increases the count returned for that pet."""
    s = fresh_scheduler(
        make_task(id=1, pet_id=1),
        make_task(id=2, pet_id=1),
    )
    assert len(s.get_tasks_for_pet(pet_id=1)) == 2


def test_get_tasks_for_owner_excludes_other_owners():
    """get_tasks_for_owner only returns tasks belonging to that owner's pets."""
    owner_a = make_owner(id=1, name="Alex")
    owner_b = make_owner(id=2, name="Blake")

    pet_a = make_pet(id=1, owner_id=1)
    pet_b = make_pet(id=2, name="Luna", owner_id=2)
    owner_a.add_pet(pet_a)
    owner_b.add_pet(pet_b)

    s = fresh_scheduler(
        make_task(id=1, pet_id=1),   # belongs to owner_a
        make_task(id=2, pet_id=2),   # belongs to owner_b
    )

    a_tasks = s.get_tasks_for_owner(owner_a)
    assert len(a_tasks) == 1
    assert a_tasks[0].pet_id == pet_a.id


def test_remove_pet_from_owner():
    """remove_pet() correctly reduces the owner's pet count."""
    owner = make_owner()
    owner.add_pet(make_pet(id=1, name="Buddy"))
    owner.add_pet(make_pet(id=2, name="Luna"))
    assert len(owner.get_pets()) == 2
    owner.remove_pet(pet_id=1)
    assert len(owner.get_pets()) == 1
    assert owner.get_pets()[0].name == "Luna"
