from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MeetupStatus(str, enum.Enum):
    open = "open"
    full = "full"
    closed = "closed"
    expired = "expired"


class Meetup(Base):
    __tablename__ = "meetups"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cafe_id = Column(Integer, ForeignKey("cafes.id"), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    purpose_tags = Column(String(200), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    max_members = Column(Integer, default=4)
    status = Column(Enum(MeetupStatus), default=MeetupStatus.open)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organizer = relationship("User", back_populates="meetups_created")
    cafe = relationship("Cafe", back_populates="meetups")
    members = relationship("MeetupMember", back_populates="meetup", cascade="all, delete-orphan")
    messages = relationship("MeetupMessage", back_populates="meetup", cascade="all, delete-orphan", order_by="MeetupMessage.created_at")

    @property
    def current_count(self):
        return len([m for m in self.members if m.status == "joined"])

    @property
    def is_joinable(self):
        return self.status == MeetupStatus.open and self.current_count < self.max_members


class MeetupMember(Base):
    __tablename__ = "meetup_members"

    id = Column(Integer, primary_key=True, index=True)
    meetup_id = Column(Integer, ForeignKey("meetups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="joined")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    meetup = relationship("Meetup", back_populates="members")
    user = relationship("User", back_populates="meetup_memberships")


class MeetupMessage(Base):
    __tablename__ = "meetup_messages"

    id = Column(Integer, primary_key=True, index=True)
    meetup_id = Column(Integer, ForeignKey("meetups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    meetup = relationship("Meetup", back_populates="messages")
    user = relationship("User")
