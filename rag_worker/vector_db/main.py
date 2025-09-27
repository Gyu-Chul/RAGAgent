import json
import os
import db_utils
import config
from chains import embedding_chain, search_chain, EmbeddingInput, SearchInput, format_docs

def create_test_data_file():
    """임베딩 테스트를 위한 샘플 JSON 파일을 생성합니다."""
    if not os.path.exists(config.TEST_DATA_PATH) or os.path.getsize(config.TEST_DATA_PATH) == 0:
        print(f"'{config.TEST_DATA_PATH}' 파일이 없거나 비어있어 새로 생성합니다.")
        sample_data = [
            {"type": "function", "name": "calculate_sum", "code": "def calculate_sum(a, b): return a + b"},
            {"type": "class", "name": "MyCalculator", "code": "class MyCalculator: def add(self, a, b): return a + b"},
            {"type": "function", "name": "calculate_product", "code": "def calculate_product(a, b): return a * b"}
        ]
        with open(config.TEST_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(sample_data, f, indent=2)

def main_menu():
    """메인 메뉴를 표시하고 사용자 입력을 받아 해당 기능을 실행합니다."""
    
    create_test_data_file() # 테스트 파일 준비

    while True:
        print("\n===== Milvus LangChain CLI =====")
        print("1. 컬렉션 생성")
        print("2. 컬렉션 목록 보기")
        print("3. 컬렉션 삭제")
        print("4. 문서 임베딩 (LangChain)")
        print("5. 벡터 검색 (LangChain)")
        print("0. 종료")
        print("================================")
        
        choice = input("원하는 작업의 번호를 입력하세요: ")

        if choice == '1':
            print("사용 가능한 모델 키:", ", ".join(config.EMBEDDING_MODELS.keys()))
            model_key = input(f"사용할 모델 키를 입력하세요 (기본값: {config.DEFAULT_MODEL_KEY}): ") or config.DEFAULT_MODEL_KEY
            
            model_conf = config.EMBEDDING_MODELS.get(model_key)
            if not model_conf:
                print("❌ 잘못된 모델 키입니다.")
                continue

            collection_name = input(f"생성할 컬렉션 이름 (기본값: {model_key}_collection): ") or f"{model_key}_collection"
            
            # 선택된 모델의 dim 값을 직접 전달
            db_utils.create_milvus_collection(collection_name, dim=model_conf["dim"])
        
        elif choice == '2':
            db_utils.list_milvus_collections()

        elif choice == '3':
            name = input("삭제할 컬렉션 이름을 입력하세요: ")
            if name:
                db_utils.delete_milvus_collection(name)
            else:
                print("⚠️ 컬렉션 이름이 입력되지 않았습니다.")

        elif choice == '4':
            print("사용 가능한 모델 키:", ", ".join(config.EMBEDDING_MODELS.keys()))
            model_key = input(f"사용할 모델 키를 입력하세요 (기본값: {config.DEFAULT_MODEL_KEY}): ") or config.DEFAULT_MODEL_KEY
            
            collection_name = input(f"임베딩할 컬렉션 이름 (기본값: {model_key}_collection): ") or f"{model_key}_collection"
            file_path = input(f"JSON 파일 경로 (기본값: {config.TEST_DATA_PATH}): ") or config.TEST_DATA_PATH

            inp = EmbeddingInput(json_path=file_path, collection_name=collection_name, model_key=model_key)
            result = embedding_chain.invoke(inp)
            print(result.get("message", "오류 발생"))

        elif choice == '5':
            c_name = input(f"검색할 컬렉션 이름 (기본값: {config.DEFAULT_MODEL_KEY}_collection): ") or f"{config.DEFAULT_MODEL_KEY}_collection"
            query = input("검색어를 입력하세요: ")
            
            # 👇 검색 모드 선택 UI 추가
            print("--- 검색 모드 선택 ---")
            print("1. 하이브리드 검색 (기본값)")
            print("2. 벡터 검색")
            print("3. BM25 검색")
            mode_choice = input("선택: ")
            
            mode_map = {"1": "hybrid", "2": "vector", "3": "bm25"}
            search_mode = mode_map.get(mode_choice, "hybrid")

            if query:
                inp = SearchInput(query=query, collection_name=c_name, search_mode=search_mode)
                docs = search_chain.invoke(inp)
                print("\n🔍 검색 결과:")
                print(format_docs(docs))
            else:
                print("⚠️ 검색어가 입력되지 않았습니다.")
        elif choice == '0':
            print("프로그램을 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 번호입니다. 다시 입력해주세요.")

if __name__ == "__main__":
    main_menu()