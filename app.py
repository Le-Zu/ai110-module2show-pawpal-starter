import streamlit as st
from datetime import datetime

# ---------------------------------------------------------------------------
# Step 1: Import backend classes from pawpal_system.py
# ---------------------------------------------------------------------------
from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Step 2: Application "memory" via st.session_state
#
# Streamlit re-runs the entire script on every interaction.
# We check whether each object already exists in session_state before
# creating it — this keeps data alive across button clicks and form submits.
# Think of st.session_state as a persistent dictionary for this browser tab.
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None          # set when owner profile is saved

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

if "next_pet_id" not in st.session_state:
    st.session_state.next_pet_id = 1       # auto-increment pet IDs

if "next_task_id" not in st.session_state:
    st.session_state.next_task_id = 1      # auto-increment task IDs

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🐾 PawPal+")
st.caption("A pet care planning assistant powered by Python classes.")
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
        # First save — create the Owner object and store it in session_state
        st.session_state.owner = Owner(
            id=1,
            name=owner_name,
            email=owner_email,
            phone=owner_phone,
            address=owner_address,
        )
        st.success(f"Profile created for {owner_name}!")
    else:
        # Already exists — update in place using the Owner method
        st.session_state.owner.update_profile(
            name=owner_name, email=owner_email,
            phone=owner_phone, address=owner_address,
        )
        st.success("Profile updated!")

if st.session_state.owner:
    st.caption(f"Logged in as **{st.session_state.owner.name}** — {st.session_state.owner.email}")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a Pet
# ---------------------------------------------------------------------------

st.subheader("🐶 Add a Pet")

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
            pet_age     = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            pet_weight  = st.number_input("Weight (kg)", min_value=0.1, max_value=200.0, value=5.0, step=0.1)

        add_pet = st.form_submit_button("➕ Add Pet")

    # Step 3: Wire the form submit to owner.add_pet()
    if add_pet:
        if not pet_name.strip():
            st.warning("Please enter a pet name.")
        else:
            new_pet = Pet(
                id=st.session_state.next_pet_id,
                name=pet_name,
                species=pet_species,
                breed=pet_breed,
                age=int(pet_age),
                weight=float(pet_weight),
                owner_id=st.session_state.owner.id,
            )
            st.session_state.owner.add_pet(new_pet)   # Owner method handles the list
            st.session_state.next_pet_id += 1
            st.success(f"{pet_name} added!")

    # Show current pets
    pets = st.session_state.owner.get_pets()
    if pets:
        st.markdown("**Your pets:**")
        for pet in pets:
            st.markdown(f"- {pet.get_info()}")
    else:
        st.caption("No pets added yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Schedule a Task
# ---------------------------------------------------------------------------

st.subheader("📋 Schedule a Task")

owner    = st.session_state.owner
pets     = owner.get_pets() if owner else []

if not owner or not pets:
    st.info("Add at least one pet before scheduling tasks.")
else:
    with st.form("add_task_form"):
        col1, col2 = st.columns(2)
        with col1:
            task_title  = st.text_input("Task title", value="Morning Feed")
            task_desc   = st.text_input("Notes", value="")
            task_type   = st.selectbox("Type", [t.value.replace("_", " ").title() for t in TaskType])
        with col2:
            pet_options = {p.name: p for p in pets}
            chosen_pet  = st.selectbox("Pet", list(pet_options.keys()))
            task_time   = st.time_input("Time", value=datetime.now().replace(hour=8, minute=0).time())
            task_freq   = st.selectbox("Frequency", [f.value.title() for f in Frequency])

        add_task = st.form_submit_button("➕ Add Task")

    # Step 3: Wire the form submit to scheduler.add_task()
    if add_task:
        selected_pet  = pet_options[chosen_pet]
        selected_type = TaskType(task_type.lower().replace(" ", "_"))
        selected_freq = Frequency(task_freq.lower())
        due_dt        = datetime.combine(datetime.today(), task_time)

        new_task = Task(
            id=st.session_state.next_task_id,
            title=task_title,
            description=task_desc,
            type=selected_type,
            due_date=due_dt,
            frequency=selected_freq,
            pet_id=selected_pet.id,
        )
        st.session_state.scheduler.add_task(new_task)   # Scheduler method handles the list
        st.session_state.next_task_id += 1
        st.success(f"Task '{task_title}' scheduled for {chosen_pet} at {task_time.strftime('%I:%M %p')}!")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate Schedule
# ---------------------------------------------------------------------------

st.subheader("📅 Today's Schedule")

if st.button("🗓 Generate Schedule"):
    owner     = st.session_state.owner
    scheduler = st.session_state.scheduler

    if not owner or not owner.get_pets():
        st.warning("Add an owner and at least one pet first.")
    else:
        # Step 3: Wire to scheduler.get_tasks_for_owner() — the bridge method
        # Owner provides pet IDs → Scheduler filters its task list by those IDs
        all_tasks = scheduler.get_tasks_for_owner(owner)
        today_tasks = [t for t in all_tasks if t.due_date.date() == datetime.today().date()]
        today_tasks.sort(key=lambda t: t.due_date)

        pet_map = {p.id: p for p in owner.get_pets()}

        ICONS = {
            TaskType.FEEDING:    "🍽",
            TaskType.MEDICATION: "💊",
            TaskType.EXERCISE:   "🐾",
            TaskType.VET_VISIT:  "🏥",
            TaskType.GROOMING:   "✂️",
        }

        if not today_tasks:
            st.info("No tasks scheduled for today.")
        else:
            st.markdown(f"### {datetime.today().strftime('%A, %B %d %Y')}")
            for task in today_tasks:
                pet    = pet_map.get(task.pet_id)
                icon   = ICONS.get(task.type, "•")
                time   = task.due_date.strftime("%I:%M %p")
                status = "✅" if task.is_completed else "⬜"

                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.markdown(f"### {icon}")
                    with col2:
                        st.markdown(f"**{time} — {task.title}** {status}")
                        st.caption(f"{pet.name} ({pet.species})  ·  {task.type.value.replace('_',' ').title()}  ·  Repeats {task.frequency.value}  ·  {task.description}")
                st.divider()

            st.caption(f"{len(today_tasks)} task(s) · {sum(t.is_completed for t in today_tasks)} completed")
