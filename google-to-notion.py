# import os
# import re
# import tempfile
# import base64
# import requests
# from datetime import datetime, timedelta
# import boto3
# import chromedriver_autoinstaller
# from selenium.webdriver.chrome.service import Service
# from urllib.parse import urlparse, unquote
# from PIL import Image
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from notion_client import Client as NotionClient

# # ─── 환경변수 로드 (GitHub Actions용) ─────────────────────────────────────
# CHROME_BINARY = os.getenv("CHROME_BINARY", "/usr/bin/google-chrome")
# SMORE_USER_DATA = os.getenv("SMORE_USER_DATA")
# SMORE_PROFILE = os.getenv("SMORE_PROFILE")

# # Google 인증 파일 처리
# GOOGLE_CRED = os.getenv(
#     "GOOGLE_APPLICATION_CREDENTIALS", "/tmp/google_credentials.json"
# )

# SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
# SHEET_RANGE = os.getenv("SHEET_RANGE")
# AWS_REGION = os.getenv("AWS_DEFAULT_REGION")
# S3_BUCKET = os.getenv("S3_BUCKET_NAME")
# NOTION_TOKEN = os.getenv("NOTION_TOKEN")
# NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID")
# TEST_OFFSET = int(os.getenv("TEST_OFFSET", "0"))
# TEST_LIMIT = int(os.getenv("TEST_LIMIT", "0"))

# # 다운로드 디렉토리
# DOWNLOAD_DIR = os.getenv("SMORE_DOWNLOAD_DIR", tempfile.gettempdir())
# os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# # ─── 클라이언트 초기화 ─────────────────────────────────────────────────────
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# ga_creds = service_account.Credentials.from_service_account_file(
#     GOOGLE_CRED, scopes=SCOPES
# )
# sheets = build("sheets", "v4", credentials=ga_creds)

# s3 = boto3.client("s3", region_name=AWS_REGION)
# notion = NotionClient(auth=NOTION_TOKEN)

# SHEET_NAME = SHEET_RANGE.split("!")[0]

# # ─── 헤더 매핑 ─────────────────────────────────────────────────────────────
# HEADER_TO_PROP = {
#     "순번": "순번",
#     "출산을 증명할 수 있는 이미지 파일을 첨부해 주세요 등본, 가족관계증명서, 출생증명서, 산모수첩 중 택1": "증명서 이미지",
#     "타가몰에서 사용 중이신 아이디를 알려주세요💛 간편가입 하신 경우 앱 아이디를 입력해주세요.(ex.1234567@N)": "타가몰 아이디",
#     "신청자 본인의 성함을 적어주세요 😃 ※ 표기 오류로 인한 대상 제외 및 경품 미수령시 책임지지 않습니다.": "이름",
#     "📱 연락 가능한 번호를 적어주세요💛 (예: 010-1234-5678)": "연락처",
#     "보듬박스를 받으실 상세 주소를 적어 주세요.💛 ※ 표기 오류로 인한 대상 제외 및 경품 미수령시 책임지지 않습니다.": "주소",
#     "📅 아기 출생 예정일이나 출생일을 알려주세요💛": "출생일",
#     "담당자": "담당자",
#     "적/부": "적/부",
# }


# def normalize_header(h: str) -> str:
#     return re.sub(r"\s+", " ", h.replace("\n", " ").strip())


# NORM_HEADER_TO_PROP = {normalize_header(k): v for k, v in HEADER_TO_PROP.items()}


# # ─── Excel serial date 변환 ─────────────────────────────────────────────────
# def excel_serial_to_datetime(serial) -> datetime:
#     try:
#         days = float(serial)
#     except:
#         return None
#     epoch = datetime(1899, 12, 30) if days >= 61 else datetime(1899, 12, 31)
#     return epoch + timedelta(days=days)


