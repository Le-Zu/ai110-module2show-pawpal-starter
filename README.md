# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

PawPal+ goes beyond a simple task list with four intelligent scheduling features built into `Scheduler`:

| Feature | Method | What it does |
|---|---|---|
| **Sort by time** | `sort_tasks_by_time(tasks)` | Orders any task list chronologically using the `HH:MM` time string as a sort key, so the day always reads top-to-bottom regardless of insertion order. |
| **Filter tasks** | `filter_by_status(completed)` / `filter_by_pet_name(name, owner)` | Narrows the task list to pending or completed items, or to a single pet by name (case-insensitive). Useful for focused daily views. |
| **Auto-recurring tasks** | `mark_task_complete(task_id)` | Marks a task done and immediately creates the next occurrence using Python's `timedelta` — daily tasks advance by 1 day, weekly by 7 days, monthly by 30. One-time tasks are closed with no follow-up. |
| **Conflict detection** | `detect_conflicts(window_minutes, same_pet_only)` | Scans all unique task pairs with `itertools.combinations` and returns plain-English warning strings for any two tasks scheduled within `window_minutes` of each other. Flags both same-pet and cross-pet overlaps without crashing. |

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
| Sorting | 3 | Chronological order after out-of-order insertion; midnight (00:00) sorts first; original list is not mutated |
| Recurrence | 5 | Daily → +1 day; Weekly → +7 days; ONCE → `None` returned and no new task added; new task is appended to scheduler; invalid ID handled safely |
| Conflict detection | 6 | Same-pet same-time flagged; gap beyond window ignored; boundary (exactly at limit) included; cross-pet flagged by default; cross-pet ignored with `same_pet_only=True`; empty scheduler returns no warnings |
| Filtering | 4 | Pending-only and completed-only filters; named-pet filter returns correct subset; unknown pet name returns empty list |
| Owner / pet relationship | 3 | Task count increases on add; `get_tasks_for_owner` excludes other owners' tasks; `remove_pet` correctly reduces count |

### Confidence level

**High** for core scheduling logic. All critical paths — recurring task generation, conflict detection boundaries, sort stability, and owner isolation — are covered by explicit assertions. Edge cases tested include midnight times, the exact conflict-window boundary, ONCE tasks, and cross-owner data separation.

Areas that would benefit from more testing with additional time:
- `expand_recurring()` across month/year boundaries
- `generate_schedule()` with an empty task list
- `Scheduler.send_reminder()` output capture
- Full Streamlit UI integration (would require `streamlit.testing`)

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
