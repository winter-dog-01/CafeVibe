from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.cafe import Cafe, CafePhoto
from app.models.tag import Tag
from app.models.user import User
from app.models.review import Review
from app.models.reservation import Reservation
from app.models.meetup import Meetup, MeetupMember
from app.dependencies import require_admin
from slugify import slugify
import shutil, uuid, os

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = "app/static/uploads/cafes"


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    stats = {
        "cafes": db.query(Cafe).count(),
        "users": db.query(User).count(),
        "reviews": db.query(Review).count(),
        "reservations": db.query(Reservation).count(),
    }
    recent_cafes = db.query(Cafe).order_by(Cafe.created_at.desc()).limit(5).all()
    pending_reviews = db.query(Review).filter(Review.is_approved == False).all()
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request, "current_user": current_user,
        "stats": stats, "recent_cafes": recent_cafes, "pending_reviews": pending_reviews,
    })


@router.get("/cafes", response_class=HTMLResponse)
def admin_cafes(request: Request, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    cafes = db.query(Cafe).order_by(Cafe.created_at.desc()).all()
    tags = db.query(Tag).all()
    return templates.TemplateResponse("admin/cafes.html", {
        "request": request, "current_user": current_user, "cafes": cafes, "tags": tags,
    })


@router.post("/cafes")
async def create_cafe(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    address: str = Form(...),
    district: str = Form(""),
    phone: str = Form(""),
    opening_hours: str = Form(""),
    instagram_url: str = Form(""),
    is_featured: bool = Form(False),
    tag_ids: list[int] = Form(default=[]),
    cover: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    slug = slugify(name, allow_unicode=True)
    base_slug = slug
    counter = 1
    while db.query(Cafe).filter(Cafe.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    cover_url = None
    if cover and cover.filename:
        ext = cover.filename.rsplit(".", 1)[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(cover.file, f)
        cover_url = f"/static/uploads/cafes/{filename}"

    cafe = Cafe(
        name=name, slug=slug, description=description, address=address,
        district=district, phone=phone, opening_hours=opening_hours,
        instagram_url=instagram_url,
        is_featured=is_featured, cover_image_url=cover_url,
    )
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        cafe.tags = tags
    db.add(cafe)
    db.commit()
    return RedirectResponse("/admin/cafes", status_code=302)


@router.post("/cafes/{cafe_id}/delete")
def delete_cafe(cafe_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    cafe = db.get(Cafe, cafe_id)
    if cafe:
        db.delete(cafe)
        db.commit()
    return RedirectResponse("/admin/cafes", status_code=302)


@router.post("/cafes/{cafe_id}/toggle")
def toggle_cafe(cafe_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    cafe = db.get(Cafe, cafe_id)
    if cafe:
        cafe.is_active = not cafe.is_active
        db.commit()
    return RedirectResponse("/admin/cafes", status_code=302)


@router.post("/cafes/{cafe_id}/toggle-featured")
def toggle_featured(cafe_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    cafe = db.get(Cafe, cafe_id)
    if cafe:
        cafe.is_featured = not cafe.is_featured
        db.commit()
    return RedirectResponse(f"/admin/cafes/{cafe_id}/edit", status_code=302)


@router.get("/cafes/{cafe_id}/edit", response_class=HTMLResponse)
def edit_cafe_page(cafe_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    from sqlalchemy.orm import joinedload
    from app.models.user import UserRole
    cafe = db.query(Cafe).options(joinedload(Cafe.photos), joinedload(Cafe.tags)).filter(Cafe.id == cafe_id).first()
    if not cafe:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    tags = db.query(Tag).all()
    owners = db.query(User).filter(User.role.in_([UserRole.owner, UserRole.member])).order_by(User.display_name).all()
    return templates.TemplateResponse("admin/cafe_edit.html", {
        "request": request, "current_user": current_user, "cafe": cafe, "tags": tags, "owners": owners,
    })


@router.post("/cafes/{cafe_id}/edit")
async def update_cafe(
    cafe_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    address: str = Form(...),
    district: str = Form(""),
    phone: str = Form(""),
    opening_hours: str = Form(""),
    instagram_url: str = Form(""),
    is_featured: bool = Form(False),
    is_active: bool = Form(False),
    tag_ids: list[int] = Form(default=[]),
    cover: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    cafe = db.get(Cafe, cafe_id)
    if not cafe:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)

    if cafe.name != name:
        new_slug = slugify(name, allow_unicode=True)
        base_slug = new_slug
        counter = 1
        while db.query(Cafe).filter(Cafe.slug == new_slug, Cafe.id != cafe_id).first():
            new_slug = f"{base_slug}-{counter}"
            counter += 1
        cafe.slug = new_slug

    cafe.name = name
    cafe.description = description
    cafe.address = address
    cafe.district = district
    cafe.phone = phone
    cafe.opening_hours = opening_hours
    cafe.instagram_url = instagram_url
    cafe.is_featured = is_featured
    cafe.is_active = is_active

    if cover and cover.filename:
        ext = cover.filename.rsplit(".", 1)[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(cover.file, f)
        cafe.cover_image_url = f"/static/uploads/cafes/{filename}"

    cafe.tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
    db.commit()
    return RedirectResponse(f"/admin/cafes/{cafe_id}/edit?saved=1", status_code=302)


@router.post("/cafes/{cafe_id}/photos")
async def add_cafe_photo(
    cafe_id: int,
    photo: UploadFile = File(...),
    caption: str = Form(""),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    cafe = db.get(Cafe, cafe_id)
    if not cafe:
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    ext = photo.filename.rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    from sqlalchemy.orm import joinedload
    cafe_with_photos = db.query(Cafe).options(joinedload(Cafe.photos)).filter(Cafe.id == cafe_id).first()
    max_order = max((p.sort_order for p in cafe_with_photos.photos), default=0) + 1
    db.add(CafePhoto(cafe_id=cafe_id, url=f"/static/uploads/cafes/{filename}", caption=caption, sort_order=max_order))
    db.commit()
    return RedirectResponse(f"/admin/cafes/{cafe_id}/edit", status_code=302)


@router.post("/cafes/{cafe_id}/photos/{photo_id}/toggle-cover")
def toggle_cover_photo(
    cafe_id: int, photo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    from fastapi.responses import JSONResponse
    photo = db.get(CafePhoto, photo_id)
    if photo and photo.cafe_id == cafe_id:
        photo.is_cover = not photo.is_cover
        db.commit()
        return JSONResponse({"is_cover": photo.is_cover})
    from fastapi import HTTPException
    raise HTTPException(status_code=404)


@router.post("/cafes/{cafe_id}/photos/{photo_id}/delete")
def delete_cafe_photo(
    cafe_id: int, photo_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    photo = db.get(CafePhoto, photo_id)
    if photo and photo.cafe_id == cafe_id:
        db.delete(photo)
        db.commit()
    return RedirectResponse(f"/admin/cafes/{cafe_id}/edit", status_code=302)


@router.get("/reviews", response_class=HTMLResponse)
def admin_reviews(request: Request, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    return templates.TemplateResponse("admin/reviews.html", {
        "request": request, "current_user": current_user, "reviews": reviews,
    })


@router.post("/reviews/{review_id}/approve")
def approve_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    review = db.get(Review, review_id)
    if review:
        review.is_approved = True
        db.commit()
    return RedirectResponse("/admin/reviews", status_code=302)


@router.post("/reviews/{review_id}/delete")
def delete_review(review_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    review = db.get(Review, review_id)
    if review:
        db.delete(review)
        db.commit()
    return RedirectResponse("/admin/reviews", status_code=302)


@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    # 每位 owner 管理的店家
    owner_cafes = {}
    for cafe in db.query(Cafe).filter(Cafe.owner_id.isnot(None)).all():
        owner_cafes.setdefault(cafe.owner_id, []).append(cafe)
    return templates.TemplateResponse("admin/users.html", {
        "request": request, "current_user": current_user, "users": users, "owner_cafes": owner_cafes,
    })


@router.post("/users/{user_id}/toggle")
def toggle_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    user = db.get(User, user_id)
    if user and user.id != current_user.id:
        user.is_active = not user.is_active
        db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/users/{user_id}/set-role")
def set_user_role(user_id: int, role: str = Form(...), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    from app.models.user import UserRole
    user = db.get(User, user_id)
    if user and user.id != current_user.id and role in ("member", "owner"):
        user.role = UserRole(role)
        db.commit()
    return RedirectResponse("/admin/users", status_code=302)


@router.post("/cafes/{cafe_id}/assign-owner")
def assign_cafe_owner(cafe_id: int, owner_id: int = Form(...), db: Session = Depends(get_db), current_user=Depends(require_admin)):
    from app.models.user import UserRole
    cafe = db.get(Cafe, cafe_id)
    if cafe:
        old_owner_id = cafe.owner_id
        new_owner_id = owner_id if owner_id else None
        cafe.owner_id = new_owner_id

        # 升級新店長角色
        if new_owner_id:
            new_owner = db.get(User, new_owner_id)
            if new_owner and new_owner.role == UserRole.member:
                new_owner.role = UserRole.owner

        # 若舊店長被移除，且名下已無其他店家，則降回 member
        if old_owner_id and old_owner_id != new_owner_id:
            old_owner = db.get(User, old_owner_id)
            if old_owner and old_owner.role == UserRole.owner:
                still_owns = db.query(Cafe).filter(Cafe.owner_id == old_owner_id, Cafe.id != cafe_id).count()
                if still_owns == 0:
                    old_owner.role = UserRole.member

        db.commit()
    return RedirectResponse(f"/admin/cafes/{cafe_id}/edit?saved=1", status_code=302)


@router.get("/users/search")
def search_users(q: str = "", db: Session = Depends(get_db), current_user=Depends(require_admin)):
    from fastapi.responses import JSONResponse
    if not q or len(q) < 1:
        return JSONResponse([])
    results = (
        db.query(User)
        .filter(
            User.email.contains(q) |
            User.display_name.contains(q) |
            User.username.contains(q)
        )
        .limit(8)
        .all()
    )
    return JSONResponse([{
        "id": u.id,
        "email": u.email,
        "name": u.display_name or u.username,
        "role": u.role.value,
    } for u in results])


@router.get("/meetups", response_class=HTMLResponse)
def admin_meetups(request: Request, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    from sqlalchemy.orm import joinedload
    meetups = (
        db.query(Meetup)
        .options(
            joinedload(Meetup.organizer),
            joinedload(Meetup.cafe),
            joinedload(Meetup.members).joinedload(MeetupMember.user),
        )
        .order_by(Meetup.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("admin/meetups.html", {
        "request": request, "current_user": current_user, "meetups": meetups,
    })


@router.post("/meetups/{meetup_id}/delete")
def delete_meetup(meetup_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    meetup = db.get(Meetup, meetup_id)
    if meetup:
        db.query(MeetupMember).filter(MeetupMember.meetup_id == meetup_id).delete()
        db.delete(meetup)
        db.commit()
    return RedirectResponse("/admin/meetups", status_code=302)
