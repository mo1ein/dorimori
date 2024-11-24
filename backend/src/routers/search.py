from fastapi import APIRouter, Query, Request, HTTPException, Depends
from typing import List
from src.services.search import Search
from src.model.products import ListProductPoint

router = APIRouter()

def extract_filters(
    query: str = Query(..., description="Search query text"),
    from_price: float | None = Query(None, description="Minimum price"),
    to_price: float | None = Query(None, description="Maximum price"),
    category_name: str | None = Query(None, description=""),
    brand_name: str | None = Query(None, description=""),
    shop_name: str | None = Query(None, description=""),
    colors: List[str] = Query([], description="Colors (list of strings, e.g., red, blue)"),
    sizes: List[str] = Query([], description="Sizes (list of strings, e.g., S, M, L)"),
    status: str | None = Query(None, description="States (state of sale, e.g., OUT_OF_STOCK, IN_STOCK)"),
    link: str | None = Query(None, description=""),
    rating: float | None = Query(None, description=""),
    material: str | None = Query(None, description="Example: 30% COTTON, 70% POLYESTER"),
):
    """
    Extracts predefined filters from query parameters for use in the search endpoint.

    Args:
        query (str): The main search query text.
        from_price (float | None): Minimum price filter.
        to_price (float | None): Maximum price filter.
        category_name (str | None): Filter by category name.
        brand_name (str | None): Filter by brand name.
        shop_name (str | None): Filter by shop name.
        colors (List[str]): List of colors to filter by.
        sizes (List[str]): List of sizes to filter by.
        status (str | None): Filter by product availability status.
        link (str | None): Filter by product link.
        rating (float | None): Filter by product rating.
        material (str | None): Filter by material composition.

    Returns:
        dict: A dictionary containing the search query and filters for further processing.
    """
    return {
        "query": query,
        "filters": {
            "from_price": from_price,
            "to_price": to_price,
            "category_name": category_name,
            "brand_name": brand_name,
            "shop_name": shop_name,
            "colors": colors,
            "sizes": sizes,
            "status": status,
            "link": link,
            "rating": rating,
            "material": material,
        },
    }

@router.get("/api/v1/search", response_model=ListProductPoint, tags=["Search"])
def search(
    request: Request,
    query_params: dict = Depends(extract_filters)
) -> ListProductPoint:
    """
    Search for products based on a query text and optional filters.

    This endpoint accepts query parameters for filtering product data, processes the filters dynamically,
    and invokes the `Search` service to perform a vector similarity search.

    Args:
        request (Request): The FastAPI Request object.
        query_params (dict): Dictionary of query parameters and filters extracted by `extract_filters`.

    Returns:
       ListProductPoint: A list of product points matching the query and filters.

    Raises:
        HTTPException: If an error occurs during the search process, a 500 status code is returned with the error details.
    """
    # todo: can move this part to service and also use pydantic
    try:
        dynamic_filters = dict(request.query_params)
        text = query_params["query"]
        filters = []

        predefined_keys = query_params["filters"].keys()
        for key in predefined_keys:
            dynamic_filters.pop(key, None)

        for field, value in query_params["filters"].items():
            if value is not None:
                if field == "from_price":
                    filters.append({"field": "current_price", "operation": "gte", "value": float(value)})
                elif field == "to_price":
                    filters.append({"field": "current_price", "operation": "lte", "value": float(value)})
                elif isinstance(value, list) and value:  # Handle lists (e.g., colors, sizes)
                    for item in value:
                        filters.append({"field": field, "operation": "eq", "value": item})
                elif isinstance(value, (str, float, bool, int)):  # Handle single values
                    filters.append({"field": field, "operation": "eq", "value": value})

        for field, value in dynamic_filters.items():
            if value is not None:
                filters.append({"field": field, "operation": "eq", "value": value})

        search_logic = Search()
        result = search_logic.find_similar(
            text=text,
            filters=filters
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
