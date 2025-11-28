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
    関数名はそのまま維持しますが、中身は「横棒グラフ（データバー）」を生成します。
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
    percentages = [] # グラフの長さ用（0-100%）
    text_labels = [] # 表示用テキスト（例: "18 / 20"）
    
    label_map = {
        'color_harmony': '色の調和',
        'fit_and_silhouette': 'シルエット',
        'item_coordination': '組み合わせ',
        'cleanliness_material': '清潔感',
        'accessories_balance': '小物・アクセ',
        'trendness': 'トレンド',
        'tpo_suitability': 'TPO',
        'photogenic_quality': '写真映え'
    }

    # 辞書の順序を維持したいので、label_mapのキー順で回す
    for key, label_text in label_map.items():
        score = aspect_scores.get(key, 0)
        
        # 満点を取得
        max_score = SCORE_WEIGHTS.get(key, 10.0)
        if max_score == 0: max_score = 10.0
        
        # キャップ処理
        if score > max_score: score = max_score

        # グラフの長さ用に100%換算
        pct = (score / max_score) * 100
        
        labels.append(label_text)
        percentages.append(pct)
        text_labels.append(f"{int(score)}/{int(max_score)}")

    # 表示順を逆にする（グラフは下から描画されるため、リストを反転させて上から表示させる）
    labels = labels[::-1]
    percentages = percentages[::-1]
    text_labels = text_labels[::-1]

    # --- 描画 ---
    # 横長の比率に設定
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')

    # Y軸の位置（項目数分）
    y_pos = range(len(labels))

    # 1. 背景のバー（薄いグレーで満点=100%の長さを描画）
    ax.barh(y_pos, [100]*len(y_pos), height=0.6, align='center', 
            color='gray', alpha=0.2, edgecolor='none')

    # 2. スコアのバー（ピンクで実際のスコアを描画）
    # 角を少し丸く見せるためにlinewidthを太くしたりもできますが、シンプルに描画
    bars = ax.barh(y_pos, percentages, height=0.6, align='center', 
                   color='#ec4899', edgecolor='none', alpha=0.9)

    # 3. テキスト表示（バーの右端に「18/20」のような数字を表示）
    for i, (pct, text) in enumerate(zip(percentages, text_labels)):
        # バーの少し右側に配置
        ax.text(102, i, text, va='center', ha='left', 
                color='white', fontsize=11, fontweight='bold')

    # --- 見た目の調整 ---
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11, color='white')
    
    # 不要な枠線や目盛りを消す
    ax.set_xlim(0, 115) # テキストが入るように右側を空ける
    ax.set_xticks([])   # 下の目盛り（0, 20, 40...）を消す
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # 軸のティック（ヒゲ）を消す
    ax.tick_params(axis='y', length=0)

    # 保存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{chart_base64}"
