from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cafe_id = Column(Integer, ForeignKey("cafes.id"), nullable=False)
    date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=False)
    guests = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reservations")
    cafe = relationship("Cafe", back_populates="reservations")
