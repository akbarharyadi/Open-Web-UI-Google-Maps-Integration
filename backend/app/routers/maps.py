"""Google Maps API endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
import requests

from app.config import Settings, get_settings
from app.models import (
    PlaceSearchRequest, PlaceSearchResponse,
    DirectionsRequest, DirectionsResponse,
    GeocodeRequest, GeocodeResponse,
    PlaceDetailsResponse, ErrorResponse
)
from app.services import MapsService

router = APIRouter()


def get_maps_service(settings: Settings = Depends(get_settings)) -> MapsService:
    """
    Dependency injection for MapsService.

    Args:
        settings: Application settings

    Returns:
        MapsService instance
    """
    return MapsService(settings)


@router.post(
    "/search",
    response_model=PlaceSearchResponse,
    summary="Search for places",
    description="Search for places using Google Maps Places API",
    responses={
        200: {"description": "Successful search"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def search_places(
    request: PlaceSearchRequest,
    service: MapsService = Depends(get_maps_service)
) -> PlaceSearchResponse:
    """
    Search for places using Google Maps Places API.

    Args:
        request: Search parameters (query, location, radius)
        service: Maps service instance

    Returns:
        PlaceSearchResponse with list of matching places
    """
    return await service.search_places(request)


@router.get(
    "/place/{place_id}",
    response_model=PlaceDetailsResponse,
    summary="Get place details",
    description="Get detailed information about a specific place"
)
async def get_place_details(
    place_id: str,
    service: MapsService = Depends(get_maps_service)
) -> PlaceDetailsResponse:
    """
    Get detailed information about a specific place.

    Args:
        place_id: Google Maps Place ID
        service: Maps service instance

    Returns:
        PlaceDetailsResponse with detailed place information
    """
    return await service.get_place_details(place_id)


@router.post(
    "/directions",
    response_model=DirectionsResponse,
    summary="Get directions",
    description="Get turn-by-turn directions between two locations"
)
async def get_directions(
    request: DirectionsRequest,
    service: MapsService = Depends(get_maps_service)
) -> DirectionsResponse:
    """
    Get directions between two locations.

    Args:
        request: Directions parameters (origin, destination, mode)
        service: Maps service instance

    Returns:
        DirectionsResponse with route information
    """
    return await service.get_directions(request)


@router.post(
    "/geocode",
    response_model=GeocodeResponse,
    summary="Geocode address",
    description="Convert an address to geographic coordinates"
)
async def geocode_address(
    request: GeocodeRequest,
    service: MapsService = Depends(get_maps_service)
) -> GeocodeResponse:
    """
    Convert an address to geographic coordinates.

    Args:
        request: Geocoding parameters (address)
        service: Maps service instance

    Returns:
        GeocodeResponse with location coordinates
    """
    return await service.geocode_address(request)

@router.get("/embed", response_model=dict,
    summary="Embed map iframe src",
    description="Get embed map iframe src (server-side, key not exposed to client)")
async def embed_search(q: str = Query(...), zoom: int = Query(14, ge=1, le=21),
                       width: int = Query(600), height: int = Query(400),
                       service: MapsService = Depends(get_maps_service)):
    """
    Return embed iframe src (server-side). The API key is only used on server.
    """
    try:
        src = await service.get_embed_src(q=q, zoom=zoom)
        return {"src": src}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate embed src")

@router.get("/static", response_model=dict,
    summary="Static map URL",
    description="Get static map URL (server-side, key not exposed to client)")
async def static_map_url(q: str = Query(...), width: int = Query(600), height: int = Query(400),
                         markers: str = Query("", description="markers param, encoded"),
                         service: MapsService = Depends(get_maps_service)):
    """
    Return static map URL that includes key server-side. markers should be already URL-encoded if needed.
    """
    try:
        # Build static map URL (server-side)
        key = service.settings.google_maps_api_key or service.settings.google_maps_embed_key
        if not key:
            raise RuntimeError("maps key not configured")
        # markers is optional pre-encoded; if empty, center on q
        if markers:
            src = f"https://maps.googleapis.com/maps/api/staticmap?{markers}&size={width}x{height}&scale=2&key={key}"
        else:
            from urllib.parse import urlencode
            params = {
                "key": key,
                "size": f"{width}x{height}",
                "scale": 2,
                "center": q,
                "zoom": 13
            }
            src = "https://maps.googleapis.com/maps/api/staticmap?" + urlencode(params)
        return {"src": src}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate static map src")

@router.get("/static-image",
    summary="Static map image proxy",
    description="Proxy static map image content (server-side, key not exposed to client)")
async def static_map_image(q: str = Query(...), width: int = Query(600), height: int = Query(400),
                           markers: str = Query("", description="markers param, encoded"),
                           service: MapsService = Depends(get_maps_service)):
    """
    Return actual static map image content by proxying to Google Maps API.
    This allows Open WebUI to display images directly via our backend.
    """
    try:
        # Build static map URL (server-side)
        key = service.settings.google_maps_api_key or service.settings.google_maps_embed_key
        if not key:
            raise HTTPException(status_code=500, detail="Maps API key not configured")

        # Build the Google Maps URL
        from urllib.parse import urlencode
        params = {
            "key": key,
            "size": f"{width}x{height}",
            "scale": 2,
        }

        if markers:
            google_url = f"https://maps.googleapis.com/maps/api/staticmap?{markers}&size={width}x{height}&scale=2&key={key}"
        else:
            params.update({"center": q, "zoom": 13})
            google_url = "https://maps.googleapis.com/maps/api/staticmap?" + urlencode(params)

        # Proxy the request to Google Maps
        response = requests.get(google_url, timeout=10)
        response.raise_for_status()

        # Return the image content with proper headers
        from fastapi.responses import Response
        return Response(
            content=response.content,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch map image: {str(e)}")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate static map image")

@router.get("/embed",
    response_model=dict,
    summary="Get Google Maps embed URL",
    description="Returns JSON with Google Maps embed URL built server-side with API key")
async def embed_map(
    q: str = Query(..., description="Search query for the map"),
    zoom: int = Query(14, ge=1, le=21, description="Zoom level (1-21)"),
    width: int = Query(600, description="Map width in pixels (for future compatibility)"),
    height: int = Query(400, description="Map height in pixels (for future compatibility)"),
    service: MapsService = Depends(get_maps_service)
):
    """
    Generate Google Maps embed URL server-side.

    Returns JSON with the embed src URL that includes the API key.
    This allows iframes to point directly to Google's embed service.
    """
    try:
        embed_url = await service.get_embed_src(q=q, zoom=zoom)
        return {"src": embed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate embed src")

@router.get("/embed-redirect",
    summary="Redirect to Google Maps embed",
    description="Direct redirect to Google Maps embed URL (bypasses iframe sandbox)")
async def embed_map_redirect(
    q: str = Query(..., description="Search query for the map"),
    zoom: int = Query(14, ge=1, le=21, description="Zoom level (1-21)"),
    width: int = Query(600, description="Map width in pixels (for future compatibility)"),
    height: int = Query(400, description="Map height in pixels (for future compatibility)"),
    service: MapsService = Depends(get_maps_service)
):
    """
    Redirect directly to Google Maps embed URL.

    This allows iframes to load Google Maps directly without any
    intermediate HTML or JavaScript that could be sandboxed.
    """
    try:
        embed_url = await service.get_embed_src(q=q, zoom=zoom)
        return RedirectResponse(
            url=embed_url,
            status_code=302
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate embed src")