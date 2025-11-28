import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

# スコープ設定
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

def get_client():
    # Render環境変数から読み込むか、ローカルのファイルから読み込むか
    # 本番では環境変数 'GOOGLE_CREDENTIALS_JSON' にJSONの中身を丸ごと入れるのが安全ですが
    # ここでは簡易的にファイル読み込みで書きます
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
    client = gspread.authorize(creds)
    return client

def get_ranking():
    """ランキングトップ100を取得"""
    try:
        client = get_client()
        sheet = client.open("FashionRanking").sheet1
        # 全データ取得
        records = sheet.get_all_records()
        
        # 点数(score)で降順ソート
        sorted_records = sorted(records, key=lambda x: x['score'], reverse=True)
        
        # トップ100だけ返す
        return sorted_records[:100]
    except Exception as e:
        print(f"Ranking Error: {e}")
        return []

def add_ranking_entry(name, score, delete_pass):
    """ランキングに登録"""
    try:
        client = get_client()
        sheet = client.open("FashionRanking").sheet1
        
        # ヘッダーが無い場合は作成
        if sheet.row_count == 0 or sheet.cell(1,1).value == "":
            sheet.append_row(["name", "score", "date", "delete_pass"])

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 行を追加
        sheet.append_row([name, score, date_str, delete_pass])
        return True
    except Exception as e:
        print(f"Add Ranking Error: {e}")
        return False

def delete_ranking_entry(name, delete_pass):
    """名前とパスワードが一致したら削除"""
    try:
        client = get_client()
        sheet = client.open("FashionRanking").sheet1
        records = sheet.get_all_records()
        
        # 削除対象の行を探す（後ろから探すと行ズレが起きにくい）
        # get_all_recordsはヘッダー分(1行)を除いたリストなので、
        # 行番号は index + 2 になる (1始まり + ヘッダー分)
        
        for i, record in enumerate(records):
            # 文字列として比較
            if str(record['name']) == str(name) and str(record['delete_pass']) == str(delete_pass):
                sheet.delete_rows(i + 2)
                return True
        return False
    except Exception as e:
        print(f"Delete Error: {e}")
        return False
