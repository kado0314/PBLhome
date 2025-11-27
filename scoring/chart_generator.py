import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import io
import base64
import os
from .rules_db import SCORE_WEIGHTS

# ダークテーマ設定
plt.style.use('dark_background')

def generate_radar_chart(aspect_scores):
    """
    ファッション採点結果をレーダーチャートとして描画
    """
    # --- フォント設定 ---
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(base_dir, 'fonts', 'KleeOne-Regular.ttf')
        
        if os.path.exists(font_path):
            font_manager.fontManager.addfont(font_path)
            font_prop = font_manager.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_prop.get_name()
        else:
            plt.rcParams['font.family'] = 'sans-serif'
    except Exception as e:
        print(f"Font Warning: {e}")

    # --- データ準備 ---
    labels = []
    values = []     # グラフ描画用（0-20に正規化）
    raw_values = [] # テキスト表示用（素点）
    
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
        
        # 満点の設定を取得（デフォルト10）
        max_score = SCORE_WEIGHTS.get(key, 10.0)
        if max_score == 0: max_score = 10.0

        # ▼▼▼ 安全対策: AIが満点以上の数値を出したら満点に丸める ▼▼▼
        if score > max_score:
            score = max_score
        
        raw_values.append(score)

        # グラフ用に20点満点スケールに換算 (例: 15点満点で15点なら、グラフ上は20の位置)
        normalized_score = (score / max_score) * 20
        values.append(normalized_score)

    # 閉じた多角形にする
    values_closed = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    # --- 描画 ---
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')

    # プロット
    ax.plot(angles_closed, values_closed, color='#ec4899', linewidth=2, linestyle='solid')
    ax.fill(angles_closed, values_closed, color='#ec4899', alpha=0.3)

    # 軸の設定
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=11, color='white')
    
    # グリッド設定
    ax.set_yticklabels([])
    ax.set_yticks([5, 10, 15, 20])
    ax.set_ylim(0, 22) # 表示範囲を少し余裕を持たせる
    ax.grid(color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
    ax.spines['polar'].set_color('gray')

    # ▼▼▼ 点数表示の修正箇所 ▼▼▼
    for angle, val, raw_val in zip(angles, values, raw_values):
        # 修正: 距離を +3.0 から +1.2 に変更し、点のすぐそばに表示させる
        ax.text(angle, val + 1.2, f"{raw_val}", 
                color='white', ha='center', va='center', 
                fontsize=10, fontweight='bold')

    # 保存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{chart_base64}"
