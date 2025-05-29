import streamlit as st
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
import pandas as pd
from datetime import date
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from math import floor, ceil

# Set Streamlit page config (must be first)
st.set_page_config(page_title="PMU Tracker", layout="wide")

# Custom CSS
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
            background-color: rgba(255, 255, 255, 0.1);
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

def get_db():
    return SessionLocal()

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
    field_team = relationship("Employee", back_populates="tasks")

class FarmerData(Base):
    __tablename__ = "farmer_data"
    id = Column(Integer, primary_key=True)
    farmer_name = Column(String)
    number_of_cows = Column(Integer)
    yield_per_cow = Column(Float)
    date = Column(String)

# Preloaded users
preloaded_users = [
    ("Somanchi", "rsomanchi@tns.org", "password1"),
    ("Ranu", "rladdha@tns.org", "password2"),
    ("Pari", "paris@tns.org", "password3"),
    ("Muskan", "mkaushal@tns.org", "password4"),
    ("Rupesh", "rmukherjee@tns.org", "password5"),
    ("Shifali", "shifalis@tns.org", "password6"),
    ("Bhavya Kharoo", "bkharoo@tns.org", "password8")
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
            db.add(Program(name=program_name, description=f"Description for {program_name}", employee_id=1))
            db.commit()
        except IntegrityError:
            db.rollback()

# Drop and create tables
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# Preload data
preload_users()
preload_programs()

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
        "SAKSHAM Dashboard": "saksham_dashboard",
        "Training": "training",
        "Settings": "settings",
        "Google Drive": "google_drive",
        "Team Chat": "team_chat",
        "Email": "email",
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
    tab1, tab2, tab3, tab4 = st.tabs(["Field Team Dashboard", "PMU Dashboard", "Heritage Dashboard", "Ksheersagar Dashboard"])

    with tab1:
        st.subheader("📊 Progress")
        st.write("This is where you can display field team progress and metrics.")

    with tab2:
        pmu_dashboard(user)

    with tab3:
        heritage_dashboard()
 
    with tab4:
        ksheersagar_dashboard()


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
        wp_counts = wp_status_df["Status"].value_counts().reindex(["Not Started", "In Progress", "Completed"], fill_value=0)
        st.write("#### Workplans")
        st.dataframe(wp_counts.reset_index().rename(columns={"index": "Status", "Status": "Count"}))

        # Targets Summary
        tgt_status_df = pd.DataFrame([t.status for t in targets], columns=["Status"])
        tgt_counts = tgt_status_df["Status"].value_counts().reindex(["Not Started", "In Progress", "Completed"], fill_value=0)
        st.write("#### Targets")
        st.dataframe(tgt_counts.reset_index().rename(columns={"index": "Status", "Status": "Count"}))

        # Schedules
        st.write("#### Schedules")
        schedule_df = pd.DataFrame([{
            "Date": s.date,
            "Start": s.start_time,
            "End": s.end_time,
            "GMeet": s.gmeet_link or "N/A"
        } for s in schedules])
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
            workstream_titles = [ws.title for ws in db.query(WorkStream).filter_by(employee_id=user.id).all()]
            workstream = st.selectbox("Workstream", ["Select..."] + workstream_titles, index=0)

            submitted = st.form_submit_button("Save Work Plan")
            if submitted:
                if workstream != "Select...":
                    workstream_obj = db.query(WorkStream).filter_by(title=workstream, employee_id=user.id).first()
                    new_workplan = WorkPlan(
                        title=title, details=details,
                        deadline=str(deadline), status=status,
                        supervisor_id=user.id, workstream_id=workstream_obj.id
                    )
                    db.add(new_workplan)
                    db.commit()
                    st.success("✅ Work Plan saved successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Please select a workstream.")

    # Add New Target
    with st.expander("➕ Add New Target"):
        with st.form("target_form"):
            description = st.text_area("Target Description")
            deadline = st.date_input("Target Deadline")
            status = st.selectbox("Target Status", ["Not Started", "In Progress", "Completed"])

            if st.form_submit_button("Save Target"):
                new_target = Target(description=description, deadline=str(deadline), status=status, employee_id=user.id)
                db.add(new_target)
                db.commit()
                st.success("✅ Target saved.")
                st.experimental_rerun()

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
                    new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(plan.status))
                    submit_progress = st.form_submit_button("Update Progress")
                    if submit_progress:
                        plan.status = new_status
                        db.commit()
                        st.success("Progress updated!")
                        st.experimental_rerun()
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
                    new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(tgt.status))
                    submit_progress = st.form_submit_button("Update Progress")
                    if submit_progress:
                        tgt.status = new_status
                        db.commit()
                        st.success("Progress updated!")
                        st.experimental_rerun()
    else:
        st.info("No targets found.")

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
                new_program = Program(name=name, description=description, status=status, employee_id=st.session_state.user.id)
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
            st.markdown(f"**Name**: {program.name} | **Description**: {program.description} | **Status**: {program.status}")
    else:
        st.info("No programs found.")