# # ─── 파일명 안전 생성 ───────────────────────────────────────────────────────
# def safe_key_name(row_idx: int, filename: str) -> str:
#     base, ext = os.path.splitext(filename)
#     b64 = base64.urlsafe_b64encode(base.encode("utf-8")).decode("ascii")
#     return f"row{row_idx}_{b64}{ext}"


# # ─── S3 업로드 ─────────────────────────────────────────────────────────────
# # def upload_to_s3(local: str, key: str) -> str:
# # import mimetypes


# # ctype, _ = mimetypes.guess_type(local)
# # s3.upload_file(
# #     Filename=local,
# #     Bucket=S3_BUCKET,
# #     Key=key,
# #     ExtraArgs={
# #         "ACL": "public-read",
# #         "ContentType": ctype or "application/octet-stream",
# #     },
# # )
# # return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
# # 이미지인 경우 압축
# def upload_to_s3(local, key):
#     # 이미지 압축 및 리사이즈 시도
#     try:
#         from PIL import Image

#         img = Image.open(local)
#         # 최대 가로/세로 1024px로 리사이즈
#         resample = getattr(Image, "Resampling", Image).LANCZOS
#         img.thumbnail((1024, 1024), resample)
#         ext = os.path.splitext(local)[1].lower()
#         quality = 75  # 수정: 품질 낮춰 용량 줄이기
#         if ext in (".jpg", ".jpeg"):
#             img.save(local, format="JPEG", optimize=True, quality=quality)
#         else:
#             # PNG 등은 JPEG로 변환
#             rgb = img.convert("RGB")
#             jpeg_path = os.path.splitext(local)[0] + ".jpg"
#             rgb.save(jpeg_path, format="JPEG", optimize=True, quality=quality)
#             local = jpeg_path
#     except ImportError:
#         # PIL 미설치 시 압축 생략
#         pass
#     except Exception as e:
#         print(f"[압축 오류] {local}: {e}")
#     # S3 업로드
#     import mimetypes

#     ctype, _ = mimetypes.guess_type(local)
#     s3.upload_file(
#         Filename=local,
#         Bucket=S3_BUCKET,
#         Key=key,
#         ExtraArgs={
#             "ACL": "public-read",
#             "ContentType": ctype or "application/octet-stream",
#         },
#     )
#     return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"


# def get_smore_cookies():
#     driver_path = chromedriver_autoinstaller.install()
#     opts = Options()
#     opts.binary_location = CHROME_BINARY

#     # GitHub Actions 환경용 옵션 추가
#     opts.add_argument("--headless")
#     opts.add_argument("--no-sandbox")
#     opts.add_argument("--disable-dev-shm-usage")
#     opts.add_argument("--disable-gpu")
#     opts.add_argument("--remote-debugging-port=9222")

#     # 기존 옵션
#     if SMORE_USER_DATA:
#         opts.add_argument(f"--user-data-dir={SMORE_USER_DATA}")
#     if SMORE_PROFILE:
#         opts.add_argument(f"--profile-directory={SMORE_PROFILE}")

#     driver = webdriver.Chrome(service=Service(driver_path), options=opts)
#     try:
#         driver.get("https://smore.im")
#         return {c["name"]: c["value"] for c in driver.get_cookies()}
#     finally:
#         driver.quit()


# def download_smore_image(page_url, cookies, row_idx):
#     driver_path = chromedriver_autoinstaller.install()
#     opts = Options()
#     opts.binary_location = CHROME_BINARY
#     opts.add_argument(f"--user-data-dir={SMORE_USER_DATA}")
#     opts.add_argument(f"--profile-directory={SMORE_PROFILE}")
#     driver = webdriver.Chrome(service=Service(driver_path), options=opts)
#     try:
#         driver.get(page_url)
#         link = WebDriverWait(driver, 15).until(
#             EC.element_to_be_clickable((By.ID, "download"))
#         )
#         file_url = link.get_attribute("href")
#         sess = requests.Session()
#         sess.cookies.update(cookies)
#         resp = sess.get(file_url, stream=True, timeout=30)
#     finally:
#         driver.quit()

