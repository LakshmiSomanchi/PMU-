import streamlit as st
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
from datetime import date
import os
import datetime
import io
from PIL import Image
import plotly
print(plotly.__version__)
import plotly.express as px

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
    password = Column(String)
    workstreams = relationship("WorkStream", back_populates="employee")
    targets = relationship("Target", back_populates="employee")
    programs = relationship("Program", back_populates="employee")
    schedules = relationship("Schedule", back_populates="employee")
    workplans = relationship("WorkPlan", back_populates="supervisor")
    field_teams = relationship("FieldTeam", back_populates="pmu")

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
    date = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    employee = relationship("Employee", back_populates="schedules")

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

# Drop all tables and recreate them
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

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
                background-color: rgba(255, 255, 255, 0.3);
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
        "Heritage Survey": "heritage_survey",
        "Cotton Baseline Survey": "cotton_baseline_survey",
        "Tools": "tools",
        "Training": "training",
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

    # Tabs for different dashboards
    dashboard_tabs = st.tabs(["Field Team Dashboard", "PMU Dashboard", "Heritage Dashboard", "Ksheersagar Dashboard", "SAKSHAM Dashboard"])

    for tab in dashboard_tabs:
        with tab:
            st.subheader(f"📊 {tab.label}")
            st.write("This is where you can display progress and other metrics.")
            employees = db.query(Employee).all()
            for emp in employees:
                st.markdown(f"**{emp.name}**: Progress details here...")

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
            "role": "Admin",
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

