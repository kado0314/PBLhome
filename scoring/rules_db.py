# rules_db.py

# 評価軸のウェイト（合計100点）
SCORE_WEIGHTS = {
    "color_harmony": 20.0,
    "fit_and_silhouette": 20.0,
    "item_coordination": 15.0,
    "cleanliness_material": 15.0,
    "accessories_balance": 10.0,
    "trendness": 10.0,
    "tpo_suitability": 5.0,
    "photogenic_quality": 5.0
}

# 評価バイアスの調整例（fit_and_silhouetteで利用）
BIAS_ADJUSTMENTS = {
    "male": {
        "focus_items": ["jacket", "shirt", "slacks"], 
        "silhouette_std_range": (0.2, 0.3) # 簡易的な標準プロポーション
    },
    "female": {
        "focus_items": ["skirt", "onepiece", "heels"], 
        "silhouette_std_range": (0.15, 0.25)
    },
    "neutral": {
        "focus_items": [],
        "silhouette_std_range": (0.2, 0.35)
    }
}

# TPO適合性ルール（非常に簡易的）
TPO_RULES = {
    "date": {"forbidden_patterns": ["camouflage", "excessive_logos"], "min_cleanliness": 0.6},
    "work": {"forbidden_patterns": ["neon_colors", "shorts"], "min_cleanliness": 0.8},
    
    # ▼▼▼ 修正: 「友達と遊ぶ」シーンを追加 ▼▼▼
    "friends": {"forbidden_patterns": [], "min_cleanliness": 0.5} # 特に禁止事項なし、清潔感の基準も少し緩め
    # ▲▲▲ 修正 ▲▲▲
}

