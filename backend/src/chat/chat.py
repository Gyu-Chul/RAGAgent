from fastapi import APIRouter

router = APIRouter()

@router.get("/request", status_code=201)
async def request(message,branch,room,id):

    print(message,branch,room,id)

    return 0