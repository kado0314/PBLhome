import os
from flask import Flask, render_template, send_from_directory
from scoring import create_app as create_scoring_app
from scoring.routes import scoring_bp

app = Flask(__name__)

# ==========================================
# 1. 採点アプリ
# ==========================================
app.register_blueprint(scoring_bp, url_prefix='/scoring')

# ==========================================
# 2. ポータル画面 (トップページ)
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# 3. Privacyフォルダ
# ==========================================
@app.route('/Privacy/<path:filename>')
def serve_privacy(filename):
    return send_from_directory('Privacy', filename)

@app.route('/Privacy/')
def serve_privacy_index():
    return send_from_directory('Privacy', 'index.html')

# ==========================================
# 4. Typameraフォルダ
# ==========================================
@app.route('/Typamera/<path:filename>')
def serve_typamera(filename):
    return send_from_directory('Typamera', filename)

# ==========================================
# 起動設定
# ==========================================
if __name__ == '__main__':
    app.run(debug=True)
