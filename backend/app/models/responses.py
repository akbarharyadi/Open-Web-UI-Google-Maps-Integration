"""Response models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List


class PlaceLocation(BaseModel):
    """Location coordinates."""

    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")


class PlaceResult(BaseModel):
    """Individual place search result."""

    name: str = Field(..., description="Place name")
    address: str = Field(..., description="Formatted address")
    place_id: str = Field(..., description="Google Maps Place ID")
    rating: Optional[float] = Field(None, description="Average rating (0-5)")
    user_ratings_total: Optional[int] = Field(None, description="Number of ratings")
    location: PlaceLocation = Field(..., description="Geographic coordinates")
    types: Optional[List[str]] = Field(None, description="Place types")
    google_maps_url: str = Field(..., description="Google Maps URL")


class PlaceSearchResponse(BaseModel):
    """Response model for place search."""

    query: str = Field(..., description="Original search query")
    results: List[PlaceResult] = Field(..., description="List of matching places")
    count: int = Field(..., description="Number of results returned")


class PlaceDetailsResponse(BaseModel):
    """Response model for place details."""

    name: str
    formatted_address: str
    formatted_phone_number: Optional[str] = None
    international_phone_number: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    opening_hours: Optional[dict] = None
    location: PlaceLocation
    types: Optional[List[str]] = None
    google_maps_url: str


class DirectionsStep(BaseModel):
    """Individual direction step."""

    instruction: str = Field(..., description="HTML instructions")
    distance: str = Field(..., description="Distance text (e.g., '0.5 km')")
    duration: str = Field(..., description="Duration text (e.g., '5 mins')")


class DirectionsRoute(BaseModel):
    """Directions route information."""

    summary: str = Field(..., description="Route summary")
    distance: str = Field(..., description="Total distance")
    duration: str = Field(..., description="Total duration")
    start_address: str = Field(..., description="Starting address")
    end_address: str = Field(..., description="Ending address")
    steps: List[DirectionsStep] = Field(..., description="Turn-by-turn steps")


class DirectionsResponse(BaseModel):
    """Response model for directions."""

    origin: str
    destination: str
    mode: str
    route: DirectionsRoute
    google_maps_url: str


class GeocodeLocation(BaseModel):
    """Geocoding result location."""

    formatted_address: str
    location: PlaceLocation
    location_type: str
    place_id: str


class GeocodeResponse(BaseModel):
    """Response model for geocoding."""

    address: str = Field(..., description="Original address query")
    results: List[GeocodeLocation] = Field(..., description="Geocoding results")
    count: int = Field(..., description="Number of results")