#     resp.raise_for_status()
#     if "text/html" in resp.headers.get("Content-Type", ""):
#         raise RuntimeError("HTML 반환됨(로그인 필요?): " + page_url)

#     cd = resp.headers.get("content-disposition", "")
#     m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(
#         r"filename=?\"?([^\";]+)\"?", cd
#     )
#     orig = unquote(m.group(1)) if m else os.path.basename(urlparse(file_url).path)
#     filename = safe_key_name(row_idx, orig)
#     local = os.path.join(DOWNLOAD_DIR, filename)
#     with open(local, "wb") as f:
#         for chunk in resp.iter_content(1024):
#             f.write(chunk)
#     return local


# # ─── 메인 ─────────────────────────────────────────────────────────────────
# def sheet_to_notion_s3():
#     cookies = get_smore_cookies()
#     res = (
#         sheets.spreadsheets()
#         .values()
#         .get(
#             spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE, valueRenderOption="FORMULA"
#         )
#         .execute()
#     )
#     rows = res.get("values", [])
#     if len(rows) < 2:
#         print("데이터 없음")
#         return

#     headers = [normalize_header(h) for h in rows[0]]
#     done_idx = headers.index("이관완료") if "이관완료" in headers else None
#     data_rows = rows[1:]
#     recs = data_rows[TEST_OFFSET : TEST_OFFSET + TEST_LIMIT]
#     db_props = notion.databases.retrieve(database_id=NOTION_DB_ID)["properties"]

#     for i, row in enumerate(recs, start=TEST_OFFSET + 2):
#         # ─── 여기서 S열 '완료' 체크 ─────────────────────────────
#         if done_idx is not None and len(row) > done_idx:
#             cell_val = row[done_idx].strip()
#             # '완료'로 시작(예: "완료", "완료<")하면 건너뜁니다
#             if cell_val.startswith("완료"):
#                 print(f"[Row {i}] 이미 완료된 행, 건너뜁니다")
#                 continue
#         data = {headers[j]: row[j] if j < len(row) else "" for j in range(len(headers))}
#         props, image_urls = {}, []

#         for hdr, val in data.items():
#             if not val:
#                 continue
#             prop = NORM_HEADER_TO_PROP.get(normalize_header(hdr))
#             if not prop or prop not in db_props:
#                 continue
#             ptype = db_props[prop]["type"]
#             if ptype == "files":
#                 # m = re.match(r'=HYPERLINK\("([^"\)]+)"', val)
#                 # url = m.group(1) if m else val
#                 m = re.match(r'=HYPERLINK\("([^"]+)"(?:\s*,\s*"([^"]+)")?\)', val)
#                 url = m.group(1)  # 실제 다운로드 URL
#                 disp = m.group(2) if m and m.group(2) else None  # 옵션 표시명
#                 try:
#                     local = download_smore_image(url, cookies, i)
#                     key = safe_key_name(i, os.path.basename(local))
#                     s3_url = upload_to_s3(local, key)
#                     original_name = disp or os.path.basename(local)
#                     if len(original_name) > 100:
#                         display_name = original_name[:97] + "..."
#                     else:
#                         display_name = original_name
#                     props[prop] = {
#                         "files": [
#                             {
#                                 # "name": os.path.basename(local),
#                                 "name": display_name,
#                                 "external": {"url": s3_url},
#                             }
#                         ]
#                     }
#                     image_urls.append(s3_url)
#                 except Exception as e:
#                     print(f"[Row {i}] 파일 오류: {e}")
#                 continue
#             if ptype == "date":
#                 m2 = re.match(
#                     r"^=DATE\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", str(val)
#                 )
#                 if m2:
#                     y, mo, da = map(int, m2.groups())
#                     props[prop] = {"date": {"start": datetime(y, mo, da).isoformat()}}
#                 else:
#                     dt = excel_serial_to_datetime(val)
#                     if dt:
#                         props[prop] = {"date": {"start": dt.isoformat()}}
#                 continue
#             if ptype == "url":
#                 props[prop] = {"url": val.strip()}
#                 continue
#             if ptype == "title":
#                 props[prop] = {"title": [{"text": {"content": str(val)}}]}
#                 continue
#             if ptype == "rich_text":
#                 props[prop] = {"rich_text": [{"text": {"content": str(val)}}]}
#                 continue