def heritage_survey():
    # Heritage Program - SNF Survey Code
    SAVE_DIR = 'survey_responses'
    os.makedirs(SAVE_DIR, exist_ok=True)

    dict_translations = {
        'English': {
            'Language': 'Language', 'Farmer Profile': 'Farmer Profile', 'VLCC Name': 'VLCC Name',
            'HPC/MCC Code': 'HPC/MCC Code', 'Types': 'Type', 'HPC': 'HPC', 'MCC': 'MCC',
            'Farmer Name': 'Farmer Name', 'Farmer Code': 'Farmer Code / Pourer ID', 'Gender': 'Gender',
            'Male': 'Male', 'Female': 'Female', 'Farm Details': 'Farm Details',
            'Number of Cows': 'Number of Cows', 'No. of Cattle in Milk': 'No. of Cattle in Milk',
            'No. of Calves/Heifers': 'No. of Calves/Heifers', 'No. of Desi cows': 'No. of Desi cows',
            'No. of Cross breed cows': 'No. of Cross breed cows', 'No. of Buffalo': 'No. of Buffalo',
            'Milk Production': 'Milk Production (liters/day)', 'Specific Questions': 'Specific Questions',
            'Green Fodder': 'Green Fodder', 'Type of Green Fodder': 'Type of Green Fodder (Multiple Select)',
            'Quantity of Green Fodder': 'Quantity of Green Fodder (Kg/day)',
            'Dry Fodder': 'Dry Fodder', 'Type of Dry Fodder': 'Type of Dry Fodder (Multiple Select)',
            'Quantity of Dry Fodder': 'Quantity of Dry Fodder (Kg/day)',
            'Pellet Feed': 'Pellet Feed', 'Pellet Feed Brand': 'Pellet Feed Brand (Multiple Select)',
            'Quantity of Pellet Feed': 'Quantity of Pellet Feed (Kg/day)',
            'Mineral Mixture': 'Mineral Mixture',
            'Mineral Mixture Brand': 'Mineral Mixture Brand',
            'Quantity of Mineral Mixture': 'Quantity of Mineral Mixture (gm/day)',
            'Silage': 'Silage', 'Source and Price of Silage': 'Source and Price of Silage',
            'Quantity of Silage': 'Quantity of Silage (Kg/day)', 'Source of Water': 'Source of Water (Multiple Select)',
            'Name of Surveyor': 'Name of Surveyor', 'Date of Visit': 'Date of Visit',
            'Submit': 'Submit', 'Yes': 'Yes', 'No': 'No', 'Download CSV': 'Download CSV'
        },
        # Add other languages as needed...
    }

    # Streamlit Page Config
    st.set_page_config(page_title="Heritage Dairy Survey", page_icon="🐄", layout="centered")

    # Language Selection
    lang = st.selectbox("Language / भाषा / భाषा", ("English", "Hindi", "Telugu"))
    labels = dict_translations.get(lang, dict_translations['English'])

    # Title
    st.title(labels['Farmer Profile'])

    VLCC_NAMES = ["3025-K.V.PALLE", "3026-KOTHA PALLE", "3028-BONAMVARIPALLE", "3029-BOMMAICHERUVUPALLI", "3030-BADDALAVARIPALLI"]
    GREEN_FODDER_OPTIONS = ["Napier", "Maize", "Sorghum"]
    DRY_FODDER_OPTIONS = ["Paddy Straw", "Maize Straw", "Ragi Straw", "Ground Nut Crop Residues"]
    PELLET_FEED_BRANDS = ["Heritage Milk Rich", "Heritage Milk Joy", "Heritage Power Plus", "Kamadhenu", "Godrej"]
    MINERAL_MIXTURE_BRANDS = ["Herita Vit", "Herita Min", "Other (Specify)"]
    WATER_SOURCE_OPTIONS = ["Panchayat", "Borewell", "Water Streams"]
    SURVEYOR_NAMES = ["Shiva Shankaraiah", "Reddisekhar", "Balakrishna", "Somasekhar", "Mahesh Kumar"]

    # Form Start
    with st.form("survey_form"):
        st.header(labels['Farmer Profile'])
        vlcc_name = st.selectbox(labels['VLCC Name'], VLCC_NAMES)
        hpc_code = st.text_input(labels['HPC/MCC Code'])
        types = st.selectbox(labels['Types'], (labels['HPC'], labels['MCC']))
        farmer_name = st.text_input(labels['Farmer Name'])
        farmer_code = st.text_input(labels['Farmer Code'])
        gender = st.selectbox(labels['Gender'], (labels['Male'], labels['Female']))

        st.header(labels['Farm Details'])
        cows = st.number_input(labels['Number of Cows'], min_value=0)
        cattle_in_milk = st.number_input(labels['No. of Cattle in Milk'], min_value=0)
        calves = st.number_input(labels['No. of Calves/Heifers'], min_value=0)
        desi_cows = st.number_input(labels['No. of Desi cows'], min_value=0)
        crossbreed_cows = st.number_input(labels['No. of Cross breed cows'], min_value=0)
        buffalo = st.number_input(labels['No. of Buffalo'], min_value=0)
        milk_production = st.number_input(labels['Milk Production'], min_value=0.0)

        st.header(labels['Specific Questions'])
        green_fodder = st.selectbox(labels['Green Fodder'], (labels['Yes'], labels['No']))
        green_fodder_types = st.multiselect(labels['Type of Green Fodder'], GREEN_FODDER_OPTIONS)
        green_fodder_qty = st.number_input(labels['Quantity of Green Fodder'], min_value=0.0)
        dry_fodder = st.selectbox(labels['Dry Fodder'], (labels['Yes'], labels['No']))
        dry_fodder_types = st.multiselect(labels['Type of Dry Fodder'], DRY_FODDER_OPTIONS)
        dry_fodder_qty = st.number_input(labels['Quantity of Dry Fodder'], min_value=0.0)

        pellet_feed = st.selectbox(labels['Pellet Feed'], (labels['Yes'], labels['No']))
        pellet_feed_brands = st.multiselect(labels['Pellet Feed Brand'], PELLET_FEED_BRANDS)
        pellet_feed_qty = st.number_input(labels['Quantity of Pellet Feed'], min_value=0.0)

        mineral_mixture = st.selectbox(labels['Mineral Mixture'], (labels['Yes'], labels['No']))
        mineral_brand = st.selectbox(labels['Mineral Mixture Brand'], MINERAL_MIXTURE_BRANDS)
        mineral_qty = st.number_input(labels['Quantity of Mineral Mixture'], min_value=0.0)

        silage = st.selectbox(labels['Silage'], (labels['Yes'], labels['No']))
        silage_source = st.text_input(labels['Source and Price of Silage'])
        silage_qty = st.number_input(labels['Quantity of Silage'], min_value=0.0)

        water_sources = st.multiselect(labels['Source of Water'], WATER_SOURCE_OPTIONS)
        surveyor_name = st.selectbox(labels['Name of Surveyor'], SURVEYOR_NAMES)
        visit_date = st.date_input(labels['Date of Visit'])
        submit = st.form_submit_button(labels['Submit'])

    if submit:
        data = {
            'VLCC Name': vlcc_name,
            'HPC/MCC Code': hpc_code,
            'Types': types,
            'Farmer Name': farmer_name,
            'Farmer Code': farmer_code,
            'Gender': gender,
            'Number of Cows': cows,
            'No. of Cattle in Milk': cattle_in_milk,
            'No. of Calves/Heifers': calves,
            'No. of Desi cows': desi_cows,
            'No. of Cross breed cows': crossbreed_cows,
            'No. of Buffalo': buffalo,
            'Milk Production (liters/day)': milk_production,
            'Green Fodder': green_fodder,
            'Type of Green Fodder': ", ".join(green_fodder_types),
            'Quantity of Green Fodder (Kg/day)': green_fodder_qty,
            'Dry Fodder': dry_fodder,
            'Type of Dry Fodder': ", ".join(dry_fodder_types),
            'Quantity of Dry Fodder (Kg/day)': dry_fodder_qty,
            'Pellet Feed': pellet_feed,
            'Pellet Feed Brand': ", ".join(pellet_feed_brands),
            'Quantity of Pellet Feed (Kg/day)': pellet_feed_qty,
            'Mineral Mixture': mineral_mixture,
            'Mineral Mixture Brand': mineral_brand,
            'Quantity of Mineral Mixture (gm/day)': mineral_qty,
            'Silage': silage,
            'Source and Price of Silage': silage_source,
            'Quantity of Silage (Kg/day)': silage_qty,
            'Source of Water': ", ".join(water_sources),
            'Surveyor Name': surveyor_name,
            'Date of Visit': visit_date.isoformat()
        }

        # Save CSV
        df = pd.DataFrame([data])
        filename = f"survey_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(os.path.join(SAVE_DIR, filename), index=False, encoding='utf-8')
        st.success("✅ Survey Submitted and Saved!")

