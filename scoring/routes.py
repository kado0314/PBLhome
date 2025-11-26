import base64
from flask import Blueprint, render_template, request, url_for
from .scorer_main import FashionScorer
from .chart_generator import generate_radar_chart

# ▼▼▼ 修正: static_folder と static_url_path を指定 ▼▼▼
scoring_bp = Blueprint(
    "scoring", 
    __name__, 
    template_folder="templates",
    static_folder="static",      # scoringフォルダ内のstaticを参照
    static_url_path="/static"    # URL上での見え方
)

@scoring_bp.route("/", methods=["GET"])
def index():
    # ... (中略) ... (既存のコードと同じ)
    return render_template("saiten.html", uploaded_image_data=False, selected_gender="neutral", selected_scene="date", score=None)

@scoring_bp.route("/saiten", methods=["GET", "POST"])
def saiten():
    # ... (中略) ... (既存のコードと同じ)
    # ※変更なしですが、context全体は維持してください
    if request.method == "GET":
        return render_template(
            "saiten.html",
            uploaded_image_data=False,
            selected_gender="neutral",
            selected_scene="date",
            score=None
        )
        
    image_file = request.files.get("image_file")
    user_gender = request.form.get("user_gender", "neutral")
    intended_scene = request.form.get("intended_scene", "date")

    if not image_file:
        return render_template(
            "saiten.html", 
            score=None, 
            feedback=["画像がアップロードされていません。"],
            selected_gender=user_gender,
            selected_scene=intended_scene
        )

    image_data = base64.b64encode(image_file.read()).decode("utf-8")
    
    scorer = FashionScorer(user_gender=user_gender)
    metadata = {
        "user_locale": "ja-JP", 
        "intended_scene": intended_scene,
        "user_gender": user_gender
    }
    result = scorer.analyze(image_data, metadata)

    aspect_scores = result.get("subscores", None)
    if not aspect_scores:
        aspect_scores = {
            "color_harmony": 0, "fit_and_silhouette": 0, "item_coordination": 0,
            "cleanliness_material": 0, "accessories_balance": 0, "trendness": 0,
            "tpo_suitability": 0, "photogenic_quality": 0
        }

    radar_chart_data = generate_radar_chart(aspect_scores)

    return render_template(
        "saiten.html",
        uploaded_image_data=f"data:image/png;base64,{image_data}",
        score=result.get("overall_score", "N/A"),
        recommendation=result.get("recommendation", ""),
        feedback=result.get("explanations", ["詳細な説明はありません。"]),
        radar_chart_data=radar_chart_data,
        selected_gender=user_gender,
        selected_scene=intended_scene
    )
