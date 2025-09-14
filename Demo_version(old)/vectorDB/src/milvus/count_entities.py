from pymilvus import Collection, MilvusException

def count_entities(collection_name: str) -> str:
    try:
        collection = Collection(name=collection_name)
        count = collection.num_entities
        return f'📊 Collection "{collection_name}" has {count} entities.'
    except MilvusException as e:
        return f'❌ 엔티티 개수 조회 실패: {e}'
    except Exception as e:
        return f'❌ 알 수 없는 오류: {e}'
