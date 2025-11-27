import base64
from flask import Blueprint, render_template, request, url_for
from .scorer_main import FashionScorer
from .chart_generator import generate_radar_chart

scoring_bp = Blueprint(
    "scoring", 
    __name__, 
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

@scoring_bp.route("/", methods=["GET"])
def index():
    # ▼▼▼ 性別初期値を削除 ▼▼▼
    return render_template("saiten.html", uploaded_image_data=False, selected_scene="date", score=None)

@scoring_bp.route("/saiten", methods=["GET", "POST"])
def saiten():
    if request.method == "GET":
        return render_template(
            "saiten.html",
            uploaded_image_data=False,
            selected_scene="date",
            score=None
        )
        
    image_file = request.files.get("image_file")
    # ▼▼▼ 性別取得を削除 ▼▼▼
    intended_scene = request.form.get("intended_scene", "date")

    if not image_file:
        return render_template(
            "saiten.html", 
            score=None, 
            feedback=["画像がアップロードされていません。"],
            selected_scene=intended_scene
        )

    image_data = base64.b64encode(image_file.read()).decode("utf-8")
    
    # ▼▼▼ 性別引数を削除して初期化 ▼▼▼
    scorer = FashionScorer()
    metadata = {
        "user_locale": "ja-JP", 
        "intended_scene": intended_scene
    }
    result = scorer.analyze(image_data, metadata)

    # グラフ用データの安全な取得
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
        selected_scene=intended_scene
    )
