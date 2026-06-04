from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.cafe import Cafe
from app.models.tag import Tag
from app.models.meetup import Meetup, MeetupStatus, MeetupMember, MeetupMessage
from app.models.review import Review, ReviewScore
from app.dependencies import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    featured = (
        db.query(Cafe)
        .options(joinedload(Cafe.photos), joinedload(Cafe.tags), joinedload(Cafe.reviews))
        .filter(Cafe.is_active == True, Cafe.is_featured == True)
        .limit(8)
        .all()
    )
    newest = (
        db.query(Cafe)
        .options(joinedload(Cafe.photos), joinedload(Cafe.tags))
        .filter(Cafe.is_active == True)
        .order_by(Cafe.created_at.desc())
        .limit(8)
        .all()
    )
    hot_meetups = (
        db.query(Meetup)
        .options(joinedload(Meetup.organizer), joinedload(Meetup.cafe), joinedload(Meetup.members))
        .filter(Meetup.status == MeetupStatus.open)
        .order_by(Meetup.created_at.desc())
        .limit(3)
        .all()
    )
    return templates.TemplateResponse("home.html", {
        "request": request,
        "current_user": current_user,
        "featured_cafes": featured,
        "newest_cafes": newest,
        "hot_meetups": hot_meetups,
    })


@router.get("/explore", response_class=HTMLResponse)
def explore(
    request: Request,
    q: str = Query(default=""),
    tags: list[str] = Query(default=[]),
    sort: str = Query(default="newest"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    all_tags = db.query(Tag).order_by(Tag.category, Tag.name).all()
    query = db.query(Cafe).options(
        joinedload(Cafe.photos), joinedload(Cafe.tags), joinedload(Cafe.reviews)
    ).filter(Cafe.is_active == True)

    if q:
        query = query.filter(
            Cafe.name.contains(q) |
            Cafe.description.contains(q) |
            Cafe.district.contains(q) |
            Cafe.address.contains(q) |
            Cafe.city.contains(q)
        )
    if tags:
        for tag_slug in tags:
            query = query.filter(Cafe.tags.any(Tag.slug == tag_slug))
    if sort == "rating":
        cafes = sorted(query.all(), key=lambda c: c.avg_scores["overall"], reverse=True)
    elif sort == "reviews":
        cafes = sorted(query.all(), key=lambda c: c.review_count, reverse=True)
    else:
        cafes = query.order_by(Cafe.created_at.desc()).all()

    tag_groups = {}
    for tag in all_tags:
        tag_groups.setdefault(tag.category, []).append(tag)

    return templates.TemplateResponse("explore.html", {
        "request": request,
        "current_user": current_user,
        "cafes": cafes,
        "tag_groups": tag_groups,
        "selected_tags": tags,
        "query": q,
        "sort": sort,
        "total": len(cafes),
    })


@router.get("/meetups", response_class=HTMLResponse)
def meetups_board(
    request: Request,
    q: str = Query(default=""),
    cafe_id: int = Query(default=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.meetup import Meetup, MeetupStatus, MeetupMember
    from datetime import datetime

    query = (
        db.query(Meetup)
        .options(
            joinedload(Meetup.organizer),
            joinedload(Meetup.cafe),
            joinedload(Meetup.members).joinedload(MeetupMember.user),
        )
        .filter(Meetup.status.in_([MeetupStatus.open, MeetupStatus.full]))
        .filter(Meetup.scheduled_at >= datetime.now())
        .order_by(Meetup.scheduled_at)
    )
    if q:
        query = query.filter(
            Meetup.title.contains(q) |
            Meetup.purpose_tags.contains(q) |
            Meetup.description.contains(q)
        )
    if cafe_id:
        query = query.filter(Meetup.cafe_id == cafe_id)

    meetups = query.all()
    cafes = db.query(Cafe).filter(Cafe.is_active == True).order_by(Cafe.name).all()

    joined_ids = set()
    if current_user:
        joined_ids = {
            m.meetup_id for m in
            db.query(MeetupMember).filter(MeetupMember.user_id == current_user.id).all()
        }

    return templates.TemplateResponse("meetups.html", {
        "request": request,
        "current_user": current_user,
        "meetups": meetups,
        "cafes": cafes,
        "query": q,
        "selected_cafe": cafe_id,
        "joined_ids": joined_ids,
        "total": len(meetups),
    })


@router.get("/meetups/{meetup_id}", response_class=HTMLResponse)
def meetup_detail(
    meetup_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    meetup = (
        db.query(Meetup)
        .options(
            joinedload(Meetup.organizer),
            joinedload(Meetup.cafe),
            joinedload(Meetup.members).joinedload(MeetupMember.user),
        )
        .filter(Meetup.id == meetup_id)
        .first()
    )
    if not meetup:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="揪團不存在")

    is_member = False
    is_organizer = False
    if current_user:
        is_member = any(m.user_id == current_user.id for m in meetup.members)
        is_organizer = meetup.organizer_id == current_user.id

    return templates.TemplateResponse("meetup_detail.html", {
        "request": request,
        "current_user": current_user,
        "meetup": meetup,
        "is_member": is_member,
        "is_organizer": is_organizer,
    })


@router.get("/cafe/{slug}", response_class=HTMLResponse)
def cafe_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cafe = (
        db.query(Cafe)
        .options(
            joinedload(Cafe.photos),
            joinedload(Cafe.tags),
            joinedload(Cafe.reviews).joinedload(Review.user),
            joinedload(Cafe.reviews).joinedload(Review.scores),
            joinedload(Cafe.reviews).joinedload(Review.photos),
            joinedload(Cafe.meetups).joinedload(Meetup.organizer),
            joinedload(Cafe.meetups).joinedload(Meetup.members).joinedload(MeetupMember.user),
        )
        .filter(Cafe.slug == slug, Cafe.is_active == True)
        .first()
    )
    if not cafe:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="找不到此咖啡廳")

    is_favorited = False
    if current_user:
        from app.models.favorite import Favorite
        is_favorited = bool(
            db.query(Favorite).filter_by(user_id=current_user.id, cafe_id=cafe.id).first()
        )

    active_meetups = [m for m in cafe.meetups if m.status == MeetupStatus.open]
    approved_reviews = [r for r in cafe.reviews if r.is_approved]

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "current_user": current_user,
        "cafe": cafe,
        "is_favorited": is_favorited,
        "active_meetups": active_meetups,
        "reviews": approved_reviews,
        "avg_scores": cafe.avg_scores,
    })
