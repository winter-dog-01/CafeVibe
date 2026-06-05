"""填入範例資料，執行前請先確認已執行 init_db.py"""
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.cafe import Cafe, CafePhoto
from app.models.tag import Tag
from app.models.review import Review, ReviewScore
from app.models.meetup import Meetup, MeetupStatus, MeetupMember
from app.services.auth_service import hash_password as get_password_hash
import app.models

db = SessionLocal()

# ───────────── 清空舊資料 ─────────────
print("清空舊資料...")
db.query(MeetupMember).delete()
db.query(Meetup).delete()
db.query(ReviewScore).delete()
db.query(Review).delete()
db.query(CafePhoto).delete()
db.execute(__import__('sqlalchemy').text("DELETE FROM cafe_tags"))
db.query(Cafe).delete()
db.query(Tag).delete()
db.query(User).delete()
db.commit()

# ───────────── 用戶 ─────────────
print("建立用戶...")
admin = User(
    username="admin",
    email="admin@cafevibe.com",
    hashed_password=get_password_hash("admin123"),
    display_name="管理員",
    role=UserRole.admin,
    is_active=True,
)
owner = User(
    username="owner",
    email="owner@cafevibe.com",
    hashed_password=get_password_hash("owner123"),
    display_name="咖啡廳老闆",
    role=UserRole.owner,
    is_active=True,
)
alice = User(
    username="alice",
    email="alice@cafevibe.com",
    hashed_password=get_password_hash("user123"),
    display_name="Alice Wang",
    bio="熱愛探索台北各式咖啡廳 ☕",
    role=UserRole.member,
    is_active=True,
)
brian = User(
    username="brian",
    email="brian@cafevibe.com",
    hashed_password=get_password_hash("user123"),
    display_name="Brian Chen",
    bio="在咖啡廳讀書是我的日常",
    role=UserRole.member,
    is_active=True,
)
db.add_all([admin, owner, alice, brian])
db.commit()

# ───────────── 標籤 ─────────────
print("建立標籤...")
tags_data = [
    # 風格
    ("韓系風格", "korean-style", "style", "🇰🇷"),
    ("工業風", "industrial", "style", "🏭"),
    ("日系簡約", "japanese-minimal", "style", "⛩️"),
    ("復古老宅", "vintage", "style", "🏚️"),
    # 餐點
    ("極致抹茶", "matcha", "food", "🍵"),
    ("手工甜點", "handmade-dessert", "food", "🍰"),
    ("精品咖啡", "specialty-coffee", "food", "☕"),
    ("輕食早午餐", "brunch", "food", "🥗"),
    # 實用
    ("不限時", "not-time-limited", "practical", "⏰"),
    ("插座充足", "many-outlets", "practical", "🔌"),
    ("高速 WiFi", "wifi", "practical", "📶"),
    ("深夜營業", "late-night", "practical", "🌙"),
    ("寵物友善", "pet-friendly", "practical", "🐾"),
]
tags = {}
for name, slug, category, icon in tags_data:
    t = Tag(name=name, slug=slug, category=category, icon=icon)
    db.add(t)
    tags[slug] = t
db.commit()

# ───────────── 咖啡廳 ─────────────
print("建立咖啡廳...")
cafe1 = Cafe(
    name="Simple Kaffa 興波咖啡",
    slug="simple-kaffa",
    description="台灣精品咖啡代表，多次獲得世界咖啡師大賽殊榮，每一杯都是極致工藝的呈現。",
    address="台北市大安區仁愛路四段300巷9弄6號",
    district="大安區",
    city="台北市",
    phone="02-2700-0901",
    opening_hours="週一至週五 08:00–18:00，週六日 09:00–18:00",
    cover_image_url="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&q=80",
    is_active=True,
    is_featured=True,
    owner_id=owner.id,
)
cafe2 = Cafe(
    name="Cama Café 中山店",
    slug="cama-cafe-zhongshan",
    description="平價親民的精品咖啡連鎖品牌，中山店座位寬敞，不限時，適合長時間工作。",
    address="台北市中山區南京西路16號",
    district="中山區",
    city="台北市",
    phone="02-2558-0808",
    opening_hours="每日 07:30–21:30",
    cover_image_url="https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80",
    is_active=True,
    is_featured=True,
)
cafe3 = Cafe(
    name="MO²抹茶咖啡",
    slug="mo2-matcha",
    description="台北最受歡迎的抹茶主題咖啡廳，日式簡約空間，必點濃厚抹茶拿鐵與抹茶千層。",
    address="台北市信義區松仁路28號",
    district="信義區",
    city="台北市",
    opening_hours="週一至週四 11:00–21:00，週五至週日 10:00–22:00",
    cover_image_url="https://images.unsplash.com/photo-1511920170033-f8396924c348?w=800&q=80",
    is_active=True,
    is_featured=True,
)
cafe4 = Cafe(
    name="RUFOUS COFFEE",
    slug="rufous-coffee",
    description="隱身在巷弄的精品咖啡館，工業風裝潢，主打單品手沖，深受文青喜愛。",
    address="台北市大安區敦化南路一段190巷39號",
    district="大安區",
    city="台北市",
    opening_hours="週二至週日 10:00–18:00（週一公休）",
    cover_image_url="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80",
    is_active=True,
    is_featured=False,
)
cafe5 = Cafe(
    name="Barista Way Coffee",
    slug="barista-way",
    description="深夜咖啡廳首選，凌晨2點才打烊，提供穩定的WiFi與充足插座，是夜貓子的天堂。",
    address="台北市松山區民生東路五段36巷3號",
    district="松山區",
    city="台北市",
    opening_hours="每日 14:00–02:00",
    cover_image_url="https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80",
    is_active=True,
    is_featured=False,
)

