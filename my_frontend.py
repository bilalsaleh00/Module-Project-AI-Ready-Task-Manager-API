import streamlit as st
import requests

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Task Manager",
    page_icon="✅",
    layout="wide"
)

# -------------------------
# Session State
# -------------------------

if "token" not in st.session_state:
    st.session_state["token"] = None

if "username" not in st.session_state:
    st.session_state["username"] = None


# -------------------------
# API Helper Functions
# -------------------------

def auth_headers():
    return {
        "Authorization": f"Bearer {st.session_state['token']}"
    }


def get_current_user():
    try:
        response = requests.get(
            f"{API}/auth/me",
            headers=auth_headers()
        )

        if response.status_code == 401:
            return "unauthorized"

        if response.ok:
            return response.json()

        return None

    except requests.exceptions.ConnectionError:
        return "connection_error"


def get_tasks():
    try:
        response = requests.get(
            f"{API}/tasks/",
            headers=auth_headers()
        )

        if response.status_code == 401:
            return "unauthorized"

        if response.ok:
            return response.json()

        return None

    except requests.exceptions.ConnectionError:
        return "connection_error"


def create_task(title, description=""):
    try:
        response = requests.post(
            f"{API}/tasks/",
            headers=auth_headers(),
            json={
                "title": title,
                "description": description,
                "completed": False
            }
        )

        if response.status_code == 401:
            return "unauthorized"

        if response.ok:
            return response.json()

        return None

    except requests.exceptions.ConnectionError:
        return "connection_error"


def update_task(task_id, completed):
    try:
        response = requests.patch(
            f"{API}/tasks/{task_id}",
            headers=auth_headers(),
            json={
                "completed": completed
            }
        )

        if response.status_code == 401:
            return "unauthorized"

        return response.ok

    except requests.exceptions.ConnectionError:
        return "connection_error"


# -------------------------
# Auth Gate
# -------------------------

if st.session_state["token"] is None:

    st.title("🔐 Task Manager Login")

    with st.form("login_form"):

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Login"
        )

        if submitted:

            try:
                response = requests.post(
                    f"{API}/auth/token",
                    data={
                        "username": username,
                        "password": password
                    }
                )

                if response.status_code == 200:

                    data = response.json()

                    st.session_state["token"] = data[
                        "access_token"
                    ]

                    st.session_state["username"] = username

                    st.rerun()

                else:
                    st.error(
                        "Invalid username or password."
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Cannot connect to the API. "
                    "Make sure FastAPI is running."
                )

    st.stop()


# -------------------------
# Get Current User
# -------------------------

current_user = get_current_user()

if current_user == "connection_error":
    st.error(
        "❌ Cannot connect to the API. "
        "Make sure FastAPI is running."
    )
    st.stop()

if current_user == "unauthorized":
    st.warning(
        "Your session expired. Please log in again."
    )

    st.session_state["token"] = None
    st.session_state["username"] = None

    st.rerun()

if current_user:

    st.session_state["username"] = current_user.get(
        "username",
        st.session_state["username"]
    )


# -------------------------
# Sidebar
# -------------------------

with st.sidebar:

    st.title("Account")

    st.write(
        f"Logged in as **{st.session_state['username']}**"
    )

    if st.button("Logout"):

        st.session_state["token"] = None
        st.session_state["username"] = None

        st.rerun()


# -------------------------
# Load Tasks
# -------------------------

tasks = get_tasks()

if tasks == "connection_error":

    st.error(
        "❌ Cannot connect to the API. "
        "Is the backend running?"
    )

    st.stop()


if tasks == "unauthorized":

    st.warning(
        "Session expired. Please log in again."
    )

    st.session_state["token"] = None
    st.session_state["username"] = None

    st.rerun()


if tasks is None:

    st.error(
        "Failed to load tasks."
    )

    st.stop()


# -------------------------
# Dashboard
# -------------------------

st.title("✅ Task Manager")

total_tasks = len(tasks)

completed_tasks = sum(
    1 for task in tasks
    if task["completed"]
)

pending_tasks = (
    total_tasks - completed_tasks
)


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Tasks",
        total_tasks
    )

with col2:
    st.metric(
        "Completed",
        completed_tasks
    )

with col3:
    st.metric(
        "Pending",
        pending_tasks
    )


st.divider()


# -------------------------
# Add Task Form
# -------------------------

st.subheader("Add New Task")

with st.form(
    "add_task_form",
    clear_on_submit=True
):

    new_title = st.text_input(
        "Task Title"
    )

    new_description = st.text_area(
        "Description"
    )

    add_task = st.form_submit_button(
        "➕ Add Task"
    )

    if add_task:

        if not new_title.strip():

            st.warning(
                "Please enter a task title."
            )

        else:

            result = create_task(
                new_title.strip(),
                new_description.strip()
            )

            if result == "connection_error":

                st.error(
                    "Cannot connect to API."
                )

            elif result == "unauthorized":

                st.session_state["token"] = None
                st.session_state["username"] = None
                st.rerun()

            elif result:

                st.success(
                    "Task added successfully!"
                )

                st.rerun()

            else:

                st.error(
                    "Failed to create task."
                )


st.divider()


# -------------------------
# Task List
# -------------------------

st.subheader("Your Tasks")

if not tasks:

    st.info(
        "You don't have any tasks yet."
    )

else:

    for task in tasks:

        col_text, col_button = st.columns(
            [4, 1]
        )

        with col_text:

            if task["completed"]:

                st.write(
                    f"✅ **{task['title']}**"
                )

            else:

                st.write(
                    f"⬜ **{task['title']}**"
                )

            if task.get("description"):

                st.caption(
                    task["description"]
                )

        with col_button:

            if task["completed"]:
                button_label = "Undo"
            else:
                button_label = "Complete"

            if st.button(
                button_label,
                key=f"task_{task['id']}"
            ):

                result = update_task(
                    task["id"],
                    not task["completed"]
                )

                if result == "connection_error":

                    st.error(
                        "Cannot connect to API."
                    )

                elif result == "unauthorized":

                    st.session_state["token"] = None
                    st.session_state["username"] = None

                    st.rerun()

                elif result:

                    st.rerun()

                else:

                    st.error(
                        "Failed to update task."
                    )

        st.divider()