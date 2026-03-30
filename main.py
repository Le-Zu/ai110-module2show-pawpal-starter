from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

owner = Owner(id=1, name="Alex Johnson", email="alex@email.com",
              phone="555-1234", address="123 Maple St")

buddy    = Pet(id=1, name="Buddy",    species="Dog", breed="Labrador",
               age=3, weight=28.5, owner_id=1)
whiskers = Pet(id=2, name="Whiskers", species="Cat", breed="Siamese",
               age=5, weight=4.2,  owner_id=1)

owner.add_pet(buddy)
owner.add_pet(whiskers)

today = datetime.now()

TASK_ICON = {
    TaskType.FEEDING:    "🍽 ",
    TaskType.MEDICATION: "💊",
    TaskType.EXERCISE:   "🐾",
    TaskType.VET_VISIT:  "🏥",
    TaskType.GROOMING:   "✂ ",
}

def print_tasks(tasks: list[Task], pet_map: dict) -> None:
    if not tasks:
        print("    (none)")
        return
    for task in tasks:
        pet    = pet_map.get(task.pet_id)
        icon   = TASK_ICON.get(task.type, "•")
        time_s = task.due_date.strftime("%I:%M %p  %a %b %d")
        status = "✓" if task.is_completed else "○"
        print(f"    {status} {time_s}  {icon}  {task.title:<22}  [{pet.name}]  id={task.id}")

def section(title: str) -> None:
    print()
    print("=" * 62)
    print(f"  {title}")
    print("=" * 62)

# ---------------------------------------------------------------------------
# Tasks  (added out of order — evening before morning — to stress sorting)
# ---------------------------------------------------------------------------

scheduler = Scheduler(reminders_enabled=True)

scheduler.add_task(Task(id=5, title="Evening Feed",
    description="1 cup dry kibble",
    type=TaskType.FEEDING,    due_date=today.replace(hour=18, minute=0),
    frequency=Frequency.DAILY,  pet_id=1))

scheduler.add_task(Task(id=3, title="Morning Walk",
    description="30-min walk around the block",
    type=TaskType.EXERCISE,   due_date=today.replace(hour=9, minute=0),
    frequency=Frequency.WEEKLY, pet_id=1))

scheduler.add_task(Task(id=6, title="Brushing",
    description="5-min coat brush",
    type=TaskType.GROOMING,   due_date=today.replace(hour=19, minute=0),
    frequency=Frequency.WEEKLY, pet_id=2))

scheduler.add_task(Task(id=1, title="Morning Feed",
    description="1 cup dry kibble",
    type=TaskType.FEEDING,    due_date=today.replace(hour=7, minute=0),
    frequency=Frequency.DAILY,  pet_id=1))

scheduler.add_task(Task(id=4, title="Vet Check-up",
    description="Annual wellness exam",
    type=TaskType.VET_VISIT,  due_date=today.replace(hour=11, minute=0),
    frequency=Frequency.ONCE,   pet_id=2))

scheduler.add_task(Task(id=2, title="Insulin Shot",
    description="2 units, left shoulder",
    type=TaskType.MEDICATION, due_date=today.replace(hour=8, minute=30),
    frequency=Frequency.DAILY,  pet_id=2))

# --- Deliberate conflicts for Step 4 ---
# Same-pet conflict: Buddy has two tasks 15 min apart
scheduler.add_task(Task(id=7, title="Flea Treatment",
    description="Apply between shoulder blades",
    type=TaskType.MEDICATION, due_date=today.replace(hour=9, minute=15),
    frequency=Frequency.ONCE,   pet_id=1))

# Cross-pet conflict: both pets scheduled at exactly the same time
scheduler.add_task(Task(id=8, title="Whiskers Morning Feed",
    description="Half can wet food",
    type=TaskType.FEEDING,    due_date=today.replace(hour=7, minute=0),
    frequency=Frequency.DAILY,  pet_id=2))

pet_map = {p.id: p for p in owner.get_pets()}

# ---------------------------------------------------------------------------
# Demo 1 & 2: Insertion order vs sorted
# ---------------------------------------------------------------------------

section("1. RAW INSERTION ORDER  (unsorted)")
print_tasks(scheduler.get_tasks_for_date(today), pet_map)

section("2. SORTED BY TIME  (sort_tasks_by_time)")
print_tasks(scheduler.sort_tasks_by_time(
    scheduler.get_tasks_for_date(today)), pet_map)

# ---------------------------------------------------------------------------
# Demo 3: Filtering
# ---------------------------------------------------------------------------

section("3a. FILTER — pending tasks only")
print_tasks(scheduler.sort_tasks_by_time(
    scheduler.filter_by_status(completed=False)), pet_map)

section("3b. FILTER — Buddy's tasks only")
print_tasks(scheduler.sort_tasks_by_time(
    scheduler.filter_by_pet_name("Buddy", owner)), pet_map)

# ---------------------------------------------------------------------------
# Demo 4: Step 3 — mark_task_complete() auto-schedules next occurrence
# ---------------------------------------------------------------------------

section("4. AUTO-RECURRING — mark_task_complete()")

daily_task  = next(t for t in scheduler._tasks if t.id == 1)  # Morning Feed (DAILY)
weekly_task = next(t for t in scheduler._tasks if t.id == 3)  # Morning Walk (WEEKLY)
once_task   = next(t for t in scheduler._tasks if t.id == 4)  # Vet Check-up (ONCE)

print(f"\n  Completing '{daily_task.title}' (DAILY, id={daily_task.id}) ...")
next_daily = scheduler.mark_task_complete(daily_task.id)
print(f"    ✓ Marked done. Next occurrence auto-created:")
print(f"      id={next_daily.id}  due={next_daily.due_date.strftime('%a %b %d at %I:%M %p')}"
      f"  (+1 day via timedelta)")

print(f"\n  Completing '{weekly_task.title}' (WEEKLY, id={weekly_task.id}) ...")
next_weekly = scheduler.mark_task_complete(weekly_task.id)
print(f"    ✓ Marked done. Next occurrence auto-created:")
print(f"      id={next_weekly.id}  due={next_weekly.due_date.strftime('%a %b %d at %I:%M %p')}"
      f"  (+7 days via timedelta)")

print(f"\n  Completing '{once_task.title}' (ONCE, id={once_task.id}) ...")
no_next = scheduler.mark_task_complete(once_task.id)
print(f"    ✓ Marked done. No follow-up created (ONCE task) → returned: {no_next}")

print(f"\n  All tasks after completions (showing new auto-scheduled entries):")
print_tasks(scheduler.sort_tasks_by_time(list(scheduler._tasks)), pet_map)

# ---------------------------------------------------------------------------
# Demo 5: Step 4 — detect_conflicts()
# ---------------------------------------------------------------------------

section("5a. CONFLICT DETECTION — same-pet only  (same_pet_only=True)")
warnings = scheduler.detect_conflicts(window_minutes=30, same_pet_only=True)
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No same-pet conflicts.")

section("5b. CONFLICT DETECTION — all conflicts incl. cross-pet  (same_pet_only=False)")
warnings = scheduler.detect_conflicts(window_minutes=30, same_pet_only=False)
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No conflicts detected.")

print()
