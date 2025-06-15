from pymilvus import utility, connections
from list_collections import list_collections

def delete_collection() :
    connections.connect(
        alias="default",
        host="127.0.0.1",
        port=19530
    )

    list_collections()

    collection_name = input("Which Collection: ")

    if utility.has_collection(collection_name):
        print("Delete complete.")
        utility.drop_collection(collection_name)
    else:
        print("없는 컬렉션입니다.")



if __name__ == "__main__":
    delete_collection()
