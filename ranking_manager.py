import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

# スコープ設定
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# ▼▼▼ あなたのスプレッドシートID ▼▼▼
SPREADSHEET_KEY = "17QqxdjbY5OM8zGLPcrjn_-d1ZVCifvFH4dp9feOjfDk"

def get_client():
    # credentials.jsonを探して認証
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
    client = gspread.authorize(creds)
    return client

def get_ranking():
    """ランキングトップ100を取得"""
    try:
        client = get_client()
        # ▼▼▼ IDで指定して開く ▼▼▼
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        records = sheet.get_all_records()
        
        valid_records = []
        for r in records:
            try:
                r['score'] = float(r['score'])
                valid_records.append(r)
            except:
                continue

        sorted_records = sorted(valid_records, key=lambda x: x['score'], reverse=True)
        return sorted_records[:100]
    except Exception as e:
        print(f"Ranking Fetch Error: {e}")
        return []

def add_ranking_entry(name, score, delete_pass):
    """ランキングに登録"""
    try:
        client = get_client()
        # ▼▼▼ IDで指定して開く ▼▼▼
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["name", "score", "date", "delete_pass"])

        date_str = datetime.now().strftime("%Y-%m-%d")
        sheet.append_row([name, score, date_str, delete_pass])
        return True
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False

def delete_ranking_entry(name, delete_pass):
    """名前とパスワードが一致したら削除"""
    try:
        client = get_client()
        # ▼▼▼ IDで指定して開く ▼▼▼
        sheet = client.open_by_key(SPREADSHEET_KEY).sheet1
        records = sheet.get_all_records()
        
        deleted = False
        for i, record in reversed(list(enumerate(records))):
            row_num = i + 2
            if str(record['name']) == str(name) and str(record['delete_pass']) == str(delete_pass):
                sheet.delete_rows(row_num)
                deleted = True
                break
                
        return deleted
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
