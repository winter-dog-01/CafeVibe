from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cafe import Cafe
from app.models.review import Review, ReviewScore
from app.models.reservation import Reservation, ReservationStatus
from app.models.meetup import Meetup, MeetupMember, MeetupStatus, MeetupMessage
from app.models.favorite import Favorite
from app.dependencies import get_current_user, require_login
from datetime import date, datetime

router = APIRouter(prefix="/api")


@router.post("/favorites/toggle")
def toggle_favorite(
    cafe_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    existing = db.query(Favorite).filter_by(user_id=current_user.id, cafe_id=cafe_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return JSONResponse({"favorited": False})
    db.add(Favorite(user_id=current_user.id, cafe_id=cafe_id))
    db.commit()
    return JSONResponse({"favorited": True})


@router.post("/reviews")
def post_review(
    request: Request,
    cafe_id: int = Form(...),
    content: str = Form(""),
    score_coffee: float = Form(...),
    score_dessert: float = Form(...),
    score_ambience: float = Form(...),
    score_focus: float = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    review = Review(user_id=current_user.id, cafe_id=cafe_id, content=content)
    db.add(review)
    db.flush()
    for dim, val in [("coffee", score_coffee), ("dessert", score_dessert),
                     ("ambience", score_ambience), ("focus", score_focus)]:
        db.add(ReviewScore(review_id=review.id, dimension=dim, score=val))
    db.commit()
    cafe = db.get(Cafe, cafe_id)
    return RedirectResponse(f"/cafe/{cafe.slug}#reviews", status_code=302)


@router.post("/reservations")
def make_reservation(
    request: Request,
    cafe_id: int = Form(...),
    res_date: date = Form(...),
    time_slot: str = Form(...),
    guests: int = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    if res_date < date.today():
        raise HTTPException(status_code=400, detail="不能預約過去的日期")
    existing = db.query(Reservation).filter_by(
        cafe_id=cafe_id, date=res_date, time_slot=time_slot, status=ReservationStatus.confirmed
    ).count()
    if existing >= 10:
        raise HTTPException(status_code=400, detail="此時段已額滿")
    reservation = Reservation(
        user_id=current_user.id, cafe_id=cafe_id,
        date=res_date, time_slot=time_slot, guests=guests, notes=notes,
    )
    db.add(reservation)
    db.commit()
    return RedirectResponse("/profile?tab=reservations", status_code=302)


@router.post("/meetups")
def create_meetup(
    request: Request,
    cafe_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    purpose_tags: str = Form(""),
    scheduled_at: datetime = Form(...),
    max_members: int = Form(4),
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    meetup = Meetup(
        organizer_id=current_user.id, cafe_id=cafe_id, title=title,
        description=description, purpose_tags=purpose_tags,
        scheduled_at=scheduled_at, max_members=max_members,
    )
    db.add(meetup)
    db.flush()
    db.add(MeetupMember(meetup_id=meetup.id, user_id=current_user.id))
    db.commit()
    cafe = db.get(Cafe, cafe_id)
    referer = request.headers.get("referer", "")
    if "/meetups" in referer:
        return RedirectResponse("/meetups", status_code=302)
    return RedirectResponse(f"/cafe/{cafe.slug}#meetups", status_code=302)


@router.post("/meetups/{meetup_id}/join")
def join_meetup(
    meetup_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    meetup = db.get(Meetup, meetup_id)
    if not meetup or not meetup.is_joinable:
        raise HTTPException(status_code=400, detail="此揪團無法加入")
    if db.query(MeetupMember).filter_by(meetup_id=meetup_id, user_id=current_user.id).first():
        raise HTTPException(status_code=400, detail="你已報名此揪團")
    db.add(MeetupMember(meetup_id=meetup_id, user_id=current_user.id))
    if meetup.current_count + 1 >= meetup.max_members:
        meetup.status = MeetupStatus.full
    db.commit()
    referer = request.headers.get("referer", "")
    if "/meetups" in referer:
        return RedirectResponse(f"/meetups?joined={meetup_id}", status_code=302)
    return RedirectResponse(f"/cafe/{meetup.cafe.slug}?joined={meetup_id}#meetups", status_code=302)


@router.post("/meetups/{meetup_id}/leave")
def leave_meetup(
    meetup_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    meetup = db.get(Meetup, meetup_id)
    if not meetup:
        raise HTTPException(status_code=404)
    if meetup.organizer_id == current_user.id:
        raise HTTPException(status_code=400, detail="發起人不能退出揪團")
    member = db.query(MeetupMember).filter_by(meetup_id=meetup_id, user_id=current_user.id).first()
    if member:
        db.delete(member)
        if meetup.status == MeetupStatus.full:
            meetup.status = MeetupStatus.open
        db.commit()
    referer = request.headers.get("referer", "")
    if f"/meetups/{meetup_id}" in referer:
        return RedirectResponse(f"/meetups/{meetup_id}", status_code=302)
    if "/meetups" in referer:
        return RedirectResponse("/meetups", status_code=302)
    return RedirectResponse(f"/cafe/{meetup.cafe.slug}#meetups", status_code=302)


@router.get("/meetups/{meetup_id}/messages")
def get_messages(
    meetup_id: int,
    after: int = 0,
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    is_member = db.query(MeetupMember).filter_by(meetup_id=meetup_id, user_id=current_user.id).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="僅限揪團成員查看")
    msgs = db.query(MeetupMessage).filter(
        MeetupMessage.meetup_id == meetup_id,
        MeetupMessage.id > after
    ).order_by(MeetupMessage.created_at).limit(50).all()
    return JSONResponse([{
        "id": m.id,
        "content": m.content,
        "user": m.user.display_name or m.user.username,
        "initial": (m.user.display_name or m.user.username)[:1].upper(),
        "is_me": m.user_id == current_user.id,
        "time": m.created_at.strftime("%H:%M"),
    } for m in msgs])


@router.post("/meetups/{meetup_id}/messages")
def post_message(
    meetup_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_login),
):
    is_member = db.query(MeetupMember).filter_by(meetup_id=meetup_id, user_id=current_user.id).first()
    if not is_member:
        raise HTTPException(status_code=403)
    content = content.strip()
    if not content:
        raise HTTPException(status_code=400)
    db.add(MeetupMessage(meetup_id=meetup_id, user_id=current_user.id, content=content))
    db.commit()
    return JSONResponse({"ok": True})
