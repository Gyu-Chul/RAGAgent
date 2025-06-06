from pymilvus import utility, connections


connections.connect(
    alias="default",
    host="127.0.0.1",
    port=19530
)

collection_name = "text_embeddings"

if utility.has_collection(collection_name):
    print("기존 컬렉션이 있어 삭제합니다.")
    utility.drop_collection(collection_name)
else:
    print("없는 컬렉션입니다.")
