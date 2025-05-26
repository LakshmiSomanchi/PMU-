import streamlit as st
import os
from pathlib import Path
import json
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
from math import floor

# Set the Streamlit page configuration
st.set_page_config(page_title="PMU Tracker", layout="wide")

# Define the base directory for training materials
BASE_DIR = "training_materials"
PROGRAMS = ["Cotton", "Dairy"]
CATEGORIES = ["Presentations", "Videos", "Audios", "Quizzes"]

# Ensure the directory structure exists
for program in PROGRAMS:
    for category in CATEGORIES:
        Path(f"{BASE_DIR}/{program.lower()}/{category.lower()}").mkdir(parents=True, exist_ok=True)

# Custom CSS for agriculture theme
st.markdown("""
    <style>
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #D1F5D4; /* Green for nature */
        }
        [data-testid="stSidebar"] .css-qrbaxs {
            color: #ffffff; /* White text for sidebar */
            font-weight: bold;
            font-size: 16px;
        }
        /* Header Styling */
        .header {
            text-align: center;
            font-size: 42px;
            color: #6B4226; /* Soil Brown */
            padding: 20px;
            background-color: #EEE8AA; /* Wheat Color */
            border-radius: 15px;
            border: 2px solid #6B4226;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
        }
        /* Page Background */
        .stApp {
            background-color: #F5F5DC; /* Beige for natural tones */
        }
        /* Links */
        a {
            color: #4caf50; /* Green for links */
            font-weight: bold;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
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
        "Tools": "tools",  # New Tools section
        "SAKSHAM": "saksham",  # New SAKSHAM section
        "Samriddh Sakhi": "samriddh_sakhi",  # New Samriddh Sakhi section
        "Logout": "logout"
    }
    selection = st.sidebar.radio("Go to", list(menu_options.keys()))
    return menu_options[selection]

def tools():
    st.subheader("🛠️ Tools")
    tool_options = {
        "Cotton": "cotton_tools",
        "Dairy": "dairy_tools"
    }
    selected_tool = st.selectbox("Select a Tool", list(tool_options.keys()))
    
    if selected_tool == "Cotton":
        cotton_tools()
    elif selected_tool == "Dairy":
        dairy_tools()

def cotton_tools():
    st.subheader("🌾 Cotton Tools")
    if st.button("Open Plant Population Tool"):
        st.session_state.tool = "plant_population_tool"
        st.experimental_rerun()  # Redirect to the Plant Population Tool

def dairy_tools():
    st.subheader("🥛 Dairy Tools")
    st.write("Dairy tools will be added here in the future.")

def saksham():
    st.subheader("🌟 SAKSHAM")
    st.write("Welcome to the SAKSHAM section.")
    if st.button("Open Plant Population Tool"):
        st.session_state.tool = "plant_population_tool"
        st.experimental_rerun()  # Redirect to the Plant Population Tool

def plant_population_tool():
    st.set_page_config(page_title="Plant Population Tool", layout="wide")

    # Detect dark mode for adaptive styling
    is_dark = st.get_option("theme.base") == "dark"

    text_color = "#f8f9fa" if is_dark else "#0A0A0A"
    bg_color = "#0A9396" if is_dark else "#e0f2f1"

    # Apply full page background color
    st.markdown(f"""
    <style>
        html, body, [class*="css"]  {{
            background-color: {bg_color};
            font-family: 'Helvetica', sans-serif;
        }}
        .block-container {{
            padding-top: 3rem;
            padding-bottom: 3rem;
        }}
        .stMetricValue {{
            font-size: 1.5rem !important;
            color: {text_color};
        }}
        .stMetricLabel {{
            font-weight: bold;
            color: {text_color};
        }}
        h1, h2, h3, h4, h5 {{
            color: {text_color};
        }}
        .stButton>button {{
            background-color: #0A9396;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 0.6em 1.5em;
        }}
        .stButton>button:hover {{
            background-color: #007f86;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.title("🌿 Plant Population & Seed Requirement Tool")
    st.markdown("""<hr style='margin-top: -15px; margin-bottom: 25px;'>""", unsafe_allow_html=True)

    with st.container():
        st.header("📥 Farmer Survey Entry")
        st.markdown("Fill in the details below to calculate how many seed packets are required for optimal plant population.")

        with st.form("survey_form"):
            col0, col1, col2 = st.columns(3)
            farmer_name = col0.text_input("👤 Farmer Name")
            farmer_id = col1.text_input("🆔 Farmer ID")
            state = col2.selectbox("🗺️ State", ["Maharashtra", "Gujarat"])

            spacing_unit = st.selectbox("📏 Spacing Unit", ["cm", "m"])
            col3, col4, col5 = st.columns(3)
            row_spacing = col3.number_input("↔️ Row Spacing (between rows)", min_value=0.01, step=0.1)
            plant_spacing = col4.number_input("↕️ Plant Spacing (between plants)", min_value=0.01, step=0.1)
            land_acres = col5.number_input("🌾 Farm Area (acres)", min_value=0.01, step=0.1)

            submitted = st.form_submit_button("🔍 Calculate")

    if submitted and farmer_name and farmer_id:
        st.markdown("---")

        germination_rate_per_acre = {"Maharashtra": 14000, "Gujarat": 7400}
        confidence_interval = 0.90
        seeds_per_packet = 7500
        acre_to_m2 = 4046.86

        if spacing_unit == "cm":
            row_spacing /= 100
            plant_spacing /= 100

        plant_area_m2 = row_spacing * plant_spacing
        plants_per_m2 = 1 / plant_area_m2
        field_area_m2 = land_acres * acre_to_m2
        calculated_plants = plants_per_m2 * field_area_m2

        target_plants = germination_rate_per_acre[state] * land_acres
        required_seeds = target_plants / confidence_interval
        required_packets = floor(required_seeds / seeds_per_packet)

        st.subheader("📊 Output Summary")
        st.markdown("""<div style='margin-bottom: 20px;'>Calculated results for seed packet distribution:</div>""", unsafe_allow_html=True)
        col6, col7, col8, col9 = st.columns(4)
        col6.metric("🧮 Calculated Capacity", f"{int(calculated_plants):,} plants")
        col7.metric("🎯 Target Plants", f"{int(target_plants):,} plants")
        col8.metric("🌱 Required Seeds", f"{int(required_seeds):,} seeds")
        col9.metric("📦 Seed Packets Needed", f"{required_packets} packets")

        st.markdown("""<hr style='margin-top: 25px;'>""", unsafe_allow_html=True)
        st.caption("ℹ️ Based on 7500 seeds per 450g packet and 90% germination confidence. Packets are rounded down to the nearest full packet.")

    elif submitted:
        st.error("⚠️ Please enter both Farmer Name and Farmer ID to proceed.")

def samriddh_sakhi():
    st.subheader("🌼 Samriddh Sakhi")
    st.write("Welcome to the Samriddh Sakhi section. This section will contain resources and tools for empowerment.")

def admin_login():
    """Admin login for restricted access."""
    if st.session_state.is_admin:
        st.sidebar.success("✅ You are logged in as Admin.")
        return True

    st.sidebar.subheader("🔒 Admin Login")
    admin_username = st.sidebar.text_input("Admin Username", type="default", key="admin_username")
    admin_password = st.sidebar.text_input("Admin Password", type="password", key="admin_password")
    if st.sidebar.button("Login"):
        if admin_username == "admin" and admin_password == "admin123":
            st.sidebar.success("✅ Login Successful!")
            st.session_state.is_admin = True
            return True
        else:
            st.sidebar.error("❌ Invalid credentials. Please try again.")
    return False

# File type validation based on category
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

# --- Main Content ---
def dashboard(user):
    st.title("📊 Dashboard")
    st.markdown("Welcome to the Dashboard!")

    # Add a Gamified Header for the Main Page
    st.markdown("""
    <div class="header">
        🌾 <span style="font-weight: bold;">Farmer Training Program</span> 🌾
    </div>
    """, unsafe_allow_html=True)

    # Add Interactive Gamification Elements
    st.markdown("### 🎮 Level Up Your Farming Skills!")
    st.markdown("""
        <p>Welcome to the Farmer Training Program! Complete tasks, learn new skills, and earn rewards to become a <b>Master Farmer</b>.</p>
        <ul>
            <li>📚 Access training materials</li>
            <li>🎯 Complete quizzes</li>
            <li>🏆 Earn badges</li>
        </ul>
    """, unsafe_allow_html=True)

    # Add a Button for a Gamified Start
    if st.button("🌟 Start Your Journey"):
        st.success("🎉 You're on your way to becoming a Master Farmer! Explore the training materials below.")

    # Admin Authentication with Session State
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False  # Initialize admin state

    # Check if the user is an admin
    is_admin = admin_login()

    if is_admin:
        st.sidebar.header("⚙️ Admin Panel")
        st.sidebar.markdown("Welcome, Admin!")

        # --- Admin Feature: Upload Content ---
        st.header("📤 Upload Training Content")
        selected_program = st.selectbox("🌟 Select Program", PROGRAMS, key="program_dropdown")
        selected_category = st.selectbox("📂 Select Category", CATEGORIES, key="category_dropdown")
        uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "mp4", "mp3", "json", "pptx", "xlsx", "png", "jpg", "jpeg"])

        if uploaded_file:
            save_dir = f"{BASE_DIR}/{selected_program.lower()}/{selected_category.lower()}"
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

        # --- Admin Feature: Delete Content ---
        st.header("🗑️ Delete Training Content")
        delete_program = st.selectbox("🗂️ Select Program to View Files", PROGRAMS, key="delete_program_dropdown")
        delete_category = st.selectbox("📂 Select Category to View Files", CATEGORIES, key="delete_category_dropdown")
        delete_folder_path = Path(BASE_DIR) / delete_program.lower() / delete_category.lower()

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

    else:
        st.warning("You must be an admin to upload or delete training materials.")

    selected_program = st.sidebar.selectbox("🌟 Choose a Program", PROGRAMS, key="view_program_dropdown")
    selected_category = st.sidebar.radio("📂 Select Training Material", CATEGORIES, key="view_category_radio")

    # Get the folder path for the selected program and category
    folder_path = Path(BASE_DIR) / selected_program.lower() / selected_category.lower()

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
            live_dashboard()
        elif selected_tab == "reports":
            reports()
        elif selected_tab == "settings":
            settings()
        elif selected_tab == "tools":
            tools()  # New tools section
        elif selected_tab == "saksham":
            saksham()  # New SAKSHAM section
        elif selected_tab == "samriddh_sakhi":
            samriddh_sakhi()  # New Samriddh Sakhi section
        elif selected_tab == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")

    # Check if the Plant Population Tool should be displayed
    if "tool" in st.session_state and st.session_state.tool == "plant_population_tool":
        plant_population_tool()  # Call the Plant Population Tool function

if __name__ == "__main__":
    main()
