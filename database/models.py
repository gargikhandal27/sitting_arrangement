"""
SQLAlchemy models – normalized schema for the Examination Allocation System.
"""
from datetime import datetime, date, time
from typing import Optional, List

from sqlalchemy import (
    String, Integer, Boolean, DateTime, Date, Time, Text, Float,
    ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base


# -------------------------------------------------
# Core Master Data
# -------------------------------------------------

class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    roll_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    student_name: Mapped[str] = mapped_column(String(200), nullable=False)
    batch: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations: Mapped[List["SessionRegistration"]] = relationship(back_populates="student")
    assignments: Mapped[List["StudentSeatAssignment"]] = relationship(back_populates="student")

    def __repr__(self) -> str:
        return f"<Student {self.student_id} – {self.student_name}>"


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    room_name: Mapped[str] = mapped_column(String(200), nullable=False)
    rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    columns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    layout_source: Mapped[str] = mapped_column(String(50), default="manual")  # manual | image | csv
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seats: Mapped[List["Seat"]] = relationship(back_populates="classroom", cascade="all, delete-orphan")
    images: Mapped[List["ClassroomImage"]] = relationship(back_populates="classroom", cascade="all, delete-orphan")
    unavailable_seats: Mapped[List["UnavailableSeat"]] = relationship(back_populates="classroom", cascade="all, delete-orphan")
    supervisor_assignments: Mapped[List["SupervisorAssignment"]] = relationship(back_populates="classroom")

    def __repr__(self) -> str:
        return f"<Classroom {self.room_id} – {self.room_name}>"


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("classroom_id", "seat_code", name="uq_classroom_seat_code"),
        Index("ix_seat_classroom_row_col", "classroom_id", "row_number", "column_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    seat_code: Mapped[str] = mapped_column(String(50), nullable=False)
    row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    image_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    detection_source: Mapped[str] = mapped_column(String(50), default="manual")  # manual | auto | corrected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    classroom: Mapped["Classroom"] = relationship(back_populates="seats")
    assignments: Mapped[List["StudentSeatAssignment"]] = relationship(back_populates="seat")

    def __repr__(self) -> str:
        return f"<Seat {self.seat_code} in classroom_id={self.classroom_id}>"


class UnavailableSeat(Base):
    __tablename__ = "unavailable_seats"
    __table_args__ = (
        UniqueConstraint("classroom_id", "row_number", "column_number", name="uq_unavailable_seat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    column_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    classroom: Mapped["Classroom"] = relationship(back_populates="unavailable_seats")


class ClassroomImage(Base):
    __tablename__ = "classroom_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    image_type: Mapped[str] = mapped_column(String(50), default="photograph")  # photograph | floor_plan
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    classroom: Mapped["Classroom"] = relationship(back_populates="images")


class Supervisor(Base):
    __tablename__ = "supervisors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supervisor_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supervisor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments: Mapped[List["SupervisorAssignment"]] = relationship(back_populates="supervisor")

    def __repr__(self) -> str:
        return f"<Supervisor {self.supervisor_id} – {self.supervisor_name}>"


# -------------------------------------------------
# Examination Session
# -------------------------------------------------

class ExaminationSession(Base):
    __tablename__ = "examination_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    session_name: Mapped[str] = mapped_column(String(200), nullable=False)
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | configured | solved | verified | archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations: Mapped[List["SessionRegistration"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    plans: Mapped[List["SeatingPlan"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ExaminationSession {self.session_code}>"


class SessionRegistration(Base):
    __tablename__ = "session_registrations"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("examination_sessions.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ExaminationSession"] = relationship(back_populates="registrations")
    student: Mapped["Student"] = relationship(back_populates="registrations")


# -------------------------------------------------
# Seating Plan & Assignments
# -------------------------------------------------

class SeatingPlan(Base):
    __tablename__ = "seating_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("examination_sessions.id", ondelete="CASCADE"), nullable=False)
    plan_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | solved | verified | rejected
    solver_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    solver_runtime_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rooms_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    students_assigned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    configuration_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session: Mapped["ExaminationSession"] = relationship(back_populates="plans")
    student_assignments: Mapped[List["StudentSeatAssignment"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    supervisor_assignments: Mapped[List["SupervisorAssignment"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    verification: Mapped[Optional["VerificationResult"]] = relationship(back_populates="plan", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<SeatingPlan {self.plan_name} ({self.status})>"


class StudentSeatAssignment(Base):
    __tablename__ = "student_seat_assignments"
    __table_args__ = (
        UniqueConstraint("plan_id", "student_id", name="uq_plan_student"),
        UniqueConstraint("plan_id", "seat_id", name="uq_plan_seat"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("seating_plans.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="CASCADE"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped["SeatingPlan"] = relationship(back_populates="student_assignments")
    student: Mapped["Student"] = relationship(back_populates="assignments")
    seat: Mapped["Seat"] = relationship(back_populates="assignments")


class SupervisorAssignment(Base):
    __tablename__ = "supervisor_assignments"
    __table_args__ = (
        UniqueConstraint("plan_id", "supervisor_id", name="uq_plan_supervisor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("seating_plans.id", ondelete="CASCADE"), nullable=False)
    supervisor_id: Mapped[int] = mapped_column(ForeignKey("supervisors.id", ondelete="CASCADE"), nullable=False)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    duty_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan: Mapped["SeatingPlan"] = relationship(back_populates="supervisor_assignments")
    supervisor: Mapped["Supervisor"] = relationship(back_populates="assignments")
    classroom: Mapped["Classroom"] = relationship(back_populates="supervisor_assignments")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("seating_plans.id", ondelete="CASCADE"), unique=True, nullable=False)
    overall_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    checks_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    violations_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    plan: Mapped["SeatingPlan"] = relationship(back_populates="verification")
