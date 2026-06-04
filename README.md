# CafeVibe 跑咖網站

台灣咖啡廳探索與社群平台，提供多維度評分、線上預約、揪團功能。

---

## 環境需求

開始之前，請確認電腦已安裝下列軟體：

| 軟體 | 版本需求 | 下載連結 |
|------|----------|----------|
| Python | 3.11 以上 | https://www.python.org/downloads/ |
| XAMPP | 任意版本 | https://www.apachefriends.org/ |
| Git | 任意版本 | https://git-scm.com/ |

---

## 安裝步驟

### 第一步：下載專案

```bash
git clone https://github.com/你的帳號/cafevibe.git
cd cafevibe
```

---

### 第二步：建立虛擬環境並安裝套件

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows：
venv\Scripts\activate
# Mac / Linux：
source venv/bin/activate

# 安裝所有套件
pip install -r requirements.txt
```

> 如果安裝過程出現錯誤，請確認 Python 版本為 3.11 以上：`python --version`

---

### 第三步：啟動 XAMPP 並建立資料庫

1. 開啟 **XAMPP Control Panel**
2. 點擊 **Apache** 和 **MySQL** 旁的 **Start**
3. 開啟瀏覽器，前往 `http://localhost/phpmyadmin`
4. 點擊左側「**新增**」，建立資料庫：
   - 資料庫名稱：`cafevibe`
   - 編碼：`utf8mb4_unicode_ci`
5. 點擊「**建立**」

---

### 第四步：設定環境變數

複製範本檔並修改內容：

```bash
copy .env.example .env
```

用記事本或 VS Code 開啟 `.env`，預設內容如下（XAMPP 預設不需要修改）：

```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/cafevibe
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
APP_NAME=CafeVibe
DEBUG=True
```

> 如果你的 MySQL 有設定密碼，請將 `root:` 改為 `root:你的密碼`

---

### 第五步：初始化資料庫

```bash
python init_db.py
```

這個指令會自動建立所有資料表。

---

### 第六步：（選用）填入範例資料

如果想要有假資料可以瀏覽，執行：

```bash
python seed.py
```

---

### 第七步：啟動伺服器

```bash
uvicorn main:app --reload
```

成功後會看到：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

開啟瀏覽器前往 **http://127.0.0.1:8000** 即可使用。

---

## 常見問題

**Q：`pip install` 時出現 `Microsoft Visual C++ required` 錯誤**
A：前往 https://visualstudio.microsoft.com/visual-cpp-build-tools/ 安裝 Build Tools

**Q：啟動時出現 `Access denied for user 'root'@'localhost'`**
A：`.env` 裡的資料庫密碼不正確，請確認 XAMPP MySQL 的密碼設定

**Q：啟動時出現 `Table doesn't exist`**
A：請確認已執行 `python init_db.py`

**Q：開啟網頁後畫面空白或 500 錯誤**
A：確認 XAMPP 的 MySQL 正在運行（Control Panel 中為綠色 Running 狀態）

**Q：`venv\Scripts\activate` 出現執行原則錯誤（Windows）**
A：以系統管理員身份開啟 PowerShell，執行：
```
Set-ExecutionPolicy RemoteSigned
```

---

## 專案結構

```
cafevibe/
├── main.py              # 程式進入點
├── init_db.py           # 建立資料表
├── seed.py              # 填入範例資料
├── requirements.txt     # Python 套件清單
├── .env.example         # 環境變數範本
└── app/
    ├── models/          # 資料庫模型
    ├── routers/         # 路由處理
    ├── services/        # 商業邏輯
    ├── templates/       # HTML 模板
    └── static/          # CSS、JS、圖片
```

---

## 預設管理員帳號

執行 `seed.py` 後會建立測試帳號：

| 角色 | Email | 密碼 |
|------|-------|------|
| 管理員 | admin@cafevibe.com | admin123 |
| 一般用戶 | user@cafevibe.com | user123 |

> 正式使用前請記得修改密碼
