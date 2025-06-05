import streamlit as st
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import IntegrityError
import pandas as pd
import sqlite3
from datetime import date, datetime, time
import os
from PIL import Image
from io import BytesIO
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from math import floor, ceil
import json
import requests
import calendar
import streamlit.components.v1 as components
from typing import Optional, List, Dict, Any

# --- Configuration and Constants ---
st.set_page_config(page_title="PMU Tracker", layout="wide")

DATABASE_URL = "sqlite:///pmu.db"
KANBAN_DB = "kanban.db"
CHAT_DB = "chat.db"
API_BASE_URL = "https://api.example.com" # Replace with your actual base API URL if deployed

Base = declarative_base()

# --- Database Setup (SQLAlchemy) ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Integration (Placeholder) ---
def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API GET Error on '{endpoint}': {e}")
        return None

def api_post(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API POST Error on '{endpoint}': {e}")
        return None

def api_put(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        response = requests.put(f"{API_BASE_URL}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API PUT Error on '{endpoint}': {e}")
        return None

# --- SQLAlchemy Models ---
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    workstreams = relationship("WorkStream", back_populates="employee")
    targets = relationship("Target", back_populates="employee")
    programs = relationship("Program", back_populates="employee")
    schedules = relationship("Schedule", back_populates="employee")
    workplans = relationship("WorkPlan", back_populates="supervisor")
    field_teams = relationship("FieldTeam", back_populates="pmu")
    meetings = relationship("Meeting", back_populates="employee")
    calendar_tasks = relationship("CalendarTask", back_populates="employee")

class WorkStream(Base):
    __tablename__ = "workstreams"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="workstreams")
    workplans = relationship("WorkPlan", back_populates="workstream")

class WorkPlan(Base):
    __tablename__ = "workplans"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    details = Column(Text)
    deadline = Column(Date)
    status = Column(String, default="Not Started")
    workstream_id = Column(Integer, ForeignKey("workstreams.id"))
    workstream = relationship("WorkStream", back_populates="workplans")
    supervisor_id = Column(Integer, ForeignKey("employees.id"))
    supervisor = relationship("Employee", back_populates="workplans")

class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    deadline = Column(Date)
    status = Column(String, default="Not Started")
    employee_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="targets")

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(Text)
    status = Column(String, default="Active")
    employee_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="programs")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date)
    start_time = Column(String)
    end_time = Column(String)
    employee = relationship("Employee", back_populates="schedules")
    gmeet_link = Column(String, nullable=True)

class FieldTeam(Base):
    __tablename__ = "field_teams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    pmu_id = Column(Integer, ForeignKey("employees.id"))
    pmu = relationship("Employee", back_populates="field_teams")
    tasks = relationship("Task", back_populates="field_team")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    deadline = Column(Date)
    status = Column(String, default="Not Started")
    field_team_id = Column(Integer, ForeignKey("field_teams.id"))
    field_team = relationship("FieldTeam", back_populates="tasks")

class FarmerData(Base):
    __tablename__ = "farmer_data"
    id = Column(Integer, primary_key=True)
    farmer_name = Column(String)
    number_of_cows = Column(Integer)
    yield_per_cow = Column(Float)
    date = Column(Date)

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date)
    start_time = Column(String)
    end_time = Column(String)
    description = Column(String)
    employee = relationship("Employee", back_populates="meetings")

class CalendarTask(Base):
    __tablename__ = "calendar_tasks"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date)
    task = Column(Text)
    employee = relationship("Employee", back_populates="calendar_tasks")

# --- Preloading Data ---
preloaded_users = [
    ("Somanchi", "rsomanchi@tns.org", "password1"),
    ("Ranu", "rladdha@tns.org", "password2"),
    ("Pari", "paris@tns.org", "password3"),
    ("Muskan", "mkaushal@tns.org", "password4"),
    ("Rupesh", "rmukherjee@tns.org", "password5"),
    ("Shifali", "shifalis@tns.org", "password6"),
    ("Aditya", "ayuvaraj@tns.org", "password7"),
    ("Bhavya Kharoo", "bkharoo@tns.org", "password8"),
    ("Kriti Suneha", "ksuneha@tns.org", "password9"),
    ("Sandeep GS", "gssandeep@tns.org", "password10"),
    ("Nikhitha VK", "vknikhitha@tns.org", "password11"),
]

initial_programs = ["Water Program", "Education Program", "Ksheersagar 2.0", "SAKSHAM"]

def preload_data():
    with SessionLocal() as db:
        for name, email, password in preloaded_users:
            if not db.query(Employee).filter_by(email=email).first():
                try:
                    db.add(Employee(name=name, email=email, password=password))
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    st.warning(f"User {email} already exists.")

        first_employee = db.query(Employee).first()
        if first_employee:
            for program_name in initial_programs:
                if not db.query(Program).filter_by(name=program_name).first():
                    try:
                        db.add(
                            Program(
                                name=program_name,
                                description=f"Description for {program_name}",
                                employee_id=first_employee.id,
                            )
                        )
                        db.commit()
                    except IntegrityError:
                        db.rollback()
                        st.warning(f"Program '{program_name}' already exists.")
        else:
            st.error("No employees found to associate programs with. Please add users first.")

def create_and_preload_db():
    Base.metadata.create_all(bind=engine)
    preload_data()

create_and_preload_db()

