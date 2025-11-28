import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime
import os
import io
import base64

# スコープ設定
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# ▼▼▼ あなたのスプレッドシートID ▼▼▼
SPREADSHEET_KEY = "17QqxdjbY5OM8zGLPcrjn_-d1ZVCifvFH4dp9feOjfDk"

# ▼▼▼ 作成していただいたフォルダIDを設定しました ▼▼▼
DRIVE_FOLDER_ID = "1vEwJH5G1FyDpO8W2PsdRjkV45MAD6e-G"

def get_creds():
    return ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)

def get_client():
    creds = get_creds()
    client = gspread.authorize(creds)
    return client

def get_drive_service():
    creds = get_creds()
    service = build('drive', 'v3', credentials=creds)
    return service

def upload_image_to_drive(image_data_base64, filename):
    """Base64画像をGoogleドライブにアップロードして表示用URLを返す"""
    try:
        service = get_drive_service()
        
        # Base64ヘッダーの除去とデコード
        if ',' in image_data_base64:
            image_data_base64 = image_data_base64.split(',')[1]
            
        image_data = base64.b64decode(image_data_base64)
        fh = io.BytesIO(image_data)
        
        file_metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaIoBaseUpload(fh, mimetype='image/jpeg', resumable=True)
        
        # アップロード実行
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')
        
        # 公開設定にする（全員が閲覧可能）
        permission = {'type': 'anyone', 'role': 'reader'}
        service.permissions().create(fileId=file_id, body=permission).execute()

        # サムネイルリンクを取得してサイズを大きくするハック
        file_info = service.files().get(fileId=file_id, fields='thumbnailLink').execute()
        thumbnail_link = file_info.get('thumbnailLink')
        
        if thumbnail_link:
            # 末尾の=s220などを=s600に変更して大きめの画像を取得
            return thumbnail_link.rsplit('=', 1)[0] + '=s600'
        return ""

    except Exception as e:
        print(f"Image Upload Error: {e}")
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
    """ランキングに登録（画像対応）"""
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        # ヘッダー確認・作成
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["name", "score", "date", "delete_pass", "image_url"])
        
        # 既存シートにimage_url列がない場合の対応
        header = sheet.row_values(1)
        if "image_url" not in header:
            sheet.update_cell(1, len(header) + 1, "image_url")

        # 画像アップロード処理
        image_url = ""
        if image_data_base64:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # ファイル名に名前を含めてユニークにする
            filename = f"ranking_{timestamp}_{name}.jpg"
            image_url = upload_image_to_drive(image_data_base64, filename)

        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 行を追加
        sheet.append_row([name, score, date_str, delete_pass, image_url])
        return True
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False

def delete_ranking_entry(name, delete_pass):
    """削除処理（厳密比較版）"""
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
