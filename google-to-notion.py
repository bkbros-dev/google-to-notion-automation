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
import json
from datetime import datetime, timedelta
import boto3
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote
from PIL import Image

from google.oauth2 import service_account
from googleapiclient.discovery import build
from notion_client import Client as NotionClient

# ─── 환경변수 로드 ─────────────────────────────────────────────────────────
load_dotenv()


def get_env_or_fail(key, required=True):
    """환경변수를 가져오되, 필수값이 없으면 에러"""
    value = os.getenv(key)
    if required and not value:
        raise ValueError(f"필수 환경변수 {key}가 설정되지 않았습니다.")
    return value


# 환경변수 설정
GOOGLE_CRED = get_env_or_fail("GOOGLE_APPLICATION_CREDENTIALS", False)
GOOGLE_CRED_JSON = get_env_or_fail("GOOGLE_CREDENTIALS_JSON", False)
SPREADSHEET_ID = get_env_or_fail("SPREADSHEET_ID")
SHEET_RANGE = get_env_or_fail("SHEET_RANGE")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")
S3_BUCKET = get_env_or_fail("S3_BUCKET_NAME")
NOTION_TOKEN = get_env_or_fail("NOTION_TOKEN")
NOTION_DB_ID = get_env_or_fail("NOTION_DATABASE_ID")
TEST_OFFSET = int(os.getenv("TEST_OFFSET", "0"))
TEST_LIMIT = int(os.getenv("TEST_LIMIT", "0"))

# Smore 쿠키 (JSON 형태)
SMORE_COOKIES = os.getenv("SMORE_COOKIES", "{}")

# 다운로드 디렉토리
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", tempfile.gettempdir())
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

print("🔧 환경 설정 확인:")
print(f"  - Google Creds: {'✅' if GOOGLE_CRED or GOOGLE_CRED_JSON else '❌'}")
print(f"  - AWS Region: {AWS_REGION}")
print(f"  - S3 Bucket: {S3_BUCKET}")
print(f"  - Download Dir: {DOWNLOAD_DIR}")

# ─── 클라이언트 초기화 ─────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Google Credentials 처리
if GOOGLE_CRED and os.path.exists(GOOGLE_CRED):
    ga_creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CRED, scopes=SCOPES
    )
    print("✅ Google 인증: 파일 기반")
elif GOOGLE_CRED_JSON:
    try:
        cred_data = json.loads(GOOGLE_CRED_JSON)
        ga_creds = service_account.Credentials.from_service_account_info(
            cred_data, scopes=SCOPES
        )
        print("✅ Google 인증: JSON 기반")
    except json.JSONDecodeError:
        raise ValueError("GOOGLE_CREDENTIALS_JSON이 유효한 JSON이 아닙니다.")
else:
    raise ValueError("Google Credentials를 찾을 수 없습니다.")

# 클라이언트 초기화
sheets = build("sheets", "v4", credentials=ga_creds)
s3 = boto3.client("s3", region_name=AWS_REGION)
notion = NotionClient(auth=NOTION_TOKEN)

# AWS 연결 테스트
try:
    s3.head_bucket(Bucket=S3_BUCKET)
    print("✅ S3 연결 성공")
except Exception as e:
    print(f"❌ S3 연결 실패: {e}")

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

# ─── 유틸리티 함수들 ────────────────────────────────────────────────────


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


# ─── S3 업로드 함수 ──────────────────────────────────────────────────
def upload_to_s3(local_path, key):
    """이미지 압축 및 S3 업로드"""
    print(f"📤 S3 업로드 시작: {key}")

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {local_path}")

    compressed_path = local_path

    # 이미지 압축
    try:
        with Image.open(local_path) as img:
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            resample = getattr(Image, "Resampling", Image).LANCZOS
            img.thumbnail((1024, 1024), resample)

            jpeg_path = os.path.splitext(local_path)[0] + ".jpg"
            img.save(jpeg_path, format="JPEG", optimize=True, quality=75)
            compressed_path = jpeg_path
            key = os.path.splitext(key)[0] + ".jpg"

            if jpeg_path != local_path:
                try:
                    os.remove(local_path)
                except:
                    pass

        print(f"🗜️ 이미지 압축 완료: {compressed_path}")

    except Exception as e:
        print(f"⚠️ 압축 실패, 원본 사용: {e}")
        compressed_path = local_path

    # S3 업로드
    try:
        file_size = os.path.getsize(compressed_path)
        print(f"📏 파일 크기: {file_size:,} bytes")

        import mimetypes

        content_type, _ = mimetypes.guess_type(compressed_path)

        with open(compressed_path, "rb") as f:
            s3.upload_fileobj(
                f,
                S3_BUCKET,
                key,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": content_type or "image/jpeg",
                    "CacheControl": "max-age=31536000",
                },
            )

        s3_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        print(f"✅ S3 업로드 완료: {s3_url}")

        try:
            os.remove(compressed_path)
        except:
            pass

        return s3_url

    except Exception as e:
        print(f"❌ S3 업로드 실패: {e}")
        raise


