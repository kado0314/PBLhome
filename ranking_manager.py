import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import cloudinary
import cloudinary.uploader
import base64
import os
import json

# スコープ設定
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# スプレッドシートID
SPREADSHEET_KEY = "17QqxdjbY5OM8zGLPcrjn_-d1ZVCifvFH4dp9feOjfDk"

# Cloudinaryの設定 (環境変数から取得)
cloudinary.config(
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
  secure = True
)

def get_client():
    """Google Sheetsの認証クライアントを取得"""
    try:
        # 環境変数 GOOGLE_CREDENTIALS_JSON から認証情報を読み込む
        creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        
        if creds_json_str:
            creds_dict = json.loads(creds_json_str)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        else:
            # ローカル環境用フォールバック（credentials.jsonがある場合）
            if os.path.exists('credentials.json'):
                creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
            else:
                raise Exception("Google Credentials not found in Environment Variables or file.")

        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Authentication Error: {e}")
        return None

def upload_image_to_cloudinary(image_data_base64):
    """画像をCloudinaryにアップロード"""
    if not image_data_base64:
        return ""
        
    try:
        # data URIスキーム (data:image/jpeg;base64,...) がついている場合は除去
        if ',' in image_data_base64:
            image_data_base64 = image_data_base64.split(',')[1]
            
        # Cloudinaryへアップロード
        # タイムスタンプ等を付与してユニークにする
        response = cloudinary.uploader.upload(
            image_data_base64, 
            folder="fashion_ranking",
            resource_type="image"
        )
        print(f"Cloudinary Upload Success: {response.get('secure_url')}")
        return response['secure_url']
    except Exception as e:
        # ここでエラーが出ている可能性が高いので詳細を表示
        print(f"Cloudinary Upload Error: {e}")
        return ""

def _delete_image_by_url(image_url):
    """URLからCloudinaryの画像を削除する内部関数"""
    if not image_url: return
    try:
        filename_with_ext = image_url.split('/')[-1]
        public_id_name = filename_with_ext.split('.')[0]
        full_public_id = f"fashion_ranking/{public_id_name}"
        cloudinary.uploader.destroy(full_public_id)
        print(f"Cloudinary Image Deleted: {full_public_id}")
    except Exception as e:
        print(f"Image Delete Error: {e}")

# ▼▼▼ 入力チェック＆整形関数 ▼▼▼
def _normalize_str(value):
    """数値を文字列化し、.0を削除し、空白を除去"""
    if value is None: return ""
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def _is_valid_input(text):
    """
    セキュリティチェック:
    1. 文字と数字のみ許可 (isalnum) -> 記号・スペース禁止
    2. Excel関数のトリガー文字 (=, +, -, @) で始まっていないか確認
    """
    s = _normalize_str(text)
    if not s: return False
    
    # 関数インジェクション対策
    if s.startswith(('=', '+', '-', '@')):
        return False
        
    # 文字・数字のみ許可 (日本語OK, 記号NG)
    if not s.isalnum():
        return False
        
    return True

def get_ranking():
    """ランキングトップ100を取得"""
    try:
        client = get_client()
        if not client: return []

        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        records = sheet.get_all_records()
        
        valid_records = []
        for r in records:
            try:
                r['score'] = float(r['score'])
                if 'image_url' not in r: r['image_url'] = ""
                valid_records.append(r)
            except:
                continue

        sorted_records = sorted(valid_records, key=lambda x: x['score'], reverse=True)
        return sorted_records[:100]
    except Exception as e:
        print(f"Ranking Fetch Error: {e}")
        return []

def prune_ranking(sheet):
    """100位以下を削除するお掃除関数"""
    try:
        records = sheet.get_all_records()
        if len(records) <= 100: return

        def get_score(r):
            try: return float(r['score'])
            except: return -1.0
            
        sorted_records = sorted(records, key=get_score, reverse=True)
        items_to_delete = sorted_records[100:]
        
        print(f"--- Pruning: Cleaning up {len(items_to_delete)} items ---")

        for item in items_to_delete:
            name = item.get('name')
            delete_pass = item.get('delete_pass')
            delete_ranking_entry(name, delete_pass, sheet)
            
    except Exception as e:
        print(f"Pruning Error: {e}")

def add_ranking_entry(name, score, delete_pass, image_data_base64=None):
    """ランキングに登録"""
    # ▼▼▼ 厳密な入力チェック ▼▼▼
    if not _is_valid_input(name):
        print("Invalid Name Format")
        return False
    if not _is_valid_input(delete_pass):
        print("Invalid Password Format")
        return False

    try:
        client = get_client()
        if not client: return False

        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["name", "score", "date", "delete_pass", "image_url"])
        
        header = sheet.row_values(1)
        if "image_url" not in header:
            sheet.update_cell(1, len(header) + 1, "image_url")

        image_url = ""
        # Cloudinaryへのアップロード試行
        if image_data_base64:
            print("Attempting to upload image to Cloudinary...")
            image_url = upload_image_to_cloudinary(image_data_base64)
            if not image_url:
                print("Warning: Image upload returned empty URL.")

        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 念のため、書き込み時に再度エスケープ処理（文字列として強制）
        clean_name = _normalize_str(name)
        clean_pass = _normalize_str(delete_pass)
        
        # スプレッドシートに行を追加
        sheet.append_row([clean_name, score, date_str, clean_pass, image_url])
        
        prune_ranking(sheet)
        return True
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False

def delete_ranking_entry(name, delete_pass, sheet_obj=None):
    """削除処理"""
    try:
        if sheet_obj:
            sheet = sheet_obj
        else:
            client = get_client()
            if not client: return False
            sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
            
        records = sheet.get_all_records()
        deleted = False
        target_name = _normalize_str(name)
        target_pass = _normalize_str(delete_pass)

        print(f"--- Delete Request: Name=[{target_name}], Pass=[{target_pass}] ---")

        for i, record in reversed(list(enumerate(records))):
            row_num = i + 2
            sheet_name = _normalize_str(record.get('name', ''))
            sheet_pass = _normalize_str(record.get('delete_pass', ''))
            
            if sheet_name == target_name and sheet_pass == target_pass:
                image_url = record.get('image_url', '')
                _delete_image_by_url(image_url)
                sheet.delete_rows(row_num)
                deleted = True
                print(f"!!! Deleted Row {row_num} !!!")
                break
        
        return deleted
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
