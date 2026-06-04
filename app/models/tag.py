from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


cafe_tags_table = Table(
    "cafe_tags",
    Base.metadata,
    Column("cafe_id", Integer, ForeignKey("cafes.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(60), unique=True, nullable=False)
    category = Column(String(30), nullable=False)
    icon = Column(String(10), nullable=True)

    cafes = relationship("Cafe", secondary="cafe_tags", back_populates="tags")


# Alias for __init__ import compatibility
CafeTag = cafe_tags_table
