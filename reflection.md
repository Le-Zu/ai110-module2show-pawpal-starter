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

  Claude Code was used throughout every phase of the project via the **Cursor IDE terminal**, running Claude directly from the command line. This setup made it feel like a pair programmer embedded in the development environment rather than a separate chat tool. AI was used across four distinct modes:

  1. **Design brainstorming** — the initial UML was sketched by prompting Claude to suggest attributes, methods, and relationships for a pet care domain. The output was a starting point, not a final answer.
  2. **Code generation** — class skeletons, dataclass stubs, and method signatures were generated from the UML, then reviewed before keeping.
  3. **Algorithmic implementation** — sorting, filtering, recurring task logic, and conflict detection were built by describing the behavior in plain English and iterating on the output.
  4. **Debugging** — the `st.time_input` bug (time not updating on new tasks) was diagnosed by describing the symptom; Claude identified that `datetime.now()` being called on every Streamlit re-run was resetting the widget's value.

- What kinds of prompts or questions were most helpful?

  The most effective prompts were **specific and role-defining** rather than open-ended. Examples that worked well:
  - *"Review this skeleton for missing relationships or potential logic bottlenecks"* — produced actionable feedback with clear reasoning for each change.
  - *"How would the Scheduler retrieve all tasks from the Owner's pets?"* — framed around a concrete question rather than asking Claude to write everything, which kept architectural control with the developer.

Vague prompts like "build the scheduler" produced too much at once and made it harder to evaluate what was correct. Narrower prompts targeting one method or one decision at a time gave more trustworthy results.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

When Claude generated the initial class skeleton, it included a `Pet.get_tasks(scheduler: Scheduler)` method — a way for a Pet to look up its own tasks by passing in the Scheduler. This was rejected. The problem is that `Pet` is a `@dataclass` (a pure data object) and should have no dependency on the `Scheduler` coordinator. Accepting that suggestion would have created circular coupling: the data layer depending on the logic layer. The method was removed entirely, and task lookup was kept exclusively in `Scheduler.get_tasks_for_pet()`.

A second modification was made to `detect_conflicts()`. Claude's original version returned `list[tuple[Task, Task]]` — raw task pairs. This was changed to return `list[str]` (plain-English warning messages) so the method could be called directly in both the terminal output and the Streamlit UI without extra formatting logic at every call site.

- How did you evaluate or verify what the AI suggested?

Every generated method was verified against two standards: (1) **does it match the UML contract?** — checking that signatures, return types, and side effects were consistent with the design; and (2) **does the test suite pass?** — the 23-test pytest suite served as an objective check. When `detect_conflicts()` was refactored from a manual index loop to `itertools.combinations`, the tests confirmed the behavior was identical before the change was committed.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

The 23-test suite covered six behavioral categories: task completion and rescheduling, sort order correctness (including the midnight edge case), recurrence logic across all frequency types, conflict detection boundaries, status and name-based filtering, and owner-pet data isolation. Each test was written against a specific, observable behavior — not against implementation details — so the tests remain valid even if the internal logic is refactored.

- Why were these tests important?

  The recurring task and conflict detection methods are the most behaviorally complex parts of the system. Without tests, a subtle off-by-one in the timedelta calculation or an indentation error in `detect_conflicts` (which actually occurred during the `itertools.combinations` refactor and silently broke the method) would have been invisible until a user reported a wrong result. The test suite caught the indentation bug immediately on the next run.

**b. Confidence**

- How confident are you that your scheduler works correctly?

  **High confidence** for the core scheduling behaviors covered by the test suite. The boundary tests (midnight sorting, exact conflict window limit, ONCE task returning `None`) give particular confidence that edge cases are handled correctly, not just the happy path.

- What edge cases would you test next if you had more time?

  - `expand_recurring()` across a month-end boundary (e.g., a monthly task on January 31)
  - `mark_task_complete()` called twice on the same task
  - Two owners with pets of the same name — verifying `filter_by_pet_name` isolates correctly by owner
  - Streamlit UI integration tests using `streamlit.testing.v1` to verify the "✓ Done" button triggers `mark_task_complete()` and re-renders the schedule

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

The separation between the data layer (`Pet`, `Task` as dataclasses) and the logic layer (`Scheduler` as a regular class) held up cleanly throughout the entire build. Every feature added in Phase 3 — sorting, filtering, recurring tasks, conflict detection — slotted into `Scheduler` without touching `Pet` or `Task`. That architectural boundary, decided in Phase 1 and defended when AI suggested otherwise (the `Pet.get_tasks()` method), proved its value. The Streamlit UI wiring also worked cleanly because `session_state` was structured around the same objects from the start.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

The `Frequency` enum currently drives both recurrence logic and display labels. A cleaner design would separate those concerns — an enum for the domain value and a separate mapping for UI display strings — so that adding a new frequency (e.g., `BIWEEKLY`) requires changing only one place. The conflict detection window is also currently a fixed parameter; a real app would let the owner configure their preferred buffer time per task type (medication conflicts matter at 15 minutes; grooming conflicts might not matter at 60). lastl,y fully implement a am/pm format for time, rather than the current 24-hour field option.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Using Claude Code in the **Cursor IDE terminal** across separate sessions for each phase taught a concrete lesson about what it means to be a "lead architect" when working with powerful AI tools. Closing Cursor or the terminal at the end of one session and reopening it the next day meant Claude started fresh — no memory of prior decisions. This forced every architectural decision to be recorded in the code itself (docstrings, type annotations, clear method names) and in `reflection.md`, rather than living only in a chat history.

Separate sessions per phase also helped maintain focus. Each session had a single goal — UML, skeleton, implementation, algorithms, testing, UI — which prevented scope creep and made it easier to pick up exactly where the previous session left off, since the codebase itself was the shared context rather than a conversation thread.

The biggest shift was learning that **the developer's job is not to write code — it is to make decisions and verify output.** Claude could generate a working `detect_conflicts()` method in seconds, but it could not know that the return type should be `list[str]` instead of `list[tuple]` without being told why. It could not know that `Pet.get_tasks()` violated the separation-of-concerns principle without the architect enforcing that boundary. Every session, the most important work happened before any code was written: framing the right question, defining the constraints, and deciding what "correct" looked like before asking Claude to produce it.


