from fastapi import APIRouter

router = APIRouter()

@router.get("/test1")
def get_sample1():
    return {
        "message": "This is sample1 response",
        "data": [1, 2, 3]
    }

@router.get("/test2")
def get_sample2():
    return {
        "message": "This is sample2 response",
        "items": {"a": "foo", "b": "bar"}
    }
