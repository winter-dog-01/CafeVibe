"""執行這個腳本來建立資料庫與所有資料表"""
import pymysql
from app.config import settings


def create_database():
    # Parse DATABASE_URL to get connection params
    url = settings.database_url
    # mysql+pymysql://user:password@host:port/dbname
    parts = url.split("://")[1]
    userpass, rest = parts.split("@")
    user = userpass.split(":")[0]
    password = userpass.split(":")[1] if ":" in userpass else ""
    hostport_db = rest
    if "/" in hostport_db:
        hostport, dbname = hostport_db.rsplit("/", 1)
    else:
        hostport, dbname = hostport_db, "cafevibe"
    host = hostport.split(":")[0]
    port = int(hostport.split(":")[1]) if ":" in hostport else 3306

    conn = pymysql.connect(host=host, user=user, password=password, port=port)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        print(f"[OK] Database '{dbname}' created or already exists")
    finally:
        conn.close()


if __name__ == "__main__":
    print("[1/2] Creating database...")
    create_database()

    print("[2/2] Creating all tables...")
    from app.database import Base, engine
    import app.models
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created!")
    print("\nNext: python seed.py  (insert sample data)")
    print("Then: uvicorn main:app --reload")
