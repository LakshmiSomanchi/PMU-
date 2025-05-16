import streamlit as st
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
from datetime import date
import os

# Set Streamlit page config (must be first)
st.set_page_config(page_title="PMU Tracker", layout="wide")

# ✅ Custom CSS with sidebar background image and global page background image
st.markdown("""
    <style>
        body {
            background-image: url("https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/refs/heads/main/3309939.jpg");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
        }

        .stApp {
            background-color: rgba(255, 255, 255, 0.75); /* Increased transparency for better visibility */
        }

        section[data-testid="stSidebar"] > div:first-child {
            background-image: url("https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/main/graphic-2d-colorful-wallpaper-with-grainy-gradients.jpg");
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
    workstreams = relationship("WorkStream", back_populates="employee")
    targets = relationship("Target", back_populates="employee")
    programs = relationship("Program", back_populates="employee")
    schedules = relationship("Schedule", back_populates="employee")

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

# Drop all tables and recreate them
Base.metadata.drop_all(bind=engine)  # This will drop all tables
Base.metadata.create_all(bind=engine)  # This will recreate the tables

if "user" not in st.session_state:
    st.session_state.user = None

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
        "auto_email_summary": False
    }

preloaded_users = [
    ("Somanchi", "rsomanchi@tns.org"),
    ("Ranu", "rladdha@tns.org"),
    ("Pari", "paris@tns.org"),
    ("Muskan", "mkaushal@tns.org"),
    ("Rupesh", "rmukherjee@tns.org"),
    ("Shifali", "shifalis@tns.org"),
    ("Pragya Bharati", "pbharati@tns.org")
]

def get_db():
    return SessionLocal()

def preload_users():
    db = get_db()
    for name, email in preloaded_users:
        try:
            db.add(Employee(name=name, email=email))
            db.commit()
        except IntegrityError:
            db.rollback()

def display_notice():
    st.markdown("""
        <style>
            .notice {
                background-color: rgba(255, 255, 255, 0.1); /* transparent white */
                padding: 5px;
                border-radius: 15px;
            }
        </style>
    """, unsafe_allow_html=True)


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
    st.sidebar.markdown("""
        <style>
            .sidebar {
                background-image: url('https://raw.githubusercontent.com/LakshmiSomanchi/PMU-/main/graphic-2d-colorful-wallpaper-with-grainy-gradients.jpg'); /* Update with your sidebar image path */
                background-size: cover;
                color: white;
                padding: 20px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    menu_options = {
        "Dashboard": "dashboard",
        "Manage Programs": "manage_programs",
        "Reports": "reports",
        "Employee Scheduling": "scheduling",
        "Settings": "settings",
        "Logout": "logout"
    }
    selection = st.sidebar.radio("Go to", list(menu_options.keys()))
    return menu_options[selection]

def dashboard(user):
    db = get_db()

    st.markdown("<h1 style='text-align:center; color:#1a73e8;'>🚀 Project Management Dashboard</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("### Logged in as")
    st.sidebar.success(user.name)
    if st.sidebar.button("🔓 Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    tabs = st.tabs(["👤 My Dashboard", "🌍 Team Overview", "📊 Tracker Report", "👥 User Management", "🎯 Target Management", "📚 Programs"])

    with tabs[0]:
        st.subheader("📌 Your Activities, Targets & Progress")
        my_ws = db.query(WorkStream).filter_by(employee_id=user.id).all()
        my_targets = db.query(Target).filter_by(employee_id=user.id).all()

        with st.expander("➕ Add Workstream"):
            with st.form("add_ws"):
                ws_title = st.text_input("Workstream Title")
                ws_desc = st.text_area("Description")
                ws_category = st.selectbox("Category", ["Cotton", "Dairy", "Water", "PMU", "Cotton Desk", "Heritage", "Abbott"])
                if st.form_submit_button("Add"):
                    db.add(WorkStream(title=ws_title, description=ws_desc, category=ws_category, employee_id=user.id))
                    db.commit()
                    st.success("Workstream added")

        with st.expander("➕ Add Workplan"):
            if my_ws:
                ws_options = {f"{ws.title}": ws.id for ws in my_ws}
                with st.form("add_wp"):
                    selected_ws = st.selectbox("Workstream", list(ws_options.keys()))
                    wp_title = st.text_input("Title")
                    wp_details = st.text_area("Details")
                    wp_deadline = st.date_input("Deadline", date.today())
                    wp_status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
                    if st.form_submit_button("Add Workplan"):
                        db.add(WorkPlan(title=wp_title, details=wp_details, deadline=str(wp_deadline), status=wp_status, workstream_id=ws_options[selected_ws]))
                        db.commit()
                        st.success("Workplan added")

        with st.expander("➕ Add Target"):
            with st.form("add_target"):
                target_desc = st.text_input("Target Description")
                target_deadline = st.date_input("Target Deadline", date.today())
                target_status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
                if st.form_submit_button("Add Target"):
                    db.add(Target(description=target_desc, deadline=str(target_deadline), status=target_status, employee_id=user.id))
                    db.commit()
                    st.success("Target added")

        for ws in my_ws:
            st.markdown(f"### 🌟 {ws.title} (Category: {ws.category})")
            st.markdown(f"_Description_: {ws.description}")
            for wp in ws.workplans:
                badge = "✅" if wp.status == "Completed" else ("🔹" if wp.status == "In Progress" else "⚪")
                badge_color = "badge-completed" if wp.status == "Completed" else ("badge-in-progress" if wp.status == "In Progress" else "badge-not-started")
                st.markdown(f"<span class='{badge_color}'>{badge}</span> **{wp.title}** | 📅 {wp.deadline} | _{wp.status}_<br>{wp.details}", unsafe_allow_html=True)

        st.subheader("🎯 Your Targets")
        for target in my_targets:
            badge = "✅" if target.status == "Completed" else ("🔹" if target.status == "In Progress" else "⚪")
            badge_color = "badge-completed" if target.status == "Completed" else ("badge-in-progress" if target.status == "In Progress" else "badge-not-started")
            st.markdown(f"<span class='{badge_color}'>{badge}</span> **{target.description}** | 📅 {target.deadline} | _{target.status}_", unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("🌐 Team Workstreams and Plans")
        all_ws = db.query(WorkStream).all()
        for ws in all_ws:
            st.markdown(f"<div style='background:#e3f2fd;padding:10px;border-left:6px solid #42a5f5;margin-bottom:10px;'>", unsafe_allow_html=True)
            st.markdown(f"<strong>{ws.title}</strong> (Category: {ws.category}) by <em>{ws.employee.name}</em><br><small>{ws.description}</small>", unsafe_allow_html=True)
            for wp in ws.workplans:
                st.markdown(f"<li><b>{wp.title}</b> | {wp.deadline} | {wp.status}<br>{wp.details}</li>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.subheader("📊 Progress Tracker Report")
        employees = db.query(Employee).all()
        report_data = []
        for emp in employees:
            total_ws = db.query(WorkStream).filter_by(employee_id=emp.id).count()
            total_wp = sum(len(ws.workplans) for ws in emp.workstreams)
            completed_wp = sum(len([wp for wp in ws.workplans if wp.status == "Completed"]) for ws in emp.workstreams)
            total_targets = len(emp.targets)
            completed_targets = sum(1 for target in emp.targets if target.status == "Completed")
            report_data.append({
                "Employee": emp.name,
                "Workstreams": total_ws,
                "Workplans": total_wp,
                "Completed Workplans": completed_wp,
                "Targets": total_targets,
                "Completed Targets": completed_targets,
                "Workplan Completion %": (completed_wp / total_wp * 100) if total_wp > 0 else 0,
                "Target Completion %": (completed_targets / total_targets * 100) if total_targets > 0 else 0
            })
        df = pd.DataFrame(report_data)
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("Employee")[["Workplans", "Completed Workplans", "Targets", "Completed Targets"]])

        # Download option for the report
        csv = df.to_csv(index=False)
        st.download_button("Download Report", csv, "team_progress_report.csv", "text/csv")

    with tabs[3]:
        st.subheader("👥 Manage Users")
        with st.form("add_user"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            if st.form_submit_button("Add"):
                try:
                    db.add(Employee(name=new_name, email=new_email))
                    db.commit()
                    st.success("User added successfully")
                except IntegrityError:
                    db.rollback()
                    st.error("User already exists")

        with st.form("remove_user"):
            remove_email = st.text_input("Email to Remove")
            if st.form_submit_button("Delete"):
                user_to_remove = db.query(Employee).filter(Employee.email == remove_email).first()
                if user_to_remove:
                    db.delete(user_to_remove)
                    db.commit()
                    st.success("User deleted")
                else:
                    st.warning("Email not found")

    with tabs[4]:
        st.subheader("🎯 Manage Targets")
        all_targets = db.query(Target).all()
        for target in all_targets:
            st.markdown(f"**{target.description}** | 📅 {target.deadline} | _{target.status}_")
            if st.button(f"Complete Target: {target.description}"):
                target.status = "Completed"
                db.commit()
                st.success(f"Target '{target.description}' marked as completed.")

    with tabs[5]:  # Programs tab
        st.subheader("📚 Manage Programs")
        
        # Initialize a session state list to hold multiple programs
        if "programs" not in st.session_state:
            st.session_state.programs = []

        # Form to add a new program
        with st.form("add_program", clear_on_submit=True):
            new_program_name = st.text_input("Program Name")
            new_program_description = st.text_area("Program Description")
            new_program_status = st.selectbox("Program Status", ["Active", "Completed", "On Hold"])
            if st.form_submit_button("Add Program"):
                if new_program_name:  # Ensure the program name is not empty
                    # Append the new program details to the session state
                    st.session_state.programs.append({
                        "name": new_program_name,
                        "description": new_program_description,
                        "status": new_program_status
                    })
                    st.success(f"Program '{new_program_name}' added to the list.")

        # Display the list of programs to be added
        st.subheader("Programs to be Added")
        for program in st.session_state.programs:
            st.markdown(f"**{program['name']}** - {program['description']} | Status: {program['status']}")

        # Button to save all programs to the database
        if st.button("Save All Programs"):
            for program in st.session_state.programs:
                try:
                    db.add(Program(name=program['name'], description=program['description'], status=program['status'], employee_id=user.id))
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    st.error(f"Program '{program['name']}' already exists.")
            st.session_state.programs = []  # Clear the list after saving
            st.success("All programs saved successfully.")

        # Display existing programs
        st.subheader("Existing Programs")
        programs = db.query(Program).filter_by(employee_id=user.id).all()
        for program in programs:
            col1, col2 = st.columns([3, 1])
            col1.markdown(f"**{program.name}** - {program.description} | Status: {program.status}")
            with col2:
                if st.button(f"Update Status for {program.name}"):
                    new_status = st.selectbox("Select New Status", ["Active", "Completed", "On Hold"], key=program.id)
                    program.status = new_status
                    db.commit()
                    st.success(f"Status for '{program.name}' updated to '{new_status}'.")

def settings():
    st.subheader("⚙️ Settings")
    
    # User Preferences
    st.markdown("### User Preferences")
    theme = st.selectbox("Theme", ["Light", "Dark"], index=0)
    notification = st.selectbox("Notification Settings", ["Email", "In-app", "None"], index=0)
    language = st.selectbox("Language Preferences", ["English", "Spanish", "French"], index=0)

    # Project Preferences
    st.markdown("### Project Preferences")
    project_timeline = st.selectbox("Default Project Timeline", ["Daily", "Weekly", "Monthly"], index=1)
    units = st.selectbox("Units of Measurement", ["Hours", "Days", "Cost Units"], index=0)
    progress_metric = st.selectbox("Default Progress Tracking Metrics", ["% Complete", "Milestones"], index=0)

    # Access Control
    st.markdown("### Access Control")
    role = st.selectbox("Role-based Access Permissions", ["Admin", "Manager", "Viewer"], index=0)
    api_key = st.text_input("API Key/Token Management", "")

    # Report Configuration
    st.markdown("### Report Configuration")
    report_frequency = st.selectbox("Default Report Frequency", ["Weekly", "Bi-weekly", "Monthly"], index=0)
    report_format = st.selectbox("Report Formats", ["PDF", "Excel", "JSON"], index=0)
    auto_email_summary = st.checkbox("Auto-email Summary", value=False)

    if st.button("Save Settings"):
        st.session_state.settings.update({
            "theme": theme,
            "notification": notification,
            "language": language,
            "project_timeline": project_timeline,
            "units": units,
            "progress_metric": progress_metric,
            "role": role,
            "api_key": api_key,
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
            if user:
                st.session_state.user = user
                st.success(f"Welcome, {user.name}!")

    # Display the dashboard if a user is logged in
    if st.session_state.user is not None:
        selected_tab = sidebar()
        if selected_tab == "dashboard":
            dashboard(st.session_state.user)
        elif selected_tab == "scheduling":
            scheduling(st.session_state.user)
        elif selected_tab == "manage_programs":
            # Call the manage programs function here
            st.subheader("Manage Programs")
            # Add your manage programs code here
        elif selected_tab == "reports":
            reports()
        elif selected_tab == "settings":
            settings()
        elif selected_tab == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")

if __name__ == "__main__":
    main()
