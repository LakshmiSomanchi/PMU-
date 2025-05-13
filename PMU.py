import streamlit as st
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd

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
    st.sidebar.title(f"🎮 Welcome, {user.name}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

    st.title("🏆 Workstream Dashboard")
    tabs = st.tabs(["👤 My Dashboard", "🌍 Team Overview", "📊 Tracker Report", "👥 User Management"])

    with tabs[0]:
        st.subheader("🎯 Your Workstreams")
        my_ws = db.query(WorkStream).filter_by(employee_id=user.id).all()

        with st.expander("➕ Add Workstream"):
            with st.form("add_ws"):
                ws_title = st.text_input("Workstream Title")
                ws_desc = st.text_area("Description")
                if st.form_submit_button("Add"):
                    db.add(WorkStream(title=ws_title, description=ws_desc, employee_id=user.id))
                    db.commit()
                    st.success("Workstream added")

        with st.expander("➕ Add Workplan to Your Workstreams"):
            if my_ws:
                ws_options = {f"{ws.title}": ws.id for ws in my_ws}
                with st.form("add_wp"):
                    selected_ws = st.selectbox("Select Workstream", list(ws_options.keys()))
                    wp_title = st.text_input("Plan Title")
                    wp_details = st.text_area("Plan Details")
                    if st.form_submit_button("Add Plan"):
                        db.add(WorkPlan(title=wp_title, details=wp_details, workstream_id=ws_options[selected_ws]))
                        db.commit()
                        st.success("Workplan added")

        for ws in my_ws:
            st.markdown(f"#### ✅ {ws.title}")
            st.markdown(f"{ws.description}")
            for wp in ws.workplans:
                st.markdown(f"- 🧩 **{wp.title}**: {wp.details}")
            if st.button(f"🗑️ Delete '{ws.title}'", key=f"del-{ws.id}"):
                db.query(WorkPlan).filter_by(workstream_id=ws.id).delete()
                db.delete(ws)
                db.commit()
                st.warning("Deleted!")
                st.stop()

    with tabs[1]:
        st.subheader("🌐 Team Workstreams and Plans")
        all_ws = db.query(WorkStream).all()
        for ws in all_ws:
            st.markdown(f"<div style='background:#f0f4ff;padding:10px;border-left:6px solid #1e88e5;margin-bottom:10px;'>", unsafe_allow_html=True)
            st.markdown(f"<strong>{ws.title}</strong> by <em>{ws.employee.name}</em><br><small>{ws.description}</small>", unsafe_allow_html=True)
            for wp in ws.workplans:
                st.markdown(f"<li><b>{wp.title}</b>: {wp.details}</li>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.subheader("📊 Overall Progress Tracker")
        employees = db.query(Employee).all()
        report_data = []
        for emp in employees:
            total_ws = db.query(WorkStream).filter_by(employee_id=emp.id).count()
            total_wp = sum(len(ws.workplans) for ws in emp.workstreams)
            report_data.append({"Employee": emp.name, "Workstreams": total_ws, "Workplans": total_wp})
        df = pd.DataFrame(report_data)
        st.dataframe(df.style.background_gradient(cmap="Blues"))
        st.bar_chart(df.set_index("Employee"))

    with tabs[3]:
        st.subheader("👥 Admin - Manage Users")
        with st.form("add_user"):
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            if st.form_submit_button("Add User"):
                db.add(Employee(name=new_name, email=new_email))
                db.commit()
                st.success("User added")

        with st.form("remove_user"):
            remove_email = st.text_input("User Email to Remove")
            if st.form_submit_button("Delete User"):
                user = db.query(Employee).filter(Employee.email == remove_email).first()
                if user:
                    db.delete(user)
                    db.commit()
                    st.success("User deleted")
                else:
                    st.warning("User not found")

def main():
    preload_users()
    st.set_page_config(page_title="Team Tracker", layout="wide")
    st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        border-radius: 8px;
        background-color: #1e88e5;
        color: white;
        padding: 0.5rem 1.2rem;
        font-weight: bold;
    }
    .stTextInput>div>input, .stTextArea textarea {
        border-radius: 6px;
        padding: 0.4rem;
        border: 1px solid #ccc;
    }
    .stSelectbox>div>div {
        border-radius: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.user:
        st.title("🧑 Select Your Email")
        db = get_db()
        all_users = db.query(Employee).all()
        user_emails = [user.email for user in all_users]
        selected_email = st.selectbox("Login as", user_emails)
        if st.button("Continue"):
            user = db.query(Employee).filter_by(email=selected_email).first()
            st.session_state.user = user
            st.experimental_rerun()
    else:
        dashboard(st.session_state.user)

if __name__ == "__main__":
    main()
