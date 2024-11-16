from fastapi import APIRouter, Query
from src.services.search import Search
from src.model.products import ListProductPoint

router = APIRouter()

# todo: fix const instead of search
@router.get("/api/v1/search", response_model=ListProductPoint, tags=["Search"])

def search(query: str = Query(...)) -> ListProductPoint:
    search_logic = Search()
    # todo: convert to model
    return search_logic.find_similar(query)