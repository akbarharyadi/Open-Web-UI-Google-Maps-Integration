"""Google Maps service containing business logic."""

import googlemaps
from typing import List
import logging
from fastapi import HTTPException, status

from app.config import Settings
from app.models import (
    PlaceSearchRequest, PlaceSearchResponse, PlaceResult, PlaceLocation,
    DirectionsRequest, DirectionsResponse, DirectionsRoute, DirectionsStep,
    GeocodeRequest, GeocodeResponse, GeocodeLocation,
    PlaceDetailsResponse
)

logger = logging.getLogger(__name__)


class MapsService:
    """Service class for Google Maps operations."""

    def __init__(self, settings: Settings):
        """
        Initialize Maps service.

        Args:
            settings: Application settings with API key
        """
        self.settings = settings
        self._client = None

    @property
    def client(self) -> googlemaps.Client:
        """
        Get or create Google Maps client instance.

        Returns:
            Configured Google Maps client

        Raises:
            HTTPException: If API key is not configured
        """
        if self._client is None:
            if not self.settings.google_maps_api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Google Maps API key not configured"
                )

            try:
                self._client = googlemaps.Client(
                    key=self.settings.google_maps_api_key,
                    timeout=self.settings.api_timeout
                )
            except Exception as e:
                logger.error(f"Failed to create Google Maps client: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to initialize Google Maps client: {str(e)}"
                )

        return self._client

    async def search_places(self, request: PlaceSearchRequest) -> PlaceSearchResponse:
        """
        Search for places using Google Maps Places API.

        Args:
            request: Search parameters (query, location, radius)

        Returns:
            PlaceSearchResponse with list of matching places
        """
        try:
            logger.info(
                f"Searching places: query='{request.query}', "
                f"location='{request.location}', radius={request.radius}"
            )

            # Geocode location if provided
            lat_lng = None
            if request.location:
                lat_lng = await self._geocode_location(request.location)

            # Search places
            if lat_lng:
                # Location-based search
                search_result = self.client.places_nearby(
                    location=lat_lng,
                    keyword=request.query,
                    radius=request.radius
                )
            else:
                # Text search
                search_result = self.client.places(query=request.query)

            # Extract and format results
            raw_results = search_result.get('results', [])

            if not raw_results:
                logger.info(f"No results found for query: {request.query}")
                return PlaceSearchResponse(
                    query=request.query,
                    results=[],
                    count=0
                )

            places = self._format_place_results(raw_results)
            logger.info(f"Found {len(places)} results")

            return PlaceSearchResponse(
                query=request.query,
                results=places,
                count=len(places)
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {str(e)}"
            )

    async def get_place_details(self, place_id: str) -> PlaceDetailsResponse:
        """
        Get detailed information about a specific place.

        Args:
            place_id: Google Maps Place ID

        Returns:
            PlaceDetailsResponse with detailed place information
        """
        try:
            logger.info(f"Fetching details for place_id: {place_id}")

            # Get place details
            place_details = self.client.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'formatted_phone_number',
                    'international_phone_number', 'website', 'rating',
                    'user_ratings_total', 'price_level', 'opening_hours',
                    'geometry', 'types'
                ]
            )

            result = place_details.get('result', {})

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place not found: {place_id}"
                )

            location = result['geometry']['location']

            # Format opening hours
            opening_hours = None
            if 'opening_hours' in result:
                opening_hours = {
                    'open_now': result['opening_hours'].get('open_now'),
                    'weekday_text': result['opening_hours'].get('weekday_text', [])
                }

            return PlaceDetailsResponse(
                name=result.get('name', 'Unknown'),
                formatted_address=result.get('formatted_address', 'N/A'),
                formatted_phone_number=result.get('formatted_phone_number'),
                international_phone_number=result.get('international_phone_number'),
                website=result.get('website'),
                rating=result.get('rating'),
                user_ratings_total=result.get('user_ratings_total'),
                price_level=result.get('price_level'),
                opening_hours=opening_hours,
                location=PlaceLocation(
                    lat=location['lat'],
                    lng=location['lng']
                ),
                types=result.get('types', []),
                google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching place details: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch place details: {str(e)}"
            )

    async def get_directions(self, request: DirectionsRequest) -> DirectionsResponse:
        """
        Get directions between two locations.

        Args:
            request: Directions parameters (origin, destination, mode)

        Returns:
            DirectionsResponse with route information
        """
        try:
            logger.info(
                f"Getting directions: {request.origin} -> "
                f"{request.destination} ({request.mode})"
            )

            # Get directions
            directions = self.client.directions(
                origin=request.origin,
                destination=request.destination,
                mode=request.mode
            )

            if not directions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No route found from {request.origin} to {request.destination}"
                )

            # Extract first route
            route = directions[0]
            leg = route['legs'][0]

            # Format steps
            steps = [
                DirectionsStep(
                    instruction=step['html_instructions'],
                    distance=step['distance']['text'],
                    duration=step['duration']['text']
                )
                for step in leg['steps']
            ]

            # Create Google Maps URL
            google_maps_url = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={request.origin}"
                f"&destination={request.destination}"
                f"&travelmode={request.mode}"
            )

            return DirectionsResponse(
                origin=request.origin,
                destination=request.destination,
                mode=request.mode,
                route=DirectionsRoute(
                    summary=route.get('summary', 'Route'),
                    distance=leg['distance']['text'],
                    duration=leg['duration']['text'],
                    start_address=leg['start_address'],
                    end_address=leg['end_address'],
                    steps=steps
                ),
                google_maps_url=google_maps_url
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Directions error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get directions: {str(e)}"
            )

    async def geocode_address(self, request: GeocodeRequest) -> GeocodeResponse:
        """
        Convert an address to geographic coordinates.

        Args:
            request: Geocoding parameters (address)

        Returns:
            GeocodeResponse with location coordinates
        """
        try:
            logger.info(f"Geocoding address: {request.address}")

            # Geocode address
            geocode_result = self.client.geocode(request.address)

            if not geocode_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not geocode address: {request.address}"
                )

            # Format results
            results = [
                GeocodeLocation(
                    formatted_address=result['formatted_address'],
                    location=PlaceLocation(
                        lat=result['geometry']['location']['lat'],
                        lng=result['geometry']['location']['lng']
                    ),
                    location_type=result['geometry']['location_type'],
                    place_id=result['place_id']
                )
                for result in geocode_result[:5]  # Max 5 results
            ]

            return GeocodeResponse(
                address=request.address,
                results=results,
                count=len(results)
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Geocoding error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Geocoding failed: {str(e)}"
            )

    # Private helper methods

    async def _geocode_location(self, location: str) -> dict:
        """
        Geocode a location string to coordinates.

        Args:
            location: Location string (e.g., "New York, NY")

        Returns:
            Dictionary with 'lat' and 'lng' keys

        Raises:
            HTTPException: If location cannot be geocoded
        """
        try:
            geocode_result = self.client.geocode(location)
            if geocode_result:
                lat_lng = geocode_result[0]['geometry']['location']
                logger.info(f"Geocoded location: {lat_lng}")
                return lat_lng
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Could not find location: {location}"
                )
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid location: {location}"
            )

    def _format_place_results(self, raw_results: List[dict]) -> List[PlaceResult]:
        """
        Format raw Google Maps place results.

        Args:
            raw_results: Raw results from Google Maps API

        Returns:
            List of formatted PlaceResult objects
        """
        places = []
        for place in raw_results[:self.settings.max_results]:
            location = place['geometry']['location']
            place_id = place.get('place_id', '')

            places.append(PlaceResult(
                name=place.get('name', 'Unknown'),
                address=place.get('vicinity') or place.get('formatted_address', 'N/A'),
                place_id=place_id,
                rating=place.get('rating'),
                user_ratings_total=place.get('user_ratings_total'),
                location=PlaceLocation(
                    lat=location['lat'],
                    lng=location['lng']
                ),
                types=place.get('types', []),
                google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            ))

        return places
