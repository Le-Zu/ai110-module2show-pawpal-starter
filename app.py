import streamlit as st
from datetime import datetime, time

from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state — objects live here between every Streamlit re-run
# ---------------------------------------------------------------------------
if "owner"        not in st.session_state: st.session_state.owner        = None
if "scheduler"    not in st.session_state: st.session_state.scheduler    = Scheduler()
if "next_pet_id"  not in st.session_state: st.session_state.next_pet_id  = 1
if "next_task_id" not in st.session_state: st.session_state.next_task_id = 1

ICONS = {
    TaskType.FEEDING:    "🍽",
    TaskType.MEDICATION: "💊",
    TaskType.EXERCISE:   "🐾",
    TaskType.VET_VISIT:  "🏥",
    TaskType.GROOMING:   "✂️",
}

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("A smart pet care planning assistant.")
st.divider()

# ---------------------------------------------------------------------------
# Section 1: Owner Profile
# ---------------------------------------------------------------------------
st.subheader("👤 Owner Profile")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name  = st.text_input("Name",  value=st.session_state.owner.name  if st.session_state.owner else "")
        owner_phone = st.text_input("Phone", value=st.session_state.owner.phone if st.session_state.owner else "")
    with col2:
        owner_email   = st.text_input("Email",   value=st.session_state.owner.email   if st.session_state.owner else "")
        owner_address = st.text_input("Address", value=st.session_state.owner.address if st.session_state.owner else "")
    save_profile = st.form_submit_button("💾 Save Profile")

if save_profile:
    if not owner_name.strip():
        st.warning("Please enter a name before saving.")
    elif st.session_state.owner is None:
        st.session_state.owner = Owner(id=1, name=owner_name, email=owner_email,
                                       phone=owner_phone, address=owner_address)
        st.success(f"Profile created for **{owner_name}**!")
    else:
        st.session_state.owner.update_profile(name=owner_name, email=owner_email,
                                              phone=owner_phone, address=owner_address)
        st.success("Profile updated!")

if st.session_state.owner:
    st.caption(f"Logged in as **{st.session_state.owner.name}** — {st.session_state.owner.email}")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a Pet
# ---------------------------------------------------------------------------
st.subheader("🐶 Pets")

if st.session_state.owner is None:
    st.info("Save your owner profile above before adding pets.")
