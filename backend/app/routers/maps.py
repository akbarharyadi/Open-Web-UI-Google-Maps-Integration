"""Google Maps API endpoints."""

from fastapi import APIRouter, Depends

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
