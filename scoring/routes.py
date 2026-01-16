import base64
from flask import Blueprint, render_template, request, jsonify
from .scorer_main import FashionScorer
from .chart_generator import generate_radar_chart
import sys
import os
from ranking_manager import get_ranking, add_ranking_entry, delete_ranking_entry

scoring_bp = Blueprint(
    "scoring", 
    __name__, 
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

@scoring_bp.route("/", methods=["GET"])
def index():
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
    intended_scene = request.form.get("intended_scene", "date")

    if not image_file:
        return render_template(
            "saiten.html", 
            score=None, 
            feedback=["画像がアップロードされていません。"],
            selected_scene=intended_scene
        )

    image_data = base64.b64encode(image_file.read()).decode("utf-8")
    
    scorer = FashionScorer()
    metadata = {
        "user_locale": "ja-JP", 
        "intended_scene": intended_scene
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
    
    user_score = result.get("overall_score", 0)

    # ▼▼▼ ランクイン判定ロジック ▼▼▼
    ranking = get_ranking()
    rank_in = False
    
    if len(ranking) < 10:
        rank_in = True
    else:
        # 10位（リストの最後）のスコアより高ければランクイン
        lowest_score = ranking[-1]['score']
        if user_score >= lowest_score:
            rank_in = True

    return render_template(
        "saiten.html",
        uploaded_image_data=f"data:image/png;base64,{image_data}",
        score=user_score,
        recommendation=result.get("recommendation", ""),
        feedback=result.get("explanations", ["詳細な説明はありません。"]),
        radar_chart_data=radar_chart_data,
        selected_scene=intended_scene,
        rank_in=rank_in  # ▼ これをHTMLに渡す
    )

# ▼▼▼ ランキング用API ▼▼▼

@scoring_bp.route("/api/ranking", methods=["GET"])
def api_get_ranking():
    data = get_ranking()
    return jsonify(data)

@scoring_bp.route("/api/ranking", methods=["POST"])
def api_add_ranking():
    data = request.json
    name = data.get("name")
    score = data.get("score")
    delete_pass = data.get("delete_pass")
    # 画像データを受け取る
    image_data = data.get("image_data")
    
    if not name or score is None:
        return jsonify({"success": False, "message": "データが不足しています"}), 400
        
    # 戻り値 (success, message) を受け取る
    success, msg = add_ranking_entry(name, float(score), delete_pass, image_data)
    
    if success:
        return jsonify({"success": True, "message": msg})
    else:
        return jsonify({"success": False, "message": msg}), 400

@scoring_bp.route("/api/ranking/delete", methods=["POST"])
def api_delete_ranking():
    data = request.json
    name = data.get("name")
    delete_pass = data.get("delete_pass")
    
    if not name or not delete_pass:
        return jsonify({"success": False, "message": "情報が不足しています"}), 400

    success = delete_ranking_entry(name, delete_pass)
    if success:
        return jsonify({"success": True, "message": "削除しました"})
    else:
        return jsonify({"success": False, "message": "削除できませんでした（パスワード不一致など）"}), 400
