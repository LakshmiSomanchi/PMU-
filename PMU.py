import streamlit as st
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from datetime import date

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

class WorkStream(Base):
    __tablename__ = "workstreams"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
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

Base.metadata.create_all(bind=engine)

if "user" not in st.session_state:
    st.session_state.user = None

preloaded_users = [
    ("Somanchi", "rsomanchi@tns.org"),
    ("Ranu", "Rladdha@tns.org"),
    ("Pari", "Paris@tns.org"),
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
        if not db.query(Employee).filter_by(email=email).first():
            db.add(Employee(name=name, email=email))
    db.commit()

def dashboard(user):
    db = get_db()
    st.markdown("<h1 style='text-align:center; color:#1a73e8;'>🚀 Project Management Dashboard</h1>", unsafe_allow_html=True)

    st.sidebar.markdown("### Logged in as")
    st.sidebar.success(user.name)
    if st.sidebar.button("🔓 Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    tabs = st.tabs(["👤 My Dashboard", "🌍 Team Overview", "📊 Tracker Report", "👥 User Management"])

    with tabs[0]:
        st.subheader("📌 Your Activities, Targets & Progress")
        my_ws = db.query(WorkStream).filter_by(employee_id=user.id).all()

        with st.expander("➕ Add Workstream"):
            with st.form("add_ws"):
                ws_title = st.text_input("Workstream Title")
                ws_desc = st.text_area("Description")
                if st.form_submit_button("Add"):
                    db.add(WorkStream(title=ws_title, description=ws_desc, employee_id=user.id))
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

        for ws in my_ws:
            st.markdown(f"### 🎯 {ws.title}")
            st.markdown(f"_Description_: {ws.description}")
            for wp in ws.workplans:
                badge = "✅" if wp.status == "Completed" else ("🟡" if wp.status == "In Progress" else "⚪")
                st.markdown(f"- {badge} **{wp.title}** | 📆 {wp.deadline} | _{wp.status}_<br>{wp.details}", unsafe_allow_html=True)

    with tabs[1]:
        st.subheader("🌐 Team Workstreams and Plans")
        all_ws = db.query(WorkStream).all()
        for ws in all_ws:
            st.markdown(f"<div style='background:#f0f9ff;padding:10px;border-left:6px solid #1e88e5;margin-bottom:10px;'>", unsafe_allow_html=True)
            st.markdown(f"<strong>{ws.title}</strong> by <em>{ws.employee.name}</em><br><small>{ws.description}</small>", unsafe_allow_html=True)
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
            report_data.append({"Employee": emp.name, "Workstreams": total_ws, "Workplans": total_wp, "Completed": completed_wp})
        df = pd.DataFrame(report_data)
        st.dataframe(df)
        st.bar_chart(df.set_index("Employee")[["Workplans", "Completed"]])

    with tabs[3]:
        st.subheader("👥 Manage Users")
        with st.form("add_user"):
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            if st.form_submit_button("Add"):
                db.add(Employee(name=new_name, email=new_email))
                db.commit()
                st.success("User added successfully")

        with st.form("remove_user"):
            remove_email = st.text_input("Email to Remove")
            if st.form_submit_button("Delete"):
                user = db.query(Employee).filter(Employee.email == remove_email).first()
                if user:
                    db.delete(user)
                    db.commit()
                    st.success("User deleted")
                else:
                    st.warning("Email not found")

def main():
    preload_users()
    st.set_page_config(page_title="PMU Tracker", layout="wide")
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #007acc;
        color: white;
        padding: 0.4rem 1rem;
        font-weight: bold;
    }
    .stTextInput>div>input, .stTextArea textarea, .stSelectbox>div>div {
        border-radius: 6px;
        border: 1px solid #ccc;
    }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.user:
        st.title("🔐 Login")
        db = get_db()
        all_users = db.query(Employee).all()
        emails = [u.email for u in all_users]
        selected = st.selectbox("Select your email", ["Select..."] + emails, index=0)
        if selected != "Select...":
            user = db.query(Employee).filter_by(email=selected).first()
            st.session_state.user = user
            st.experimental_rerun()
    else:
        dashboard(st.session_state.user)

if __name__ == "__main__":
    main()
