import matplotlib
matplotlib.use('Agg') # サーバー上でGUIを使わない設定（必須）
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import io
import base64
import os
# ▼▼▼ ここでエラーが出ないよう、このファイルがあるか後で確認します ▼▼▼
from .rules_db import SCORE_WEIGHTS

# ダークテーマ設定
plt.style.use('dark_background')

def generate_radar_chart(aspect_scores):
    """
    ファッション採点結果をレーダーチャートとして描画
    """
    # --- フォント設定（サーバー上のKleeOneフォントを読み込む） ---
    try:
        # 現在のファイル(scoring/chart_generator.py)から見て ../fonts/KleeOne-Regular.ttf を探す
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, 'fonts', 'KleeOne-Regular.ttf')
        
        if os.path.exists(font_path):
            font_manager.fontManager.addfont(font_path)
            font_prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
        else:
            # フォントがない場合は英語フォントで逃げる（クラッシュ防止）
            plt.rcParams['font.family'] = 'sans-serif'
    except Exception as e:
        print(f"Font Warning: {e}")

    # --- データ準備 ---
    labels = []
    values = []
    
    label_map = {
        'color_harmony': '色の調和',
        'fit_and_silhouette': 'シルエット',
        'item_coordination': '組み合わせ',
        'cleanliness_material': '清潔感',
        'accessories_balance': '小物',
        'trendness': 'トレンド',
        'tpo_suitability': 'TPO',
        'photogenic_quality': '写真映え'
    }

    for key, score in aspect_scores.items():
        labels.append(label_map.get(key, key))
        # SCORE_WEIGHTSがない場合はデフォルト10点で計算（エラー防止）
        max_score = SCORE_WEIGHTS.get(key, 10.0)
        normalized_score = (score / max_score) * 20
        values.append(normalized_score)

    # 閉じた多角形にする
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    # --- 描画 ---
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')

    ax.plot(angles, values, color='#ec4899', linewidth=2, linestyle='solid')
    ax.fill(angles, values, color='#ec4899', alpha=0.3)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=11, color='white')
    
    ax.set_yticklabels([])
    ax.set_yticks([5, 10, 15, 20])
    ax.grid(color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
    ax.spines['polar'].set_color('gray')

    # 保存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{chart_base64}"
