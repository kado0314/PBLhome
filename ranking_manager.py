import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import cloudinary
import cloudinary.uploader
import base64

# スコープ設定 (スプレッドシート用)
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# スプレッドシートID (そのまま)
SPREADSHEET_KEY = "17QqxdjbY5OM8zGLPcrjn_-d1ZVCifvFH4dp9feOjfDk"

# ▼▼▼ Cloudinaryの設定 (ダッシュボードを見て書き換えてください) ▼▼▼
cloudinary.config(
  cloud_name = "dqluizsxn", 
  api_key = "733249596838179", 
  api_secret = "fJ1tto-eIbv19SBQBkI9r5rJb3Q",
  secure = True
)

def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
    client = gspread.authorize(creds)
    return client

def upload_image_to_cloudinary(image_data_base64):
    """Base64画像をCloudinaryにアップロードして表示用URLを返す"""
    try:
        # Base64ヘッダー(data:image/...)が付いている場合はそのまま渡せます
        # CloudinaryはBase64文字列を直接アップロード可能です
        
        # アップロード実行 (フォルダ分けしたい場合は folder="fashion_ranking" を追加)
        response = cloudinary.uploader.upload(
            image_data_base64, 
            folder="fashion_ranking",
            resource_type="image"
        )
        
        # 安全なHTTPSのURLを返す
        return response['secure_url']

    except Exception as e:
        print(f"Cloudinary Upload Error: {e}")
        return ""

def get_ranking():
    """ランキングトップ100を取得"""
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        records = sheet.get_all_records()
        
        valid_records = []
        for r in records:
            try:
                r['score'] = float(r['score'])
                if 'image_url' not in r:
                    r['image_url'] = ""
                valid_records.append(r)
            except:
                continue

        sorted_records = sorted(valid_records, key=lambda x: x['score'], reverse=True)
        return sorted_records[:100]
    except Exception as e:
        print(f"Ranking Fetch Error: {e}")
        return []

def add_ranking_entry(name, score, delete_pass, image_data_base64=None):
    """ランキングに登録"""
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        # ヘッダー作成
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["name", "score", "date", "delete_pass", "image_url"])
        
        # 既存ヘッダー対応
        header = sheet.row_values(1)
        if "image_url" not in header:
            sheet.update_cell(1, len(header) + 1, "image_url")

        # 画像アップロード処理 (Cloudinaryへ)
        image_url = ""
        if image_data_base64:
            image_url = upload_image_to_cloudinary(image_data_base64)

        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 行を追加
        sheet.append_row([name, score, date_str, delete_pass, image_url])
        return True
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False

def delete_ranking_entry(name, delete_pass):
    """削除処理"""
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        records = sheet.get_all_records()
        
        deleted = False
        target_name = str(name).strip()
        target_pass = str(delete_pass).strip()

        print(f"--- Delete Request: Name=[{target_name}], Pass=[{target_pass}] ---")

        for i, record in reversed(list(enumerate(records))):
            row_num = i + 2
            sheet_name = str(record.get('name', '')).strip()
            sheet_pass = str(record.get('delete_pass', '')).strip()
            
            if sheet_name == target_name and sheet_pass == target_pass:
                sheet.delete_rows(row_num)
                deleted = True
                print(f"!!! Deleted Row {row_num} !!!")
                break
        
        return deleted
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
def delete_ranking_entry(name, delete_pass):
    """名前とパスワードが一致したら、スプレッドシートと画像のデータを削除"""
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        records = sheet.get_all_records()
        
        deleted = False
        target_name = str(name).strip()
        target_pass = str(delete_pass).strip()

        print(f"--- Delete Request: Name=[{target_name}], Pass=[{target_pass}] ---")

        for i, record in reversed(list(enumerate(records))):
            row_num = i + 2
            sheet_name = str(record.get('name', '')).strip()
            sheet_pass = str(record.get('delete_pass', '')).strip()
            
            if sheet_name == target_name and sheet_pass == target_pass:
                # ▼▼▼ 追加: 画像削除処理 ▼▼▼
                image_url = record.get('image_url', '')
                if image_url:
                    try:
                        # URLからPublic ID (ファイルID) を抽出するロジック
                        # 例: https://.../upload/v1234/fashion_ranking/filename.jpg
                        # Cloudinaryで削除するには "fashion_ranking/filename" (拡張子なし) が必要
                        
                        # URLの最後のパーツ（filename.jpg）を取得
                        filename_with_ext = image_url.split('/')[-1]
                        # 拡張子 (.jpg) を除去
                        public_id_name = filename_with_ext.split('.')[0]
                        # フォルダ名を付与
                        full_public_id = f"fashion_ranking/{public_id_name}"
                        
                        # Cloudinaryから削除を実行
                        cloudinary.uploader.destroy(full_public_id)
                        print(f"Cloudinary Image Deleted: {full_public_id}")
                        
                    except Exception as img_err:
                        print(f"Cloudinary Delete Error (Ignored): {img_err}")

                # ▼▼▼ スプレッドシートの行削除 ▼▼▼
                sheet.delete_rows(row_num)
                deleted = True
                print(f"!!! Deleted Row {row_num} !!!")
                break
        
        return deleted
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
