import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import cloudinary
import cloudinary.uploader
import base64

# スコープ設定
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# スプレッドシートID
SPREADSHEET_KEY = "17QqxdjbY5OM8zGLPcrjn_-d1ZVCifvFH4dp9feOjfDk"

# ▼▼▼ Cloudinaryの設定 (ご自身のものが入っている前提) ▼▼▼
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
    """画像をCloudinaryにアップロード"""
    try:
        if ',' in image_data_base64:
            image_data_base64 = image_data_base64.split(',')[1]
            
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
    """URLからCloudinaryの画像を削除する内部関数"""
    if not image_url: return
    try:
        # URLからpublic_idを抽出
        # 例: https://.../upload/v1234/fashion_ranking/filename.jpg
        filename_with_ext = image_url.split('/')[-1]
        public_id_name = filename_with_ext.split('.')[0]
        full_public_id = f"fashion_ranking/{public_id_name}"
        
        cloudinary.uploader.destroy(full_public_id)
        print(f"Cloudinary Image Deleted: {full_public_id}")
    except Exception as e:
        print(f"Image Delete Error: {e}")

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
    """【復活】100位以下を削除するお掃除関数"""
    try:
        records = sheet.get_all_records()
        if len(records) <= 100:
            return # 100件以下なら何もしない

        # スコアで降順ソート（高い順）
        def get_score(r):
            try: return float(r['score'])
            except: return -1.0
            
        sorted_records = sorted(records, key=get_score, reverse=True)
        
        # 101位以降のデータを取得（削除対象）
        items_to_delete = sorted_records[100:]
        
        print(f"--- Pruning: Cleaning up {len(items_to_delete)} items ---")

        # 削除対象をループ
        for item in items_to_delete:
            name = item.get('name')
            delete_pass = item.get('delete_pass')
            
            # 既存の削除関数を再利用して消す（画像も消える）
            delete_ranking_entry(name, delete_pass, sheet)
            
    except Exception as e:
        print(f"Pruning Error: {e}")

def add_ranking_entry(name, score, delete_pass, image_data_base64=None):
    """ランキングに登録 ＆ 自動お掃除"""
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["name", "score", "date", "delete_pass", "image_url"])
        
        header = sheet.row_values(1)
        if "image_url" not in header:
            sheet.update_cell(1, len(header) + 1, "image_url")

        image_url = ""
        if image_data_base64:
            image_url = upload_image_to_cloudinary(image_data_base64)

        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # データを追加
        sheet.append_row([name, score, date_str, delete_pass, image_url])
        
        # ▼▼▼ 追加後、100件を超えていたら下位を削除 ▼▼▼
        prune_ranking(sheet)
        
        return True
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False

def delete_ranking_entry(name, delete_pass, sheet_obj=None):
    """名前とパスワードが一致したら削除（画像含む）"""
    try:
        # sheetオブジェクトが渡されていれば再利用、なければ新規取得
        if sheet_obj:
            sheet = sheet_obj
        else:
            client = get_client()
            sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
            
        records = sheet.get_all_records()
        
        deleted = False
        target_name = str(name).strip()
        target_pass = str(delete_pass).strip()

        # 後ろから検索して削除
        for i, record in reversed(list(enumerate(records))):
            row_num = i + 2
            sheet_name = str(record.get('name', '')).strip()
            sheet_pass = str(record.get('delete_pass', '')).strip()
            
            if sheet_name == target_name and sheet_pass == target_pass:
                # 画像削除（共通関数を使用）
                image_url = record.get('image_url', '')
                _delete_image_by_url(image_url)

                # 行削除
                sheet.delete_rows(row_num)
                deleted = True
                print(f"!!! Deleted Row {row_num} (Name: {target_name}) !!!")
                break
        
        return deleted
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
