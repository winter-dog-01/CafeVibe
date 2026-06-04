from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.cafe import Cafe
from app.models.reservation import Reservation, ReservationStatus
from app.dependencies import require_owner

router = APIRouter(prefix="/owner")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def owner_dashboard(request: Request, db: Session = Depends(get_db), current_user=Depends(require_owner)):
    cafes = db.query(Cafe).filter(Cafe.owner_id == current_user.id).all()
    cafe_ids = [c.id for c in cafes]

    pending = (
        db.query(Reservation)
        .options(joinedload(Reservation.user), joinedload(Reservation.cafe))
        .filter(Reservation.cafe_id.in_(cafe_ids), Reservation.status == ReservationStatus.pending)
        .order_by(Reservation.date, Reservation.time_slot)
        .all()
    ) if cafe_ids else []

    confirmed = (
        db.query(Reservation)
        .options(joinedload(Reservation.user), joinedload(Reservation.cafe))
        .filter(Reservation.cafe_id.in_(cafe_ids), Reservation.status == ReservationStatus.confirmed)
        .order_by(Reservation.date, Reservation.time_slot)
        .all()
    ) if cafe_ids else []

    return templates.TemplateResponse("owner/dashboard.html", {
        "request": request,
        "current_user": current_user,
        "cafes": cafes,
        "pending": pending,
        "confirmed": confirmed,
    })


@router.post("/reservations/{res_id}/confirm")
def confirm_reservation(res_id: int, db: Session = Depends(get_db), current_user=Depends(require_owner)):
    res = db.query(Reservation).options(joinedload(Reservation.cafe)).filter(Reservation.id == res_id).first()
    if res and res.cafe.owner_id == current_user.id:
        res.status = ReservationStatus.confirmed
        db.commit()
    return RedirectResponse("/owner", status_code=302)


@router.post("/reservations/{res_id}/cancel")
def cancel_reservation(res_id: int, db: Session = Depends(get_db), current_user=Depends(require_owner)):
    res = db.query(Reservation).options(joinedload(Reservation.cafe)).filter(Reservation.id == res_id).first()
    if res and res.cafe.owner_id == current_user.id:
        res.status = ReservationStatus.cancelled
        db.commit()
    return RedirectResponse("/owner", status_code=302)


@router.post("/reservations/{res_id}/complete")
def complete_reservation(res_id: int, db: Session = Depends(get_db), current_user=Depends(require_owner)):
    res = db.query(Reservation).options(joinedload(Reservation.cafe)).filter(Reservation.id == res_id).first()
    if res and res.cafe.owner_id == current_user.id:
        res.status = ReservationStatus.completed
        db.commit()
    return RedirectResponse("/owner", status_code=302)
