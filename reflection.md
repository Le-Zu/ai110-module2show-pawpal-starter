# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The initial UML design used four classes connected in a simple hierarchy: Owner → Pet → Task, with a Scheduler sitting alongside to manage task execution. The diagram focused on keeping each class responsible for its own data and exposing clean methods for interacting with that data. Owner, pet, task have primary keys of int type id. Pet, scheduler, task have foreign keys of ownerId, tasks, petID. Primary and foreign keys allow for the non-complex relationsships (like "Owner has Pets").

- What classes did you include, and what responsibilities did you assign to each?

  - **Owner** — represents the person using the app. Holds contact information (name, email, phone, address) and is responsible for managing their list of pets via `addPet()`, `removePet()`, and `getPets()`.
  - **Pet** — represents an individual animal. Stores identifying and health-related attributes (species, breed, age, weight) and links back to its owner via `ownerId`. Responsible for providing its own info and returning its associated tasks via `getTasks()`.
  - **Task** — represents a single care action assigned to a pet (e.g., feeding, medication, grooming, vet visit, exercise). Holds scheduling data (dueDate, frequency) and completion state. Responsible for marking itself complete via `complete()` and rescheduling via `reschedule()`.
  - **Scheduler** — central coordinator that manages all tasks across all pets. Responsible for adding/removing tasks, querying tasks by pet or date, sending reminders, and generating a full schedule. Separated from Owner and Pet so scheduling logic is not scattered across multiple classes.

**b. Design changes**

- Did your design change during implementation?

One notable change occurred when translating the UML into Python code. Then, when asking Claude Code AI for feedback

- If yes, describe at least one change and why you made it.

  In the UML diagram, `Owner` and `Scheduler` were designed as similar-level classes. During implementation, `Pet` and `Task` were converted to Python `@dataclass` objects while `Owner` and `Scheduler` remained regular classes. This distinction was made because `Pet` and `Task` are primarily data containers — they benefit from the auto-generated `__init__` and `__repr__` that dataclasses provide. `Owner` and `Scheduler`, by contrast, manage internal mutable state (`_pets`, `_tasks`) and have more complex behavior, making a regular class with explicit `__init__` a cleaner fit. A `TaskType` enum was also added (not in the original sketch) to replace a plain string field, making task categories explicit and preventing invalid values.

  **Claude Code AI feedback:**

  After reviewing the generated skeleton, four issues were identified and corrected:

  1. **Removed `Pet.get_tasks(scheduler)` method.** A dataclass (pure data object) should not depend on the `Scheduler` coordinator. Having `Pet` call into `Scheduler` creates circular coupling and means `Pet` can't be used independently. Task lookup was removed from `Pet` entirely — it belongs only in `Scheduler` via `get_tasks_for_pet()`.

  2. **Replaced `frequency: str` with a `Frequency` enum.** A plain string for frequency (e.g. `"daily"`, `"weekly"`) is fragile — any typo produces a silent bug. A `Frequency` enum (ONCE, DAILY, WEEKLY, MONTHLY) makes valid values explicit, matching the same reasoning used for `TaskType`.

  3. **Added `get_tasks_for_owner(owner)` to `Scheduler`.** The original design had no way to retrieve all tasks across all of an owner's pets — a natural query for a dashboard or summary view. This method closes the missing relationship between `Owner` and `Scheduler`.

  4. **Typed `generate_schedule()` return as `dict[int, list[Task]]`.** A bare `dict` return type gives callers no information about the structure. Typing it as `dict[int, list[Task]]` (pet_id → tasks) makes the contract explicit and catches misuse earlier.

  5. **Removed unused imports** (`field` from dataclasses, `Optional` from typing). Neither was referenced anywhere in the skeleton.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

  The scheduler considers three constraints ranked by priority:
  1. **Time** (`due_date`) — the primary constraint. All sorting, filtering, conflict detection, and recurring projection are anchored to the task's datetime. Missing a time window for medication or feeding has direct health consequences.
  2. **Task type** (`TaskType` enum) — an implicit urgency signal. MEDICATION and FEEDING are inherently more time-critical than GROOMING or EXERCISE. This acts as a tiebreaker when tasks share a due time.
  3. **Frequency** (`Frequency` enum) — determines recurrence cadence (daily, weekly, monthly, once). It drives `mark_task_complete()` auto-scheduling and `expand_recurring()` projection but does not affect ordering within a day.

- How did you decide which constraints mattered most?

  Time was ranked first because the app's core job is answering "what needs to happen and when." Task type was ranked second because not all same-time conflicts are equally urgent — two grooming tasks overlapping matters less than a medication and a feeding overlapping. Frequency was ranked last because it governs future scheduling, not the urgency of what's happening right now.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

  `detect_conflicts()` compares every unique pair of tasks using `itertools.combinations(tasks, 2)` — an O(n²) algorithm. A more efficient approach would sort tasks by time first and only compare adjacent pairs, reducing the complexity to O(n log n). This version was considered and rejected.

- Why is that tradeoff reasonable for this scenario?

  The sorted-adjacent approach has a correctness flaw in this context: if task A is at 9:00, task B at 9:20, and task C at 9:40, A and C are 40 minutes apart (no conflict), but B sits between them. An adjacent-only scan would never compare A and C directly. At pet-care scale — typically 5–20 tasks per day — the O(n²) full-pair comparison is negligible in cost and catches every conflict correctly. Optimizing to O(n log n) here would add complexity without a measurable benefit.

  **Algorithm review note:** During this phase, `detect_conflicts()` was also refactored from a manual double `for i / for j` index loop to `for a, b in combinations(self._tasks, 2)`. The index version worked correctly but required the reader to infer that `j = i + 1` means "unique pairs." `combinations` states that intent directly in the function name. Both versions are O(n²) — the change was purely for readability, not performance.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
