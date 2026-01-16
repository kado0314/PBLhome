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

# Cloudinaryの設定
cloudinary.config(
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "dqluizsxn"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY", "733249596838179"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET", "fJ1tto-eIbv19SBQBkI9r5rJb3Q"),
  secure = True
)

def get_client():
    """Google Sheets認証クライアントを取得"""
    try:
        creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if creds_json_str:
            creds_dict = json.loads(creds_json_str)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        else:
            if os.path.exists('credentials.json'):
                creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
            else:
                return None
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Authentication Error: {e}")
        return None

def upload_image_to_cloudinary(image_data_base64):
    """画像をCloudinaryにアップロード"""
    if not image_data_base64: return ""
    try:
        # ▼▼▼ 修正箇所: ヘッダーを削除しない！ ▼▼▼
        # CloudinaryのSDKは、data:image/... というヘッダーを見て「これは画像データだ」と判断します。
        # これがないとファイルパスだと誤解して「ファイル名が長すぎる」というエラーになります。
        
        response = cloudinary.uploader.upload(
            image_data_base64, 
            folder="fashion_ranking",
            resource_type="image"
        )
        return response['secure_url']
    except Exception as e:
        print(f"Cloudinary Upload Error: {e}")
        return ""

def _delete_image_by_url(image_url):
    """画像削除"""
    if not image_url: return
    try:
        filename_with_ext = image_url.split('/')[-1]
        public_id_name = filename_with_ext.split('.')[0]
        full_public_id = f"fashion_ranking/{public_id_name}"
        cloudinary.uploader.destroy(full_public_id)
        print(f"Deleted Image: {full_public_id}")
    except Exception as e:
        print(f"Image Delete Error: {e}")

def _normalize_str(value):
    if value is None: return ""
    s = str(value).strip()
    if s.endswith(".0"): s = s[:-2]
    return s

def _is_valid_input(text):
    s = _normalize_str(text)
    if not s: return False
    if s.startswith(('=', '+', '-', '@')): return False
    if not s.isalnum(): return False
    return True

def get_ranking():
    """ランキングTOP10取得"""
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
            except: continue
            
        sorted_records = sorted(valid_records, key=lambda x: x['score'], reverse=True)
        # 表示用はTOP10のみ
        return sorted_records[:10]
    except Exception as e:
        print(f"Ranking Fetch Error: {e}")
        return []

def prune_ranking(sheet):
    """10件超え自動削除（TOP10のみ維持）"""
    try:
        records = sheet.get_all_records()
        # ▼▼▼ 修正箇所: 10件より多ければ削除開始 ▼▼▼
        if len(records) <= 10: return
        
        def get_score(r):
            try: return float(r['score'])
            except: return -1.0
            
        sorted_records = sorted(records, key=get_score, reverse=True)
        
        # 11位以降（インデックス10～）を削除対象にする
        items_to_delete = sorted_records[10:]
        
        print(f"--- Pruning: Cleaning up {len(items_to_delete)} items ---")
        for item in items_to_delete:
            delete_ranking_entry(item.get('name'), item.get('delete_pass'), sheet)
            
    except Exception as e:
        print(f"Pruning Error: {e}")

def add_ranking_entry(name, score, delete_pass, image_data_base64=None):
    """登録処理"""
    if not _is_valid_input(name): return False, "名前に記号は使えません"
    if delete_pass and not _is_valid_input(delete_pass): return False, "パスワードに記号は使えません"

    try:
        client = get_client()
        if not client: return False, "サーバーエラー"
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["name", "score", "date", "delete_pass", "image_url"])
        
        header = sheet.row_values(1)
        if "image_url" not in header:
            sheet.update_cell(1, len(header) + 1, "image_url")

        # 重複チェック
        clean_name = _normalize_str(name)
        records = sheet.get_all_records()
        for r in records:
            if _normalize_str(r.get('name')) == clean_name:
                return False, "その名前は既に使用されています"

        image_url = ""
        if image_data_base64:
            image_url = upload_image_to_cloudinary(image_data_base64)

        date_str = datetime.now().strftime("%Y-%m-%d")
        clean_pass = _normalize_str(delete_pass)
        
        sheet.append_row([clean_name, score, date_str, clean_pass, image_url])
        
        # 追加後にTOP10制限処理を実行
        prune_ranking(sheet)
        
        return True, "登録しました"
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False, "サーバーエラーが発生しました"

def delete_ranking_entry(name, delete_pass, sheet_obj=None):
    """削除処理"""
    try:
        if sheet_obj: sheet = sheet_obj
        else:
            client = get_client()
            if not client: return False
            sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
            
        records = sheet.get_all_records()
        deleted = False
        target_name = _normalize_str(name)
        target_pass = _normalize_str(delete_pass)

        # 後ろから検索
        for i, record in reversed(list(enumerate(records))):
            row_num = i + 2
            sheet_name = _normalize_str(record.get('name', ''))
            sheet_pass = _normalize_str(record.get('delete_pass', ''))
            
            if sheet_name == target_name and sheet_pass == target_pass:
                image_url = record.get('image_url', '')
                _delete_image_by_url(image_url)
                
                sheet.delete_rows(row_num)
                deleted = True
                print(f"Deleted Row {row_num}")
                break
        
        return deleted
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
