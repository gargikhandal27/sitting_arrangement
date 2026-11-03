"""
Classroom Layout Service
Unified representation of seats, adjacency, and manual layout management.
"""
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from database.models import Classroom, Seat, UnavailableSeat


@dataclass
class SeatInfo:
    """Unified seat representation used by the solver and UI."""
    seat_id: int                  # database primary key
    seat_code: str
    classroom_id: int
    room_id: str
    row: Optional[int]
    col: Optional[int]
    is_available: bool
    is_confirmed: bool
    detection_source: str = "manual"


@dataclass
class ClassroomLayout:
    """Unified classroom layout used throughout the system."""
    classroom_id: int
    room_id: str
    room_name: str
    rows: Optional[int]
    columns: Optional[int]
    layout_source: str
    is_available: bool
    seats: List[SeatInfo] = field(default_factory=list)

    @property
    def total_seats(self) -> int:
        return len(self.seats)

    @property
    def usable_seats(self) -> int:
        return sum(1 for s in self.seats if s.is_available)

    @property
    def confirmed(self) -> bool:
        return all(s.is_confirmed for s in self.seats) and len(self.seats) > 0


def get_classroom_layout(db: Session, classroom_id: int) -> Optional[ClassroomLayout]:
    """Load a classroom and its seats into the unified representation."""
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        return None

    seats = db.scalars(
        select(Seat).where(Seat.classroom_id == classroom_id).order_by(Seat.row_number, Seat.column_number)
    ).all()

    seat_infos = [
        SeatInfo(
            seat_id=s.id,
            seat_code=s.seat_code,
            classroom_id=classroom.id,
            room_id=classroom.room_id,
            row=s.row_number,
            col=s.column_number,
            is_available=s.is_available,
            is_confirmed=s.is_confirmed,
            detection_source=s.detection_source,
        )
        for s in seats
    ]

    return ClassroomLayout(
        classroom_id=classroom.id,
        room_id=classroom.room_id,
        room_name=classroom.room_name,
        rows=classroom.rows,
        columns=classroom.columns,
        layout_source=classroom.layout_source,
        is_available=classroom.is_available,
        seats=seat_infos,
    )


def get_all_layouts(db: Session) -> List[ClassroomLayout]:
    classrooms = db.scalars(select(Classroom).order_by(Classroom.room_id)).all()
    return [get_classroom_layout(db, c.id) for c in classrooms if c is not None]


def create_manual_classroom(
    db: Session,
    room_id: str,
    room_name: str,
    rows: int,
    columns: int,
    is_available: bool = True,
) -> Tuple[bool, str, Optional[int]]:
    """
    Create a new classroom with a regular grid of seats.
    Returns (success, message, classroom_id)
    """
    if rows <= 0 or columns <= 0:
        return False, "Rows and columns must be positive integers.", None

    existing = db.scalar(select(Classroom).where(Classroom.room_id == room_id))
    if existing:
        return False, f"Classroom with room_id '{room_id}' already exists.", None

    classroom = Classroom(
        room_id=room_id.strip(),
        room_name=room_name.strip(),
        rows=rows,
        columns=columns,
        is_available=is_available,
        layout_source="manual",
    )
    db.add(classroom)
    db.flush()

    for r in range(1, rows + 1):
        for c in range(1, columns + 1):
            seat = Seat(
                classroom_id=classroom.id,
                seat_code=f"R{r}C{c}",
                row_number=r,
                column_number=c,
                is_available=True,
                is_confirmed=True,
                detection_source="manual",
            )
            db.add(seat)

    db.commit()
    return True, f"Created classroom '{room_id}' with {rows * columns} seats.", classroom.id


def set_seat_availability(
    db: Session,
    seat_id: int,
    is_available: bool,
    reason: Optional[str] = None,
) -> Tuple[bool, str]:
    """Mark a single seat available or unavailable."""
    seat = db.get(Seat, seat_id)
    if not seat:
        return False, "Seat not found."

    seat.is_available = is_available
    seat.is_confirmed = True

    # Maintain UnavailableSeat table for audit
    if not is_available:
        existing = db.scalar(
            select(UnavailableSeat).where(
                UnavailableSeat.classroom_id == seat.classroom_id,
                UnavailableSeat.row_number == seat.row_number,
                UnavailableSeat.column_number == seat.column_number,
            )
        )
        if not existing and seat.row_number is not None and seat.column_number is not None:
            db.add(UnavailableSeat(
                classroom_id=seat.classroom_id,
                row_number=seat.row_number,
                column_number=seat.column_number,
                reason=reason or "Marked unavailable by administrator",
            ))
    else:
        # Remove from unavailable list if present
        db.execute(
            delete(UnavailableSeat).where(
                UnavailableSeat.classroom_id == seat.classroom_id,
                UnavailableSeat.row_number == seat.row_number,
                UnavailableSeat.column_number == seat.column_number,
            )
        )

    db.commit()
    status = "available" if is_available else "unavailable"
    return True, f"Seat {seat.seat_code} marked as {status}."


def confirm_layout(db: Session, classroom_id: int) -> Tuple[bool, str]:
    """Mark all seats of a classroom as confirmed."""
    seats = db.scalars(select(Seat).where(Seat.classroom_id == classroom_id)).all()
    if not seats:
        return False, "No seats found for this classroom."

    for s in seats:
        s.is_confirmed = True
    db.commit()
    return True, f"Layout confirmed for {len(seats)} seats."


def build_adjacency_list(
    layout: ClassroomLayout,
    mode: str = "horizontal_vertical",
) -> Dict[int, List[int]]:
    """
    Build adjacency list from a ClassroomLayout.
    mode: "horizontal" | "horizontal_vertical"
    Returns dict: seat_id -> list of neighboring seat_ids
    """
    # Map (row, col) -> seat_id for quick lookup
    pos_to_id: Dict[Tuple[int, int], int] = {}
    for s in layout.seats:
        if s.row is not None and s.col is not None and s.is_available:
            pos_to_id[(s.row, s.col)] = s.seat_id

    adjacency: Dict[int, List[int]] = {s.seat_id: [] for s in layout.seats if s.is_available}

    for s in layout.seats:
        if not s.is_available or s.row is None or s.col is None:
            continue

        neighbors = []
        # Horizontal neighbors
        for dc in (-1, 1):
            key = (s.row, s.col + dc)
            if key in pos_to_id:
                neighbors.append(pos_to_id[key])

        # Vertical neighbors
        if mode == "horizontal_vertical":
            for dr in (-1, 1):
                key = (s.row + dr, s.col)
                if key in pos_to_id:
                    neighbors.append(pos_to_id[key])

        adjacency[s.seat_id] = neighbors

    return adjacency


def get_layout_summary(db: Session) -> List[Dict]:
    """Return a list of summary dicts for UI display."""
    layouts = get_all_layouts(db)
    return [
        {
            "classroom_id": lay.classroom_id,
            "room_id": lay.room_id,
            "room_name": lay.room_name,
            "rows": lay.rows,
            "columns": lay.columns,
            "total_seats": lay.total_seats,
            "usable_seats": lay.usable_seats,
            "layout_source": lay.layout_source,
            "confirmed": lay.confirmed,
            "is_available": lay.is_available,
        }
        for lay in layouts
    ]