# ─── Smore 쿠키 관리 ──────────────────────────────────────────────────
def get_smore_cookies():
    """환경변수에서 쿠키 로드"""
    try:
        if SMORE_COOKIES and SMORE_COOKIES != "{}":
            cookies = json.loads(SMORE_COOKIES)
            print(f"✅ 쿠키 로드 완료: {len(cookies)}개")
            return cookies
        else:
            print("⚠️ 쿠키가 설정되지 않음. 수동 설정 필요.")
            return {}
    except json.JSONDecodeError:
        print("❌ 쿠키 JSON 파싱 실패")
        return {}


# ─── Smore 파일 다운로드 (BeautifulSoup 완전 제거) ─────────────────────────────
def download_smore_image_direct(page_url, cookies, row_idx):
    """BeautifulSoup 없이 Smore API에서 직접 파일 다운로드"""
    print(f"⬇️ Smore API 다운로드 시작: Row {row_idx}")

    try:
        session = requests.Session()

        # 쿠키 설정
        if cookies:
            session.cookies.update(cookies)

        # 헤더 설정
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin",
            "Referer": "https://smore.im/",
        }

        print(f"🔗 API 직접 호출: {page_url}")

        # 먼저 HEAD 요청으로 확인
        try:
            head_response = session.head(page_url, headers=headers, timeout=10)
            print(f"📊 HEAD 응답: {head_response.status_code}")
            print(
                f"📋 Content-Type: {head_response.headers.get('Content-Type', 'Unknown')}"
            )
            print(
                f"📏 Content-Length: {head_response.headers.get('Content-Length', 'Unknown')}"
            )
        except:
            print("⚠️ HEAD 요청 실패, GET으로 진행")

        # 실제 파일 다운로드
        response = session.get(page_url, headers=headers, stream=True, timeout=60)
        print(f"📊 GET 응답: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ HTTP 오류: {response.status_code}")
            return create_error_image(row_idx, f"HTTP {response.status_code}")

        # Content-Type 확인
        content_type = response.headers.get("Content-Type", "").lower()
        print(f"📋 실제 Content-Type: {content_type}")

        # HTML 응답이면 인증 실패 또는 오류
        if "text/html" in content_type:
            print("❌ HTML 응답 감지 - 인증 실패 또는 접근 거부")
            # 응답 내용 일부 확인
            try:
                content_preview = response.text[:300]
                print(f"📄 HTML 미리보기: {content_preview}")

                # 특정 오류 메시지 확인
                if any(
                    keyword in content_preview.lower()
                    for keyword in [
                        "login",
                        "unauthorized",
                        "forbidden",
                        "access denied",
                    ]
                ):
                    return create_error_image(row_idx, "인증 필요")
                else:
                    return create_error_image(row_idx, "HTML 응답")
            except:
                return create_error_image(row_idx, "인증 오류")

        # JSON 응답이면 API 오류
        if "application/json" in content_type:
            try:
                error_data = response.json()
                print(f"📄 JSON 오류: {error_data}")
                error_msg = error_data.get("message", "API 오류")
                return create_error_image(row_idx, error_msg)
            except:
                return create_error_image(row_idx, "JSON 파싱 오류")

        # 파일명 추출
        filename = f"smore_file_{row_idx}.jpg"
        content_disposition = response.headers.get("content-disposition", "")
        if content_disposition:
            # Content-Disposition 파싱
            patterns = [
                r"filename\*=UTF-8\'\'([^;]+)",
                r'filename="([^"]+)"',
                r"filename=([^;,]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, content_disposition, re.IGNORECASE)
                if match:
                    filename = unquote(match.group(1).strip('"'))
                    print(f"📝 추출된 파일명: {filename}")
                    break

        # 안전한 파일명 생성
        safe_filename = safe_key_name(row_idx, filename)
        local_path = os.path.join(DOWNLOAD_DIR, safe_filename)

        # 파일 저장
        total_size = 0
        print("💾 파일 저장 중...")
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        print(f"✅ 실제 파일 다운로드 완료!")
        print(f"📁 경로: {local_path}")
        print(f"📏 크기: {total_size:,} bytes")

        # 파일 크기 검증
        if total_size < 1000:  # 1KB 미만이면 의심
            print("⚠️ 파일 크기가 매우 작습니다. 내용 확인...")
            try:
                with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(200)
                    print(f"📄 파일 내용: {content}")
                    if any(
                        word in content.lower()
                        for word in ["error", "login", "unauthorized", "forbidden"]
                    ):
                        print("❌ 오류 응답 파일 감지")
                        return create_error_image(row_idx, "인증 오류")
            except:
                # 바이너리 파일이면 정상일 가능성
                print("🔍 바이너리 파일로 추정, 정상 처리")

        # 이미지 파일인지 확인
        try:
            with Image.open(local_path) as img:
                print(f"🖼️ 이미지 확인: {img.format} {img.size} {img.mode}")
        except Exception as e:
            print(f"⚠️ 이미지 검증 실패: {e}")
            # 이미지가 아니어도 일단 진행

        return local_path

    except requests.exceptions.Timeout:
        print("❌ 타임아웃 오류")
        return create_error_image(row_idx, "타임아웃")
    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류")
        return create_error_image(row_idx, "연결 실패")
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return create_error_image(row_idx, f"네트워크: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        return create_error_image(row_idx, f"오류: {e}")


def create_error_image(row_idx, error_msg):
    """오류 이미지 생성"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 이미지 생성
        img = Image.new("RGB", (800, 600), color="#f8f9fa")
        draw = ImageDraw.Draw(img)

        # 폰트 설정
        try:
            font_title = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
            )
            font_text = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
            )
        except:
            try:
                font_title = ImageFont.truetype("arial.ttf", 28)
                font_text = ImageFont.truetype("arial.ttf", 18)
            except:
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()

        # 텍스트 작성
        title = "Smore 파일 다운로드 실패"
        subtitle = f"Row {row_idx}"
        error_text = f"오류: {error_msg}"
        solution1 = "해결 방법:"
        solution2 = "1. Smore 로그인 후 쿠키 설정"
        solution3 = "2. 수동으로 파일 다운로드"
        solution4 = "3. API 접근 권한 확인"

        # 텍스트 그리기
        y_pos = 100
        draw.text((50, y_pos), title, fill="#dc3545", font=font_title)
        y_pos += 50
        draw.text((50, y_pos), subtitle, fill="#6c757d", font=font_text)
        y_pos += 40
        draw.text((50, y_pos), error_text, fill="#495057", font=font_text)
        y_pos += 60
        draw.text((50, y_pos), solution1, fill="#28a745", font=font_text)
        y_pos += 30
        draw.text((70, y_pos), solution2, fill="#6c757d", font=font_text)
        y_pos += 25
        draw.text((70, y_pos), solution3, fill="#6c757d", font=font_text)
        y_pos += 25
        draw.text((70, y_pos), solution4, fill="#6c757d", font=font_text)

        # 테두리
        draw.rectangle([20, 20, 780, 580], outline="#dee2e6", width=3)

        # 저장
        error_path = os.path.join(DOWNLOAD_DIR, f"smore_error_row_{row_idx}.jpg")
        img.save(error_path, format="JPEG", quality=90)

        print(f"🖼️ 오류 이미지 생성: {error_path}")
        return error_path

    except Exception as e:
        print(f"❌ 오류 이미지 생성 실패: {e}")
        # 텍스트 파일로 대체
        error_path = os.path.join(DOWNLOAD_DIR, f"smore_error_{row_idx}.txt")
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(f"Smore download failed for row {row_idx}\n")
            f.write(f"Error: {error_msg}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"URL pattern: https://smore.im/api/form/download?fileId=...\n")
        return error_path


# ─── 메인 처리 함수들 ────────────────────────────────────────────────────


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
        elif ptype == "select":
            props[prop] = {"select": {"name": str(val).strip()}}

    return props, image_urls


def process_file_property(val, prop, ptype, cookies, row_idx):
    """파일 속성 처리"""
    try:
        # HYPERLINK 파싱
        m = re.match(r'=HYPERLINK\("([^"]+)"(?:\s*,\s*"([^"]+)")?\)', val)
        if not m:
            print(f"❌ HYPERLINK 파싱 실패: {val}")
            return None, []

        url = m.group(1)
        disp = m.group(2) or f"파일_{row_idx}"

        print(f"🔗 파일 URL: {url}")
        print(f"📝 표시명: {disp}")

        # 파일 다운로드
        local_path = download_smore_image_direct(url, cookies, row_idx)

        # S3 업로드
        key = safe_key_name(row_idx, os.path.basename(local_path))
        s3_url = upload_to_s3(local_path, key)

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
        # =DATE() 함수 파싱
        m = re.match(r"^=DATE\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", str(val))
        if m:
            y, mo, da = map(int, m.groups())
            return {"date": {"start": datetime(y, mo, da).isoformat()}}

        # Excel 시리얼 날짜 변환
        dt = excel_serial_to_datetime(val)
        if dt:
            return {"date": {"start": dt.isoformat()}}

    except Exception as e:
        print(f"⚠️ 날짜 변환 실패: {e}")

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
        print(f"✅ 완료 표시: {cell}")
    except Exception as e:
        print(f"⚠️ 완료 표시 실패: {e}")


def add_image_blocks(page_id, image_urls, row_idx):
    """이미지 블록 추가"""
    for url in image_urls:
        try:
            ext = os.path.splitext(urlparse(url).path)[1].lower()
            block_type = "file" if ext == ".pdf" else "image"

            block = {
                "object": "block",
                "type": block_type,
                block_type: {"type": "external", "external": {"url": url}},
            }

            notion.blocks.children.append(block_id=page_id, children=[block])
            print(f"🖼️ 블록 추가 완료")

        except Exception as e:
            print(f"⚠️ 블록 추가 실패: {e}")


# ─── 메인 함수 ─────────────────────────────────────────────────────────────
def sheet_to_notion_s3():
    """메인 처리 함수"""
    print("🚀 Google Sheets to Notion 처리 시작")

    try:
        # 쿠키 로드
        cookies = get_smore_cookies()

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
        error_count = 0

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
                    if image_urls:
                        add_image_blocks(page["id"], image_urls, i)

                    success_count += 1
                    print(f"✅ [Row {i}] 처리 완료")
                else:
                    print(f"⚠️ [Row {i}] 매핑된 속성 없음")
                    error_count += 1

            except Exception as e:
                print(f"❌ [Row {i}] 처리 실패: {e}")
                import traceback

                traceback.print_exc()
                error_count += 1
                continue

        print(f"\n🎉 처리 완료:")
        print(f"  - 성공: {success_count}개")
        print(f"  - 실패: {error_count}개")
        print(f"  - 전체: {len(recs)}개")

        if error_count > 0:
            print("\n💡 오류 해결 방법:")
            print("  1. SMORE_COOKIES 환경변수 설정")
            print("  2. AWS 자격증명 확인")
            print("  3. Smore API 접근 권한 확인")

    except Exception as e:
        print(f"❌ 전체 처리 실패: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    sheet_to_notion_s3()

# ================================================================
# 쿠키 수동 설정 방법:
# 1. 브라우저에서 smore.im 로그인
# 2. F12 > Application > Cookies에서 모든 쿠키 복사
# 3. JSON 형태로 변환하여 환경변수 설정:
#    SMORE_COOKIES='{"PHPSESSID":"실제값","session_id":"실제값"}'
#
# 또는 개별 테스트:
# curl -I "https://smore.im/api/form/download?fileId=3SJ9V2BprZQL5uuiAaGim9Sc124mEg"
# ================================================================
