from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

owner = Owner(id=1, name="Alex Johnson", email="alex@email.com",
              phone="555-1234", address="123 Maple St")

buddy = Pet(id=1, name="Buddy", species="Dog", breed="Labrador",
            age=3, weight=28.5, owner_id=1)

whiskers = Pet(id=2, name="Whiskers", species="Cat", breed="Siamese",
               age=5, weight=4.2, owner_id=1)

owner.add_pet(buddy)
owner.add_pet(whiskers)

# ---------------------------------------------------------------------------
# Tasks  (mix of pets, types, and times today)
# ---------------------------------------------------------------------------

today = datetime.now()

tasks = [
    Task(id=1, title="Morning Feed",      description="1 cup dry kibble",
         type=TaskType.FEEDING,    due_date=today.replace(hour=7,  minute=0),
         frequency=Frequency.DAILY,  pet_id=1),

    Task(id=2, title="Insulin Shot",      description="2 units, left shoulder",
         type=TaskType.MEDICATION, due_date=today.replace(hour=8,  minute=30),
         frequency=Frequency.DAILY,  pet_id=2),

    Task(id=3, title="Morning Walk",      description="30-min walk around the block",
         type=TaskType.EXERCISE,   due_date=today.replace(hour=9,  minute=0),
         frequency=Frequency.DAILY,  pet_id=1),

    Task(id=4, title="Vet Check-up",      description="Annual wellness exam",
         type=TaskType.VET_VISIT,  due_date=today.replace(hour=11, minute=0),
         frequency=Frequency.ONCE,   pet_id=2),

    Task(id=5, title="Evening Feed",      description="1 cup dry kibble",
         type=TaskType.FEEDING,    due_date=today.replace(hour=18, minute=0),
         frequency=Frequency.DAILY,  pet_id=1),

    Task(id=6, title="Brushing",          description="5-min coat brush",
         type=TaskType.GROOMING,   due_date=today.replace(hour=19, minute=0),
         frequency=Frequency.WEEKLY, pet_id=2),
]

scheduler = Scheduler(reminders_enabled=True)
for task in tasks:
    scheduler.add_task(task)

# ---------------------------------------------------------------------------
# Pet lookup helper  (id -> Pet)
# ---------------------------------------------------------------------------

pet_map: dict[int, Pet] = {p.id: p for p in owner.get_pets()}

# ---------------------------------------------------------------------------
# Print today's schedule
# ---------------------------------------------------------------------------

TASK_ICON = {
    TaskType.FEEDING:    "🍽 ",
    TaskType.MEDICATION: "💊",
    TaskType.EXERCISE:   "🐾",
    TaskType.VET_VISIT:  "🏥",
    TaskType.GROOMING:   "✂ ",
}

schedule = scheduler.generate_schedule()   # dict[pet_id -> sorted tasks]

print()
print("=" * 50)
print(f"  TODAY'S SCHEDULE — {today.strftime('%A, %B %d %Y')}")
print("=" * 50)

# Collect and sort all of today's tasks across pets by due_date
todays_tasks = scheduler.get_tasks_for_date(today)
todays_tasks.sort(key=lambda t: t.due_date)

if not todays_tasks:
    print("  No tasks scheduled for today.")
else:
    for task in todays_tasks:
        pet    = pet_map.get(task.pet_id)
        icon   = TASK_ICON.get(task.type, "•")
        time   = task.due_date.strftime("%I:%M %p")
        status = "✓" if task.is_completed else "○"

        print(f"\n  {status} {time}  {icon}  {task.title}")
        print(f"       Pet      : {pet.name} ({pet.species})")
        print(f"       Type     : {task.type.value.replace('_', ' ').title()}")
        print(f"       Notes    : {task.description}")
        print(f"       Repeats  : {task.frequency.value}")

print()
print("=" * 50)
print(f"  {len(todays_tasks)} task(s) scheduled  |  "
      f"{sum(t.is_completed for t in todays_tasks)} completed")
print("=" * 50)
print()
