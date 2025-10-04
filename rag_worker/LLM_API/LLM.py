import openai
import sys, os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수를 찾을 수 없습니다. .env 파일을 확인하세요.")

client = openai.OpenAI(api_key=api_key)

def ask_question(prompt: str) -> str:
    """
    주어진 프롬프트를 GPT 모델에게 보내고 답변을 받아오는 가장 기본적인 함수.
    """
    # 모델 설정
    fixed_model = "gpt-3.5-turbo"
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",   "content": prompt}
    ]

    print(f"--- {fixed_model} 모델에게 질문 전송 ---")
    
    # OpenAI API 호출 (스트리밍 없이)
    # try:
    #     resp = client.chat.completions.create(
    #         model=fixed_model,
    #         messages=messages,
    #         temperature=0.1,
    #         max_tokens=1024
    #     )
        
    #     response_content = resp.choices[0].message.content
    #     return response_content

    # except Exception as e:
    #     print(f"❌ OpenAI API 호출 중 오류 발생: {e}")
    #     return "답변을 받아오는 데 실패했습니다."

    return "test"


# # 지원하는 모델 목록 (GPT-3.5와 유사한 성능의 모델들)
# MODELS = [
#     "gpt-3.5-turbo",
#     "gpt-3.5-turbo-1106", 
#     "gpt-3.5-turbo-0125",
#     "gpt-4o-mini"
# ]

# current_model_index = 0

# def get_next_model():
#     """교차적으로 다음 모델을 반환"""
#     global current_model_index
#     model = MODELS[current_model_index]
#     current_model_index = (current_model_index + 1) % len(MODELS)
#     return model

# def ask_question(prompt: str, use_stream: bool = False, model: str = None):
#     messages = [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user",   "content": prompt}
#     ]

#     # 모델이 지정되지 않으면 다음 모델을 교차적으로 선택
#     if model is None:
#         model = get_next_model()

#     # 반환값을 하나(resp)로만 받는다
#     resp = client.chat.completions.create(
#         model=model,
#         messages=messages,
#         stream=use_stream,
#         temperature=0.1,
#         max_tokens=500
#     )

#     if use_stream:
#         # 스트리밍 모드: resp는 iterator of chunks
#         response_content = ""
#         for chunk in resp:
#             delta = chunk.choices[0].delta.content
#             if delta:
#                 response_content += delta
#         return {"model": model, "response": response_content}
#     else:
#         # 논스트리밍 모드: resp.choices에서 메시지 내용 추출
#         full_content = "".join(
#             choice.message.content or ""
#             for choice in resp.choices
#         )
#         return {"model": model, "response": full_content}

# def get_models_info():
#     """현재 사용 가능한 모델 정보를 반환"""
#     models_info = []
#     for i, model in enumerate(MODELS):
#         models_info.append({
#             "index": i + 1,
#             "name": model,
#             "is_current": i == current_model_index
#         })
#     return models_info



# def set_model(model_number: int):
#     """특정 모델을 선택"""
#     global current_model_index
#     if 1 <= model_number <= len(MODELS):
#         current_model_index = model_number - 1
#         return {"success": True, "message": f"모델 변경: {MODELS[current_model_index]}"}
#     else:
#         return {"success": False, "message": f"잘못된 모델 번호입니다. 1~{len(MODELS)} 사이의 숫자를 입력하세요."}
