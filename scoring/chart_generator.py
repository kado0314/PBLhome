import matplotlib
matplotlib.use('Agg') # サーバー用設定
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
    ファッション採点結果をレーダーチャートとして描画（点数表示付き）
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
    values = []     # グラフ描画用（正規化された値）
    raw_values = [] # テキスト表示用（実際の素点）
    
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
        
        # 素点を保存
        raw_values.append(score)

        # グラフ用に20点満点スケールに正規化
        max_score = SCORE_WEIGHTS.get(key, 10.0)
        if max_score == 0: max_score = 10.0 # ゼロ除算防止
        normalized_score = (score / max_score) * 20
        values.append(normalized_score)

    # 閉じた多角形にする（描画用データのみ）
    values_closed = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    # --- 描画 ---
    # 図全体の設定
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('none') # 背景透明
    ax.set_facecolor('none')        # グラフ内背景透明

    # プロット（線と塗りつぶし）
    ax.plot(angles_closed, values_closed, color='#ec4899', linewidth=2, linestyle='solid')
    ax.fill(angles_closed, values_closed, color='#ec4899', alpha=0.3)

    # 軸の設定
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=11, color='white')
    
    # Y軸（グリッド）の設定
    ax.set_yticklabels([]) # 目盛り数値は消す
    ax.set_yticks([5, 10, 15, 20])
    ax.set_ylim(0, 23) # 点数表示のために少し余白を広げる
    ax.grid(color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
    ax.spines['polar'].set_color('gray')

    # ▼▼▼ 点数の表示（ここを追加） ▼▼▼
    # 実際の点数(raw_values)を表示し、位置は正規化された値(values)に基づく
    for angle, val, raw_val in zip(angles, values, raw_values):
        # val + 2.5 の位置に表示（ドットの少し外側）
        ax.text(angle, val + 3.0, f"{raw_val}", 
                color='white', ha='center', va='center', 
                fontsize=10, fontweight='bold')

    # 保存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{chart_base64}"
