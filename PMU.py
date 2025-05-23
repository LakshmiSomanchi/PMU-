import streamlit as st
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
from datetime import date
import os
from pathlib import Path  # Import Path for directory creation

# Set Streamlit page config (must be first)
st.set_page_config(page_title="PMU Tracker", layout="wide")

# Custom CSS with sidebar background image and global page background image
st.markdown("""
    <style>
        body {
            background-image: url("https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/light%20pink%20background%20with%20real%20green%20leaves%20in%20the%20right%20side_corner.jpg");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
        }

        .stApp {
            background-color: rgba(255, 255, 255, 0.1); /* Increased transparency for better visibility */
        }

        section[data-testid="stSidebar"] > div:first-child {
            background-image: url("https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/light%20green%20plain%20background.jpg");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
            color: white;
            padding: 20px;
            border-radius: 0 10px 10px 0;
        }
       
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] h5,
        section[data-testid="stSidebar"] h6,
        section[data-testid="stSidebar"] .stRadio label {
            color: white !important;
        }

        h1, h2, h3, h4 {
            color: #003566;
        }

        .streamlit-expanderHeader {
            background-color: #dceefb;
            border: 1px solid #cce0ff;
            border-radius: 10px;
        }

        .stButton > button {
            background-color: #0077b6;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1em;
        }
        .stButton > button:hover {
            background-color: #0096c7;
        }

        .stDataFrame {
            background-color: #ffffff;
            border: 5px solid #ccc;
        }

        .stTabs [role="tab"] {
            background-color: #edf6ff;
            padding: 10px;
            border-radius: 10px 10px 0 0;
            margin-right: 5px;
            border: 1px solid #b6d4fe;
        }

        .stTabs [role="tab"][aria-selected="true"] {
            background-color: #0077b6;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# SQLite + SQLAlchemy setup
DATABASE_URL = "sqlite:///pmu.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Models
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)  # Added password field
    workstreams = relationship("WorkStream", back_populates="employee")
    targets = relationship("Target", back_populates="employee")
    programs = relationship("Program", back_populates="employee")
    schedules = relationship("Schedule", back_populates="employee")
    workplans = relationship("WorkPlan", back_populates="supervisor")  # Added relationship for workplans
    field_teams = relationship("FieldTeam", back_populates="pmu")  # Relationship to Field Teams

class WorkStream(Base):
    __tablename__ = "workstreams"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)  # New field for category
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
    supervisor_id = Column(Integer, ForeignKey("employees.id"))  # Added supervisor relationship
    supervisor = relationship("Employee", back_populates="workplans")  # Relationship to Employee

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
    description = Column(Text)  # New field for description
    status = Column(String, default="Active")  # New field for status
    employee_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="programs")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    employee = relationship("Employee", back_populates="schedules")

class FieldTeam(Base):
    __tablename__ = "field_teams"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    pmu_id = Column(Integer, ForeignKey("employees.id"))  # PMU supervisor
    pmu = relationship("Employee", back_populates="field_teams")
    tasks = relationship("Task", back_populates="field_team")  # Relationship to tasks assigned to the field team

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
    yield_per_cow = Column(Float)  # Yield per cow
    date = Column(String)  # Date of the record

# Drop all tables and recreate them
Base.metadata.drop_all(bind=engine)  # This will drop all tables
Base.metadata.create_all(bind=engine)  # This will recreate the tables

# Initialize session state for user if not already done
if "user" not in st.session_state:
    st.session_state.user = None

# Preloaded users
preloaded_users = [
    ("Somanchi", "rsomanchi@tns.org", "password1"),
    ("Ranu", "rladdha@tns.org", "password2"),
    ("Pari", "paris@tns.org", "password3"),
    ("Muskan", "mkaushal@tns.org", "password4"),
    ("Rupesh", "rmukherjee@tns.org", "password5"),
    ("Shifali", "shifalis@tns.org", "password6"),
    ("Pragya Bharati", "pbharati@tns.org", "password7")
]

def get_db():
    return SessionLocal()

def preload_users():
    db = get_db()
    for name, email, password in preloaded_users:
        try:
            db.add(Employee(name=name, email=email, password=password))
            db.commit()
        except IntegrityError:
            db.rollback()

def display_notice():
    st.markdown("""
        <style>
            .notice {
                background-color: rgba(255, 255, 255, 0.3); /* transparent white */
                padding: 5px;
                border-radius: 15px;
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
            <p>Target-setting and progress meetings will be documented within the system</p>
            <h3>Communication Guidelines</h3>
            <p>Any technical issues or submission challenges should be reported within the window</p>
            <p>Use official channels for queries to ensure swift response</p>
            <p>We appreciate your cooperation in making this system a success. Let’s keep progress transparent, teamwork tight, and targets in sight.</p>
            <p>For questions or support, please contact rsomanchi@tns.org.</p>
            <p>Let the tracking begin – elegantly, efficiently, and with a touch of excellence.</p>
            <p>On behalf of the Coordination Team</p>
        </div>
    """, unsafe_allow_html=True)

def sidebar():
    st.sidebar.title("Navigation")
    menu_options = {
        "Dashboard": "dashboard",
        "Manage Programs": "manage_programs",
        "Reports": "reports",
        "Employee Scheduling": "scheduling",
        "Field Team Management": "field_team_management",  # New section for field teams
        "Live Dashboard": "live_dashboard",  # New section for live dashboard
        "Settings": "settings",
        "Logout": "logout"
    }
    selection = st.sidebar.radio("Go to", list(menu_options.keys()))
    return menu_options[selection]

def dashboard(user):
    db = get_db()
    st.markdown("<<h1 style='text-align:center; color:#1a73e8;'>🚀 Project Management Dashboard</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("### Logged in as")
    st.sidebar.success(user.name)
    if st.sidebar.button("🔓 Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    # Tabs for different dashboards
    dashboard_tabs = st.tabs(["Field Team Dashboard", "PMU Dashboard", "Heritage Dashboard", "Ksheersagar Dashboard", "SAKSHAM Dashboard"])

    for tab in dashboard_tabs:
        with tab:
            st.subheader(f"📊 Progress")
            # Here you can add specific content for each dashboard
            # For example, you can display progress for each section
            st.write("This is where you can display progress and other metrics.")

            # Example of displaying employee progress
            employees = db.query(Employee).all()
            for emp in employees:
                st.markdown(f"**{emp.name}**:Status")  # Replace with actual progress data

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
    total_yield = sum(farmer.yield_per_cow for farmer in farmer_data)  # Assuming yield_per_cow is daily yield
    yield_per_cow = total_yield / total_cows if total_cows > 0 else 0

    # Display metrics
    st.metric("🧮 Total Farmers", total_farmers)
    st.metric("🐄 Total Cows", total_cows)
    st.metric("🍼 Total Yield (L)", total_yield)
    st.metric("📊 Yield per Cow (L)", round(yield_per_cow, 2))

    # Create a DataFrame for detailed view
    df = pd.DataFrame({
        "Farmer Name": [farmer.farmer_name for farmer in farmer_data],
        "Number of Cows": [farmer.number_of_cows for farmer in farmer_data],
        "Yield per Cow (L)": [farmer.yield_per_cow for farmer in farmer_data]
    })

    st.subheader("📊 Farmer Data Overview")
    st.dataframe(df)

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
            "role": "Admin",  # Default role
            "report_frequency": "Weekly",
            "report_format": "PDF",
            "auto_email_summary": False
        }

    # User Preferences
    st.markdown("### User Preferences")
    theme = st.selectbox("Theme", ["Light", "Dark"], index=["Light", "Dark"].index(st.session_state.settings["theme"]))
    notification = st.selectbox("Notification Settings", ["Email", "In-app", "None"], index=["Email", "In-app", "None"].index(st.session_state.settings["notification"]))
    language = st.selectbox("Language Preferences", ["English", "Spanish", "French"], index=["English", "Spanish", "French"].index(st.session_state.settings["language"]))

    # Project Preferences
    st.markdown("### Project Preferences")
    project_timeline = st.selectbox("Default Project Timeline", ["Daily", "Weekly", "Monthly"], index=["Daily", "Weekly", "Monthly"].index(st.session_state.settings["project_timeline"]))
    units = st.selectbox("Units of Measurement", ["Hours", "Days", "Cost Units"], index=["Hours", "Days", "Cost Units"].index(st.session_state.settings["units"]))
    progress_metric = st.selectbox("Default Progress Tracking Metrics", ["% Complete", "Milestones"], index=["% Complete", "Milestones"].index(st.session_state.settings["progress_metric"]))

    # Access Control
    st.markdown("### Access Control")
    role = st.selectbox("Role-based Access Permissions", ["Admin", "Manager", "Viewer"], index=["Admin", "Manager", "Viewer"].index(st.session_state.settings["role"]))

    # Report Configuration
    st.markdown("### Report Configuration")
    report_frequency = st.selectbox("Default Report Frequency", ["Weekly", "Bi-weekly", "Monthly"], index=["Weekly", "Bi-weekly", "Monthly"].index(st.session_state.settings["report_frequency"]))
    report_format = st.selectbox("Report Formats", ["PDF", "Excel", "JSON"], index=["PDF", "Excel", "JSON"].index(st.session_state.settings["report_format"]))
    auto_email_summary = st.checkbox("Auto-email Summary", value=st.session_state.settings["auto_email_summary"])

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
        st.session_state.settings.update({
            "theme": theme,
            "notification": notification,
            "language": language,
            "project_timeline": project_timeline,
            "units": units,
            "progress_metric": progress_metric,
            "role": role,
            "report_frequency": report_frequency,
            "report_format": report_format,
            "auto_email_summary": auto_email_summary
        })
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
            "Action Items": []
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
        if st.form_submit_button("Add Schedule"):
            db.add(Schedule(employee_id=user.id, date=str(schedule_date), start_time=str(start_time), end_time=str(end_time)))
            db.commit()
            st.success("Schedule added successfully!")

    st.subheader("Your Schedules")
    schedules = db.query(Schedule).filter_by(employee_id=user.id).all()
    for schedule in schedules:
        st.markdown(f"**Date**: {schedule.date} | **Start**: {schedule.start_time} | **End**: {schedule.end_time}")

def field_team_management():
    db = get_db()
    st.subheader("👥 Field Team Management")

    # Add Field Team
    with st.form("add_field_team"):
        team_name = st.text_input("Field Team Name")
        if st.form_submit_button("Add Field Team"):
            if team_name:
                new_team = FieldTeam(name=team_name)
                db.add(new_team)
                db.commit()
                st.success(f"Field Team '{team_name}' added successfully!")
            else:
                st.error("Field Team Name cannot be empty.")

    # Display Existing Field Teams
    st.subheader("Existing Field Teams")
    field_teams = db.query(FieldTeam).all()
    if field_teams:
        for team in field_teams:
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**Team Name**: {team.name}")
            if col2.button(f"Delete {team.name}", key=team.id):
                db.delete(team)
                db.commit()
                st.success(f"Field Team '{team.name}' deleted successfully!")
                st.experimental_rerun()  # Refresh the page to update the list
    else:
        st.write("No field teams available.")

def main():
    preload_users()
    db = get_db()
    
    # Initialize session state for user if not already done
    if "user" not in st.session_state:
        st.session_state.user = None

    # Display the login section if no user is logged in
    if st.session_state.user is None:
        st.title("🔐 Login")
        display_notice()
        all_users = db.query(Employee).all()
        emails = [u.email for u in all_users]
        selected = st.selectbox("Select your email", ["Select..."] + emails, index=0)

        if selected != "Select...":
            user = db.query(Employee).filter_by(email=selected).first()
            password = st.text_input("Password", type="password")
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
        elif selected_tab == "scheduling":
            scheduling(st.session_state.user)
        elif selected_tab == "field_team_management":
            field_team_management() 
        elif selected_tab == "live_dashboard":
            live_dashboard()  # New section for live dashboard
        elif selected_tab == "reports":
            reports()
        elif selected_tab == "settings":
            settings()
        elif selected_tab == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")

if __name__ == "__main__":
    main()
