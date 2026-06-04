from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cafe_id = Column(Integer, ForeignKey("cafes.id"), nullable=False)
    content = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reviews")
    cafe = relationship("Cafe", back_populates="reviews")
    scores = relationship("ReviewScore", back_populates="review", cascade="all, delete-orphan")
    photos = relationship("ReviewPhoto", back_populates="review", cascade="all, delete-orphan")

    @property
    def score_dict(self):
        return {s.dimension: s.score for s in self.scores}

    @property
    def overall_score(self):
        if not self.scores:
            return 0
        return round(sum(s.score for s in self.scores) / len(self.scores), 1)


class ReviewScore(Base):
    __tablename__ = "review_scores"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    dimension = Column(String(30), nullable=False)  # coffee, dessert, ambience, focus
    score = Column(Float, nullable=False)

    review = relationship("Review", back_populates="scores")


class ReviewPhoto(Base):
    __tablename__ = "review_photos"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    url = Column(String(500), nullable=False)

    review = relationship("Review", back_populates="photos")