#         if props:
#             # print(f"[Row {i}] props=", props)  # debug
#             page = notion.pages.create(
#                 parent={"database_id": NOTION_DB_ID}, properties=props
#             )
#             print(f"[Row {i}] Notion 등록 완료", list(props.keys()))

#             # 수정: Google Sheets S열에 '완료' 표시
#             cell = f"{SHEET_NAME}!S{i}"
#             sheets.spreadsheets().values().update(
#                 spreadsheetId=SPREADSHEET_ID,
#                 range=cell,
#                 valueInputOption="USER_ENTERED",
#                 body={"values": [["완료"]]},
#             ).execute()
#             print(f"[Row {i}] 시트에 ‘완료’ 표기 완료 → {cell}")

#             # ─── 블록 삽입 (오류 나면 건너뛰기) ───────────────────────────────────
#             for url in image_urls:
#                 ext = os.path.splitext(urlparse(url).path)[1].lower()
#                 if ext == ".pdf":
#                     block = {
#                         "object": "block",
#                         "type": "file",
#                         "file": {"type": "external", "external": {"url": url}},
#                     }
#                 else:
#                     block = {
#                         "object": "block",
#                         "type": "image",
#                         "image": {"type": "external", "external": {"url": url}},
#                     }

#                 try:
#                     notion.blocks.children.append(block_id=page["id"], children=[block])
#                     print(f"[Row {i}] 블록 삽입 완료 → {url}")
#                 except Exception as e:
#                     print(f"[Row {i}] 블록 삽입 오류, 건너뜁니다: {url} ▶ {e}")

#         else:
#             print(f"[Row {i}] 매핑된 속성 없음")


# if __name__ == "__main__":
#     sheet_to_notion_s3()

import os
import re
import tempfile
import base64
import requests
from datetime import datetime, timedelta
import boto3
import chromedriver_autoinstaller
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from google.oauth2 import service_account
from googleapiclient.discovery import build
from notion_client import Client as NotionClient

# ─── 환경변수 로드 ─────────────────────────────────────────────────────────
load_dotenv()


# 웹 배포 환경을 위한 기본값 설정
def get_env_with_default(key, default=None):
    """환경변수를 가져오되, 없으면 기본값 사용"""
    value = os.getenv(key, default)
    if not value and key in ["CHROME_BINARY", "SMORE_USER_DATA", "SMORE_PROFILE"]:
        print(f"⚠️ {key} 환경변수가 설정되지 않음. 기본값 사용.")
    return value


# 환경변수 설정 (웹 배포 환경 대응)
CHROME_BINARY = get_env_with_default("CHROME_BINARY")
SMORE_USER_DATA = get_env_with_default("SMORE_USER_DATA")
SMORE_PROFILE = get_env_with_default("SMORE_PROFILE", "Default")
GOOGLE_CRED = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_RANGE = os.getenv("SHEET_RANGE")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID")
TEST_OFFSET = int(os.getenv("TEST_OFFSET", "0"))
TEST_LIMIT = int(os.getenv("TEST_LIMIT", "0"))

# 다운로드 디렉토리 (웹 환경 대응)
DOWNLOAD_DIR = os.getenv("SMORE_DOWNLOAD_DIR", tempfile.gettempdir())
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

print(f"🔧 환경 설정:")
print(f"  - Chrome Binary: {CHROME_BINARY}")
print(f"  - User Data: {SMORE_USER_DATA}")
print(f"  - Download Dir: {DOWNLOAD_DIR}")
print(f"  - S3 Bucket: {S3_BUCKET}")

