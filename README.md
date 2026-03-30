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