def saksham_dashboard():
    st.subheader("🌱 SAKSHAM Dashboard")
    st.title("🌿 Plant Population & Seed Requirement Tool")
    st.markdown("""<hr style='margin-top: -15px; margin-bottom: 25px;'>""", unsafe_allow_html=True)

    with st.container():
        st.header("📅 Farmer Survey Entry")
        st.markdown("Fill in the details below to calculate how many seed packets are required for optimal plant population.")

        with st.form("survey_form"):
            col0, col1, col2 = st.columns(3)
            farmer_name = col0.text_input("👤 Farmer Name")
            farmer_id = col1.text_input("🆔 Farmer ID")
            state = col2.selectbox("🗽 State", ["Maharashtra", "Gujarat"])

            spacing_unit = st.selectbox("📏 Spacing Unit", ["cm", "m"])
            col3, col4, col5 = st.columns(3)
            row_spacing = col3.number_input("↔️ Row Spacing (between rows)", min_value=0.01, step=0.1)
            plant_spacing = col4.number_input("↕️ Plant Spacing (between plants)", min_value=0.01, step=0.1)
            land_acres = col5.number_input("🌾 Farm Area (acres)", min_value=0.01, step=0.1)

            mortality = st.slider("😓 Mortality %", min_value=0.0, max_value=100.0, value=5.0)

            submitted = st.form_submit_button("🔍 Calculate")

        if submitted and farmer_name and farmer_id:
            st.markdown("---")

            # Constants
            germination_rate_per_acre = {"Maharashtra": 14000, "Gujarat": 7400}
            confidence_interval = 0.70
            seeds_per_packet = 5625
            acre_to_m2 = 4046.86

            # Convert spacing
            if spacing_unit == "cm":
                row_spacing /= 100
                plant_spacing /= 100

            # Calculations
            plant_area_m2 = row_spacing * plant_spacing
            plants_per_m2 = 1 / plant_area_m2
            field_area_m2 = land_acres * acre_to_m2
            total_plants = plants_per_m2 * field_area_m2

            # Corrected Target Plants Calculation
            target_plants = total_plants * confidence_interval  # Based on calculated total plants

            required_seeds = target_plants / confidence_interval
            required_packets = floor(required_seeds / seeds_per_packet)

            effective_germination = confidence_interval * (1 - mortality / 100)
            expected_plants = total_plants * effective_germination
            gaps = total_plants - expected_plants
            gap_seeds = gaps / effective_germination
            gap_packets = floor(gap_seeds / seeds_per_packet)

            # Output
            st.subheader("<span style='font-size: 1.8rem;'>📊 Output Summary</span>", unsafe_allow_html=True)
            col6, col7, col8, col9 = st.columns(4)
            col6.metric("🧬 Calculated Capacity", f"{int(total_plants):,} plants")
            col7.metric("🎯 Target Plants", f"{int(target_plants):,} plants")
            col8.metric("🌱 Required Seeds", f"{int(required_seeds):,} seeds")
            col9.metric("📦 Seed Packets Needed", f"{required_packets} packets")

            st.markdown("""<hr style='margin-top: 25px;'>""", unsafe_allow_html=True)
            st.subheader("<span style='font-size: 1.8rem;'>📊 Gap Filling Summary</span>", unsafe_allow_html=True)
            col10, col11, col12 = st.columns(3)
            col10.metric("❓ Gaps (missing plants)", f"{int(gaps):,}")
            col11.metric("💼 Seeds for Gaps", f"{int(gap_seeds):,} seeds")
            col12.metric("📦 Packets for Gap Filling", f"{gap_packets} packets")

            st.caption("ℹ️ Based on 5625 seeds per 450g packet. Rounded down for field practicality. Gap seeds adjusted for mortality & germination.")

        elif submitted:
            st.error("⚠️ Please enter both Farmer Name and Farmer ID to proceed.")
