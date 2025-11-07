"""Request models for API validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class PlaceSearchRequest(BaseModel):
    """Request model for place search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query (e.g., 'pizza restaurants', 'gas stations')"
    )
    location: Optional[str] = Field(
        None,
        max_length=200,
        description="Center location for search (e.g., 'New York, NY')"
    )
    radius: int = Field(
        default=5000,
        ge=1,
        le=50000,
        description="Search radius in meters (1-50000)"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Ensure query is not just whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace")
        return v.strip()


class DirectionsRequest(BaseModel):
    """Request model for directions."""

    origin: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Starting point (address or place name)"
    )
    destination: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Ending point (address or place name)"
    )
    mode: str = Field(
        default="driving",
        description="Travel mode: driving, walking, bicycling, transit"
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Validate travel mode."""
        allowed_modes = ['driving', 'walking', 'bicycling', 'transit']
        if v.lower() not in allowed_modes:
            raise ValueError(f"Mode must be one of: {', '.join(allowed_modes)}")
        return v.lower()


class GeocodeRequest(BaseModel):
    """Request model for geocoding."""

    address: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Address to geocode"
    )