# ─── 클라이언트 초기화 ─────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Google Credentials 처리 (웹 환경 대응)
if GOOGLE_CRED and os.path.exists(GOOGLE_CRED):
    ga_creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CRED, scopes=SCOPES
    )
else:
    # 환경변수에서 JSON 직접 읽기 시도
    cred_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if cred_json:
        import json

        ga_creds = service_account.Credentials.from_service_account_info(
            json.loads(cred_json), scopes=SCOPES
        )
    else:
        raise ValueError("Google Credentials를 찾을 수 없습니다.")

sheets = build("sheets", "v4", credentials=ga_creds)
s3 = boto3.client("s3", region_name=AWS_REGION)
notion = NotionClient(auth=NOTION_TOKEN)

SHEET_NAME = SHEET_RANGE.split("!")[0]

# ─── 헤더 매핑 ─────────────────────────────────────────────────────────────
HEADER_TO_PROP = {
    "순번": "순번",
    "출산을 증명할 수 있는 이미지 파일을 첨부해 주세요 등본, 가족관계증명서, 출생증명서, 산모수첩 중 택1": "증명서 이미지",
    "타가몰에서 사용 중이신 아이디를 알려주세요💛 간편가입 하신 경우 앱 아이디를 입력해주세요.(ex.1234567@N)": "타가몰 아이디",
    "신청자 본인의 성함을 적어주세요 😃 ※ 표기 오류로 인한 대상 제외 및 경품 미수령시 책임지지 않습니다.": "이름",
    "📱 연락 가능한 번호를 적어주세요💛 (예: 010-1234-5678)": "연락처",
    "보듬박스를 받으실 상세 주소를 적어 주세요.💛 ※ 표기 오류로 인한 대상 제외 및 경품 미수령시 책임지지 않습니다.": "주소",
    "📅 아기 출생 예정일이나 출생일을 알려주세요💛": "출생일",
    "담당자": "담당자",
    "적/부": "적/부",
}


def normalize_header(h: str) -> str:
    return re.sub(r"\s+", " ", h.replace("\n", " ").strip())


NORM_HEADER_TO_PROP = {normalize_header(k): v for k, v in HEADER_TO_PROP.items()}


# ─── Chrome 옵션 설정 (웹 배포 환경용) ─────────────────────────────────────
def get_chrome_options():
    """웹 배포 환경에 최적화된 Chrome 옵션"""
    opts = Options()

    # 헤드리스 모드 (웹 환경 필수)
    opts.add_argument("--headless=new")  # 최신 헤드리스 모드

    # 웹 배포 환경 최적화 옵션
    opts.add_argument("--no-sandbox")  # 권한 문제 해결
    opts.add_argument("--disable-dev-shm-usage")  # 메모리 문제 해결
    opts.add_argument("--disable-gpu")  # GPU 비활성화
    opts.add_argument("--disable-extensions")  # 확장 기능 비활성화
    opts.add_argument("--disable-web-security")  # 보안 제한 완화
    opts.add_argument("--allow-running-insecure-content")
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-renderer-backgrounding")
    opts.add_argument("--disable-features=TranslateUI")
    opts.add_argument("--disable-ipc-flooding-protection")

    # 사용자 에이전트 설정 (봇 탐지 우회)
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 창 크기 설정
    opts.add_argument("--window-size=1920,1080")

    # Chrome 바이너리 위치 설정 (있는 경우)
    if CHROME_BINARY and os.path.exists(CHROME_BINARY):
        opts.binary_location = CHROME_BINARY

    # 사용자 데이터 디렉토리 설정 (있고 쓰기 가능한 경우)
    if SMORE_USER_DATA and os.path.exists(SMORE_USER_DATA):
        try:
            # 쓰기 권한 확인
            test_file = os.path.join(SMORE_USER_DATA, "test_write")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            opts.add_argument(f"--user-data-dir={SMORE_USER_DATA}")
            if SMORE_PROFILE:
                opts.add_argument(f"--profile-directory={SMORE_PROFILE}")
        except (PermissionError, OSError):
            print(f"⚠️ 사용자 데이터 디렉토리에 쓰기 권한 없음: {SMORE_USER_DATA}")

    return opts


