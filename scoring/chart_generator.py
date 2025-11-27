import matplotlib
matplotlib.use('Agg')  # GUIバックエンドを使わない設定
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import japanize_matplotlib
from .rules_db import SCORING_CRITERIA

# ▼▼▼ Matplotlibのスタイルをダークテーマに設定 ▼▼▼
plt.style.use('dark_background')

def generate_radar_chart(scores):
    """
    スコアの辞書を受け取り、ダークテーマのレーダーチャート画像をBase64文字列で返す。
    """
    # 1. データの準備（既存と同じ）
    labels = []
    values = []
    max_scores = []

    for key, criteria in SCORING_CRITERIA.items():
        labels.append(criteria["label"])
        values.append(scores.get(key, 0))
        max_scores.append(criteria["max_score"])

    # 閉じた多角形にするためにデータを一周させる
    values_closed = values + [values[0]]
    max_scores_closed = max_scores + [max_scores[0]]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]

    # 2. グラフの描画設定
    # ▼▼▼ 背景色を透明に設定（図全体とプロットエリア） ▼▼▼
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('none') # 図全体の背景を透明に
    ax.set_facecolor('none')        # プロットエリアの背景を透明に

    # 3. データのプロット
    # ▼▼▼ 線と塗りつぶしの色をネオンピンクに変更 ▼▼▼
    line_color = '#ec4899'  # Tailwindのpink-500
    fill_color = '#ec4899'
    
    # 実際のスコアのプロット
    ax.plot(angles_closed, values_closed, color=line_color, linewidth=2, linestyle='solid', label='スコア')
    ax.fill(angles_closed, values_closed, color=fill_color, alpha=0.4)

    # 満点の基準線（参考）
    # ▼▼▼ 基準線の色を薄いグレーに変更 ▼▼▼
    ax.plot(angles_closed, max_scores_closed, color='gray', linewidth=1, linestyle='--', label='満点基準', alpha=0.5)

    # 4. スタイルの調整（ダークテーマ向け）
    # ▼▼▼ グリッド線、目盛り、ラベルの色を調整 ▼▼▼
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=10, color='white') # ラベルを白に

    # Y軸（中心からの距離）の設定
    # 各軸で最大値が違うため、目盛りは表示せず、相対的なスケール感だけ示す
    ax.set_yticklabels([]) 
    ax.set_yticks(np.linspace(0, max(max_scores), 5)) # グリッドの間隔だけ設定
    
    # グリッド線の色設定
    ax.grid(color='gray', linestyle=':', linewidth=0.8, alpha=0.7)
    
    # 外枠の色設定
    ax.spines['polar'].set_color('gray')

    # タイトル設定（オプション、今回はHTML側で表示しているので不要ならコメントアウト）
    # plt.title('ファッション採点レーダーチャート', size=14, color='white', pad=20)

    # 凡例の表示（位置と色を調整）
    # ▼▼▼ 凡例の背景と文字色を調整 ▼▼▼
    legend = ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1), frameon=True, facecolor='#1f2937', edgecolor='gray')
    for text in legend.get_texts():
        text.set_color('white')

    # 5. 画像をメモリ上に保存してBase64変換
    buf = io.BytesIO()
    # ▼▼▼ 保存時にも背景を透明に指定 ▼▼▼
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    plt.close()

    return f"data:image/png;base64,{image_base64}"