# --- Custom CSS ---
def apply_custom_css():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,wght@0,200;0,300;0,400;0,500;0,600;0,700;0,800;1,200;1,300;1,400;1,500;1,600;1,700;1,800&display=swap');

            body {
                background-image: url("https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/2.png");
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
                background-position: center;
                font-family: 'Newsreader', serif;
            }

            .stApp {
                background-color: rgba(255, 255, 255, 0.1);
                font-family: 'Newsreader', serif;
            }

            section[data-testid="stSidebar"] > div:first-child {
                position: relative;
                padding: 20px;
                border-radius: 0 10px 10px 0;
                background-image: url("https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/Untitled%20design%20(1).png");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                color: #FFFFFF;
                z-index: 1;
                font-family: 'Newsreader', serif;
            }

            section[data-testid="stSidebar"] > div:first-child::before {
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 0 10px 10px 0;
                z-index: -1;
            }

            h1, h2, h3, h4, h5, h6, .stRadio label {
                color: #ffffff;
                font-family: 'Newsreader', serif;
            }

            .streamlit-expanderHeader {
                background-color: #dceefb;
                border: 1px solid #cce0ff;
                border-radius: 10px;
                font-family: 'Newsreader', serif;
            }

            .stButton > button {
                background-color: #0077b6;
                color: white;
                border-radius: 8px;
                padding: 0.5em 1em;
                font-family: 'Newsreader', serif;
            }

            .stButton > button:hover {
                background-color: #0096c7;
            }

            .stDataFrame {
                background-color: #ffffff;
                border: 5px solid #ccc;
                font-family: 'Newsreader', serif;
            }

            .stTabs [role="tab"] {
                background-color: #edf6ff;
                padding: 10px;
                border-radius: 10px 10px 0 0;
                margin-right: 5px;
                border: 1px solid #b6d4fe;
                font-family: 'Newsreader', serif;
            }

            .stTabs [role="tab"][aria-selected="true"] {
                background-color: #0077b6;
                color: white;
                font-family: 'Newsreader', serif;
            }

            /* Custom CSS for the pop-up modal */
            .popup-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }

            .popup-content {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                max-width: 90%;
                max-height: 90%;
                overflow: auto;
                position: relative;
            }

            .popup-close-button {
                position: absolute;
                top: 10px;
                right: 10px;
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #333;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_custom_css()

# --- Helper Functions for UI Components ---

def display_notice():
    st.markdown(
        """
        <style>
            .notice {
                background-color: rgba(255, 255, 255, 0.3);
                padding: 20px;
                border-radius: 15px;
                font-family: 'Newsreader', serif;
                margin-bottom: 20px;
            }
            .notice h2 {
                text-align: center;
                color: #020431;
                margin-bottom: 15px;
            }
            .notice p, .notice ul {
                color: #333;
                line-height: 1.6;
            }
            .notice ul {
                padding-left: 20px;
            }
            .notice li {
                margin-bottom: 5px;
            }
        </style>
        <div class="notice">
            <h2>NOTICE & PROTOCOL FOR WORKSTREAM TRACKING PLATFORM USAGE</h2>
            <p>Welcome to the PMU Tracker – your central hub for tracking progress, setting targets, and streamlining team alignment.</p>
            <p>To ensure effective and consistent usage, please review and adhere to the following protocol:</p>
            <h3>Platform Purpose</h3>
            <p>This platform serves as a shared space for all team members to:</p>
            <ul>
                <li>Submit and monitor their personal and team workplans</li>
                <li>Record progress updates</li>
                <li>Set and review short-term targets</li>
                <li>Access meeting links related to performance check-ins and planning</li>
            </ul>
            <h3>Submission Window</h3>
            <p>Each reporting cycle will open for 5 calendar days.</p>
            <p>All entries (targets, updates, plans) must be completed within this timeframe.</p>
            <p>Post-deadline, the platform will be locked for submissions, allowing only view access.</p>
            <h3>Access Protocol</h3>
            <p>Accessible to all relevant staff during the open window</p>
            <p>Platform access will be managed and monitored for compliance and integrity</p>
            <h3>Meeting Coordination</h3>
            <p>Supervisors will upload relevant meeting links and schedules directly into the platform</p>
            <p>Individuals are expected to join these sessions as per the calendar updates</p>
            <h3>Communication Guidelines</h3>
            <p>Any technical issues or submission challenges should be reported within the window</p>
            <p>Use official channels for queries to ensure swift response</p>
            <p>We appreciate your cooperation in making this system a success. Let’s keep progress transparent, teamwork tight, and targets in sight.</p>
            <p>For questions or support, please contact rsomanchi@tns.org.</p>
            <p>Let the tracking begin – elegantly, efficiently, and with a touch of excellence.</p>
            <p>On behalf of the Coordination Team</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def sidebar_navigation() -> str:
    st.sidebar.title("Navigation")
    menu_options = {
        "Dashboard": "dashboard",
        "Manage Programs": "manage_programs",
        "Reports": "reports",
        "Employee Scheduling": "scheduling",
        "Field Team Management": "field_team_management",
        "Live Dashboard": "live_dashboard",
        "SAKSHAM Dashboard": "saksham_dashboard",
        "Training": "training",
        "Settings": "settings",
        "Google Drive (Placeholder)": "google_drive",
        "Team Chat": "team_chat",
        "Email (Placeholder)": "email",
        "Calendar": "calendar_view",
        "Monthly Meeting": "monthly_meeting",
        "Logout": "logout",
    }
    selection = st.sidebar.radio("Go to", list(menu_options.keys()))
    return menu_options[selection]

# --- Pop-up for Organizational Chart ---
def show_org_chart_popup():
    image_url = "https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/Company%20Organizational%20Chart%20(4).jpg"
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        img_bytes = BytesIO(response.content)
        img = Image.open(img_bytes)

        # Using st.dialog (Streamlit 1.28+) for a more native pop-up
        if 'show_org_chart' not in st.session_state:
            st.session_state.show_org_chart = False

        if st.button("View Organizational Chart 🏢"):
            st.session_state.show_org_chart = True

        if st.session_state.show_org_chart:
            with st.container(border=True): # Use a container to simulate a modal
                st.subheader("Organizational Chart")
                st.image(img, use_container_width=True)
                if st.button("Close Chart"):
                    st.session_state.show_org_chart = False
                    st.rerun() # Rerun to close the pop-up
                st.markdown("---") # Add a separator inside the container for better visual

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load organizational chart image: {e}. Please check the URL or your internet connection.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

# --- Dashboard UI ---
def dashboard(user: Employee):
    st.markdown(
        "<h1 style='text-align:center; color:#020431;'>Project Management Dashboard</h1>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("### Logged in as")
    st.sidebar.success(user.name)
    if st.sidebar.button("🔓 Logout", key="logout_button_sidebar"):
        st.session_state.user = None
        st.rerun()

    # Place the "Meet the Team" section directly on the Dashboard
    st.markdown("---")
    st.title("🤝 Meet the Team")
    st.write("Get to know the individuals driving our success.")

    team_members = [
        {"name": "Rupesh Mukherjee", "role": "Associate Practice Leader", "photo": "https://drive.google.com/file/d/1HDqOqs5rnFDcPXr0dy0p2NBpw7jgxt-I/view?usp=drive_link"},
        {"name": "Kuntal Dutta", "role": "Sr. Manager - Field", "photo": "https://drive.google.com/file/d/1msWObOwQjuZfa-LBV9cCfI9Y096Y7RWQ/view?usp=drive_link"},
        {"name": "Shifali Sharma", "role": "Manager - Field", "photo": "https://drive.google.com/file/d/1oV23e3yA3J9AYWd-_hLqZaDi8iMczzzV/view?usp=drive_link"},
        {"name": "Jhelum Chowdhury", "role": "Consultant", "photo": "https://drive.google.com/file/d/1s-KHiHPDRTGhg8k17KK1dBo2cOsUe-v1/view?usp=drive_link"},
        {"name": "Dr. Ramakrishna", "role": "Advisor", "photo": "https://via.placeholder.com/80?text=DR"},
        {"name": "Sachin Wadpalliwar", "role": "Manager - Field", "photo": "https://drive.google.com/uc?id=1JcxGANNNz-cuNiDe5CUKh9rTWZSiPhMM"},
        {"name": "Aditya Yuvaraj", "role": "Associate - Field", "photo": "https://drive.google.com/file/d/1Kv0GjnUbx9PKw8g9hUZAccXA6RTadDAG/view?usp=drive_link"},
        {"name": "Aniket Govekar", "role": "Assistant Manager - Field", "photo": "https://via.placeholder.com/80?text=AG"},
        {"name": "Bhushan Sananse", "role": "Assistant Manager - Field", "photo": "https://drive.google.com/uc?id=1ofRfjXogxGL5hzK79ZBbx_AuUuZl8Iuu"},
        {"name": "Nilesh Dhanwate", "role": "Senior Executive - Field", "photo": "https://drive.google.com/uc?id=1XH1iEJKsbcay5dugj2Eub_fOsqXHQhfW"},
        {"name": "Subrat Ghoshal", "role": "Senior Executive - Field", "photo": "https://via.placeholder.com/80?text=SG"},
        {"name": "K Balaji", "role": "Senior Associate - Field", "photo": "https://drive.google.com/file/d/1pxOvDZQk4gY2hO-kfuwIEfGMg0iQzMFK/view?usp=drive_link"},
        {"name": "Guru Mohan Kakanuru Reddy", "role": "Assistant Manager - Field", "photo": "https://drive.google.com/uc?id=1E1-m1V6xnIhTTn69ZB9Xy4hiJmsTUTwX"},
        {"name": "Ajay Vaghela", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80?text=AV"},
        {"name": "Happy Vaishnavi", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80?text=HV"},
        {"name": "Nikhita VK", "role": "Senior Associate - Field", "photo": "https://drive.google.com/file/d/1_hR07Cd45EifHIUcCoE_cuIUbJVuCa81/view?usp=drive_link"},
        {"name": "Bhavya Kharoo", "role": "Senior Associate - Field", "photo": "https://drive.google.com/uc?id=19gP4zdJMW6SMnrt0IZRcXw2LwUMeaxEn"},
        {"name": "Kriti Suneha", "role": "Senior Associate - Field", "photo": "https://drive.google.com/file/d/12Jz53BLp0H2LmdDGYwAdnqoS55m68x3p/view?usp=drive_link"},
        {"name": "Ranu Laddha", "role": "Associate - Field", "photo": "https://via.placeholder.com/80?text=RL"},
        {"name": "Pari Sharma", "role": "Associate - Field", "photo": "https://via.placeholder.com/80?text=PS"},
        {"name": "Muskan Kaushal", "role": "Associate - Field", "photo": "https://via.placeholder.com/80?text=MK"},
        {"name": "Ramalakshmi Somanchi", "role": "Associate - Field", "photo": "https://drive.google.com/file/d/1kwsZSKYcHdwonnZpoBI1gMCRCMjqaFbO/view?usp=drive_link"},
        {"name": "Hrushikesh Tilekar", "role": "Associate", "photo": "https://via.placeholder.com/80?text=HT"},
    ]

    # Display team members in a responsive grid
    cols_per_row = 3 # Adjust as needed for screen size
    for i in range(0, len(team_members), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(team_members):
                member = team_members[i + j]
                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"**{member['name']}**")
                        st.markdown(f"*{member['role']}*")
                        try:
                            if "drive.google.com" in member["photo"] and "uc?id=" not in member["photo"]:
                                photo_id = member["photo"].split('/')[-2]
                                display_url = f"https://drive.google.com/uc?id={photo_id}"
                            else:
                                display_url = member["photo"]

                            response = requests.get(display_url, stream=True)
                            response.raise_for_status()
                            image = Image.open(BytesIO(response.content))
                            st.image(image, width=120, caption=member['name'])
                        except requests.exceptions.RequestException:
                            st.warning(f"Could not load image for {member['name']}. Using placeholder.")
                            st.image("https://via.placeholder.com/120?text=No+Photo", width=120)
                        except Exception as e:
                            st.warning(f"Error processing image for {member['name']}: {e}. Using placeholder.")
                            st.image("https://via.placeholder.com/120?text=Error", width=120)
        st.markdown("---") # Separator between rows of team members

    # Call the pop-up function for the organizational chart
    show_org_chart_popup()

    st.markdown("---") # Separator before the dashboard tabs

    # Tabs for different dashboards
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Field Team Dashboard", "PMU Dashboard", "Heritage Dashboard", "Ksheersagar Dashboard"]
    )

    with tab1:
        st.subheader("📊 Field Team Progress")
        st.write("This is where you can display field team progress and metrics.")
        display_todo()

    with tab2:
        pmu_dashboard(user)
        display_kanban()

    with tab3:
        heritage_dashboard()

    with tab4:
        ksheersagar_dashboard()

# --- Kanban Board Functions (SQLite for simplicity) ---
def get_kanban_board() -> Dict[str, List[str]]:
    conn = sqlite3.connect(KANBAN_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kanban (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            task TEXT NOT NULL
        )
    """)
    conn.commit()

    board = {"To Do": [], "In Progress": [], "Done": []}
    cursor.execute("SELECT status, task FROM kanban")
    for status, task in cursor.fetchall():
        if status in board:
            board[status].append(task)
    conn.close()
    return board

def add_kanban_task(status: str, task: str):
    conn = sqlite3.connect(KANBAN_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO kanban (status, task) VALUES (?, ?)", (status, task))
    conn.commit()
    conn.close()

def display_kanban():
    st.subheader("🗂️ Kanban Board")
    board = get_kanban_board()
    cols = st.columns(len(board))
    for i, (col_name, tasks) in enumerate(board.items()):
        with cols[i]:
            st.markdown(f"### {col_name}")
            if tasks:
                for task in tasks:
                    st.success(f"✅ {task}")
            else:
                st.info("No tasks here.")

    with st.form("Add Kanban Task"):
        task = st.text_input("Task Description", max_chars=255)
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        if st.form_submit_button("Add Task"):
            if task:
                add_kanban_task(status, task)
                st.rerun()
            else:
                st.error("Task description cannot be empty.")

# --- To-Do List Functions (Session State for simplicity) ---
def display_todo():
    st.subheader("📝 To-Do List")
    if "todo_list" not in st.session_state:
        st.session_state.todo_list = []

    with st.form("Add To-Do Item"):
        todo_item = st.text_input("Enter a to-do item:", max_chars=255)
        if st.form_submit_button("Add"):
            if todo_item:
                st.session_state.todo_list.append(todo_item)
                st.rerun()
            else:
                st.error("To-do item cannot be empty.")

    if st.session_state.todo_list:
        for i, item in enumerate(st.session_state.todo_list):
            st.write(f"{i+1}. {item}")
        if st.button("Clear All To-Dos"):
            st.session_state.todo_list = []
            st.rerun()
    else:
        st.info("Your to-do list is empty!")

def manage_programs():
    with SessionLocal() as db:
        st.subheader("Manage Programs")

        with st.form("add_program_form"):
            name = st.text_input("Program Name", max_chars=255)
            description = st.text_area("Program Description")
            status = st.selectbox("Program Status", ["Active", "Inactive"])

            if st.form_submit_button("Add Program"):
                if name:
                    try:
                        new_program = Program(
                            name=name,
                            description=description,
                            status=status,
                            employee_id=st.session_state.user.id,
                        )
                        db.add(new_program)
                        db.commit()
                        st.success(f"Program '{name}' added successfully!")
                        st.rerun()
                    except IntegrityError:
                        db.rollback()
                        st.error(f"Program '{name}' already exists.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"An error occurred while adding the program: {e}")
                else:
                    st.error("Program name cannot be empty.")

        st.subheader("Existing Programs")
        programs = db.query(Program).all()
        if programs:
            for program in programs:
                st.markdown(
                    f"**Name**: {program.name} | **Description**: {program.description} | **Status**: {program.status}"
                )
                if st.button(f"Delete {program.name}", key=f"delete_program_{program.id}"):
                    try:
                        db.delete(program)
                        db.commit()
                        st.success(f"Program '{program.name}' deleted.")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error deleting program: {e}")
        else:
            st.info("No programs found.")

def saksham_dashboard():
    st.title("🌿 Plant Population & Seed Requirement Tool")
    st.markdown(
        """<hr style='margin-top: -15px; margin-bottom: 25px;'>""",
        unsafe_allow_html=True,
    )

    with st.container():
        st.header("🗕️ Farmer Survey Entry")
        st.markdown(
            "Fill in the details below to calculate how many seed packets are required for optimal plant population."
        )

        with st.form("survey_form"):
            col0, col1, col2 = st.columns(3)
            farmer_name = col0.text_input("👤 Farmer Name")
            farmer_id = col1.text_input("🆔 Farmer ID")
            state = col2.selectbox("🏝 State", ["Maharashtra", "Gujarat"])

            spacing_unit = st.selectbox("📏 Spacing Unit", ["cm", "m"])
            col3, col4, col5 = st.columns(3)
            row_spacing = col3.number_input(
                "↔️ Row Spacing (between rows)", min_value=0.01, step=0.1
            )
            plant_spacing = col4.number_input(
                "↕️ Plant Spacing (between plants)", min_value=0.01, step=0.1
            )
            land_acres = col5.number_input(
                "🎾 Farm Area (acres)", min_value=0.01, step=0.1
            )

            mortality = st.slider("Mortality %", min_value=0.0, max_value=100.0, value=5.0)

            submitted = st.form_submit_button("🔍 Calculate")

        if submitted and farmer_name and farmer_id:
            st.markdown("---")

            germination_rate_per_acre = {"Maharashtra": 14000, "Gujarat": 7400}
            confidence_interval = 0.70
            seeds_per_packet = 5625
            acre_to_m2 = 4046.86

            if spacing_unit == "cm":
                row_spacing /= 100
                plant_spacing /= 100

            plant_area_m2 = row_spacing * plant_spacing
            plants_per_m2 = 1 / plant_area_m2
            field_area_m2 = land_acres * acre_to_m2
            total_plants = plants_per_m2 * field_area_m2

            target_plants = total_plants * confidence_interval

            required_seeds = target_plants
            required_packets = floor(required_seeds / seeds_per_packet)

            effective_germination = confidence_interval * (1 - mortality / 100)
            expected_plants = total_plants * (effective_germination + mortality / 100)
            gaps = total_plants - expected_plants
            gap_seeds = gaps / effective_germination
            gap_packets = floor(gap_seeds / seeds_per_packet)

            st.markdown(
                "### <span style='font-size: 1.8rem;'>📊 Output Summary</span>",
                unsafe_allow_html=True,
            )
            col6, col7, col8, col9 = st.columns(4)
            col6.metric("🧬 Calculated Capacity", f"{int(total_plants):,} plants")
            col7.metric("🎯 Target Plants", f"{int(target_plants):,} plants")
            col8.metric("🌱 Required Seeds", f"{int(required_seeds):,} seeds")
            col9.metric("📦 Seed Packets Needed", f"{required_packets} packets")

            st.markdown(
                """<hr style='margin-top: 25px;'>""", unsafe_allow_html=True
            )
            st.markdown(
                "### <span style='font-size: 1.8rem;'>📊 Gap Filling Summary</span>",
                unsafe_allow_html=True,
            )
            col10, col11, col12 = st.columns(3)
            col10.metric("❓ Gaps (missing plants)", f"{int(gaps):,}")
            col11.metric("💼 Seeds for Gaps", f"{int(gap_seeds):,} seeds")
            col12.metric("📦 Packets for Gap Filling", f"{gap_packets} packets")

            st.caption(
                "ℹ️ Based on 5625 seeds per 450g packet. Rounded down for field practicality. Gap seeds adjusted for mortality & germination."
            )

        elif submitted:
            st.error("⚠️ Please enter both Farmer Name and Farmer ID to proceed.")

        with SessionLocal() as db:
                    try:
                        new_farmer_data = FarmerData(
                            farmer_name=farmer_name,
                            number_of_cows=0,
                            yield_per_cow=0.0,
                            date=date.today()
                        )
                        db.add(new_farmer_data)
                        db.commit()
                        st.success("Farmer data saved.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error saving farmer data: {e}")

def live_dashboard():
    with SessionLocal() as db:
        st.subheader("📈 Live Monitoring Dashboard")

        farmer_data = db.query(FarmerData).all()
        if not farmer_data:
            st.warning("No farmer data available.")
            return

        df = pd.DataFrame([
            {
                "Farmer Name": farmer.farmer_name,
                "Number of Cows": farmer.number_of_cows,
                "Yield per Cow (L)": farmer.yield_per_cow,
                "Date": farmer.date
            } for farmer in farmer_data
        ])

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values(by='Date', ascending=False)

        total_farmers = df['Farmer Name'].nunique()
        total_cows = df['Number of Cows'].sum()
        total_yield = df['Yield per Cow (L)'].sum()
        average_yield_per_cow = df['Yield per Cow (L)'].mean() if not df.empty else 0

        st.metric("🧮 Total Farmers Recorded", total_farmers)
        st.metric("🐄 Total Cows Recorded", total_cows)
        st.metric("🍼 Total Yield Recorded (L)", f"{total_yield:,.2f}")
        st.metric("📊 Average Yield per Cow (L)", f"{average_yield_per_cow:,.2f}")

        st.subheader("📊 Farmer Data Overview")
        st.dataframe(df, use_container_width=True)

        st.subheader("📈 Data Analytics")

        daily_yield = df.groupby('Date')['Yield per Cow (L)'].sum().reset_index()
        fig_daily_yield = px.line(
            daily_yield,
            x="Date",
            y="Yield per Cow (L)",
            title="Daily Total Yield Trend",
            markers=True
        )
        st.plotly_chart(fig_daily_yield, use_container_width=True)

        fig_yield_dist = px.histogram(
            df,
            x="Yield per Cow (L)",
            nbins=10,
            title="Distribution of Yield per Cow"
        )
        st.plotly_chart(fig_yield_dist, use_container_width=True)

def heritage_dashboard():
    st.subheader("🏛️ Heritage Dashboard")
    st.markdown("### 🌍 Geographic Dashboard")
    components.iframe(
        src="https://datawrapper.dwcdn.net/jjDlA/1/",
        height=600,
        width=800,
        scrolling=True,
    )
    kpi_data = {
        "Metric": ["Milk Received (Lt per day)", "#MCCs", "#DFs", "#HPCs (VLCC)", "Total MCCs",
                   "Routes", "#Heritage Pourers", "# Other farmers(from MCCs)", "Total Active Farmers",
                   "Productivity (in lts per day per farmer)", "SNF (Baseline)%", "Fat (Baseline)%",
                   "Compliance % (with Antibiotics and Aflatoxins)"],
        "Baseline": [33000, 137, 3, 67, 207, 17, 1010, 2268, 3278, 10, 8.1, 4, 50],
        "Target": [45000, 70, 10, 134, 214, 17, 2546, 1050, 3596, 13, 8.1, 4.3, 70],
        "Progress": [15000, 67, 10, 67, 5, 4, 1536, -1218, 3596, 13, 8.15, 0.2, 70],
        "Q1": [5000, 22, 3, 22, 2, 1.0, 512, -406, 1199, 10, 8.15, 4.10, 23],
        "Q2": [5000, 22, 3, 22, 2, 1.0, 512, -406, 1199, 11, 8.2, 4.15, 23],
        "Q3": [5000, 22, 3, 22, 2, 2, 512, -406, 1199, 12, 8.25, 4.20, 23],
        "Q4": [7500, 34, 5, 34, 3, 2, 768, -609, 1798, 13, 8.30, 4.3, 35],
        "Q5": [7500, 34, 5, 34, 3, 2, 768, -609, 1798, 13, 8.30, 4.3, 35],
    }
    kpi_df = pd.DataFrame(kpi_data).set_index("Metric")

    st.subheader("Key Performance Indicators")
    st.dataframe(kpi_df, use_container_width=True)

    kpi_df_T = kpi_df.T.reset_index().rename(columns={'index': 'Period'})
    numeric_cols = [col for col in kpi_df_T.columns if col not in ['Period', '# Other farmers(from MCCs)', 'SNF (Baseline)%', 'Fat (Baseline)%', 'Compliance % (with Antibiotics and Aflatoxins)']]
    kpi_df_long = kpi_df_T.melt(id_vars=['Period'], value_vars=numeric_cols, var_name='KPI', value_name='Value')

    selected_kpi = st.selectbox(
        "Select KPI to visualize",
        kpi_df_long['KPI'].unique(),
        key="heritage_kpi_select"
    )

    fig_selected_kpi = px.line(
        kpi_df_long[kpi_df_long['KPI'] == selected_kpi],
        x="Period",
        y="Value",
        title=f"{selected_kpi} Over Time",
        markers=True
    )
    st.plotly_chart(fig_selected_kpi, use_container_width=True)

    st.markdown("---")
    st.subheader("Farmer Demographics and Impact")

    pie_data = pd.DataFrame(
        {"Category": ["Small", "Medium", "Large"], "Farmers": [6000, 4000, 2450]}
    )
    fig_pie = px.pie(
        pie_data,
        values="Farmers",
        names="Category",
        hole=0.5,
        title="Farmer Size Distribution",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    line_data = pd.DataFrame(
        {"Year": list(range(2015, 2024)), "ImpactScore": [50, 55, 61, 66, 70, 74, 78, 82, 84]}
    )
    fig_line = px.line(
        line_data, x="Year", y="ImpactScore", title="Yearly Impact Score"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    bar_data = pd.DataFrame(
        {"Gender": ["Female", "Male"], "Participation": [5200, 7250]}
    )
    fig_bar = px.bar(
        bar_data, x="Participation", y="Gender", orientation="h", title="Gender Participation"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

def ksheersagar_dashboard():
    st.subheader("🐄 Ksheersagar 2.0 Dashboard")
    st.markdown("### 🌍 Geographic Dashboard")
    components.iframe(
        src="https://datawrapper.dwcdn.net/01h0U/1/",
        height=600,
        width=800,
        scrolling=True,
    )
    kpi_data = {
        "Metric": ["Total Milk Collection (Liters)", "Number of Active Farmers",
                   "Average Milk Yield per Farmer (Liters)", "AI Coverage (%)",
                   "Animal Health Checkups"],
        "Jan": [100000, 500, 200, 60, 150],
        "Feb": [120000, 550, 210, 62, 160],
        "Mar": [110000, 520, 211, 63, 155],
        "Apr": [115000, 530, 217, 65, 165],
        "May": [125000, 560, 223, 67, 170],
    }
    kpi_df = pd.DataFrame(kpi_data).set_index("Metric")

    st.subheader("Key Performance Indicators")
    st.dataframe(kpi_df, use_container_width=True)

    kpi_df_T = kpi_df.T.reset_index().rename(columns={'index': 'Month'})
    numeric_cols = [col for col in kpi_df_T.columns if col not in ['Month']]
    kpi_df_long = kpi_df_T.melt(id_vars=['Month'], value_vars=numeric_cols, var_name='KPI', value_name='Value')

    selected_kpi = st.selectbox(
        "Select KPI to visualize",
        kpi_df_long['KPI'].unique(),
        key="ksheersagar_kpi_select_2"
    )

    fig_selected_kpi = px.line(
        kpi_df_long[kpi_df_long['KPI'] == selected_kpi],
        x="Month",
        y="Value",
        title=f"{selected_kpi} Over Time",
        markers=True
    )
    st.plotly_chart(fig_selected_kpi, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("🧬 Breed Diversity", "21 types")
    col2.metric("🧮 Avg Daily Milk (L)", "9.3")
    col3.metric("🔁 AI Coverage (%)", "67.4")

    st.markdown("---")

    breed_data = pd.DataFrame(
        {"Breed": ["Sahiwal", "Gir", "Jersey", "HF"], "Count": [3400, 2800, 1500, 900]}
    )
    fig_breed = px.pie(
        breed_data, names="Breed", values="Count", hole=0.5, title="Breed Composition"
    )
    st.plotly_chart(fig_breed, use_container_width=True)

    trend_data = pd.DataFrame(
        {"Year": list(range(2016, 2024)), "AI_Usage": [40, 45, 48, 52, 56, 60, 65, 67]}
    )
    fig_trend = px.line(
        trend_data, x="Year", y="AI_Usage", title="Artificial Insemination Coverage Over Time"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    class_data = pd.DataFrame(
        {"Class": ["<5L", "5-10L", "10-15L", ">15L"], "Farms": [2200, 3800, 2700, 1100]}
    )
    fig_class = px.bar(
        class_data, x="Farms", y="Class", orientation="h", title="Farm Distribution by Milk Output"
    )
    st.plotly_chart(fig_class, use_container_width=True)

def pmu_dashboard(user: Employee):
    with SessionLocal() as db:
        st.subheader("📋 PMU Work Plans and Targets")

        workplans = db.query(WorkPlan).filter_by(supervisor_id=user.id).all()
        targets = db.query(Target).filter_by(employee_id=user.id).all()
        schedules = db.query(Schedule).filter_by(employee_id=user.id).all()

        with st.expander("📌 Summary View"):
            st.markdown("### 🧾 Progress Overview")

            if workplans:
                wp_status_df = pd.DataFrame([wp.status for wp in workplans], columns=["Status"])
                wp_counts = (
                    wp_status_df["Status"]
                    .value_counts()
                    .reindex(["Not Started", "In Progress", "Completed"], fill_value=0)
                )
                st.write("#### Workplans")
                st.dataframe(
                    wp_counts.reset_index().rename(
                        columns={"index": "Status", "Status": "Count"}
                    ), use_container_width=True
                )
            else:
                st.info("No work plans available for summary.")

            if targets:
                tgt_status_df = pd.DataFrame([t.status for t in targets], columns=["Status"])
                tgt_counts = (
                    tgt_status_df["Status"]
                    .value_counts()
                    .reindex(["Not Started", "In Progress", "Completed"], fill_value=0)
                )
                st.write("#### Targets")
                st.dataframe(
                    tgt_counts.reset_index().rename(
                        columns={"index": "Status", "Status": "Count"}
                    ), use_container_width=True
                )
            else:
                st.info("No targets available for summary.")

            st.write("#### Schedules")
            if schedules:
                schedule_df = pd.DataFrame(
                    [
                        {
                            "Date": s.date,
                            "Start Time": s.start_time,
                            "End Time": s.end_time,
                            "GMeet Link": s.gmeet_link if s.gmeet_link else "N/A",
                        }
                        for s in schedules
                    ]
                )
                st.dataframe(schedule_df, use_container_width=True)
            else:
                st.info("No schedules available.")

        with st.expander("➕ Add New Work Plan"):
            with st.form("work_plan_form_pmu"):
                title = st.text_input("Work Plan Title", max_chars=255)
                details = st.text_area("Details")
                deadline = st.date_input("Deadline")
                status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
                workstream_titles = [
                    ws.title for ws in db.query(WorkStream).filter_by(employee_id=user.id).all()
                ]
                workstream_option = st.selectbox(
                    "Workstream", ["Select...", "Add New Workstream..."] + workstream_titles, index=0
                )

                new_workstream_title = None
                if workstream_option == "Add New Workstream...":
                    new_workstream_title = st.text_input("New Workstream Title", key="new_workstream_title_input")

                submitted = st.form_submit_button("Save Work Plan")

                if submitted:
                    if workstream_option == "Select...":
                        st.error("Please select an existing workstream or add a new one.")
                    elif workstream_option == "Add New Workstream..." and not new_workstream_title:
                        st.error("Please enter a title for the new workstream.")
                    else:
                        workstream_obj = None
                        if workstream_option == "Add New Workstream...":
                            try:
                                new_ws = WorkStream(title=new_workstream_title, description="", category="General", employee_id=user.id)
                                db.add(new_ws)
                                db.commit()
                                workstream_obj = new_ws
                                st.success(f"New workstream '{new_workstream_title}' created!")
                            except IntegrityError:
                                db.rollback()
                                st.error(f"Workstream '{new_workstream_title}' already exists. Please choose a different name.")
                                workstream_obj = db.query(WorkStream).filter_by(title=new_workstream_title, employee_id=user.id).first()
                        else:
                            workstream_obj = db.query(WorkStream).filter_by(title=workstream_option, employee_id=user.id).first()

                        if workstream_obj:
                            new_workplan = WorkPlan(
                                title=title,
                                details=details,
                                deadline=deadline,
                                status=status,
                                supervisor_id=user.id,
                                workstream_id=workstream_obj.id,
                            )
                            db.add(new_workplan)
                            db.commit()
                            st.success("✅ Work Plan saved successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to link work plan to a workstream. Please try again.")

        with st.expander("➕ Add New Target"):
            with st.form("target_form_pmu"):
                description = st.text_area("Target Description")
                deadline = st.date_input("Target Deadline")
                status = st.selectbox("Target Status", ["Not Started", "In Progress", "Completed"])

                if st.form_submit_button("Save Target"):
                    if description and deadline:
                        new_target = Target(
                            description=description,
                            deadline=deadline,
                            status=status,
                            employee_id=user.id,
                        )
                        db.add(new_target)
                        db.commit()
                        st.success("✅ Target saved.")
                        st.rerun()
                    else:
                        st.error("Please fill in all target fields.")

        st.subheader("📌 Your Work Plans and Targets")

        if workplans:
            st.write("### Work Plans")
            for plan in workplans:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Title**: {plan.title}")
                        st.markdown(f"**Details**: {plan.details}")
                        st.markdown(f"**Deadline**: {plan.deadline.strftime('%Y-%m-%d')}")
                        st.markdown(f"**Status**: {plan.status}")
                    with col2:
                        with st.form(key=f"workplan_progress_{plan.id}"):
                            new_status = st.selectbox(
                                "Update Status",
                                ["Not Started", "In Progress", "Completed"],
                                index=["Not Started", "In Progress", "Completed"].index(
                                    plan.status
                                ),
                                key=f"wp_status_{plan.id}"
                            )
                            submit_progress = st.form_submit_button("Update Progress", key=f"wp_submit_{plan.id}")
                            if submit_progress:
                                plan.status = new_status
                                db.commit()
                                st.success("Progress updated!")
                                st.rerun()
                            if st.button("Delete Work Plan", key=f"delete_wp_{plan.id}"):
                                db.delete(plan)
                                db.commit()
                                st.success("Work Plan deleted.")
                                st.rerun()

        else:
            st.info("No work plans found.")

        if targets:
            st.write("### Targets")
            for tgt in targets:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Target**: {tgt.description}")
                        st.markdown(f"**Deadline**: {tgt.deadline.strftime('%Y-%m-%d')}")
                        st.markdown(f"**Status**: {tgt.status}")
                    with col2:
                        with st.form(key=f"target_progress_{tgt.id}"):
                            new_status = st.selectbox(
                                "Update Status",
                                ["Not Started", "In Progress", "Completed"],
                                index=["Not Started", "In Progress", "Completed"].index(
                                    tgt.status
                                ),
                                key=f"tgt_status_{tgt.id}"
                            )
                            submit_progress = st.form_submit_button("Update Progress", key=f"tgt_submit_{tgt.id}")
                            if submit_progress:
                                tgt.status = new_status
                                db.commit()
                                st.success("Progress updated!")
                                st.rerun()
                            if st.button("Delete Target", key=f"delete_target_{tgt.id}"):
                                db.delete(tgt)
                                db.commit()
                                st.success("Target deleted.")
                                st.rerun()
        else:
            st.info("No targets found.")

def settings(user: Employee):
    with SessionLocal() as db:
        st.subheader("⚙️ Settings")

        if "settings" not in st.session_state:
            st.session_state.settings = {
                "theme": "Light",
                "notification": "Email",
                "language": "English",
                "project_timeline": "Weekly",
                "units": "Hours",
                "progress_metric": "% Complete",
                "report_frequency": "Weekly",
                "report_format": "PDF",
                "auto_email_summary": False,
            }

        st.markdown("### User Preferences")
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark"],
            index=["Light", "Dark"].index(st.session_state.settings["theme"]),
            key="theme_select"
        )
        notification = st.selectbox(
            "Notification Settings",
            ["Email", "In-app", "None"],
            index=["Email", "In-app", "None"].index(st.session_state.settings["notification"]),
            key="notification_select"
        )
        language = st.selectbox(
            "Language Preferences",
            ["English", "Spanish", "French"],
            index=["English", "Spanish", "French"].index(st.session_state.settings["language"]),
            key="language_select"
        )

        st.markdown("### Project Preferences")
        project_timeline = st.selectbox(
            "Default Project Timeline",
            ["Daily", "Weekly", "Monthly"],
            index=["Daily", "Weekly", "Monthly"].index(st.session_state.settings["project_timeline"]),
            key="timeline_select"
        )
        units = st.selectbox(
            "Units of Measurement",
            ["Hours", "Days", "Cost Units"],
            index=["Hours", "Days", "Cost Units"].index(st.session_state.settings["units"]),
            key="units_select"
        )
        progress_metric = st.selectbox(
            "Default Progress Tracking Metrics",
            ["% Complete", "Milestones"],
            index=["% Complete", "Milestones"].index(st.session_state.settings["progress_metric"]),
            key="progress_metric_select"
        )

        st.markdown("### Report Configuration")
        report_frequency = st.selectbox(
            "Default Report Frequency",
            ["Weekly", "Bi-weekly", "Monthly"],
            index=["Weekly", "Bi-weekly", "Monthly"].index(st.session_state.settings["report_frequency"]),
            key="report_freq_select"
        )
        report_format = st.selectbox(
            "Report Formats",
            ["PDF", "Excel", "JSON"],
            index=["PDF", "Excel", "JSON"].index(st.session_state.settings["report_format"]),
            key="report_format_select"
        )
        auto_email_summary = st.checkbox(
            "Auto-email Summary", value=st.session_state.settings["auto_email_summary"], key="auto_email_checkbox"
        )

        st.markdown("### Change Password")
        with st.form("change_password_form", clear_on_submit=True):
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Change Password"):
                if new_password and new_password == confirm_password:
                    user_to_update = db.query(Employee).filter_by(id=user.id).first()
                    if user_to_update:
                        user_to_update.password = new_password
                        db.commit()
                        st.success("Password changed successfully!")
                    else:
                        st.error("User not found.")
                elif not new_password:
                    st.error("New password cannot be empty.")
                else:
                    st.error("Passwords do not match.")

        if st.button("Save Settings", key="save_settings_button"):
            st.session_state.settings.update(
                {
                    "theme": theme,
                    "notification": notification,
                    "language": language,
                    "project_timeline": project_timeline,
                    "units": units,
                    "progress_metric": progress_metric,
                    "report_frequency": report_frequency,
                    "report_format": report_format,
                    "auto_email_summary": auto_email_summary,
                }
            )
            st.success("Settings saved successfully!")

def reports():
    st.subheader("📊 Reports")
    st.markdown("### Weekly Document Summary")

    summary_filename = f"weekly_summary_{date.today().strftime('%Y%m%d')}.csv"

    if st.button("Generate Weekly Summary"):
        with SessionLocal() as db:
            all_workplans = db.query(WorkPlan).all()
            all_targets = db.query(Target).all()

            summary_data_rows = []
            for wp in all_workplans:
                summary_data_rows.append({
                    "Type": "Work Plan",
                    "Item": wp.title,
                    "Description": wp.details,
                    "Deadline": wp.deadline.strftime('%Y-%m-%d'),
                    "Status": wp.status,
                    "Assigned To": wp.supervisor.name if wp.supervisor else "N/A"
                })
            for tgt in all_targets:
                summary_data_rows.append({
                    "Type": "Target",
                    "Item": tgt.description,
                    "Description": "",
                    "Deadline": tgt.deadline.strftime('%Y-%m-%d'),
                    "Status": tgt.status,
                    "Assigned To": tgt.employee.name if tgt.employee else "N/A"
                })

            if summary_data_rows:
                summary_df = pd.DataFrame(summary_data_rows)
                try:
                    summary_df.to_csv(summary_filename, index=False)
                    st.success(f"Weekly summary generated: **{summary_filename}**")
                except Exception as e:
                    st.error(f"Error saving summary to CSV: {e}")
            else:
                st.info("No data available to generate a summary.")

    if os.path.exists(summary_filename):
        summary_df = pd.read_csv(summary_filename)
        st.dataframe(summary_df, use_container_width=True)
        with open(summary_filename, "rb") as file:
            btn = st.download_button(
                label="Download Summary CSV",
                data=file,
                file_name=summary_filename,
                mime="text/csv",
            )
    else:
        st.info("No summary file generated yet.")

def scheduling(user: Employee):
    with SessionLocal() as db:
        st.subheader("🗓️ Employee Scheduling")

        with st.form("add_schedule"):
            schedule_date = st.date_input("Schedule Date", date.today())
            start_time = st.time_input("Start Time", time(9, 0))
            end_time = st.time_input("End Time", time(17, 0))
            generate_gmeet = st.checkbox("Generate GMeet Link?")
            gmeet_link = None
            if generate_gmeet:
                gmeet_link = st.text_input("GMeet Link (optional, will override auto-generated)", "https://meet.google.com/new")

            if st.form_submit_button("Add Schedule"):
                if start_time < end_time:
                    new_schedule = Schedule(
                        employee_id=user.id,
                        date=schedule_date,
                        start_time=str(start_time),
                        end_time=str(end_time),
                        gmeet_link=gmeet_link,
                    )
                    db.add(new_schedule)
                    db.commit()
                    st.success("Schedule added successfully!")
                    st.rerun()
                else:
                    st.error("End time must be after start time.")

        st.subheader("Your Schedules")
        schedules = db.query(Schedule).filter_by(employee_id=user.id).order_by(Schedule.date.desc()).all()
        if schedules:
            schedule_data = []
            for schedule in schedules:
                schedule_data.append({
                    "Date": schedule.date.strftime('%Y-%m-%d'),
                    "Start Time": schedule.start_time,
                    "End Time": schedule.end_time,
                    "GMeet Link": schedule.gmeet_link if schedule.gmeet_link else "N/A"
                })
            schedule_df = pd.DataFrame(schedule_data)
            st.dataframe(schedule_df, use_container_width=True)

            st.markdown("---")
            st.subheader("Manage Existing Schedules")
            schedule_to_delete_id = st.selectbox(
                "Select a schedule to delete",
                options=[s.id for s in schedules],
                format_func=lambda x: f"{db.query(Schedule).get(x).date} {db.query(Schedule).get(x).start_time}",
                index=None,
                placeholder="Select a schedule..."
            )
            if st.button("Delete Selected Schedule") and schedule_to_delete_id:
                schedule_to_delete = db.query(Schedule).get(schedule_to_delete_id)
                if schedule_to_delete:
                    db.delete(schedule_to_delete)
                    db.commit()
                    st.success("Schedule deleted successfully!")
                    st.rerun()
                else:
                    st.error("Schedule not found.")
        else:
            st.info("No schedules found.")

def field_team_management():
    with SessionLocal() as db:
        st.subheader("👥 Field Team Management")

        with st.form("add_field_team"):
            team_name = st.text_input("Field Team Name", max_chars=100)
            if st.form_submit_button("Add Field Team"):
                if team_name:
                    try:
                        new_team = FieldTeam(name=team_name, pmu_id=st.session_state.user.id)
                        db.add(new_team)
                        db.commit()
                        st.success(f"Field Team '{team_name}' added successfully!")
                        st.rerun()
                    except IntegrityError:
                        db.rollback()
                        st.error(f"Field Team '{team_name}' already exists.")
                    except Exception as e:
                        db.rollback()
                        st.error(f"An error occurred while adding the team: {e}")
                else:
                    st.error("Field Team Name cannot be empty.")

        st.subheader("Existing Field Teams")
        field_teams = db.query(FieldTeam).filter_by(pmu_id=st.session_state.user.id).all()
        if field_teams:
            for team in field_teams:
                col1, col2 = st.columns([3, 1])
                col1.markdown(f"**Team Name**: {team.name}")
                if col2.button(f"Delete {team.name}", key=f"delete_team_{team.id}"):
                    try:
                        db.delete(team)
                        db.commit()
                        st.success(f"Field Team '{team.name}' deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        db.rollback()
                        st.error(f"Error deleting team: {e}")
            st.markdown("---")
            st.subheader("Add Tasks to Field Teams")
            with st.form("add_team_task"):
                selected_team_id = st.selectbox(
                    "Select Team",
                    options=[t.id for t in field_teams],
                    format_func=lambda x: db.query(FieldTeam).get(x).name,
                    index=None,
                    placeholder="Select a team..."
                )
                task_description = st.text_area("Task Description", max_chars=500)
                task_deadline = st.date_input("Task Deadline")
                task_status = st.selectbox("Task Status", ["Not Started", "In Progress", "Completed"])

                if st.form_submit_button("Add Task to Team"):
                    if selected_team_id and task_description and task_deadline:
                        try:
                            new_task = Task(
                                description=task_description,
                                deadline=task_deadline,
                                status=task_status,
                                field_team_id=selected_team_id
                            )
                            db.add(new_task)
                            db.commit()
                            st.success("Task added to team successfully!")
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Error adding task: {e}")
                    else:
                        st.error("Please fill in all task details and select a team.")

            st.markdown("---")
            st.subheader("Team Tasks Overview")
            for team in field_teams:
                st.markdown(f"#### Tasks for {team.name}")
                tasks = db.query(Task).filter_by(field_team_id=team.id).all()
                if tasks:
                    task_data = []
                    for task in tasks:
                        task_data.append({
                            "Description": task.description,
                            "Deadline": task.deadline.strftime('%Y-%m-%d'),
                            "Status": task.status
                        })
                    task_df = pd.DataFrame(task_data)
                    st.dataframe(task_df, use_container_width=True)
                else:
                    st.info(f"No tasks for {team.name}.")
        else:
            st.info("No field teams available. Please add a team first.")

    st.subheader("🌐 Field Team API Integration (Placeholder)")
    st.write("This section will integrate with a Field Team Management API.")
    if st.button("Simulate API Call to Fetch Field Teams"):
        st.info("Attempting to fetch field team data from API...")
        dummy_data = api_get("field_teams")
        if dummy_data:
            st.json(dummy_data)
        else:
            st.warning("No data returned from API or API error occurred.")

def training():
    st.subheader("📚 Training Module")
    st.write("This section provides training materials and resources.")

    st.header("📤 Upload Training Content")
    selected_program = st.selectbox(
        "🌟 Select Program", ["Cotton", "Dairy"], key="program_dropdown"
    )
    selected_category = st.selectbox(
        "📂 Select Category",
        ["Presentations", "Videos", "Audios", "Quizzes"],
        key="category_dropdown"
    )
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=["pdf", "mp4", "mp3", "json", "pptx", "xlsx", "png", "jpg", "jpeg"],
    )

    if uploaded_file:
        if selected_program and selected_category:
            save_dir_path = Path("training_materials") / selected_program.lower() / selected_category.lower()
            save_dir_path.mkdir(parents=True, exist_ok=True)
            file_path = save_dir_path / uploaded_file.name

            if not is_valid_file_type(uploaded_file.name, selected_category):
                st.error(f"❌ Invalid file type for the **{selected_category}** category.")
            else:
                if st.button("Upload File"):
                    try:
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(
                            f"✅ File '{uploaded_file.name}' uploaded successfully to {file_path}!"
                        )
                        st.info(f"Simulating upload of '{uploaded_file.name}' to Google Drive...")
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {e}")
        else:
            st.error("Please select a program and category before uploading.")
    else:
        st.info("No file selected for upload.")

    st.header("📂 Uploaded Training Content")
    for program in ["Cotton", "Dairy"]:
        for category in ["Presentations", "Videos", "Audios", "Quizzes"]:
            folder_path = Path(f"training_materials/{program.lower()}/{category.lower()}")
            if folder_path.exists():
                files_in_folder = list(folder_path.iterdir())
                if files_in_folder:
                    st.subheader(f"{program} - {category}")
                    for file in files_in_folder:
                        st.markdown(f"- {file.name}")

def is_valid_file_type(file_name: str, category: str) -> bool:
    valid_extensions = {
        "Presentations": [".pptx", ".pdf"],
        "Videos": [".mp4", ".mov", ".avi"],
        "Audios": [".mp3", ".wav"],
        "Quizzes": [".xlsx", ".csv", ".json"],
    }
    image_extensions = [".png", ".jpg", ".jpeg", ".gif"]

    file_extension = Path(file_name).suffix.lower()

    if category in valid_extensions and file_extension in valid_extensions[category]:
        return True
    if category == "Quizzes" and file_extension in image_extensions:
        return True
    return False

def google_drive():
    st.subheader("Google Drive Integration (Placeholder)")
    st.write("This section will eventually integrate with Google Drive to manage and display documents.")

    if st.button("List Files (Placeholder)"):
        st.write("Simulating listing files from Google Drive...")
        st.markdown("- Project Documents/")
        st.markdown("  - Report_Q1_2024.pdf")
        st.markdown("  - Team_Meeting_Notes.docx")
        st.markdown("- Training Resources/")
        st.markdown("  - Onboarding_Guide.pdf")
        st.markdown("  - Video_Tutorial_1.mp4")

    st.markdown("---")
    st.write("You can also upload files here which would then be synced to Google Drive.")
    uploaded_file_gd = st.file_uploader("Upload file to Google Drive (Placeholder)", type=None)
    if uploaded_file_gd:
        st.info(f"Simulating upload of '{uploaded_file_gd.name}' to Google Drive...")
        st.success("File uploaded to Google Drive (simulated)!")

def get_team_chat() -> List[tuple[str, str]]:
    conn = sqlite3.connect(CHAT_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    cursor.execute("SELECT user, message, timestamp FROM chat ORDER BY timestamp ASC LIMIT 50")
    chats = cursor.fetchall()
    conn.close()
    return chats

def add_chat_message(user: str, message: str):
    conn = sqlite3.connect(CHAT_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat (user, message) VALUES (?, ?)", (user, message))
    conn.commit()
    conn.close()

def team_chat(user: Employee):
    st.subheader("💬 Team Chat")
    chats = get_team_chat()

    chat_container = st.container(height=400, border=True)
    for chat_user, message, timestamp in chats:
        chat_container.chat_message(chat_user).write(f"[{datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')}] {message}")

    with st.form("Send Chat Message"):
        message = st.text_input("Message", key="chat_message_input")
        if st.form_submit_button("Send"):
            if message:
                add_chat_message(user.name, message)
                st.rerun()
            else:
                st.warning("Please enter a message to send.")

def email():
    st.subheader("📧 Email Integration (Placeholder)")
    st.write("This section will eventually integrate with an email service (e.g., Gmail API).")

    with st.form("send_email_form"):
        recipient = st.text_input("Recipient Email", placeholder="recipient@example.com")
        subject = st.text_input("Subject", max_chars=255)
        body = st.text_area("Body")
        submitted = st.form_submit_button("Send Email (Placeholder)")

        if submitted:
            if recipient and subject and body:
                st.info(f"Simulating sending email to **{recipient}** with subject **'{subject}'**.")
                st.success("Email sent (simulated)!")
            else:
                st.error("Please fill in all email fields.")

def calendar_view(user: Employee):
    with SessionLocal() as db:
        st.subheader("📆 Calendar Task Manager & Meetings")

        selected_date_for_tasks = st.date_input("Select a date for tasks", date.today(), key="task_date_picker")

        with st.form("add_calendar_task"):
            task_text = st.text_input("Task for selected date", max_chars=500)
            if st.form_submit_button("Add Task"):
                if task_text:
                    new_task = CalendarTask(employee_id=user.id, date=selected_date_for_tasks, task=task_text)
                    db.add(new_task)
                    db.commit()
                    st.success("Task added!")
                    st.rerun()
                else:
                    st.error("Task description cannot be empty.")

        st.markdown(f"### 📝 Tasks on {selected_date_for_tasks.strftime('%b %d, %Y')}")
        tasks = db.query(CalendarTask).filter_by(employee_id=user.id, date=selected_date_for_tasks).all()

        if not tasks:
            st.info("No tasks for this day.")
        else:
            for t in tasks:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.write(f"- {t.task}")
                with col2:
                    if st.button("❌", key=f"del_task_{t.id}"):
                        db.delete(t)
                        db.commit()
                        st.rerun()

        st.markdown("---")

        st.subheader("Create New Meeting")
        with st.form("add_meeting"):
            meeting_date = st.date_input("Meeting Date", date.today(), key="meeting_date_picker")
            meeting_start_time = st.time_input("Meeting Start Time", time(9, 0))
            meeting_end_time = st.time_input("Meeting End Time", time(10, 0))
            meeting_description = st.text_input("Meeting Description", max_chars=500)

            if st.form_submit_button("Add Meeting"):
                if meeting_start_time < meeting_end_time and meeting_description:
                    new_meeting = Meeting(
                        employee_id=user.id,
                        date=meeting_date,
                        start_time=str(meeting_start_time),
                        end_time=str(meeting_end_time),
                        description=meeting_description,
                    )
                    db.add(new_meeting)
                    db.commit()
                    st.success("Meeting added successfully!")
                    st.rerun()
                elif not meeting_description:
                    st.error("Meeting description cannot be empty.")
                else:
                    st.error("Meeting end time must be after start time.")

        st.subheader("Your Upcoming Meetings")
        meetings = db.query(Meeting).filter_by(employee_id=user.id).order_by(Meeting.date, Meeting.start_time).all()

        if not meetings:
            st.info("No upcoming meetings.")
        else:
            for meeting in meetings:
                with st.container(border=True):
                    st.markdown(f"**Date**: {meeting.date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Time**: {meeting.start_time} - {meeting.end_time}")
                    st.markdown(f"**Description**: {meeting.description}")
                    if st.button("Delete Meeting", key=f"del_meeting_{meeting.id}"):
                        db.delete(meeting)
                        db.commit()
                        st.rerun()

        st.markdown("---")
        st.markdown("### 📅 Availability Calendar (JS Widget)")
        components.html("""
        <head>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
            <style>
                .flatpickr-calendar {
                    font-family: 'Segoe UI', sans-serif;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                }
                .flatpickr-day.available {
                    background-color: #2b2d42;
                    color: white;
                    border-radius: 50%;
                }
                .flatpickr-day.unavailable {
                    background-color: #e0e0e0;
                    color: #aaa;
                    pointer-events: none;
                }
                .flatpickr-day.selected {
                    background-color: #00b4d8 !important;
                    color: white;
                    border-radius: 50%;
                }
            </style>
        </head>
        <body>
            <input type="text" id="calendar" placeholder="Select a date" style="padding: 10px; font-size: 16px; width: 200px; border-radius: 8px; border: 1px solid #ccc;">
            <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
            <script>
                flatpickr("#calendar", {
                    inline: true,
                    defaultDate: "today",
                    onDayCreate: function(dObj, dStr, fp, dayElem) {
                        let date = dayElem.dateObj.toISOString().split('T')[0];
                        if(["2023-07-26", "2023-08-10", "2023-08-23"].includes(date)) {
                            dayElem.classList.add("available");
                        }
                        if(["2023-07-27", "2023-08-11"].includes(date)) {
                            dayElem.classList.add("unavailable");
                        }
                    },
                    onChange: function(selectedDates, dateStr, instance) {
                        window.parent.postMessage({ type: 'SELECTED_DATE_JS', value: dateStr }, '*');
                    }
                });
            </script>
        </body>
        """, height=400)

def monthly_meeting(user: Employee):
    with SessionLocal() as db:
        st.subheader("📅 Monthly Meeting Preparation")

        now = datetime.now()
        current_month = now.month
        current_year = now.year

        st.write(f"### Preparing for: {calendar.month_name[current_month]}, {current_year}")

        workplans = db.query(WorkPlan).filter_by(supervisor_id=user.id).all()
        targets = db.query(Target).filter_by(employee_id=user.id).all()
        meetings = db.query(Meeting).filter_by(employee_id=user.id).all()


        st.write("### Your Work Plans and Progress")
        if workplans:
            for plan in workplans:
                with st.container(border=True):
                    st.markdown(f"**Title**: {plan.title}")
                    st.markdown(f"**Details**: {plan.details}")
                    st.markdown(f"**Deadline**: {plan.deadline.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Current Status**: {plan.status}")

                    with st.form(key=f"monthly_wp_progress_{plan.id}"):
                        new_status = st.selectbox(
                            "Update Status for Meeting",
                            ["Not Started", "In Progress", "Completed"],
                            index=["Not Started", "In Progress", "Completed"].index(plan.status),
                            key=f"monthly_wp_status_{plan.id}"
                        )
                        progress_notes = st.text_area(
                            "Progress Notes for Meeting (e.g., challenges, successes)",
                            value=st.session_state.get(f"wp_notes_{plan.id}", ""),
                            key=f"monthly_wp_notes_{plan.id}"
                        )
                        submit_progress = st.form_submit_button("Update for Meeting")

                        if submit_progress:
                            plan.status = new_status
                            db.commit()
                            st.session_state[f"wp_notes_{plan.id}"] = progress_notes
                            st.success("Work Plan status and notes updated for meeting!")
                            st.rerun()
            st.markdown("---")
        else:
            st.info("No work plans found for this period.")

        st.write("### Your Targets and Progress")
        if targets:
            for tgt in targets:
                with st.container(border=True):
                    st.markdown(f"**Description**: {tgt.description}")
                    st.markdown(f"**Deadline**: {tgt.deadline.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Current Status**: {tgt.status}")
                    with st.form(key=f"monthly_tgt_progress_{tgt.id}"):
                        new_status = st.selectbox(
                            "Update Target Status for Meeting",
                            ["Not Started", "In Progress", "Completed"],
                            index=["Not Started", "In Progress", "Completed"].index(tgt.status),
                            key=f"monthly_tgt_status_{tgt.id}"
                        )
                        target_notes = st.text_area(
                            "Target Notes for Meeting",
                            value=st.session_state.get(f"target_notes_{tgt.id}", ""),
                            key=f"monthly_target_notes_{tgt.id}"
                        )
                        submit_progress = st.form_submit_button("Update Target for Meeting")
                        if submit_progress:
                            tgt.status = new_status
                            db.commit()
                            st.session_state[f"target_notes_{tgt.id}"] = target_notes
                            st.success("Target status and notes updated for meeting!")
                            st.rerun()
            st.markdown("---")
        else:
            st.info("No targets found for this period.")


        st.write("### Meeting Agenda Items")
        agenda_items = [
            "Review of last month's goals",
            "Progress on current work plans",
            "Discussion of any roadblocks",
            "Setting goals for the next month",
        ]
        for item in agenda_items:
            st.write(f"- {item}")

        st.write("### Additional Notes for Meeting")
        additional_notes = st.text_area(
            "Enter any additional notes for the meeting (e.g., points to discuss, questions for supervisor)",
            value=st.session_state.get("monthly_meeting_additional_notes", "")
        )
        if st.button("Save Additional Notes"):
            st.session_state["monthly_meeting_additional_notes"] = additional_notes
            st.success("Additional notes saved!")


        if st.button("Generate Meeting Summary"):
            summary = f"""
            ## Monthly Meeting Summary: {calendar.month_name[current_month]}, {current_year}

            ### Employee: {user.name}

            ---

            ### Work Plans and Progress:
            """
            if workplans:
                for plan in workplans:
                    summary += f"""
                    - **Work Plan**: {plan.title}
                      - **Details**: {plan.details}
                      - **Deadline**: {plan.deadline.strftime('%Y-%m-%d')}
                      - **Status**: {plan.status}
                      - **Notes**: {st.session_state.get(f"wp_notes_{plan.id}", "No notes provided.")}
                    """
            else:
                summary += "No work plans found for this period."

            summary += f"""
            ---

            ### Targets and Progress:
            """
            if targets:
                for tgt in targets:
                    summary += f"""
                    - **Target**: {tgt.description}
                      - **Deadline**: {tgt.deadline.strftime('%Y-%m-%d')}
                      - **Status**: {tgt.status}
                      - **Notes**: {st.session_state.get(f"target_notes_{tgt.id}", "No notes provided.")}
                    """
            else:
                summary += "No targets found for this period."


            summary += f"""
            ---

            ### General Meeting Agenda Items:
            """
            for item in agenda_items:
                summary += f"- {item}\n"

            summary += f"""
            ---

            ### Additional Notes for Discussion:
            {additional_notes if additional_notes else "No additional notes."}

            ---
            """
            st.markdown("### Generated Meeting Summary")
            st.markdown(summary)

            st.download_button(
                label="Download Meeting Summary (Markdown)",
                data=summary,
                file_name=f"monthly_meeting_summary_{user.name.replace(' ', '_')}_{current_month}_{current_year}.md",
                mime="text/markdown"
            )

# --- Main Application Logic ---
def main():
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.title("🔐 Login to PMU Tracker")
        display_notice()
        with SessionLocal() as db:
            all_users = db.query(Employee).all()
            emails = [u.email for u in all_users]
            selected_email = st.selectbox("Select your email", ["Select..."] + emails, index=0)

            if selected_email != "Select...":
                user_attempt = db.query(Employee).filter_by(email=selected_email).first()
                if user_attempt:
                    password_input = st.text_input("Password", type="password", key="login_password_input")
                    if st.button("Login"):
                        if user_attempt.password == password_input:
                            st.session_state.user = user_attempt
                            st.success(f"Welcome back, {user_attempt.name}!")
                            st.rerun()
                        else:
                            st.error("Incorrect password.")
                else:
                    st.error("User not found with this email.")
            else:
                st.info("Please select your email and enter your password to log in.")

    if st.session_state.user is not None:
        selected_page = sidebar_navigation()

        if selected_page == "dashboard":
            dashboard(st.session_state.user)
        elif selected_page == "manage_programs":
            manage_programs()
        elif selected_page == "scheduling":
            scheduling(st.session_state.user)
        elif selected_page == "field_team_management":
            field_team_management()
        elif selected_page == "live_dashboard":
            live_dashboard()
        elif selected_page == "reports":
            reports()
        elif selected_page == "settings":
            settings(st.session_state.user)
        elif selected_page == "saksham_dashboard":
            saksham_dashboard()
        elif selected_page == "training":
            training()
        elif selected_page == "google_drive":
            google_drive()
        elif selected_page == "team_chat":
            team_chat(st.session_state.user)
        elif selected_page == "email":
            email()
        elif selected_page == "calendar_view":
            calendar_view(st.session_state.user)
        elif selected_page == "monthly_meeting":
            monthly_meeting(st.session_state.user)
        elif selected_page == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")
            st.rerun()

if __name__ == "__main__":
    main()