# ─── Chrome 드라이버 초기화 함수 ──────────────────────────────────────────
def get_chrome_driver():
    """웹 배포 환경용 Chrome 드라이버 생성"""
    try:
        # ChromeDriver 자동 설치
        driver_path = chromedriver_autoinstaller.install()
        print(f"✅ ChromeDriver 경로: {driver_path}")

        # Chrome 옵션 설정
        options = get_chrome_options()

        # 서비스 설정
        service = Service(driver_path)

        # 드라이버 생성
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)  # 타임아웃 설정

        return driver

    except Exception as e:
        print(f"❌ Chrome 드라이버 생성 실패: {e}")
        raise


# ─── 기타 유틸리티 함수들 ────────────────────────────────────────────────


def excel_serial_to_datetime(serial) -> datetime:
    try:
        days = float(serial)
    except:
        return None
    epoch = datetime(1899, 12, 30) if days >= 61 else datetime(1899, 12, 31)
    return epoch + timedelta(days=days)


def safe_key_name(row_idx: int, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    b64 = base64.urlsafe_b64encode(base.encode("utf-8")).decode("ascii")
    return f"row{row_idx}_{b64}{ext}"


# ─── S3 업로드 함수 (개선) ──────────────────────────────────────────────
def upload_to_s3(local, key):
    """이미지 압축 및 S3 업로드"""
    print(f"📤 S3 업로드 시작: {key}")

    if not os.path.exists(local):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {local}")

    compressed_path = local

    # 이미지 압축
    try:
        with Image.open(local) as img:
            resample = getattr(Image, "Resampling", Image).LANCZOS
            img.thumbnail((1024, 1024), resample)

            ext = os.path.splitext(local)[1].lower()
            if ext in (".jpg", ".jpeg"):
                img.save(local, format="JPEG", optimize=True, quality=75)
            else:
                rgb = img.convert("RGB")
                jpeg_path = os.path.splitext(local)[0] + ".jpg"
                rgb.save(jpeg_path, format="JPEG", optimize=True, quality=75)
                compressed_path = jpeg_path
                key = os.path.splitext(key)[0] + ".jpg"

                try:
                    os.remove(local)
                except:
                    pass

        print(f"🗜️ 이미지 압축 완료")

    except Exception as e:
        print(f"⚠️ 압축 실패, 원본 사용: {e}")

    # S3 업로드
    try:
        import mimetypes

        ctype, _ = mimetypes.guess_type(compressed_path)

        s3.upload_file(
            Filename=compressed_path,
            Bucket=S3_BUCKET,
            Key=key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": ctype or "application/octet-stream",
            },
        )

        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        print(f"✅ S3 업로드 완료: {s3_url}")

        # 로컬 파일 정리
        try:
            os.remove(compressed_path)
        except:
            pass

        return s3_url

    except Exception as e:
        print(f"❌ S3 업로드 실패: {e}")
        raise


# ─── Smore 쿠키 획득 (웹 환경 대응) ─────────────────────────────────────────
def get_smore_cookies():
    """웹 배포 환경용 쿠키 획득"""
    print("🍪 Smore 쿠키 획득 시작")
    driver = None

    try:
        driver = get_chrome_driver()
        driver.get("https://smore.im")

        # 페이지 로드 대기
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
        print(f"✅ 쿠키 획득 완료: {len(cookies)}개")
        return cookies

    except Exception as e:
        print(f"❌ 쿠키 획득 실패: {e}")
        return {}
    finally:
        if driver:
            driver.quit()