else:
    with st.form("add_pet_form"):
        col1, col2 = st.columns(2)
        with col1:
            pet_name    = st.text_input("Pet name")
            pet_species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
            pet_breed   = st.text_input("Breed")
        with col2:
            pet_age    = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            pet_weight = st.number_input("Weight (kg)", min_value=0.1, max_value=200.0,
                                         value=5.0, step=0.1)
        add_pet = st.form_submit_button("➕ Add Pet")

    if add_pet:
        if not pet_name.strip():
            st.warning("Please enter a pet name.")
        else:
            st.session_state.owner.add_pet(Pet(
                id=st.session_state.next_pet_id,
                name=pet_name, species=pet_species, breed=pet_breed,
                age=int(pet_age), weight=float(pet_weight),
                owner_id=st.session_state.owner.id,
            ))
            st.session_state.next_pet_id += 1
            st.success(f"**{pet_name}** added!")

    pets = st.session_state.owner.get_pets()
    if pets:
        st.table([
            {"Name": p.name, "Species": p.species, "Breed": p.breed,
             "Age": p.age, "Weight (kg)": p.weight}
            for p in pets
        ])
    else:
        st.caption("No pets added yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Schedule a Task
# ---------------------------------------------------------------------------
st.subheader("📋 Schedule a Task")

owner = st.session_state.owner
pets  = owner.get_pets() if owner else []

if not owner or not pets:
    st.info("Add at least one pet before scheduling tasks.")
else:
    with st.form("add_task_form"):
        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title", value="Morning Feed")
            task_desc  = st.text_input("Notes", value="")
            task_type  = st.selectbox("Type", [t.value.replace("_", " ").title() for t in TaskType])
        with col2:
            pet_options = {p.name: p for p in pets}
            chosen_pet  = st.selectbox("Pet", list(pet_options.keys()))
            task_time   = st.time_input("Time (AM/PM)", value=time(8, 0))
            task_freq   = st.selectbox("Repeats", [f.value.title() for f in Frequency])
        add_task = st.form_submit_button("➕ Add Task")

    if add_task:
        selected_pet  = pet_options[chosen_pet]
        selected_type = TaskType(task_type.lower().replace(" ", "_"))
        selected_freq = Frequency(task_freq.lower())
        due_dt        = datetime.combine(datetime.today(), task_time)

        st.session_state.scheduler.add_task(Task(
            id=st.session_state.next_task_id,
            title=task_title, description=task_desc,
            type=selected_type, due_date=due_dt,
            frequency=selected_freq, pet_id=selected_pet.id,
        ))
        st.session_state.next_task_id += 1
        # AM/PM confirmation message
        st.success(f"**{task_title}** scheduled for {chosen_pet} "
                   f"at {task_time.strftime('%I:%M %p')} ({task_freq.lower()}).")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Today's Schedule  — smart display
# ---------------------------------------------------------------------------
st.subheader("📅 Today's Schedule")

owner     = st.session_state.owner
scheduler = st.session_state.scheduler

if not owner or not owner.get_pets():
    st.info("Add an owner and at least one pet to generate a schedule.")
else:
    pet_map     = {p.id: p for p in owner.get_pets()}
    all_tasks   = scheduler.get_tasks_for_owner(owner)
    today_tasks = [t for t in all_tasks if t.due_date.date() == datetime.today().date()]

    # --- Conflict detection: show warnings BEFORE the schedule ---
    conflicts = scheduler.detect_conflicts(window_minutes=30)
    # Only surface conflicts that involve today's tasks
    today_ids = {t.id for t in today_tasks}
    today_conflicts = [
        w for w in conflicts
        if any(f"'{t.title}'" in w for t in today_tasks)
    ]

    if today_conflicts:
        st.markdown("#### ⚠️ Scheduling Conflicts Detected")
        for warning in today_conflicts:
            # Parse out the task names and times for a pet-owner-friendly message
            st.warning(warning)
        st.caption("Consider rescheduling one of the conflicting tasks above "
                   "to avoid rushing or missing a care window.")
        st.divider()

    # --- Sort using Scheduler.sort_tasks_by_time() ---
    today_sorted = scheduler.sort_tasks_by_time(today_tasks)

    if not today_sorted:
        st.info("No tasks scheduled for today. Add tasks in the section above.")
    else:
        st.markdown(f"**{datetime.today().strftime('%A, %B %d %Y')}** — "
                    f"{len(today_sorted)} task(s)")

        # --- Filter tabs: All / Pending / Completed / By Pet ---
        tab_all, tab_pending, tab_done, tab_pet = st.tabs(
            ["All", "Pending", "Completed", "By Pet"]
        )

        def render_tasks(tasks: list, pet_map: dict, key_prefix: str) -> None:
            """Render a list of tasks as styled cards with a Mark Complete button."""
            if not tasks:
                st.caption("Nothing to show here.")
                return
            for task in tasks:
                pet    = pet_map.get(task.pet_id)
                icon   = ICONS.get(task.type, "•")
                # AM/PM time format throughout
                time_s = task.due_date.strftime("%I:%M %p").lstrip("0")

                if task.is_completed:
                    st.success(
                        f"✅ **{time_s} — {task.title}** | "
                        f"{icon} {pet.name} · {task.type.value.replace('_',' ').title()} · "
                        f"Repeats {task.frequency.value}"
                    )
                else:
                    col_info, col_btn = st.columns([5, 1])
                    with col_info:
                        st.info(
                            f"⬜ **{time_s} — {task.title}** | "
                            f"{icon} {pet.name} · {task.type.value.replace('_',' ').title()} · "
                            f"Repeats {task.frequency.value}"
                            + (f" · _{task.description}_" if task.description else "")
                        )
                    with col_btn:
                        if st.button("✓ Done", key=f"{key_prefix}_{task.id}"):
                            next_task = scheduler.mark_task_complete(task.id)
                            if next_task:
                                next_time = next_task.due_date.strftime("%I:%M %p").lstrip("0")
                                st.success(
                                    f"Done! Next **{task.title}** auto-scheduled "
                                    f"for {next_task.due_date.strftime('%a %b %d')} "
                                    f"at {next_time}."
                                )
                            else:
                                st.success(f"**{task.title}** marked complete.")
                            st.rerun()

        with tab_all:
            render_tasks(today_sorted, pet_map, "all")

        with tab_pending:
            pending = scheduler.sort_tasks_by_time(
                scheduler.filter_by_status(completed=False)
            )
            pending_today = [t for t in pending if t.due_date.date() == datetime.today().date()]
            render_tasks(pending_today, pet_map, "pending")

        with tab_done:
            done = scheduler.sort_tasks_by_time(
                scheduler.filter_by_status(completed=True)
            )
            done_today = [t for t in done if t.due_date.date() == datetime.today().date()]
            render_tasks(done_today, pet_map, "done")

        with tab_pet:
            pet_names = [p.name for p in owner.get_pets()]
            chosen = st.selectbox("Filter by pet", pet_names, key="pet_filter")
            filtered = scheduler.sort_tasks_by_time(
                scheduler.filter_by_pet_name(chosen, owner)
            )
            filtered_today = [t for t in filtered
                              if t.due_date.date() == datetime.today().date()]
            render_tasks(filtered_today, pet_map, "bypet")

        # --- Summary footer ---
        completed_count = sum(t.is_completed for t in today_sorted)
        remaining       = len(today_sorted) - completed_count
        st.divider()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total today",  len(today_sorted))
        col2.metric("Completed",    completed_count)
        col3.metric("Remaining",    remaining)
