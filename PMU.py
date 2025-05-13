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

# State init
if "user" not in st.session_state:
    st.session_state.user = None

def get_db():
    return SessionLocal()

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
        st.error("Email already registered")
        return
    user = Employee(name=name, email=email, hashed_password=bcrypt.hash(password))
    db.add(user)
    db.commit()
    st.success("Registered successfully. You can login now.")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if login(email, password):
    st.session_state.just_logged_in = True
    st.success("Welcome back!")
    st.stop()

    st.sidebar.title(f"Hello {user.name} 👋")
    if st.sidebar.button("Logout"):
       st.session_state.user = None
       st.session_state.just_logged_out = True
       st.stop()



    st.subheader("📋 Add Workstream")
    with st.form("add_ws"):
        ws_title = st.text_input("Title")
        ws_desc = st.text_area("Description")
        if st.form_submit_button("Add Workstream"):
            ws = WorkStream(title=ws_title, description=ws_desc, employee_id=user.id)
            db.add(ws)
            db.commit()
            st.success("Workstream added")

    st.subheader("📝 Add Workplan to My Workstreams")
    my_ws = db.query(WorkStream).filter_by(employee_id=user.id).all()
    if my_ws:
        ws_options = {f"{ws.title}": ws.id for ws in my_ws}
        with st.form("add_wp"):
            selected_ws = st.selectbox("Select Workstream", list(ws_options.keys()))
            wp_title = st.text_input("Plan Title")
            wp_details = st.text_area("Plan Details")
            if st.form_submit_button("Add Workplan"):
                wp = WorkPlan(title=wp_title, details=wp_details, workstream_id=ws_options[selected_ws])
                db.add(wp)
                db.commit()
                st.success("Workplan added")

    st.subheader("🔍 View All Workstreams & Plans")
    all_ws = db.query(WorkStream).all()
    for ws in all_ws:
        st.markdown(f"### {ws.title} ({ws.employee.name})")
        st.markdown(ws.description)
        for wp in ws.workplans:
            st.markdown(f"- **{wp.title}**: {wp.details}")
        if ws.employee_id == user.id:
            if st.button(f"Delete '{ws.title}'", key=f"del-ws-{ws.id}"):
                db.query(WorkPlan).filter_by(workstream_id=ws.id).delete()
                db.delete(ws)
                db.commit()
                st.success("Deleted")
                st.experimental_rerun()

if __name__ == "__main__":
    main()