# ─── Smore 파일 다운로드 (웹 환경 대응) ──────────────────────────────────────
def download_smore_image(page_url, cookies, row_idx):
    """웹 배포 환경용 파일 다운로드"""
    print(f"⬇️ 파일 다운로드 시작: Row {row_idx}")
    driver = None

    try:
        driver = get_chrome_driver()

        # 쿠키 설정을 위해 먼저 smore.im 방문
        driver.get("https://smore.im")
        for name, value in cookies.items():
            try:
                driver.add_cookie({"name": name, "value": value})
            except:
                pass

        # 실제 페이지 방문
        driver.get(page_url)

        # 다운로드 링크 대기 및 클릭
        link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "download"))
        )
        file_url = link.get_attribute("href")

        # 파일 다운로드
        sess = requests.Session()
        sess.cookies.update(cookies)

        # 헤더 설정 (봇 탐지 우회)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        resp = sess.get(file_url, stream=True, timeout=30, headers=headers)
        resp.raise_for_status()

        if "text/html" in resp.headers.get("Content-Type", ""):
            raise RuntimeError("HTML 반환됨 (로그인 실패?)")

        # 파일명 추출
        cd = resp.headers.get("content-disposition", "")
        m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(
            r"filename=?\"?([^\";]+)\"?", cd
        )
        orig = unquote(m.group(1)) if m else f"file_{row_idx}.jpg"

        filename = safe_key_name(row_idx, orig)
        local = os.path.join(DOWNLOAD_DIR, filename)

        # 파일 저장
        with open(local, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)

        print(f"✅ 다운로드 완료: {local}")
        return local

    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        raise
    finally:
        if driver:
            driver.quit()


# ─── 메인 함수 ─────────────────────────────────────────────────────────────
def sheet_to_notion_s3():
    """메인 처리 함수"""
    print("🚀 Google Sheets to Notion 처리 시작")

    try:
        # 쿠키 획득
        cookies = get_smore_cookies()
        if not cookies:
            print("⚠️ 쿠키 획득 실패, 계속 진행")

        # 시트 데이터 읽기
        print("📊 Google Sheets 데이터 읽기")
        res = (
            sheets.spreadsheets()
            .values()
            .get(
                spreadsheetId=SPREADSHEET_ID,
                range=SHEET_RANGE,
                valueRenderOption="FORMULA",
            )
            .execute()
        )

        rows = res.get("values", [])
        if len(rows) < 2:
            print("❌ 처리할 데이터가 없습니다")
            return

        headers = [normalize_header(h) for h in rows[0]]
        done_idx = headers.index("이관완료") if "이관완료" in headers else None
        data_rows = rows[1:]
        recs = (
            data_rows[TEST_OFFSET : TEST_OFFSET + TEST_LIMIT]
            if TEST_LIMIT > 0
            else data_rows[TEST_OFFSET:]
        )

        # Notion DB 속성 확인
        print("🔍 Notion 데이터베이스 확인")
        db_props = notion.databases.retrieve(database_id=NOTION_DB_ID)["properties"]

        print(f"📝 처리할 행: {len(recs)}개")

        # 각 행 처리
        success_count = 0
        for i, row in enumerate(recs, start=TEST_OFFSET + 2):
            try:
                print(f"\n📋 [Row {i}] 처리 시작")

                # 완료 체크
                if done_idx is not None and len(row) > done_idx:
                    cell_val = row[done_idx].strip()
                    if cell_val.startswith("완료"):
                        print(f"⏭️ [Row {i}] 이미 처리된 행")
                        continue

                # 데이터 처리
                data = {
                    headers[j]: row[j] if j < len(row) else ""
                    for j in range(len(headers))
                }
                props, image_urls = process_row_data(data, db_props, cookies, i)

                if props:
                    # Notion 페이지 생성
                    page = notion.pages.create(
                        parent={"database_id": NOTION_DB_ID}, properties=props
                    )

                    # 완료 표시
                    mark_row_complete(i)

                    # 이미지 블록 추가
                    add_image_blocks(page["id"], image_urls, i)

                    success_count += 1
                    print(f"✅ [Row {i}] 처리 완료")
                else:
                    print(f"⚠️ [Row {i}] 매핑된 속성 없음")

            except Exception as e:
                print(f"❌ [Row {i}] 처리 실패: {e}")
                continue

        print(f"\n🎉 처리 완료: {success_count}/{len(recs)}개 성공")

    except Exception as e:
        print(f"❌ 전체 처리 실패: {e}")
        raise


