import os
from flask import Flask, render_template, send_from_directory
# scoringフォルダの機能を取り込み
from scoring import create_app as create_scoring_app
from scoring.routes import scoring_bp

app = Flask(__name__)

# ---------------------------------------------------------
# 1. AI採点アプリ (Blueprint登録)
# ---------------------------------------------------------
# URL: /scoring/saiten などでアクセス
app.register_blueprint(scoring_bp, url_prefix='/scoring')

# ---------------------------------------------------------
# 2. ポータル画面 (トップページ)
# ---------------------------------------------------------
# URL: /
@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------------------------------------
# 3. Privacyフォルダ (静的ファイル配信)
# ---------------------------------------------------------
# URL: /Privacy/index.html など
@app.route('/Privacy/<path:filename>')
def serve_privacy(filename):
    return send_from_directory('Privacy', filename)

# ---------------------------------------------------------
# 4. Typameraフォルダ (静的ファイル配信)
# ---------------------------------------------------------
# URL: /Typamera/templates/typing.html など
@app.route('/Typamera/<path:filename>')
def serve_typamera(filename):
    return send_from_directory('Typamera', filename)

if __name__ == '__main__':
    app.run(debug=True)
