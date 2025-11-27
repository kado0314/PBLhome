from datetime import datetime
import json
from typing import Dict, Any
import base64
from PIL import Image
import io
import os
import google.generativeai as genai

class FashionScorer:
    def __init__(self, user_gender: str = "neutral", user_locale: str = "ja-JP"):
        self.user_gender = user_gender
        self.user_locale = user_locale
        
        GENAI_API_KEY = os.environ.get('GOOGLE_API_KEY')
        if not GENAI_API_KEY:
            print("Warning: GOOGLE_API_KEY is not set.")
        else:
            genai.configure(api_key=GENAI_API_KEY)
        # ★ここで最新モデルを指定します
        MODEL_NAME = "gemini-2.0-flash"
        generation_config = {
            "temperature": 1,
            "response_mime_type": "application/json",
        }
        # 安全のためAPIキーがある場合のみモデル初期化
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
        """Base64文字列からPNGファイルに変換して返す"""
        try:
            img_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(img_bytes))

            # 強制 PNG 変換
            img_io = io.BytesIO()
            image.save(img_io, format="PNG")
            return image
        except Exception:
            return None

    def analyze(self, image_base64: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        # 1. 画像をPNGとしてロード
        img = self.load_image(image_base64)
        if img is None:
            return {"error": "Invalid image data."}

        user_gender = metadata.get("user_gender", self.user_gender)
        intended_scene = metadata.get("intended_scene", "friends")

        # 2. プロンプト作成（先に定義する）
        prompt = f"""
        あなたはプロのファッションスタイリストです。以下の画像を分析し、採点してください。
        ユーザー属性: {user_gender}, 想定シーン: {intended_scene}

        以下のJSON形式のみで出力:
        {{
            "total_score": (0-100の整数),
            "recommendation": "(一言コメント)",
            "feedback_points": ["(良い点・改善点1)", "(良い点・改善点2)", "(良い点・改善点3)"],
            "details": {{
                "color_harmony": (1-20), "fit_and_silhouette": (1-20),
                "item_coordination": (1-15), "cleanliness_material": (1-15),
                "accessories_balance": (1-10), "trendness": (1-10),
                "tpo_suitability": (1-5), "photogenic_quality": (1-5)
            }}
        }}
        """

        # 3. Gemini 推論（正しい image 引数を使用）
        try:
            response = self.model.generate_content([prompt, img])
            result = json.loads(response.text)

        except Exception as e:
            return {"error": f"Gemini API error: {e}"}

        # 4. 結果を上位形式に整形
        output = {
            "overall_score": result.get("total_score", 0),
            "recommendation": result.get("recommendation", ""),
            "subscores": result.get("details", {}),
            "explanations": result.get("feedback_points", []),
            "warnings": [],
            "metadata": {
                "user_locale": metadata.get("user_locale"),
                "intended_scene": intended_scene,
                "analysis_timestamp": datetime.now().isoformat(),
                "model_version": "gemini"
            }
        }

        return output


