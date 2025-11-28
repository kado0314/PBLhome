from datetime import datetime
import json
from typing import Dict, Any
import base64
from PIL import Image
import io
import os
import google.generativeai as genai

class FashionScorer:
    # ▼▼▼ 性別引数を削除 ▼▼▼
    def __init__(self, user_locale: str = "ja-JP"):
        self.user_locale = user_locale
        
        GENAI_API_KEY = os.environ.get('GOOGLE_API_KEY')
        if not GENAI_API_KEY:
            print("Warning: GOOGLE_API_KEY is not set.")
        else:
            genai.configure(api_key=GENAI_API_KEY)
        
        # モデル設定
        MODEL_NAME = "gemini-2.0-flash"
        generation_config = {
            "temperature": 1,
            "response_mime_type": "application/json",
        }
        
        self.model = None
        if GENAI_API_KEY:
            try:
                self.model = genai.GenerativeModel(
                    model_name=MODEL_NAME,
                    generation_config=generation_config,
                )
            except Exception as e:
                print(f"Model initialization error: {e}")

    def load_image(self, image_base64: str) -> bytes | None:
        try:
            img_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(img_bytes))
            img_io = io.BytesIO()
            image.save(img_io, format="PNG")
            return image
        except Exception:
            return None

    def analyze(self, image_base64: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        img = self.load_image(image_base64)
        if img is None:
            return {"error": "Invalid image data."}

        # ▼▼▼ 性別に関する処理を削除 ▼▼▼
        intended_scene = metadata.get("intended_scene", "friends")

        # ▼▼▼ プロンプトの強化（3つのポイントと数値を強制） ▼▼▼
        prompt = f"""
        あなたはプロのファッションスタイリストです。画像を分析し、JSON形式で採点してください。
        良い点と改善点は必ず入れてください。
        想定シーン: {intended_scene}

        【重要】必ず以下のJSON形式を守ってください。
        {{
            "total_score": (0-100の整数),
            "recommendation": "(一言コメント)",
            "feedback_points": [
                "(良い点・改善点1: 具体的に)",
                "(良い点・改善点2: 具体的に)",
                "(良い点・改善点3: 具体的に)"
            ],
            "details": {{
                "color_harmony": (1-20の整数),
                "fit_and_silhouette": (1-20の整数),
                "item_coordination": (1-15の整数),
                "cleanliness_material": (1-15の整数),
                "accessories_balance": (1-10の整数),
                "trendness": (1-10の整数),
                "tpo_suitability": (1-5の整数),
                "photogenic_quality": (1-5の整数)
            }}
        }}
        """

        try:
            response = self.model.generate_content([prompt, img])
            result = json.loads(response.text)

        except Exception as e:
            print(f"Gemini API Error: {e}")
            # エラー時のダミーデータ
            return {
                "overall_score": 0,
                "recommendation": "採点エラーが発生しました。",
                "subscores": {k: 0 for k in ["color_harmony", "fit_and_silhouette", "item_coordination", "cleanliness_material", "accessories_balance", "trendness", "tpo_suitability", "photogenic_quality"]},
                "explanations": ["エラーが発生しました。", "もう一度お試しください。", "画像の状態を確認してください。"]
            }

        output = {
            "overall_score": result.get("total_score", 0),
            "recommendation": result.get("recommendation", ""),
            "subscores": result.get("details", {}),
            "explanations": result.get("feedback_points", []),
            "metadata": {
                "user_locale": metadata.get("user_locale"),
                "intended_scene": intended_scene,
                "analysis_timestamp": datetime.now().isoformat(),
            }
        }

        return output
