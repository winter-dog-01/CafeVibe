from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.reservation import Reservation
from app.models.meetup import Meetup, MeetupMember
from app.models.review import Review
from app.models.favorite import Favorite
from app.models.cafe import Cafe, CafePhoto
from app.models.tag import Tag
from app.models.user import User
from app.dependencies import require_login

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/profile", response_class=HTMLResponse)
def profile(
    request: Request,
    tab: str = Query(default="favorites"),
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    favorites = (
        db.query(Favorite)
        .options(
            joinedload(Favorite.cafe).joinedload(Cafe.photos),
            joinedload(Favorite.cafe).joinedload(Cafe.tags),
        )
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.saved_at.desc())
        .all()
    )
    reservations = (
        db.query(Reservation)
        .options(joinedload(Reservation.cafe))
        .filter(Reservation.user_id == current_user.id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    meetups_joined = (
        db.query(MeetupMember)
        .options(
            joinedload(MeetupMember.meetup).joinedload(Meetup.cafe),
            joinedload(MeetupMember.meetup).joinedload(Meetup.organizer),
            joinedload(MeetupMember.meetup).joinedload(Meetup.members),
        )
        .filter(MeetupMember.user_id == current_user.id)
        .all()
    )
    reviews = (
        db.query(Review)
        .options(joinedload(Review.cafe), joinedload(Review.scores))
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("profile/index.html", {
        "request": request,
        "current_user": current_user,
        "tab": tab,
        "favorites": favorites,
        "reservations": reservations,
        "meetups_joined": meetups_joined,
        "reviews": reviews,
    })