def cotton_baseline_survey():
    # Cotton Baseline Survey Code
    SAVE_DIR = "responses"
    os.makedirs(SAVE_DIR, exist_ok=True)

    st.set_page_config(page_title="Cotton Farming Questionnaire", layout="wide")
    st.title("🌾 Cotton Farming Questionnaire (किसान सर्वे)")

    language = st.selectbox("Select Language / भाषा निवडा / ભાષા પસંદ કરો", ["English", "Hindi", "Marathi", "Gujarati"])

    dict_translations = {
        "English": {
            "1": "Farmer Tracenet Code",
            "2": "Farmer Full Name",
            "3": "Mobile no.",
            "4": "Gender",
            "5": "Highest education",
            "6": "Village",
            "7": "Taluka/Block",
            "8": "District",
            "9": "State",
            "10": "Pincode",
            "11": "No. of males (adult) in household",
            "12": "No. of females (adult) in household",
            "13": "Children (<16) in household",
            "14": "Total Member of Household",
            "15": "No. of school-going children",
            "16": "No. of earning members in the family",
            "17": "Total Landholding (in acres)",
            "18": "Primary crop",
            "19": "Secondary crops",
            "20": "Non-organic Cotton land (in acre) (if any)",
            "21": "Organic Cotton land (in acre)",
            "22": "Years since practicing organic cotton (#)",
            "23": "Certification status (certified/IC1..)",
            "24": "Source of irrigation",
            "25": "Cultivable area (acre)",
            "26": "No. of cattle (cow and Buffalo)",
            "27": "Source of drinking water",
            "28": "Preferred selling point (Aggregator/Suminter/APMC/other Gin)",
            "29": "Has space for harvested cotton storage (Y/N)",
            "30": "Receives any agro advisory (Y/N)",
            "31": "Received any training on best practices for organic cotton?",
            "32": "Membership in FPO/FPC/SHG",
            "33": "Maintaining any Diary or Register for record keeping (Y/N)",
            "34": "Annual household income(in Rs)",
            "35": "Primary source of income",
            "36": "Secondary source of income",
            "37": "Income from Primary source (Rs.)",
            "38": "Certification cost per annum/acre",
            "39": "Avg. production of organic cotton/acre (Kg)",
            "40": "Cost of cultivation/acre (Rs)",
            "41": "Quantity sold of organic cotton (in kg)",
            "42": "Selling price per kg (Rs.)",
            "43": "Material cost for bio-inputs",
            "44": "Name of bio-input used for pest and disease management",
            "45": "Name of bio-fertilizer/compost used",
            "46": "No. of pheromone traps used / acre",
            "47": "Cost per pheromone trap",
            "48": "No. of Yellow sticky traps used / acre",
            "49": "Cost per yellow sticky trap",
            "50": "No. of Blue sticky traps used / acre",
            "51": "Cost per blue sticky trap",
            "52": "No. of bird perches used / acre",
            "53": "Irrigation cost/acre",
            "54": "No. of irrigation required for organic cotton",
            "55": "Irrigation method used",
            "56": "Any farm machinery hired (Y/N)",
            "57": "Cost of machinery hiring (Rs.)/acre",
            "58": "Local labour cost per day",
            "59": "Migrant labour cost per day",
            "60": "No. of workers required during sowing/acre",
            "61": "No. of workers required during harvesting/acre",
            "62": "Harvesting time (1st, 2nd & 3rd picking) (month)",
            "63": "Weeding method used (manual/mechanical)",
            "64": "Weeding cost/acre",
            "65": "Cost of mulching/acre",
            "66": "No. of tillage practiced",
            "67": "Tillage cost/acre",
            "68": "Land preparation cost/acre",
            "69": "Seed rate of organic cotton/acre",
            "70": "Variety of organic cotton seed (Name)",
            "71": "Name of border crop used",
            "72": "Name of the inter crop used",
            "73": "Name of cover crop",
            "74": "Name of trap crop",
            "75": "Mulching used (Y/N)",
            "76": "Type of mulching used (Bio-plastic/green/dry)",
            "77": "What precautions used during storage",
            "78": "Hired vehicle used for transportation of seed cotton (Y/N)",
            "79": "Transportation cost (Rs.)/Kg of seed cotton",
            "80": "Any quantity rejection due to contamination/impurities (Kg)",
            "81": "Price discovery mechanism",
            "82": "Payment Transaction type (Cash/online)",
            "83": "Days of credit after sell",
            "84": "Availing any govt. scheme or subsidy benefits (Y/N)",
            "85": "Opted for crop insurance (Y/N)",
            "86": "Cost of crop insurance per acre",
            "87": "Possess KCC (Y/N)",
            "88": "Possess active bank account (Y/N)",
            "89": "Crop rotation used (Y/N)",
            "90": "Crops used for rotation",
            "91": "Using any water tracking devices (Y/N)",
            "92": "Capacity of pump (in HP)",
            "93": "Maintaining Buffer zone (Y/N)",
            "94": "Utilization of crop residue (Fuel/cattle feed/biochar/in-situ composting/burning)",
            "95": "Mode of payment to workers (cash/online)",
            "96": "Any wage difference for Men and Women workers (Y/N)",
            "97": "Using any labour register (Y/N)",
            "98": "Any arrangement of safety-kit / first-aid for workers",
            "99": "Any provision of shelter & safe drinking water for workers",
            "100": "Any provision for lavatory for workers",
            "101": "Involve family members (Women) in agricultural operations",
            "102": "Any community water harvesting structure (Y/N)",
            "103": "Use of soil moisture meter (Y/N)",
        },
        # Add other languages as needed...
    }

    questions = [str(i) for i in range(1, 104)]
    labels = dict_translations.get(language, dict_translations["English"])

    responses = {}
    PHOTOS_DIR = "photos"
    os.makedirs(PHOTOS_DIR, exist_ok=True)

    with st.form("questionnaire_form"):
        for question_key in questions:
            question_text = labels.get(question_key, f"Question {question_key} (No translation)")
            if question_key == "4":
                responses[question_key] = st.selectbox(question_text, ["Male", "Female", "Others"], key=f"question_{question_key}")
                if responses[question_key] == "Others":
                    responses["others_gender"] = st.text_input("If selected Others, please specify:", key="others_gender")
            elif question_key == "24":
                responses[question_key] = st.selectbox(question_text, ["Canal", "Well", "Borewell", "River", "Farm Pond", "Community Pond", "Rain-fed not irrigated"], key=f"question_{question_key}")
            elif question_key in ["29", "30", "33", "56", "75", "78", "84", "85", "87", "88", "89", "91", "93", "96", "97", "102", "103"]:
                responses[question_key] = st.selectbox(question_text, ["Yes", "No"], key=f"question_{question_key}")
            elif question_key == "55":
                responses[question_key] = st.selectbox(question_text, ["Drip irrigation", "Sprinkler irrigation", "Flood irrigation", "Ridge and Furrow Irrigation", "Other"], key=f"question_{question_key}")
            elif question_key == "62":
                responses[question_key] = st.text_input(question_text, placeholder="e.g., month 1, month 2, month 3", key=f"question_{question_key}")
            else:
                responses[question_key] = st.text_input(question_text, key=f"question_{question_key}")

        uploaded_photo = st.file_uploader("Upload a photo (optional):", type=["jpg", "jpeg", "png"], key="uploaded_photo")
        submitted = st.form_submit_button("Submit")

    if submitted:
        required_fields = ["1", "2", "3", "4", "6", "8", "9", "10", "34", "35", "37", "39", "41", "42"]
        for field in required_fields:
            if not responses.get(field):
                st.error(f"Field '{labels[field]}' is required.")
                break
        else:
            phone_number = responses.get("3")
            if phone_number and (len(phone_number) != 10 or not phone_number.isdigit()):
                st.error("Mobile no. must be exactly 10 digits.")
            else:
                numeric_fields = ["11", "12", "13", "14", "15", "16", "17", "34", "37", "39", "41"]
                for field in numeric_fields:
                    if not str(responses.get(field)).isdigit() or int(responses.get(field)) < 0:
                        st.error(f"Field '{labels[field]}' must be a non-negative number.")
                        break
                else:
                    if uploaded_photo:
                        photo_path = os.path.join(PHOTOS_DIR, uploaded_photo.name)
                        with open(photo_path, "wb") as f:
                            f.write(uploaded_photo.getbuffer())
                        st.success(f"Photo uploaded and saved as {uploaded_photo.name}.")

                    data = {labels.get(k, k): v for k, v in responses.items()}
                    now = datetime.datetime.now()
                    filename = f"survey_{now.strftime('%Y%m%d_%H%M%S')}.csv"
                    df = pd.DataFrame([data])
                    df.to_csv(os.path.join(SAVE_DIR, filename), index=False, encoding="utf-8")
                    st.success("✅ Survey Submitted and Saved!")

