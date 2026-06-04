from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Cafe(Base):
    __tablename__ = "cafes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(300), nullable=False)
    district = Column(String(50), nullable=True)
    city = Column(String(50), default="台北市")
    phone = Column(String(20), nullable=True)
    opening_hours = Column(String(200), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    instagram_url = Column(String(300), nullable=True)
    google_maps_url = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    photos = relationship("CafePhoto", back_populates="cafe", cascade="all, delete-orphan", order_by="CafePhoto.sort_order")
    tags = relationship("Tag", secondary="cafe_tags", back_populates="cafes")
    reviews = relationship("Review", back_populates="cafe", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="cafe", cascade="all, delete-orphan")
    meetups = relationship("Meetup", back_populates="cafe", cascade="all, delete-orphan")
    favorited_by = relationship("Favorite", back_populates="cafe", cascade="all, delete-orphan")

    @property
    def avg_scores(self):
        if not self.reviews:
            return {"coffee": 0, "dessert": 0, "ambience": 0, "focus": 0, "overall": 0}
        dims = {"coffee": [], "dessert": [], "ambience": [], "focus": []}
        for review in self.reviews:
            for score in review.scores:
                if score.dimension in dims:
                    dims[score.dimension].append(score.score)
        result = {k: round(sum(v) / len(v), 1) if v else 0 for k, v in dims.items()}
        all_scores = [s for v in dims.values() for s in v]
        result["overall"] = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
        return result

    @property
    def review_count(self):
        return len(self.reviews)


class CafePhoto(Base):
    __tablename__ = "cafe_photos"

    id = Column(Integer, primary_key=True, index=True)
    cafe_id = Column(Integer, ForeignKey("cafes.id"), nullable=False)
    url = Column(String(500), nullable=False)
    caption = Column(String(200), nullable=True)
    sort_order = Column(Integer, default=0)
    is_cover = Column(Boolean, default=False)

    cafe = relationship("Cafe", back_populates="photos")