db.add_all([cafe1, cafe2, cafe3, cafe4, cafe5])
db.commit()

# 標籤關聯
cafe1.tags = [tags["specialty-coffee"], tags["japanese-minimal"], tags["handmade-dessert"]]
cafe2.tags = [tags["not-time-limited"], tags["many-outlets"], tags["wifi"], tags["brunch"]]
cafe3.tags = [tags["matcha"], tags["korean-style"], tags["handmade-dessert"]]
cafe4.tags = [tags["specialty-coffee"], tags["industrial"], tags["not-time-limited"], tags["wifi"]]
cafe5.tags = [tags["late-night"], tags["many-outlets"], tags["wifi"], tags["not-time-limited"]]
db.commit()

# 照片
photos = [
    CafePhoto(cafe_id=cafe1.id, url="https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&q=80", is_cover=True, sort_order=0),
    CafePhoto(cafe_id=cafe2.id, url="https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=800&q=80", is_cover=True, sort_order=0),
    CafePhoto(cafe_id=cafe3.id, url="https://images.unsplash.com/photo-1511920170033-f8396924c348?w=800&q=80", is_cover=True, sort_order=0),
    CafePhoto(cafe_id=cafe4.id, url="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80", is_cover=True, sort_order=0),
    CafePhoto(cafe_id=cafe5.id, url="https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80", is_cover=True, sort_order=0),
]
db.add_all(photos)
db.commit()

# ───────────── 評論 ─────────────
print("建立評論...")
def make_review(user, cafe, coffee, dessert, ambience, focus, content):
    r = Review(user_id=user.id, cafe_id=cafe.id, content=content, is_approved=True)
    db.add(r)
    db.flush()
    for dim, score in [("coffee", coffee), ("dessert", dessert), ("ambience", ambience), ("focus", focus)]:
        db.add(ReviewScore(review_id=r.id, dimension=dim, score=score))

make_review(alice, cafe1, 5, 4, 5, 3, "咖啡風味非常細緻，能感受到烘豆師的用心，環境優雅是約會首選！")
make_review(brian, cafe1, 5, 3, 4, 4, "世界冠軍等級的咖啡，每次來都有不同的手沖選擇，強烈推薦單品。")
make_review(alice, cafe2, 3, 3, 4, 5, "不限時加上充足插座，讀書寫報告的好地方，咖啡品質也在水準之上。")
make_review(brian, cafe3, 3, 5, 5, 2, "抹茶千層超好吃！拍照打卡必來，韓系裝潢很上鏡，假日記得提早來。")
make_review(alice, cafe4, 5, 2, 4, 4, "手沖咖啡很專業，老闆會介紹豆子的產地和風味，工業風空間很有個性。")
make_review(brian, cafe5, 3, 2, 3, 5, "深夜工作救星！凌晨2點還開著，網路穩定，是趕死線的最佳場所。")
db.commit()

# ───────────── 揪團 ─────────────
print("建立揪團...")
from datetime import datetime, timedelta

meetup1 = Meetup(
    title="找人一起討論 AI 論文 🤖",
    organizer_id=alice.id,
    cafe_id=cafe1.id,
    scheduled_at=datetime.now() + timedelta(days=3),
    max_members=4,
    purpose_tags="AI論文,讀書,討論",
    description="最近在讀 LLM 相關論文，想找同好一起討論，不限領域歡迎加入！",
    status=MeetupStatus.open,
)
meetup2 = Meetup(
    title="抹茶控集合！一起拍美照 📸",
    organizer_id=brian.id,
    cafe_id=cafe3.id,
    scheduled_at=datetime.now() + timedelta(days=5),
    max_members=3,
    purpose_tags="拍照互助,抹茶控,打卡",
    description="想去 MO² 拍照但一個人去感覺怪，找 2 個人一起去互拍！",
    status=MeetupStatus.open,
)
db.add_all([meetup1, meetup2])
db.commit()

m1 = MeetupMember(meetup_id=meetup1.id, user_id=alice.id)
m2 = MeetupMember(meetup_id=meetup2.id, user_id=brian.id)
db.add_all([m1, m2])
db.commit()

db.close()
print("\n✅ 範例資料填入完成！")
print("\n預設帳號：")
print("  管理員：admin@cafevibe.com  / admin123")
print("  店家  ：owner@cafevibe.com  / owner123")
print("  會員  ：alice@cafevibe.com  / user123")
print("  會員  ：brian@cafevibe.com  / user123")
print("\n啟動伺服器：uvicorn main:app --reload")
