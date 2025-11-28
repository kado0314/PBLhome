import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import io
import base64
import os
from .rules_db import SCORE_WEIGHTS

# ダークテーマ設定
plt.style.use('dark_background')

def generate_radar_chart(aspect_scores):
    """
    横棒グラフ（データバー）の極太文字バージョン
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
    percentages = []
    text_labels = []
    
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

    for key, label_text in label_map.items():
        score = aspect_scores.get(key, 0)
        max_score = SCORE_WEIGHTS.get(key, 10.0)
        if max_score == 0: max_score = 10.0
        if score > max_score: score = max_score

        pct = (score / max_score) * 100
        labels.append(label_text)
        percentages.append(pct)
        text_labels.append(f"{int(score)}/{int(max_score)}")

    labels = labels[::-1]
    percentages = percentages[::-1]
    text_labels = text_labels[::-1]

    # --- 描画 ---
    # ▼▼▼ サイズ設定 (少し横長に) ▼▼▼
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')

    y_pos = range(len(labels))

    # 背景バー
    ax.barh(y_pos, [100]*len(y_pos), height=0.6, align='center', 
            color='gray', alpha=0.2, edgecolor='none')

    # スコアバー
    ax.barh(y_pos, percentages, height=0.6, align='center', 
            color='#ec4899', edgecolor='none', alpha=0.9)

    # テキスト表示
    for i, (pct, text) in enumerate(zip(percentages, text_labels)):
        # ▼▼▼ 文字サイズを 18 (極太) に変更 ▼▼▼
        ax.text(102, i, text, va='center', ha='left', 
                color='white', fontsize=18, fontweight='bold')

    # --- 調整 ---
    ax.set_yticks(y_pos)
    # ▼▼▼ 項目名も 18 に変更 ▼▼▼
    ax.set_yticklabels(labels, fontsize=18, color='white')
    
    ax.set_xlim(0, 125) 
    ax.set_xticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)

    # 保存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{chart_base64}"
