import google.generativeai as genai
from config import Config

# Gemini API 설정
genai.configure(api_key=Config.GEMINI_API_KEY)

class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def generate_copy(self, prompt: str) -> str:
        """
        Gemini API를 사용해 마케팅 문구 생성
        """
        try:
            print("=" * 80)
            print("LLM 문구 생성")
            print("=" * 80)
            print(prompt)
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ LLM 호출 오류: {e}")
            return ""
    
    def analyze_trends(self, trend_data: list) -> dict:
        """
        트렌드 데이터 분석 및 키워드 추출
        """
        prompt = f"""
다음은 최근 수집된 트렌드 데이터입니다:
{trend_data}

이 데이터를 분석해서:
1. 주요 키워드 5개 추출
2. 각 키워드의 중요도 점수 (1-10)
3. 트렌드 카테고리 분류

JSON 형식으로 응답해주세요.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ 트렌드 분석 오류: {e}")
            return {}

