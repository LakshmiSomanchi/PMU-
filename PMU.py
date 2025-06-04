import streamlit as st
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
import sqlite3
from datetime import date, datetime
import os
from PIL import Image
from io import BytesIO
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from math import floor, ceil  # Import ceil
import json
import requests
import calendar
import streamlit.components.v1 as components

# Set Streamlit page config (must be first)
st.set_page_config(page_title="PMU Tracker", layout="wide")

# Custom CSS
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
            font-family: 'Newsreader', serif; /* Apply Newsreader font to the entire body */
        }

        .stApp {
            background-color: rgba(255, 255, 255, 0.1);
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
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
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        section[data-testid="stSidebar"] > div:first-child::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.5); /* Semi-transparent white */
            border-radius: 0 10px 10px 0;
            z-index: -1;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] .stRadio label {
            color: #ffffff;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        h1,
        h2,
        h3,
        h4 {
            color: #ffffff;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        .streamlit-expanderHeader {
            background-color: #dceefb;
            border: 1px solid #cce0ff;
            border-radius: 10px;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        .stButton > button {
            background-color: #0077b6;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1em;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        .stButton > button:hover {
            background-color: #0096c7;
        }

        .stDataFrame {
            background-color: #ffffff;
            border: 5px solid #ccc;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        .stTabs [role="tab"] {
            background-color: #edf6ff;
            padding: 10px;
            border-radius: 10px 10px 0 0;
            margin-right: 5px;
            border: 1px solid #b6d4fe;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }

        .stTabs [role="tab"][aria-selected="true"] {
            background-color: #0077b6;
            color: white;
            font-family: 'Newsreader', serif; /* Apply Newsreader font */
        }
    </style>
    """,
    unsafe_allow_html=True,
)
def main():
    st.title("🏢 Organisation Structure")

    image_url = "https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/Company%20Organizational%20Chart%20(4).jpg"
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        st.image(image, caption="Organizational Chart", use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load organizational chart: {e}")

    with st.expander("Abbott"): 
        st.subheader("Sachin Wadpalliwar - Manager - Field")
        st.markdown("- **Project**: Aditya Yuvaraj (Associate - Field) → Bhushan Sananse, Nilesh Rajkumar Dhanwate")
        st.markdown("- **Environment**: Aniket Govekar (Assistant Manager - Field) → Subrat Ghoshal, Hrushikesh Tilekar")
        st.markdown("- **Social**: Same as Environment")

    with st.expander("Heritage"):
        st.subheader("Dr. Ramakrishna")
        st.markdown("- Guru Mohan Kakanuru Reddy (Assistant Manager - Field)")
        st.markdown("- K Balaji (Senior Associate - Field)")

    with st.expander("Inditex"):
        st.subheader("Kuntal Dutta - Sr. Manager - Field")
        st.markdown("- **Project**: Gautam Bagada, Samadhan Bangale, Prabodh Pate, Sandeep G S")
        st.markdown("- **Environment**: Ajay Vaghela")
        st.markdown("- **Social**: Happy Vaishnavi, Nikhita VK")

    with st.expander("Project Management Unit"):
        st.subheader("Shifali Sharma - Manager - Field")
        st.markdown("- **Project Support**: Bhavya Kharoo, Pari Sharma, Muskan Kaushal")
        st.markdown("- **Data Platform**: Kriti Suneha, Ranu Laddha, Ramalakshmi Somanchi")
        st.markdown("- **Environment**: Ramalakshmi Somanchi, Aditya Yuvaraj")

    st.markdown("---")
    st.markdown("### Lead: Rupesh Mukherjee - Associate Practice Leader")

    st.title("🤝 Meet the Team")
    team_members = [
        {"name": "Rupesh Mukherjee", "role": "Associate Practice Leader", "photo": "https://via.placeholder.com/80"},
        {"name": "Kuntal Dutta", "role": "Sr. Manager - Field", "photo": "https://lh3.googleusercontent.com/a-/ALV-UjUM8ZsIQuisZZiC3cgBzrrRhwQtGB7Ii7tacDc4ZkP625fXUaUPwwAlF4TdGgVNQxEHj_x5TDHZLuSK9AcPAbZTWjuh1h4pkN4Jb2ImY7tmr3lO_ngbg7XF3Rj0GHAdsElcIVL59q3MuWELF4cbpJHkiwLMT4lGunhsda52r4K5vuIDRuIr8rjkpFGtxOlvKcHqYu6U7Zwflys0qzcXDJvcN5K4a-x7lPo961yZgqe_UVcdMEtKU08oaQ1JHzI98vwfY1oe5WeJ8A1QODpnR6MC2P3KdVMukf6LxfDzqE6Bpd5vWBvAf1VP7L9CNrPf_IPnCemekORg7u_WJVzditvdvJJa_FyuVyqf_hjCyMZJEj13CjY7e7q_UxrvJOjWCU2HSpRyRcapWsvvzJCZ7XrTtHVTeeuQJjIzrf3gys6gXi0_JmQrJneojlqWiXSEUnNgq0cf1F89uOKQsW8YYWzSi3HukW1pK3vtqNZv57aGMJuCNt_vlV16CNjv_OK2mSZa2mIRaePGuOq23bbaA_fz3GNmoVZF8f03RLPHFmtl_IhxblkkQe_0rKr10XDqm9jkNTHfh48FmzlNu3J0wCYmrKtQIgr_xIpWZAIC9-d5KXad5e9Bj4pl_nfohhjfA-CErBy8A46GZt_11QRiu8jwOlpi9GHFHwramR7ei6lPtFD7plxaPb9tEQvc4UkYnhP8H5LmTGKi_eiBbIzQMgpnxCIEQ42yieMCcIeiyQLC0qR10k-i1rEg_2exMmm7jY43joqitGk-ydELZmhULOxamRR3gAsMtMLgwVdYH1_ke34SEaCEiUWXTWCwhwX5lP13sDUEB5LNqDCXSLC78XtuNtpQToMv49aFeQM9Oa8CpVXr39JTUAyxnAPQMuFW5N-3eue9KzFy26CDpIspBgJ87b5RVdKRWRA62qYc3icZk122Gvq7oHJgh62CwvAAzftcTGdcy5A0rtnCk7nR-sqECjYic4s7=s272-p-k-rw-no"},
        {"name": "Shifali Sharma", "role": "Manager - Field", "photo": "https://lh3.googleusercontent.com/a-/ALV-UjVncga1Owmj4rlD8c7JOlteXs4CKepLtyxKvS33Tj3vYFfQr0c=s272-p-k-rw-no"},
        {"name": "Dr. Ramakrishna", "role": "Advisor", "photo": "https://via.placeholder.com/80"},
        {"name": "Sachin Wadpalliwar", "role": "Manager - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Aditya Yuvaraj", "role": "Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Aniket Govekar", "role": "Assistant Manager - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Bhushan Sananse", "role": "Assistant Manager - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Subrat Ghoshal", "role": "Senior Executive - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "K Balaji", "role": "Senior Associate - Field", "photo": "https://lh3.googleusercontent.com/a-/ALV-UjXPZfpYbgTI_KAz39-pp3xKFSvpnNorikyKwfa2Bc24JuxrR9I=s272-p-k-rw-no"},
        {"name": "Guru Mohan Kakanuru Reddy", "role": "Assistant Manager - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Ajay Vaghela", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Happy Vaishnavi", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Nikhita VK", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Bhavya Kharoo", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Kriti Suneha", "role": "Senior Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Ranu Laddha", "role": "Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Pari Sharma", "role": "Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Muskan Kaushal", "role": "Associate - Field", "photo": "https://via.placeholder.com/80"},
        {"name": "Ramalakshmi Somanchi", "role": "Associate - Field", "photo": "https://lh3.googleusercontent.com/a/ACg8ocLjpv_D2a-76pA8cKWU61fDWfYDwRzStF9PxufT0nGXDqy-0pw=s288-c-no"},
        {"name": "Hrushikesh Tilekar", "role": "Associate", "photo": "https://via.placeholder.com/80"},
    ]

    for member in team_members:
        cols = st.columns([1, 5])
        with cols[0]:
            st.image(member["photo"], width=80)
        with cols[1]:
            st.markdown(f"### {member['name']}")
            st.markdown(f"*{member['role']}*")
        st.markdown("---")

# Entry Point
main()
    
# SQLite + SQLAlchemy setup
DATABASE_URL = "sqlite:///pmu.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def get_db():
    return SessionLocal()

API_BASE_URL = "https://api.example.com"  # replace with your actual base API URL

def api_get(endpoint, params=None):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"GET API Error: {e}")
        return None

def api_post(endpoint, data):
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"POST API Error: {e}")
        return None

def api_put(endpoint, data):
    try:
        response = requests.put(f"{API_BASE_URL}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"PUT API Error: {e}")
        return None


# Models
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
    meetings = relationship("Meeting", back_populates="employee")  # Add relationship for meetings


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
    deadline = Column(String)
    status = Column(String, default="Not Started")
    workstream_id = Column(Integer, ForeignKey("workstreams.id"))
    workstream = relationship("WorkStream", back_populates="workplans")
    supervisor_id = Column(Integer, ForeignKey("employees.id"))
    supervisor = relationship("Employee", back_populates="workplans")


class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    deadline = Column(String)
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
    date = Column(Date)  # Change to Date type
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
    deadline = Column(String)
    status = Column(String, default="Not Started")
    field_team_id = Column(Integer, ForeignKey("field_teams.id"))
    field_team = relationship("FieldTeam", back_populates="tasks")


class FarmerData(Base):
    __tablename__ = "farmer_data"
    id = Column(Integer, primary_key=True)
    farmer_name = Column(String)
    number_of_cows = Column(Integer)
    yield_per_cow = Column(Float)
    date = Column(String)


class Meeting(Base):  # New model for meetings
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

    employee = relationship("Employee")

# Preloaded users
preloaded_users = [
    ("Somanchi", "rsomanchi@tns.org", "password1"),
    ("Ranu", "rladdha@tns.org", "password2"),
    ("Pari", "paris@tns.org", "password3"),
    ("Muskan", "mkaushal@tns.org", "password4"),
    ("Rupesh", "rmukherjee@tns.org", "password5"),
    ("Shifali", "shifalis@tns.org", "password6"),
    ("Pragya Bharati", "pbharati@tns.org", "password7"),
    ("Bhavya Kharoo", "bkharoo@tns.org", "password8"),
]

# Initial Programs
initial_programs = ["Water Program", "Education Program", "Ksheersagar 2.0", "SAKSHAM"]


def preload_users():
    db = get_db()
    for name, email, password in preloaded_users:
        try:
            db.add(Employee(name=name, email=email, password=password))
            db.commit()
        except IntegrityError:
            db.rollback()


def preload_programs():
    db = get_db()
    for program_name in initial_programs:
        try:
            db.add(
                Program(
                    name=program_name,
                    description=f"Description for {program_name}",
                    employee_id=1,
                )
            )
            db.commit()
        except IntegrityError:
            db.rollback()


# Explicitly drop tables in reverse dependency order
def drop_tables(engine):
    Base.metadata.drop_all(engine, tables=[
        Task.__table__,
        FieldTeam.__table__,
        WorkPlan.__table__,
        WorkStream.__table__,
        Target.__table__,
        Schedule.__table__,
        Meeting.__table__,  # Drop Meeting table
        Program.__table__,
        FarmerData.__table__,
        Employee.__table__,
    ])


Base.metadata.create_all(bind=engine)

# Then preload
preload_users()
preload_programs()


def display_notice():
    st.markdown(
        """
        <style>
            .notice {
                background-color: rgba(255, 255, 255, 0.3);
                padding: 5px;
                border-radius: 15px;
                font-family: 'Newsreader', serif; /* Apply Newsreader font */
            }
        </style>
        <div class="notice">
            <h2 style='text-align:center;'>NOTICE & PROTOCOL FOR WORKSTREAM TRACKING PLATFORM USAGE</h2>
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


def sidebar():
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
        "Google Drive": "google_drive",
        "Team Chat": "team_chat",
        "Email": "email",
        "Calendar": "calendar_view",  # Add Calendar to the sidebar
        "Monthly Meeting": "monthly_meeting",  # Add Monthly Meeting to the sidebar
        "Logout": "logout",
    }
    selection = st.sidebar.radio("Go to", list(menu_options.keys()))
    return menu_options[selection]


def dashboard(user):
    db = get_db()
    st.markdown(
        "<h1 style='text-align:center; color:#020431;'>Project Management Dashboard</h1>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("### Logged in as")
    st.sidebar.success(user.name)
    if st.sidebar.button("🔓 Logout"):
        st.session_state.user = None
        st.rerun()

    # Tabs for different dashboards
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Field Team Dashboard",
            "PMU Dashboard",
            "Heritage Dashboard",
            "Ksheersagar Dashboard",
        ]
    )

    with tab1:
        st.subheader("📊 Progress")
        st.write("This is where you can display field team progress and metrics.")
        display_todo()  # Add To-Do list here

    with tab2:
        pmu_dashboard(user)
        display_kanban()  # Add Kanban board here

    with tab3:
        heritage_dashboard()

    with tab4:
        ksheersagar_dashboard()

def availability_calendar():
    st.markdown("### 📅 Availability Calendar")
    components.html("""
    <script src="https://static.elfsight.com/platform/platform.js" async></script>
    <div class="elfsight-app-7597c436-6d99-481d-bece-895bfd83a14a" data-elfsight-app-lazy></div>
    """, height=800)

# Call this function from sidebar() or main() to show it globally

def ksheersagar_dashboard():
    st.subheader("🐄 Ksheersagar 2.0 Dashboard")

    st.markdown("### 🌍 Geographic Dashboard")
    components.iframe(
        src="https://datawrapper.dwcdn.net/01h0U/1/",
        height=600,
        width=800,
        scrolling=True,
    )
def pmu_dashboard(user):
    db = get_db()
    st.subheader("📋 PMU Work Plans and Targets")

    # Fetch all once at top
    workplans = db.query(WorkPlan).filter_by(supervisor_id=user.id).all()
    targets = db.query(Target).filter_by(employee_id=user.id).all()
    schedules = db.query(Schedule).filter_by(employee_id=user.id).all()

    # Summary View
    with st.expander("📌 Summary View"):
        st.markdown("### 🧾 Progress Overview")

        # Workplans Summary
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
            )
        )

        # Targets Summary
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
            )
        )

        # Schedules
        st.write("#### Schedules")
        schedule_df = pd.DataFrame(
            [
                {
                    "Date": s.date,
                    "Start": s.start_time,
                    "End": s.end_time,
                    "GMeet": s.gmeet_link or "N/A",
                }
                for s in schedules
            ]
        )
        if not schedule_df.empty:
            st.dataframe(schedule_df)
        else:
            st.info("No schedules available.")

    # Add New Work Plan
    with st.expander("➕ Add New Work Plan"):
        with st.form("work_plan_form"):
            title = st.text_input("Work Plan Title")
            details = st.text_area("Details")
            deadline = st.date_input("Deadline")
            status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
            workstream_titles = [
                ws.title
                for ws in db.query(WorkStream).filter_by(employee_id=user.id).all()
            ]
            workstream = st.selectbox(
                "Workstream", ["Select..."] + workstream_titles, index=0
            )

            submitted = st.form_submit_button("Save Work Plan")
            if submitted:
                if workstream != "Select...":
                    workstream_obj = (
                        db.query(WorkStream)
                        .filter_by(title=workstream, employee_id=user.id)
                        .first()
                    )
                    new_workplan = WorkPlan(
                        title=title,
                        details=details,
                        deadline=str(deadline),
                        status=status,
                        supervisor_id=user.id,
                        workstream_id=workstream_obj.id,
                    )
                    db.add(new_workplan)
                    db.commit()
                    st.success("✅ Work Plan saved successfully!")
                    st.rerun()
                else:
                    st.error("Please select a workstream.")

    # Add New Target
    with st.expander("➕ Add New Target"):
        with st.form("target_form"):
            description = st.text_area("Target Description")
            deadline = st.date_input("Target Deadline")
            status = st.selectbox("Target Status", ["Not Started", "In Progress", "Completed"])

            if st.form_submit_button("Save Target"):
                new_target = Target(
                    description=description,
                    deadline=str(deadline),
                    status=status,
                    employee_id=user.id,
                )
                db.add(new_target)
                db.commit()
                st.success("✅ Target saved.")
                st.rerun()

    # Display Work Plans
    st.subheader("📌 Your Work Plans and Targets")

    if workplans:
        st.write("### Work Plans")
        for plan in workplans:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**Title**: {plan.title}")
                st.markdown(f"**Details**: {plan.details}")
                st.markdown(f"**Deadline**: {plan.deadline}")
            with col2:
                st.markdown(f"**Status**: {plan.status}")
            with col3:
                with st.form(key=f"workplan_progress_{plan.id}"):
                    new_status = st.selectbox(
                        "Update Status",
                        ["Not Started", "In Progress", "Completed"],
                        index=["Not Started", "In Progress", "Completed"].index(
                            plan.status
                        ),
                    )
                    submit_progress = st.form_submit_button("Update Progress")
                    if submit_progress:
                        plan.status = new_status
                        db.commit()
                        st.success("Progress updated!")
                        st.rerun()
    else:
        st.info("No work plans found.")

    # Display Targets
    if targets:
        st.write("### Targets")
        for tgt in targets:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**Target**: {tgt.description}")
                st.markdown(f"**Deadline**: {tgt.deadline}")
            with col2:
                st.markdown(f"**Status**: {tgt.status}")
            with col3:
                with st.form(key=f"target_progress_{tgt.id}"):
                    new_status = st.selectbox(
                        "Update Status",
                        ["Not Started", "In Progress", "Completed"],
                        index=["Not Started", "In Progress", "Completed"].index(
                            tgt.status
                        ),
                    )
                    submit_progress = st.form_submit_button("Update Progress")
                    if submit_progress:
                        tgt.status = new_status
                        db.commit()
                        st.success("Progress updated!")
                        st.rerun()
    else:
        st.info("No targets found.")

