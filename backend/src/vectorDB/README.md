/connection-test  
- Milvus connection과 연결 여부를 반환
GET /api/vectorDB/connection-test  

응답 예시
{
    "success": true,
    "message": "✅ Milvus 연결 성공! (MilvusClient 사용)",
    "collections": [
        "collection_1",
        "collection_2"
    ]
}

/count-entities
- 지정한 컬렉션의 엔티티 개수를 반환
GET /api/vectorDB/count_entities?collection_name={컬렉션명}

응답 예시
{
    "success": true,
    "collection": "my_collection",
    "entity_count": 542,
    "message": "📊 Collection \"my_collection\" has 542 entities."
}

/create_collection
- ver0~3에 맞는 형태의 컬렉션을 생성
    POST /api/vectorDB/create_collection
    Content-Type: application/json
    {
        "collection_name": "my_collection",
        "description": "테스트 컬렉션",   ###### 필수X
        "version": 1
    }

응답 예시
{
    "success": true,
    "message": "컬렉션 생성 완료: my_collection (version 1)"
}



/delete_collection
- 지정한 컬렉션 삭제
    DELETE /api/vectorDB/delete_collection
    Content-Type: application/json
    {
        "collection_name": "my_collection"
    }

응답 예시
{
    "success": true,
    "message": "🗑️ 컬렉션 'my_collection' 삭제 완료"
}




/list-collections
- Milvus 서버에 존재하는 모든 컬렉션 이름 목록을 반환
GET /api/vectorDB/list_collections

응답 예시
{
    "success": true,
    "collections": ["collection_1", "collection_2"],
    "count": 2,
    "message": "✅ 총 2개의 컬렉션이 존재합니다: collection_1, collection_2"
}




/view-entities
- 지정한 컬렉션의 엔티티를 조회 (최대 100개 )
GET /api/vectorDB/view_entities?collection_name={컬렉션명}

응답 예시
{
    "success": true,
    "message": "✅ 'my_collection'에서 2개 엔티티 조회됨.",
    "entities": [
        {
            "id": "1234567890",
            "embedding_dim": 768,
            "embedding_preview": [0.12, -0.98, 0.45, 0.33, 0.01],
            "text": "def example_function(): ...",
            "file_path": "src/example.py",
            "start_line": 10,
            "end_line": 20
        },
        {
            엔티티2
        }
    ],
    "count": 2
}



/delete-entity
- 지정한 컬렉션에서 특정 ID의 엔티티를 삭제
    DELETE /api/vectorDB/delete_entity
    Content-Type: application/json
    {
        "collection_name": "my_collection",
        "entity_id": "1234567890"
    }


응답 예시
{
    "success": true,
    "message": "✅ 엔티티 ID 1234567890 삭제 완료"
}




/embed-json-file
- 업로드한 JSON 파일을 임베딩 처리 후 지정한 컬렉션에 삽입

    POST /api/vectorDB/embed_json_file
    Content-Type: application/json
    {
        "json_path": "/home/ubuntu/data/sample.json",
        "collection_name": "my_collection"
    }


응답 예시
{
    "success": true,
    "message": "🎉 250개 엔티티 삽입 완료 (⏱️ 임베딩 12.45s, 삽입 3.67s, 전체 16.12s; 배치 embed=100, payload≤4MB)",
    "total_entities": 250
}





/search-basic
- 메타데이터 필터링 없이 기본 검색
GET /api/vectorDB/search_basic
params = {
    "collection_name": collection_name,
    "query_text": query_text
}


응답 예시
{
    "success": true,
    "message": "🔍 검색 완료 (Top-3, ⏱️ 0.42초)",
    "results": [
        {
            "id": 1001,
            "text": "def example_function(): ...",
            "distance": 0.12345
        },
        {
            "id": 1002,
            "text": "def another_function(): ...",
            "distance": 0.23456
        }
    ]
}



/search-with-metadata
- 메타데이터 필터링 후 검색
GET /api/vectorDB/search_with_metadata
        params = {
            "collection_name": collection_name,
            "query_text": query_text,
            "metadata_filter": metadata_filter
        }


응답 예시
{
    "success": true,
    "message": "🔍 메타데이터 필터 검색 완료 (Top-5, ⏱️ 0.65초)",
    "results": [
        {
            "rank": 1,
            "id": 2001,
            "distance": 0.1123,
            "file_path": "src/module_a.py",
            "type": "module",
            "name": "DatabaseManager",
            "start_line": 10,
            "end_line": 45,
            "code_preview": "class DatabaseManager: ..."
        },
        {
           예시2
        }
    ]
}






/merge-json    ###### 고정경로 설정이 환경에 따라 다를 수 있음.
- 통합된 하나의 total json 생성 요청
    POST /api/vectorDB/merge-json
    Content-Type: application/json
    {"repo": "transformers"}

응답 예시
    {
    "repo": "transformers",
    "out_path": "/home/ubuntu/git-ai/git-agent/parsed_repository/transformers/transformers__all.json",
    "files_scanned": 128,
    "merged_items": 127,
    "skipped": 1
    }


