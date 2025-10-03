"""
RAG Worker Vector Database Main Module
단일 책임: 벡터 데이터베이스 메인 로직 처리
"""

import json
import os
from typing import List, Dict, Any
import db_utils
import config
from chains import embedding_chain, search_chain, EmbeddingInput, SearchInput

def create_test_data_file() -> None:
    """임베딩 테스트를 위한 샘플 JSON 파일을 생성합니다."""
    if not os.path.exists(config.TEST_DATA_PATH) or os.path.getsize(config.TEST_DATA_PATH) == 0:
        print(f"'{config.TEST_DATA_PATH}' 파일이 없거나 비어있어 새로 생성합니다.")
        sample_data = [
            {
                "type": "module",
                "name": "",
                "start_line": 1,
                "end_line": 3,
                "code": "from nicegui import ui\nfrom controller import DownloadState, run_download\nimport os",
                "file_path": "/home/gyuho/RAGAgent/Demo_version(old)/git-agent/repository/youtube_mp3_downloader/app.py",
                "_source_file": "app.json"
            },
            {
                "type": "script",
                "name": "",
                "start_line": 5,
                "end_line": 5,
                "code": "state = DownloadState()",
                "file_path": "/home/gyuho/RAGAgent/Demo_version(old)/git-agent/repository/youtube_mp3_downloader/app.py",
                "_source_file": "app.json"
            },
            {
                "type": "script",
                "name": "",
                "start_line": 7,
                "end_line": 10,
                "code": "ui.label(\"🎵 YouTube to MP3 Downloader\").classes('text-2xl font-bold text-center mt-4')\n"
                        "input_url = ui.input(\"YouTube URL\").classes('w-full')\n"
                        "status_label = ui.label()\n"
                        "progress = ui.linear_progress().classes('w-full')",
                "file_path": "/home/gyuho/RAGAgent/Demo_version(old)/git-agent/repository/youtube_mp3_downloader/app.py",
                "_source_file": "app.json"
            }
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
        print("6. 컬렉션 데이터 확인")
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

            if query:
                inp = SearchInput(query=query, collection_name=c_name)
                
                results = search_chain.invoke(inp)  # 바로 JSON 구조로 저장
                
                print("\n🔍 검색 결과 (JSON):")
                if not results:
                    print("검색 결과가 없습니다.")
                else:
                    print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print("⚠️ 검색어가 입력되지 않았습니다.")

        elif choice == '6':
            collection_name = input("데이터를 확인할 컬렉션 이름을 입력하세요: ")
            db_utils.verify_collection_data(collection_name)

        elif choice == '0':
            print("프로그램을 종료합니다.")
            break
        
        else:
            print("❌ 잘못된 번호입니다. 다시 입력해주세요.")

if __name__ == "__main__":
    main_menu()