def plant_population_tool():
    # Plant Population Tool Code
    excel_file = "plant_population_data.xlsx"
    if os.path.exists(excel_file):
        saved_data = pd.read_excel(excel_file)
    else:
        saved_data = pd.DataFrame()

    st.set_page_config(page_title="Plant Population Dashboard", layout="wide")
    st.title("🌱 Plant Population Tool")
    st.markdown("---")

    st.subheader("Field Input Parameters")

    with st.form("plant_population_form"):
        cols1 = st.columns(6)
        farmer_name = cols1[0].text_input("Farmer Name")
        field_id = cols1[1].text_input("Field ID")
        area_acre = cols1[2].number_input("Area (acre)", min_value=0.0, step=0.01)
        area_m = cols1[3].number_input("Area (m)", min_value=0.0, step=0.1)
        spacing_cm = cols1[4].text_input("Row × Plant Spacing (cm)")
        spacing_m = cols1[5].text_input("Row × Plant Spacing (m)")

        cols2 = st.columns(5)
        sowing_date = cols2[0].date_input("Sowing Date", value=date.today())
        expected_plants = cols2[1].number_input("Expected Plants", min_value=0)
        plants_emerged = cols2[2].number_input("Plants Emerged", min_value=0)
        actual_stand = cols2[3].number_input("Actual Stand (%)", min_value=0.0, max_value=100.0, step=0.1)
        missing_plants = cols2[4].number_input("Missing Plants", min_value=0)

        cols3 = st.columns(5)
        gaps_filled = cols3[0].number_input("Gaps filled", min_value=0)
        total_gaps = cols3[1].number_input("Total Gaps", min_value=0)
        gap_percent = cols3[2].number_input("Gap %", min_value=0.0, max_value=100.0, step=0.1)
        gap_filling_date = cols3[3].date_input("Gap Filling Date", value=date.today())
        success_rate = cols3[4].number_input("Success Rate (%)", min_value=0.0, max_value=100.0, step=0.1)

        cols4 = st.columns(2)
        labour_hours = cols4[0].number_input("Labour Hours", min_value=0.0, step=0.1)
        labour_efficiency = cols4[1].number_input("Labour Efficiency (gaps/hr)", min_value=0.0, step=0.1)

        submitted = st.form_submit_button("Submit")

    if submitted:
        new_entry = pd.DataFrame([{
            "Farmer Name": farmer_name,
            "Field ID": field_id,
            "Area (acre)": area_acre,
            "Area (m)": area_m,
            "Row × Plant Spacing (cm)": spacing_cm,
            "Row × Plant Spacing (m)": spacing_m,
            "Sowing Date": sowing_date,
            "Expected Plants": expected_plants,
            "Plants Emerged": plants_emerged,
            "Actual Stand (%)": actual_stand,
            "Missing Plants": missing_plants,
            "Gaps filled": gaps_filled,
            "Total Gaps": total_gaps,
            "Gap %": gap_percent,
            "Gap Filling Date": gap_filling_date,
            "Success Rate (%)": success_rate,
            "Labour Hours": labour_hours,
            "Labour Efficiency (gaps/hr)": labour_efficiency
        }])

        saved_data = pd.concat([saved_data, new_entry], ignore_index=True)
        saved_data.to_excel(excel_file, index=False)
        st.success("Data submitted and saved to Excel.")

    st.markdown("---")
    st.subheader("📊 Collected Submissions")

    if not saved_data.empty:
        with st.expander("🔍 Filter Data"):
            farmers = saved_data["Farmer Name"].unique().tolist()
            selected_farmers = st.multiselect("Farmer Name", options=farmers, default=farmers)

            fields = saved_data["Field ID"].unique().tolist()
            selected_fields = st.multiselect("Field ID", options=fields, default=fields)

            filtered_data = saved_data[
                saved_data["Farmer Name"].isin(selected_farmers) &
                saved_data["Field ID"].isin(selected_fields)
            ]

        st.dataframe(filtered_data, use_container_width=True)

        st.markdown("---")
        st.subheader("📈 Summary Analysis")

        avg_gap_percent = filtered_data["Gap %"].mean()
        avg_success_rate = filtered_data["Success Rate (%)"].mean()
        avg_efficiency = filtered_data["Labour Efficiency (gaps/hr)"].mean()
        total_expected = filtered_data["Expected Plants"].sum()
        total_emerged = filtered_data["Plants Emerged"].sum()
        total_missing = filtered_data["Missing Plants"].sum()
        total_filled = filtered_data["Gaps filled"].sum()

        st.metric("Average Gap %", f"{avg_gap_percent:.2f}%")
        st.metric("Average Success Rate", f"{avg_success_rate:.2f}%")
        st.metric("Average Labour Efficiency", f"{avg_efficiency:.2f} gaps/hr")
        st.metric("Total Expected Plants", total_expected)
        st.metric("Total Emerged Plants", total_emerged)
        st.metric("Total Missing Plants", total_missing)
        st.metric("Total Gaps Filled", total_filled)

        st.markdown("---")
        st.subheader("📊 Charts")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            fig1 = px.bar(filtered_data, x="Farmer Name", y="Gap %", color="Field ID", title="Gap % by Farmer")
            st.plotly_chart(fig1, use_container_width=True)

        with chart_col2:
            fig2 = px.line(filtered_data.sort_values("Sowing Date"), x="Sowing Date", y="Success Rate (%)", color="Farmer Name", title="Success Rate Over Time")
            st.plotly_chart(fig2, use_container_width=True)

        fig3 = px.scatter(filtered_data, x="Expected Plants", y="Plants Emerged", color="Farmer Name", size="Labour Efficiency (gaps/hr)", title="Expected vs Emerged Plants")
        st.plotly_chart(fig3, use_container_width=True)