# Kanban Board Functions
KANBAN_DB = "kanban.db"

def get_kanban_board():
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
        board[status].append(task)
    conn.close()
    return board

def add_kanban_task(status, task):
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
            for task in tasks:
                st.success(f"✅ {task}")
    with st.form("Add Kanban Task"):
        task = st.text_input("Task Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        if st.form_submit_button("Add Task") and task:
            add_kanban_task(status, task)
            st.rerun()

# To-Do List Functions
def display_todo():
    st.subheader("📝 To-Do List")
    if "todo_list" not in st.session_state:
        st.session_state.todo_list = []

    with st.form("Add To-Do Item"):
        todo_item = st.text_input("Enter a to-do item:")
        if st.form_submit_button("Add"):
            st.session_state.todo_list.append(todo_item)
            st.rerun()

    for i, item in enumerate(st.session_state.todo_list):
        st.write(f"{i+1}. {item}")

def manage_programs():
    db = get_db()
    st.subheader("Manage Programs")

    # Add New Program
    with st.form("add_program_form"):
        name = st.text_input("Program Name")
        description = st.text_area("Program Description")
        status = st.selectbox("Program Status", ["Active", "Inactive"])

        if st.form_submit_button("Add Program"):
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
            except IntegrityError:
                db.rollback()
                st.error(f"Program '{name}' already exists.")

    # Display Existing Programs
    st.subheader("Existing Programs")
    programs = db.query(Program).all()
    if programs:
        for program in programs:
            st.markdown(
                f"**Name**: {program.name} | **Description**: {program.description} | **Status**: {program.status}"
            )
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
            expected_plants = total_plants - expected_plants
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


def live_dashboard():
    db = get_db()
    st.subheader("📈 Live Monitoring Dashboard")

    # Fetch farmer data
    farmer_data = db.query(FarmerData).all()
    if not farmer_data:
        st.warning("No farmer data available.")
        return

    # Prepare data for display
    total_farmers = len(farmer_data)
    total_cows = sum(farmer.number_of_cows for farmer in farmer_data)
    total_yield = sum(farmer.yield_per_cow for farmer in farmer_data)
    yield_per_cow = total_yield / total_cows if total_cows > 0 else 0

    # Display metrics
    st.metric("🧮 Total Farmers", total_farmers)
    st.metric("🐄 Total Cows", total_cows)
    st.metric("🍼 Total Yield (L)", total_yield)
    st.metric("📊 Yield per Cow (L)", round(yield_per_cow, 2))

    # Create a DataFrame for detailed view
    df = pd.DataFrame(
        {
            "Farmer Name": [farmer.farmer_name for farmer in farmer_data],
            "Number of Cows": [farmer.number_of_cows for farmer in farmer_data],
            "Yield per Cow (L)": [farmer.yield_per_cow for farmer in farmer_data],
        }
    )

    st.subheader("📊 Farmer Data Overview")
    st.dataframe(df)

    # Data Analytics Placeholder
    st.subheader("📈 Data Analytics")
    st.write("This section will display data analytics based on the farmer data.")
    # In a real implementation, you would perform data analysis here
    # and display the results using Streamlit charts or tables.
    # Example:
    # fig = px.scatter(df, x="Number of Cows", y="Yield per Cow (L)", title="Yield vs. Cow Count")
    # st.plotly_chart(fig)


def heritage_dashboard():
    st.subheader("🏛️ Heritage Dashboard")
    # Embed the Datawrapper map iframe
    st.markdown("### 🌍 Geographic Dashboard")
    components.iframe(
        src="https://datawrapper.dwcdn.net/jjDlA/1/",
        height=600,
        width=800,
        scrolling=True,
    )
    # KPI Data
    kpi_data = {
        "Milk Received (Lt per day)": [33000, 45000, 15000, 5000, 5000, 5000, 7500, 7500],
        "#MCCs": [137, 70, 67, 22, 22, 22, 34, 34],
        "#DFs": [3, 10, 10, 3, 3, 3, 5, 5],
        "#HPCs (VLCC)": [67, 134, 67, 22, 22, 22, 34, 34],
        "Total MCCs": [207, 214, 5, 2, 2, 2, 3, 3],
        "Routes": [17, 17, 4, 1.0, 1.0, 2, 2, 2],
        "#Heritage Pourers": [1010, 2546, 1536, 512, 512, 512, 768, 768],
        "# Other farmers(from MCCs)": [2268, 1050, -1218, -406, -406, -406, -609, -609],
        "Total Active Farmers": [3278, 3596, 3596, 1199, 1199, 1199, 1798, 1798],
        "Productivity (in lts per day per farmer)": [10, 13, 13, 10, 11, 12, 13, 13],
        "SNF (Baseline)%": [8.1, 8.1, 8.15, 8.15, 8.2, 8.25, 8.30, 8.30],
        "Fat (Baseline)%": [4, 4.3, 0.2, 4.10, 4.15, 4.20, 4.3, 4.3],
        "Compliance % (with Antibiotics and Aflatoxins)": [50, 70, 70, 23, 23, 23, 35, 35],
    }
    kpi_df = pd.DataFrame(kpi_data)
    kpi_df.index = ["Baseline", "Target", "Progress", "Q1", "Q2", "Q3", "Q4", "Q5"]

    # Display KPIs
    st.subheader("Key Performance Indicators")
    st.dataframe(kpi_df)

    # Sample Chart (Milk Received)
    fig_milk = px.line(
        kpi_df,
        x=kpi_df.index,
        y="Milk Received (Lt per day)",
        title="Milk Received Over Time",
    )
    st.plotly_chart(fig_milk, use_container_width=True)

    # Sample Bar Chart (Total Active Farmers)
    fig_farmers = px.bar(
        kpi_df,
        x=kpi_df.index,
        y="Total Active Farmers",
        title="Total Active Farmers",
    )
    st.plotly_chart(fig_farmers, use_container_width=True)

    st.markdown("---")
    st.markdown(
        """
        
            
                
            
        
        """,
        unsafe_allow_html=True,
    )
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

    # Embed the Datawrapper map iframe
    st.markdown("### 🌍 Geographic Dashboard")
    components.iframe(
        src="https://datawrapper.dwcdn.net/01h0U/1/",
        height=600,
        width=800,
        scrolling=True,
    )
    # KPI Data (Replace with actual data)
    kpi_data = {
        "Total Milk Collection (Liters)": [100000, 120000, 110000, 115000, 125000],
        "Number of Active Farmers": [500, 550, 520, 530, 560],
        "Average Milk Yield per Farmer (Liters)": [200, 210, 211, 217, 223],
        "AI Coverage (%)": [60, 62, 63, 65, 67],
        "Animal Health Checkups": [150, 160, 155, 165, 170],
    }
    kpi_df = pd.DataFrame(kpi_data)
    kpi_df.index = ["Jan", "Feb", "Mar", "Apr", "May"]

    # Display KPIs
    st.subheader("Key Performance Indicators")
    st.dataframe(kpi_df)

    # Sample Chart (Total Milk Collection)
    fig_milk = px.line(
        kpi_df,
        x=kpi_df.index,
        y="Total Milk Collection (Liters)",
        title="Total Milk Collection Over Time",
    )
    st.plotly_chart(fig_milk, use_container_width=True)

    # Sample Bar Chart (Number of Active Farmers)
    fig_farmers = px.bar(
        kpi_df,
        x=kpi_df.index,
        y="Number of Active Farmers",
        title="Number of Active Farmers",
    )

    st.plotly_chart(fig_farmers, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("🧬 Breed Diversity", "21 types")
    col2.metric("🧮 Avg Daily Milk (L)", "9.3")
    col3.metric("🔁 AI Coverage (%)", "67.4")

    st.markdown("---")

    st.markdown(
        """
    
        
            
        
    
    """,
        unsafe_allow_html=True,
    )

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


def settings():
    db = get_db()
    st.subheader("⚙️ Settings")

    # Initialize settings in session state if not already done
    if "settings" not in st.session_state:
        st.session_state.settings = {
            "theme": "Light",
            "notification": "Email",
            "language": "English",
            "project_timeline": "Weekly",
            "units": "Hours",
            "progress_metric": "% Complete",
            "role": "Admin",
            "report_frequency": "Weekly",
            "report_format": "PDF",
            "auto_email_summary": False,
        }

    # User Preferences
    st.markdown("### User Preferences")
    theme = st.selectbox(
        "Theme",
        ["Light", "Dark"],
        index=["Light", "Dark"].index(st.session_state.settings["theme"]),
    )
    notification = st.selectbox(
        "Notification Settings",
        ["Email", "In-app", "None"],
        index=["Email", "In-app", "None"].index(st.session_state.settings["notification"]),
    )
    language = st.selectbox(
        "Language Preferences",
        ["English", "Spanish", "French"],
        index=["English", "Spanish", "French"].index(st.session_state.settings["language"]),
    )

    # Project Preferences
    st.markdown("### Project Preferences")
    project_timeline = st.selectbox(
        "Default Project Timeline",
        ["Daily", "Weekly", "Monthly"],
        index=["Daily", "Weekly", "Monthly"].index(st.session_state.settings["project_timeline"]),
    )
    units = st.selectbox(
        "Units of Measurement",
        ["Hours", "Days", "Cost Units"],
        index=["Hours", "Days", "Cost Units"].index(st.session_state.settings["units"]),
    )
    progress_metric = st.selectbox(
        "Default Progress Tracking Metrics",
        ["% Complete", "Milestones"],
        index=["% Complete", "Milestones"].index(st.session_state.settings["progress_metric"]),
    )

    # Report Configuration
    st.markdown("### Report Configuration")
    report_frequency = st.selectbox(
        "Default Report Frequency",
        ["Weekly", "Bi-weekly", "Monthly"],
        index=["Weekly", "Bi-weekly", "Monthly"].index(st.session_state.settings["report_frequency"]),
    )
    report_format = st.selectbox(
        "Report Formats",
        ["PDF", "Excel", "JSON"],
        index=["PDF", "Excel", "JSON"].index(st.session_state.settings["report_format"]),
    )
    auto_email_summary = st.checkbox(
        "Auto-email Summary", value=st.session_state.settings["auto_email_summary"]
    )

    # Change Password Section
    st.markdown("### Change Password")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    if st.button("Change Password"):
        if new_password == confirm_password:
            user = db.query(Employee).filter_by(id=st.session_state.user.id).first()
            user.password = new_password
            db.commit()
            st.success("Password changed successfully!")
        else:
            st.error("Passwords do not match.")

    if st.button("Save Settings"):
        st.session_state.settings.update(
            {
                "theme": theme,
                "notification": notification,
                "language": language,
                "project_timeline": project_timeline,
                "units": units,
                "progress_metric": progress_metric,
                "role": role,
                "report_frequency": report_frequency,
                "report_format": report_format,
                "auto_email_summary": auto_email_summary,
            }
        )
        st.success("Settings saved successfully!")


def reports():
    st.subheader("📊 Reports")
    st.markdown("### Weekly Document Summary")

    # Initialize summary filename
    summary_filename = ""

    # Generate a weekly summary document
    if st.button("Generate Weekly Summary"):
        summary_data = {
            "Project": [],
            "Progress Overview": [],
            "Milestones Completed": [],
            "Delays": [],
            "Blockers": [],
            "Action Items": [],
        }

        # Simulate data generation
        for i in range(1, 4):
            summary_data["Project"].append(f"Project {i}")
            summary_data["Progress Overview"].append(f"{i * 10}%")
            summary_data["Milestones Completed"].append(f"{i} milestones")
            summary_data["Delays"].append(f"{i} delays")
            summary_data["Blockers"].append(f"{i} blockers")
            summary_data["Action Items"].append(f"Action item {i}")

        summary_df = pd.DataFrame(summary_data)
        summary_filename = f"weekly_summary_{date.today()}.csv"
        summary_df.to_csv(summary_filename, index=False)
        st.success(f"Weekly summary generated: {summary_filename}")

    # Display the summary if it exists
    if summary_filename and os.path.exists(summary_filename):
        summary_df = pd.read_csv(summary_filename)
        st.dataframe(summary_df)


def scheduling(user):
    db = get_db()
    st.subheader("🗓️ Employee Scheduling")

    with st.form("add_schedule"):
        schedule_date = st.date_input("Schedule Date", date.today())
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        # GMeet Placeholder
        generate_gmeet = st.checkbox("Generate GMeet Link?")
        gmeet_link = None
        if generate_gmeet:
            gmeet_link = "https://meet.google.com/placeholder"  # Placeholder link
            st.write(f"GMeet Link (Placeholder): {gmeet_link}")

        if st.form_submit_button("Add Schedule"):
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

    st.subheader("Your Schedules")
    schedules = db.query(Schedule).filter_by(employee_id=user.id).all()
    for schedule in schedules:
        st.markdown(
            f"**Date**: {schedule.date} | **Start**: {schedule.start_time} | **End**: {schedule.end_time} | **GMeet Link**: {schedule.gmeet_link if schedule.gmeet_link else 'N/A'}"
        )


def field_team_management():
    db = get_db()
    st.subheader("👥 Field Team Management")

    # Add Field Team
    with st.form("add_field_team"):
        team_name = st.text_input("Field Team Name")
        if st.form_submit_button("Add Field Team"):
            if team_name:
                new_team = FieldTeam(name=team_name, pmu_id=st.session_state.user.id)
                db.add(new_team)
                db.commit()
                st.success(f"Field Team '{team_name}' added successfully!")
            else:
                st.error("Field Team Name cannot be empty.")

    # Display Existing Field Teams
    st.subheader("Existing Field Teams")
    field_teams = db.query(FieldTeam).filter_by(pmu_id=st.session_state.user.id).all()
    if field_teams:
        for team in field_teams:
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**Team Name**: {team.name}")
            if col2.button(f"Delete {team.name}", key=team.id):
                db.delete(team)
                db.commit()
                st.success(f"Field Team '{team.name}' deleted successfully!")
                st.rerun()
    else:
        st.write("No field teams available.")

    # Field Team API Integration Placeholder
    st.subheader("🌐 Field Team API Integration")
    st.write("This section will integrate with a Field Team Management API.")
    # In a real implementation, you would use the 'requests' library
    # to make API calls to a service like Trello, Asana, or a custom API.
    # Example:
    # api_url = "https://api.example.com/field_teams"
    # response = requests.get(api_url)
    # if response.status_code == 200:
    #     teams_data = response.json()
    #     st.write(teams_data)
    # else:
    #     st.error("Failed to fetch field team data from the API.")


def training():
    st.subheader("📚 Training Module")
    st.write("This section provides training materials and resources.")

    # Upload Training Content
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
            save_dir = f"training_materials/{selected_program.lower()}/{selected_category.lower()}"
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            file_path = os.path.join(save_dir, uploaded_file.name)

            if not is_valid_file(uploaded_file.name, selected_category):
                st.error(f"❌ Invalid file type for the **{selected_category}** category.")
            else:
                if st.button("Upload"):
                    try:
                        st.write(f"Simulating upload of '{uploaded_file.name}' to Google Drive...")
                        st.write(f"File would be saved to: {save_dir} in Google Drive.")

                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(
                            f"✅ File '{uploaded_file.name}' uploaded successfully to {save_dir} (Simulated Google Drive)!"
                        )
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {e}")
        else:
            st.error("Please select a program and category before uploading.")

    # Display Uploaded Training Content
    st.header("📂 Uploaded Training Content")
    for program in ["Cotton", "Dairy"]:
        for category in ["Presentations", "Videos", "Audios", "Quizzes"]:
            folder_path = Path(f"training_materials/{program.lower()}/{category.lower()}")
            if folder_path.exists() and any(folder_path.iterdir()):
                st.subheader(f"{program} - {category}")
                for file in os.listdir(folder_path):
                    st.markdown(f"- {file}")


def is_valid_file(file_name, category):
    valid_extensions = {
        "Presentations": [".pptx"],
        "Videos": [".mp4"],
        "Audios": [".mp3"],
        "Quizzes": [".xlsx", ".png", ".jpg", ".jpeg"],
    }
    extra_extensions = [".xlsx", ".png", ".jpg", ".jpeg"]
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_extension in extra_extensions:
        return True
    if category in valid_extensions and file_extension in valid_extensions[category]:
        return True
    return False


# Placeholder Google Drive Functionality
def google_drive():
    st.subheader("Google Drive Integration (Placeholder)")
    st.write("This section will eventually integrate with Google Drive.")

    if st.button("List Files (Placeholder)"):
        st.write("Simulating listing files from Google Drive...")
        st.write("- File 1.txt")
        st.write("- File 2.pdf")
        st.write("- File 3.docx")


# Team Chat Functions
CHAT_DB = "chat.db"


def get_team_chat():
    conn = sqlite3.connect(CHAT_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """
    )
    conn.commit()
    cursor.execute("SELECT user, message FROM chat ORDER BY id DESC LIMIT 10")
    chats = cursor.fetchall()
    conn.close()
    return chats[::-1]  # Reverse to show oldest first


def add_chat_message(user, message):
    conn = sqlite3.connect(CHAT_DB)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat (user, message) VALUES (?, ?)", (user, message))
    conn.commit()
    conn.close()


def team_chat():
    st.subheader("💬 Team Chat")
    chats = get_team_chat()
    for user, message in chats:
        st.markdown(f"**{user}**: {message}")

    with st.form("Send Chat Message"):
        user = st.text_input(
            "Your Name", value=st.session_state.user.name if "user" in st.session_state else ""
        )
        message = st.text_input("Message")
        if st.form_submit_button("Send") and user and message:
            add_chat_message(user, message)
            st.rerun()


# Placeholder Gmail Functionality
def email():
    st.subheader("Email Integration (Placeholder)")
    st.write("This section will eventually integrate with Gmail.")

    with st.form("send_email_form"):
        recipient = st.text_input("Recipient Email")
        subject = st.text_input("Subject")
        body = st.text_area("Body")
        submitted = st.form_submit_button("Send Email (Placeholder)")

        if submitted:
            st.write(f"Simulating sending email to {recipient} with subject '{subject}'.")


def calendar_view(user):
    db = get_db()
    st.subheader("📆 Calendar Task Manager")

    selected_date = st.date_input("Select a date", date.today())

    # Add task form
    with st.form("add_calendar_task"):
        task_text = st.text_input("Task for selected date")
        if st.form_submit_button("Add Task"):
            if task_text:
                new_task = CalendarTask(employee_id=user.id, date=selected_date, task=task_text)
                db.add(new_task)
                db.commit()
                st.success("Task added!")
                st.rerun()

    # Fetch and show tasks for selected date
    st.markdown(f"### 📝 Tasks on {selected_date.strftime('%b %d, %Y')}")
    tasks = db.query(CalendarTask).filter_by(employee_id=user.id, date=selected_date).all()

    if not tasks:
        st.info("No tasks for this day.")
    else:
        for t in tasks:
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.write(f"- {t.task}")
            with col2:
                if st.button("❌", key=f"del_{t.id}"):
                    db.delete(t)
                    db.commit()
                    st.experimental_rerun()

     # Calendar Widget with availability display
    st.markdown("### 📅 Availability Calendar")
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
                disable: ["2023-07-27", "2023-08-11"], // Not available
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
                    window.parent.postMessage({ type: 'SELECTED_DATE', value: dateStr }, '*');
                }
            });
        </script>
    </body>
    """, height=400)

    # Add a new meeting
    with st.form("add_meeting"):
        meeting_date = st.date_input("Meeting Date", date.today())
        meeting_start_time = st.time_input("Meeting Start Time")
        meeting_end_time = st.time_input("Meeting End Time")
        meeting_description = st.text_input("Meeting Description")

        if st.form_submit_button("Add Meeting"):
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


def monthly_meeting(user):
    db = get_db()
    st.subheader("📅 Monthly Meeting Preparation")

    # Get the current month and year
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Display the current month and year
    st.write(f"### Preparing for: {calendar.month_name[current_month]}, {current_year}")

    # Fetch the user's work plans
    workplans = db.query(WorkPlan).filter_by(supervisor_id=user.id).all()

    # Display work plans and their progress
    if workplans:
        st.write("### Your Work Plans and Progress")
        for plan in workplans:
            st.write(f"**Title**: {plan.title}")
            st.write(f"**Details**: {plan.details}")
            st.write(f"**Deadline**: {plan.deadline}")
            st.write(f"**Status**: {plan.status}")

            # Add a form to update the work plan's progress
            with st.form(key=f"workplan_progress_{plan.id}"):
                new_status = st.selectbox(
                    "Update Status",
                    ["Not Started", "In Progress", "Completed"],
                    index=["Not Started", "In Progress", "Completed"].index(plan.status),
                )
                progress_notes = st.text_area(
                    "Progress Notes", value=""
                )  # Add a text area for progress notes
                submit_progress = st.form_submit_button("Update Progress")

                if submit_progress:
                    plan.status = new_status
                    db.commit()
                    st.success("Progress updated!")
                    st.rerun()
    else:
        st.info("No work plans found.")

    # Add a section for meeting agenda items
    st.write("### Meeting Agenda Items")
    agenda_items = [
        "Review of last month's goals",
        "Progress on current work plans",
        "Discussion of any roadblocks",
        "Setting goals for the next month",
    ]
    for item in agenda_items:
        st.write(f"- {item}")

    # Add a section for additional notes
    st.write("### Additional Notes")
    additional_notes = st.text_area("Enter any additional notes for the meeting", value="")

    # Add a button to generate a meeting summary
    if st.button("Generate Meeting Summary"):
        summary = f"""
        ## Meeting Summary: {calendar.month_name[current_month]}, {current_year}

        ### Employee: {user.name}

        ### Work Plans and Progress:
        """
        if workplans:
            for plan in workplans:
                summary += f"""
                - **Title**: {plan.title}
                  - **Details**: {plan.details}
                  - **Deadline**: {plan.deadline}
                  - **Status**: {plan.status}
                """
        else:
            summary += "No work plans found."

        summary += f"""
        ### Agenda Items:
        """
        for item in agenda_items:
            summary += f"- {item}\n"

        summary += f"""
        ### Additional Notes:
        {additional_notes}
        """

        st.write("### Meeting Summary")
        st.write(summary)


def main():
    db = get_db()

    # Initialize session state for user
    if "user" not in st.session_state:
        st.session_state.user = None

    # Preload users and programs
    preload_users()
    preload_programs()

    # Display the login section if no user is logged in
    if st.session_state.user is None:
        st.title("🔐 Login")
        display_notice()
        all_users = db.query(Employee).all()
        emails = [u.email for u in all_users]
        selected = st.selectbox("Select your email", ["Select..."] + emails, index=0)

        if selected != "Select...":
            user = db.query(Employee).filter_by(email=selected).first()
            password = st.text_input("Password", type="password", key="password")
            if user and user.password == password:
                st.session_state.user = user
                st.success(f"Welcome, {user.name}!")
            elif user and user.password != password:
                st.error("Incorrect password.")

    # Display the dashboard if a user is logged in
    if st.session_state.user is not None:
        selected_tab = sidebar()
        if selected_tab == "dashboard":
            dashboard(st.session_state.user)
        elif selected_tab == "manage_programs":
            manage_programs()
        elif selected_tab == "scheduling":
            scheduling(st.session_state.user)
        elif selected_tab == "field_team_management":
            field_team_management()
        elif selected_tab == "live_dashboard":
            live_dashboard()
        elif selected_tab == "reports":
            reports()
        elif selected_tab == "settings":
            settings()
        elif selected_tab == "saksham_dashboard":
            saksham_dashboard()
        elif selected_tab == "training":
            training()
        elif selected_tab == "google_drive":
            google_drive()
        elif selected_tab == "team_chat":
            team_chat()
        elif selected_tab == "email":
            email()
        elif selected_tab == "calendar_view":
            calendar_view(st.session_state.user)
        elif selected_tab == "monthly_meeting":
            monthly_meeting(st.session_state.user)
        elif selected_tab == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")


if __name__ == "__main__":
    main()
