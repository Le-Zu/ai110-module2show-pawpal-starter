# PawPal+ — Pet Care Planning Assistant

A smart Streamlit app that helps a pet owner plan, track, and automate care tasks for one or more pets. Built with a Python class-based backend and an intelligent scheduling layer.

---

## 📸 Demo

<a href="/course_images/ai110/image.png" target="_blank"><img src="/course_images/ai110/image.png" alt="PawPal+ app screenshot showing owner profile, pet roster, task scheduler, and today's schedule with conflict detection" width="400"/></a>

---

## Features

### Core Data Model
- **Owner management** — store contact details and manage a list of pets; update profile in-place without losing data
- **Multi-pet support** — each Owner can have any number of Pets, each with species, breed, age, and weight
- **Typed tasks** — every Task carries a `TaskType` (Feeding, Grooming, Medication, Vet Visit, Exercise) and a `Frequency` (Once, Daily, Weekly, Monthly), both enforced as enums to prevent invalid values

### Smart Scheduling Algorithms
- **Sorting by time** — `sort_tasks_by_time()` returns tasks in chronological AM/PM order using an `HH:MM` string key, regardless of the order they were added
- **Status filtering** — `filter_by_status(completed)` instantly narrows the task list to pending or completed items only
- **Pet filtering** — `filter_by_pet_name(name, owner)` returns tasks for a single named pet across the full schedule (case-insensitive)
- **Daily recurrence automation** — `mark_task_complete()` marks a task done and auto-generates the next occurrence using Python `timedelta`: Daily → +1 day, Weekly → +7 days, Monthly → +30 days; ONCE tasks close with no follow-up
- **Recurring task projection** — `expand_recurring(target_date)` previews what any future date's schedule looks like based on each task's frequency rule
- **Conflict warnings** — `detect_conflicts(window_minutes)` scans every unique task pair with `itertools.combinations` and returns plain-English warning strings for any two tasks within the time window — covers both same-pet and cross-pet overlaps, never crashes

### Streamlit UI
- Owner profile form with persistent session state
- Pet roster displayed as a clean table
- Task scheduler with AM/PM time picker and repeat frequency selector
- Today's Schedule view with four filter tabs: **All**, **Pending**, **Completed**, **By Pet**
- Conflict warning banners appear at the top of the schedule before the task list
- Per-task **✓ Done** button calls `mark_task_complete()` and confirms the next auto-scheduled date
- Summary metrics footer: Total / Completed / Remaining

---

## System Architecture

The full class diagram is in [`uml_final.md`](uml_final.md) (renders in VS Code with the Mermaid extension, or on GitHub).

**Key design decisions:**
- `Pet` and `Task` are Python `@dataclass` objects — pure data, auto-generated `__init__` and `__repr__`
- `Owner` and `Scheduler` are regular classes — they manage mutable internal state (`_pets`, `_tasks`)
- `Scheduler` is the only class that holds tasks; `pet_id` on `Task` is the foreign-key bridge to `Pet`
- `Owner` and `Pet` have no reference to `Scheduler` — decoupled by design

---

## Project Structure

```
ai110-module2show-pawpal-starter/
├── pawpal_system.py   # All backend classes (Owner, Pet, Task, Scheduler, enums)
├── app.py             # Streamlit UI — wired to pawpal_system.py
├── main.py            # Terminal demo / algorithmic test ground
├── uml_final.md       # Final Mermaid.js class diagram
├── diagram.md         # Phase 1 initial UML (kept for comparison)
├── reflection.md      # Project reflection
├── tests/
│   └── test_pawpal.py # 23-test automated suite (pytest)
└── README.md
```

---

## Getting Started

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
python3 -m streamlit run app.py
```

### Run the terminal demo

```bash
python3 main.py
```

---

## Testing PawPal+

### Run the tests

```bash
python3 -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The suite contains **23 tests** across six behavioral categories:

| Category | Tests | What is verified |
|---|---|---|
| Task completion | 2 | `complete()` flips status; `reschedule()` resets date and reopens task |
| Sorting | 3 | Chronological order after out-of-order insertion; midnight (00:00) sorts first; original list not mutated |
| Recurrence | 5 | Daily → +1 day; Weekly → +7 days; ONCE → `None` with no new task; new task appended; invalid ID safe |
| Conflict detection | 6 | Same-pet flagged; outside window ignored; boundary inclusive; cross-pet flagged by default; `same_pet_only` respected; empty scheduler safe |
| Filtering | 4 | Pending-only and completed-only; named-pet returns correct subset; unknown name returns empty list |
| Owner / pet relationship | 3 | Task count increases on add; `get_tasks_for_owner` excludes other owners; `remove_pet` reduces count |

### Confidence level

**High** for core scheduling logic. All critical paths — recurring task generation, conflict detection boundaries, sort stability, and owner isolation — are covered by explicit assertions. Edge cases include midnight times, the exact conflict-window boundary, ONCE tasks, and cross-owner data separation.

Areas for future testing:
- `expand_recurring()` across month/year boundaries
- `generate_schedule()` with an empty task list
- Full Streamlit UI integration (requires `streamlit.testing`)