def process_row_data(data, db_props, cookies, row_idx):
    """행 데이터 처리"""
    props, image_urls = {}, []

    for hdr, val in data.items():
        if not val:
            continue

        prop = NORM_HEADER_TO_PROP.get(normalize_header(hdr))
        if not prop or prop not in db_props:
            continue

        ptype = db_props[prop]["type"]

        # 파일/URL 처리
        if ptype in ["files", "url"] and str(val).startswith("=HYPERLINK"):
            file_prop, urls = process_file_property(val, prop, ptype, cookies, row_idx)
            if file_prop:
                props[prop] = file_prop
                image_urls.extend(urls)

        # 다른 속성들 처리
        elif ptype == "date":
            date_prop = process_date_property(val)
            if date_prop:
                props[prop] = date_prop
        elif ptype == "url" and not str(val).startswith("=HYPERLINK"):
            props[prop] = {"url": str(val).strip()}
        elif ptype == "title":
            props[prop] = {"title": [{"text": {"content": str(val)}}]}
        elif ptype == "rich_text":
            props[prop] = {"rich_text": [{"text": {"content": str(val)}}]}

    return props, image_urls


def process_file_property(val, prop, ptype, cookies, row_idx):
    """파일 속성 처리"""
    try:
        m = re.match(r'=HYPERLINK\("([^"]+)"(?:\s*,\s*"([^"]+)")?\)', val)
        if not m:
            return None, []

        url = m.group(1)
        disp = m.group(2) or "파일"

        # 파일 다운로드 및 S3 업로드
        local = download_smore_image(url, cookies, row_idx)
        key = safe_key_name(row_idx, os.path.basename(local))
        s3_url = upload_to_s3(local, key)

        if ptype == "url":
            return {"url": s3_url}, [s3_url]
        else:  # files
            display_name = disp[:97] + "..." if len(disp) > 100 else disp
            return {"files": [{"name": display_name, "external": {"url": s3_url}}]}, [
                s3_url
            ]

    except Exception as e:
        print(f"❌ 파일 처리 실패: {e}")
        return None, []


def process_date_property(val):
    """날짜 속성 처리"""
    try:
        m = re.match(r"^=DATE\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", str(val))
        if m:
            y, mo, da = map(int, m.groups())
            return {"date": {"start": datetime(y, mo, da).isoformat()}}
        else:
            dt = excel_serial_to_datetime(val)
            if dt:
                return {"date": {"start": dt.isoformat()}}
    except:
        pass
    return None


def mark_row_complete(row_idx):
    """행 완료 표시"""
    try:
        cell = f"{SHEET_NAME}!S{row_idx}"
        sheets.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=cell,
            valueInputOption="USER_ENTERED",
            body={"values": [["완료"]]},
        ).execute()
    except Exception as e:
        print(f"⚠️ 완료 표시 실패: {e}")


def add_image_blocks(page_id, image_urls, row_idx):
    """이미지 블록 추가"""
    for url in image_urls:
        try:
            ext = os.path.splitext(urlparse(url).path)[1].lower()
            block = {
                "object": "block",
                "type": "file" if ext == ".pdf" else "image",
                (ext == ".pdf" and "file" or "image"): {
                    "type": "external",
                    "external": {"url": url},
                },
            }
            notion.blocks.children.append(block_id=page_id, children=[block])
        except Exception as e:
            print(f"⚠️ 블록 추가 실패: {e}")


if __name__ == "__main__":
    sheet_to_notion_s3()
# $Env:TEST_OFFSET = "1"; $Env:TEST_LIMIT = "10"; python google-to-notion.py
