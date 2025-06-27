# src/services/milvus_controller.py

from src.milvus.connection_test import connection_test as _connection_test
from src.milvus.create_collection import create_collection as _create
from src.milvus.delete_collection import delete_collection as _delete
from src.milvus.list_collections import list_collections as _list
from src.milvus.view_entities import view_entities as _view
from src.milvus.count_entities import count_entities as _count
from src.milvus.delete_entity import delete_entity as _delete_entity
from src.milvus.embedding import embed_json_file as _embed

def connection_test():
    return _connection_test()

def create_collection(name, desc=''):
    return _create(name, desc)

def delete_collection(name):
    return _delete(name)


def list_collection():
    collections = _list()
    if isinstance(collections, list):
        return "\n".join([f"- {name}" for name in collections])
    return collections  # 에러 메시지 반환

def view_entities(name):
    return _view(name)

def count_entities(name):
    return f'{_count(name)}'

def delete_entity(name, entity_id=None):
    if not entity_id:
        return "❌ 엔티티 ID가 제공되지 않았습니다."
    return _delete_entity(name, entity_id)


def embedding(json_path, collection_name):
    return _embed(json_path, collection_name)