# --- Heritage Dashboard ---
def heritage_dashboard():
    st.subheader("🏛️ Heritage Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🧑‍🌾 Total Farmers", "12,450")
    col2.metric("🍼 Avg Yield (L/Cow)", "7.8")
    col3.metric("📈 Impact Index", "84.2")

    st.markdown("---")
    
    india_data = pd.DataFrame({
        "State": ["Uttar Pradesh", "Maharashtra", "Bihar", "Rajasthan", "Gujarat"],
        "Code": ["UP", "MH", "BR", "RJ", "GJ"],
        "AdoptionRate": [78, 65, 83, 72, 69]
    })
    fig_map = px.choropleth(
        india_data,
        locations="Code",
        color="AdoptionRate",
        hover_name="State",
        color_continuous_scale="Blues",
        locationmode='ISO-3',
        title="Adoption Rate by State"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    pie_data = pd.DataFrame({
        "Category": ["Small", "Medium", "Large"],
        "Farmers": [6000, 4000, 2450]
    })
    fig_pie = px.pie(pie_data, values='Farmers', names='Category', hole=0.5, title="Farmer Size Distribution")
    st.plotly_chart(fig_pie, use_container_width=True)

    line_data = pd.DataFrame({
        "Year": list(range(2015, 2024)),
        "ImpactScore": [50, 55, 61, 66, 70, 74, 78, 82, 84]
    })
    fig_line = px.line(line_data, x="Year", y="ImpactScore", title="Yearly Impact Score")
    st.plotly_chart(fig_line, use_container_width=True)

    bar_data = pd.DataFrame({
        "Gender": ["Female", "Male"],
        "Participation": [5200, 7250]
    })
    fig_bar = px.bar(bar_data, x="Participation", y="Gender", orientation="h", title="Gender Participation")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- Ksheersagar Dashboard ---
def ksheersagar_dashboard():
    st.subheader("🐄 Ksheersagar 2.0 Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("🧬 Breed Diversity", "21 types")
    col2.metric("🧮 Avg Daily Milk (L)", "9.3")
    col3.metric("🔁 AI Coverage (%)", "67.4")

    st.markdown("---")

    prod_data = pd.DataFrame({
        "State": ["Punjab", "Haryana", "MP", "Karnataka", "TN"],
        "Code": ["PB", "HR", "MP", "KA", "TN"],
        "MilkProd": [870, 760, 580, 600, 620]
    })
    fig_map = px.choropleth(
        prod_data,
        locations="Code",
        color="MilkProd",
        hover_name="State",
        color_continuous_scale="YlGnBu",
        locationmode='ISO-3',
        title="Milk Production by State (L/Day)"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    breed_data = pd.DataFrame({
        "Breed": ["Sahiwal", "Gir", "Jersey", "HF"],
        "Count": [3400, 2800, 1500, 900]
    })
    fig_breed = px.pie(breed_data, names='Breed', values='Count', hole=0.5, title="Breed Composition")
    st.plotly_chart(fig_breed, use_container_width=True)

    trend_data = pd.DataFrame({
        "Year": list(range(2016, 2024)),
        "AI_Usage": [40, 45, 48, 52, 56, 60, 65, 67]
    })
    fig_trend = px.line(trend_data, x="Year", y="AI_Usage", title="Artificial Insemination Coverage Over Time")
    st.plotly_chart(fig_trend, use_container_width=True)

    class_data = pd.DataFrame({
        "Class": ["<5L", "5-10L", "10-15L", ">15L"],
        "Farms": [2200, 3800, 2700, 1100]
    })
    fig_class = px.bar(class_data, x="Farms", y="Class", orientation="h", title="Farm Distribution by Milk Output")
    st.plotly_chart(fig_class, use_container_width=True)


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
    theme = st.selectbox("Theme", ["Light", "Dark"], index=[""Light", "Dark"].index(st.session_state.settings["theme"]))
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
        # GMeet Placeholder
        generate_gmeet = st.checkbox("Generate GMeet Link?")
        gmeet_link = None
        if generate_gmeet:
            gmeet_link = "https://meet.google.com/placeholder"  # Placeholder link
            st.write(f"GMeet Link (Placeholder): {gmeet_link}")

        if st.form_submit_button("Add Schedule"):
            new_schedule = Schedule(employee_id=user.id, date=str(schedule_date), start_time=str(start_time), end_time=str(end_time), gmeet_link=gmeet_link)
            db.add(new_schedule)
            db.commit()
            st.success("Schedule added successfully!")

    st.subheader("Your Schedules")
    schedules = db.query(Schedule).filter_by(employee_id=user.id).all()
    for schedule in schedules:
        st.markdown(f"**Date**: {schedule.date} | **Start**: {schedule.start_time} | **End**: {schedule.end_time} | **GMeet Link**: {schedule.gmeet_link if schedule.gmeet_link else 'N/A'}")

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
                st.experimental_rerun()
    else:
        st.write("No field teams available.")

def training():
    st.subheader("📚 Training Module")
    st.write("This section provides training materials and resources.")

    # Upload Training Content
    st.header("📤 Upload Training Content")
    selected_program = st.selectbox("🌟 Select Program", ["Cotton", "Dairy"], key="program_dropdown")
    selected_category = st.selectbox("📂 Select Category", ["Presentations", "Videos", "Audios", "Quizzes"], key="category_dropdown")
    uploaded_file = st.file_uploader("Choose a file to upload", type=["pdf", "mp4", "mp3", "json", "pptx", "xlsx", "png", "jpg", "jpeg"])

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
                        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully to {save_dir} (Simulated Google Drive)!")
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
        "Quizzes": [".xlsx", ".png", ".jpg", ".jpeg"]
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

# In-house Team Chat Functionality
def team_chat():
    st.subheader("Team Chat")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    new_message = st.text_input("Enter your message:")
    if st.button("Send"):
        if new_message:
            st.session_state.chat_history.append(f"{st.session_state.user.name}: {new_message}")

    if st.session_state.chat_history:
        for message in st.session_state.chat_history:
            st.write(message)

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
        elif selected_tab == "logout":
            st.session_state.user = None
            st.success("You have been logged out.")

if __name__ == "__main__":
    main()