def training():
    # Training section code
    BASE_DIR = "training_materials"
    PROGRAMS = ["Cotton", "Dairy"]
    CATEGORIES = ["Presentations", "Videos", "Audios", "Quizzes"]

    for program in PROGRAMS:
        for category in CATEGORIES:
            Path(f"{BASE_DIR}/{program.lower()}/{category.lower()}").mkdir(parents=True, exist_ok=True)

    st.set_page_config(page_title="TechnoServe Training Platform", layout="wide")

    # Admin Authentication with Session State
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

    def admin_login():
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
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            file_path = os.path.join(save_dir, uploaded_file.name)

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

    # --- Main Content ---
    st.markdown("""
    <div class="header">
        🌾 <span style="font-weight: bold;">Farmer Training Program</span> 🌾
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎮 Level Up Your Farming Skills!")
    st.markdown("""
        <p>Welcome to the Farmer Training Program! Complete tasks, learn new skills, and earn rewards to become a <b>Master Farmer</b>.</p>
        <ul>
            <li>📚 Access training materials</li>
            <li>🎯 Complete quizzes</li>
            <li>🏆 Earn badges</li>
        </ul>
    """, unsafe_allow_html=True)

    if st.button("🌟 Start Your Journey"):
        st.success("🎉 You're on your way to becoming a Master Farmer! Explore the training materials below.")

    selected_program = st.sidebar.selectbox("🌟 Choose a Program", PROGRAMS, key="view_program_dropdown")
    selected_category = st.sidebar.radio("📂 Select Training Material", CATEGORIES, key="view_category_radio")

    folder_path = Path(BASE_DIR) / selected_program.lower() / selected_category.lower()

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
        elif selected_tab == "heritage_survey":
            heritage_survey()
        elif selected_tab == "cotton_baseline_survey":
            cotton_baseline_survey()
        elif selected_tab == "tools":
            plant_population_tool()
        elif selected_tab == "training":
            training()
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
