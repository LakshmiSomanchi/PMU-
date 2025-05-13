import streamlit as st
from sqlalchemy import Column, Integer, String, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from passlib.hash import bcrypt
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
    hashed_password = Column(String)
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

# Helpers
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
            db.add(Employee(name=name, email=email, hashed_password=bcrypt.hash("password")))
    db.commit()

def login(email, password):
    db = get_db()
    user = db.query(Employee).filter(Employee.email == email).first()
    if user and bcrypt.verify(password, user.hashed_password):
        st.session_state.user = user
        return True
    return False

def register(name, email, password):
    db = get_db()
    if db.query(Employee).filter(Employee.email == email).first():
        st.error("Email already exists")
        return
    db.add(Employee(name=name, email=email, hashed_password=bcrypt.hash(password)))
    db.commit()
    st.success("User registered successfully")

def delete_user(email):
    db = get_db()
    user = db.query(Employee).filter(Employee.email == email).first()
    if user:
        db.delete(user)
        db.commit()
        st.success("User deleted")
    else:
        st.warning("User not found")

def dashboard(user):
    db = get_db()
    st.sidebar.title(f"🎮 Welcome, {user.name}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.stop()

    st.title("🏆 Workstream Dashboard")
    st.markdown("### 🎯 Your Workstreams")
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

    st.markdown("---")
    st.markdown("### 🌎 Team Overview")
    all_ws = db.query(WorkStream).all()
    for ws in all_ws:
        st.markdown(f"#### 📌 {ws.title} ({ws.employee.name})")
        for wp in ws.workplans:
            st.markdown(f"- 📄 **{wp.title}**: {wp.details}")

    with st.expander("👥 Admin - Manage Users"):
        with st.form("add_user"):
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            new_pw = st.text_input("Password", type="password")
            if st.form_submit_button("Add User"):
                register(new_name, new_email, new_pw)

        with st.form("remove_user"):
            remove_email = st.text_input("User Email to Remove")
            if st.form_submit_button("Delete User"):
                delete_user(remove_email)

def main():
    preload_users()
    st.set_page_config(page_title="Team Tracker", layout="wide")

    if not st.session_state.user:
        st.title("🔐 Login")
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if login(email, password):
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
    else:
        dashboard(st.session_state.user)

if __name__ == "__main__":
    main()
