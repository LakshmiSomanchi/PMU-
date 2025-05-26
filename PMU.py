import streamlit as st
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
from datetime import date
import os
from pathlib import Path  # Import Path for directory creation
import json

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
        "Field Team Management": "field_team_management",
        "Live Dashboard": "live_dashboard",
        "Settings": "settings",
        "Logout": "logout",
        "Training": "training"  # New Training section
    }
    selection = st.sidebar.radio("Go to", list(menu_options.keys()))
    return menu_options[selection]

# --- Dashboard Section ---
def dashboard(user):
    db = get_db()
    st.markdown("<h1 style='text-align:center; color:#1a73e8;'>🚀 Project Management Dashboard</h1>", unsafe_allow_html=True)
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
                st.markdown(f"**{emp.name}**: Status")  # Replace with actual progress data

# --- Training Section ---
def training():
    st.title("📚 Training Materials")
    
    # --- Upload Content ---
    st.header("📤 Upload Training Content")
    selected_program = st.selectbox("🌟 Select Program", ["Cotton", "Dairy"], key="program_dropdown")
    selected_category = st.selectbox("📂 Select Category", ["Presentations", "Videos", "Audios", "Quizzes"], key="category_dropdown")
    uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "mp4", "mp3", "json", "pptx", "xlsx", "png", "jpg", "jpeg"])

    if uploaded_file:
        if selected_program and selected_category:  # Ensure selections are made
            save_dir = f"training_materials/{selected_program.lower()}/{selected_category.lower()}"
            Path(save_dir).mkdir(parents=True, exist_ok=True)  # Ensure directory exists
            file_path = os.path.join(save_dir, uploaded_file.name)

            # Validate file type
            if not is_valid_file(uploaded_file.name, selected_category):
                st.error(f"❌ Invalid file type for the **{selected_category}** category.")
            else:
                if st.button("Upload"):
                    try:
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully to {save_dir}!")
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {e}")
        else:
            st.error("Please select a program and category before uploading.")

    # --- Delete Content ---
    st.header("🗑️ Delete Training Content")
    delete_program = st.selectbox("🗂️ Select Program to View Files", ["Cotton", "Dairy"], key="delete_program_dropdown")
    delete_category = st.selectbox("📂 Select Category to View Files", ["Presentations", "Videos", "Audios", "Quizzes"], key="delete_category_dropdown")
    delete_folder_path = Path(f"training_materials/{delete_program.lower()}/{delete_category.lower()}")

    if delete_folder_path.exists() and any(delete_folder_path.iterdir()):
        delete_files = os.listdir(delete_folder_path)
        delete_file = st.selectbox("🗑️ Select a File to Delete", delete_files, key="delete_file_dropdown")

        if st.button("Delete File"):
            try:
                os.remove(delete_folder_path / delete_file)
                st.success(f"✅ File '{delete_file}' has been deleted!")
            except Exception as e:
                st.error(f"❌ Error deleting file: {e}")
    else:
        st.warning(f"No files available in the **{delete_category}** category of the {delete_program} program.")

    selected_program = st.sidebar.selectbox("🌟 Choose a Program", ["Cotton", "Dairy"], key="view_program_dropdown")
    selected_category = st.sidebar.radio("📂 Select Training Material", ["Presentations", "Videos", "Audios", "Quizzes"], key="view_category_radio")

    # Get the folder path for the selected program and category
    folder_path = Path(f"training_materials/{selected_program.lower()}/{selected_category.lower()}")

    # Check if the folder exists and display its contents
    if not folder_path.exists() or not any(folder_path.iterdir()):
        st.warning(f"No content available for the **{selected_category}** category in the {selected_program} program.")
    else:
        files = os.listdir(folder_path)
        for file in files:
            file_path = folder_path / file
            if file.endswith(".pdf"):
                st.markdown(f"📄 **{file}**")
                with open(file_path, "rb") as f:
                    st.download_button(label=f"⬇️ Download {file}", data=f, file_name=file)
            elif file.endswith(".mp4"):
                st.markdown(f"🎥 **{file}**")
                st.video(str(file_path))
            elif file.endswith(".mp3"):
                st.markdown(f"🎵 **{file}**")
                st.audio(str(file_path))
            elif file.endswith(".json"):
                st.markdown(f"📝 **{file}** (Quiz File)")
                with open(file_path, "r") as f:
                    st.json(json.load(f))
            elif file.endswith((".png", ".jpg", ".jpeg")):
                st.markdown(f"🖼️ **{file}**")
                st.image(str(file_path))
            elif file.endswith(".pptx"):
                st.markdown(f"📑 **{file} (PPTX)**")
                with open(file_path, "rb") as f:
                    st.download_button(label=f"⬇️ Download {file}", data=f, file_name=file)

def is_valid_file(file_name, category):
    valid_extensions = {
        "Presentations": [".pptx"],
        "Videos": [".mp4"],
        "Audios": [".mp3"],
        "Quizzes": [".xlsx", ".png", ".jpg", ".jpeg"]
    }
    # Allow Excel and Images in all categories
    extra_extensions = [".xlsx", ".png", ".jpg", ".jpeg"]
    file_extension = os.path.splitext(file_name)[1].lower()

    if file_extension in extra_extensions:
        return True
    if category in valid_extensions and file_extension in valid_extensions[category]:
        return True
    return False

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
        elif selected_tab == "training":
            training()  # Call the training section
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
        elif selected_tab == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")

if __name__ == "__main__":
    main()
