"""Google Maps service containing business logic (async-safe)."""

import logging
from typing import List, Optional
from urllib.parse import urlencode
import asyncio

import googlemaps
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
    """Service class for Google Maps operations (async-friendly)."""

    def __init__(self, settings: Settings):
        """
        Initialize Maps service.

        Args:
            settings: Application settings with API key
        """
        self.settings = settings
        self._client: Optional[googlemaps.Client] = None

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
            if not getattr(self.settings, "google_maps_api_key", None):
                logger.error("Google Maps API key not configured in settings")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Google Maps API key not configured"
                )
            try:
                # googlemaps.Client is sync; create it once
                self._client = googlemaps.Client(
                    key=self.settings.google_maps_api_key,
                    timeout=getattr(self.settings, "api_timeout", None)
                )
            except Exception as e:
                logger.exception("Failed to initialize Google Maps client")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize Google Maps client"
                )
        return self._client

    # Helper to execute sync googlemaps calls in threadpool
    async def _run_blocking(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        except Exception as e:
            logger.exception("Blocking call failed")
            raise

    # New: return server-side embed src (client will not see API key)
    async def get_embed_src(self, q: str, zoom: int = 14) -> str:
        """
        Build a Google Maps Embed API src URL server-side using secret key.
        The returned src includes the key (server-side) — you may optionally proxy/embed
        it directly or return a short-lived token instead.
        """
        key = getattr(self.settings, "google_maps_embed_key", None) or getattr(self.settings, "google_maps_api_key", None)
        if not key:
            logger.error("Embed key not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Maps embed key not configured"
            )
        params = {"key": key, "q": q, "zoom": zoom}
        embed_url = "https://www.google.com/maps/embed/v1/search?" + urlencode(params)
        logger.info(f"Generated embed URL: {embed_url}")
        return embed_url

    async def search_places(self, request: PlaceSearchRequest) -> PlaceSearchResponse:
        """
        Search for places using Google Maps Places API (async-safe).
        """
        try:
            logger.info(
                f"Searching places: query='{request.query}', location='{request.location}', radius={request.radius}"
            )

            # Geocode location if provided (blocking -> run in executor)
            lat_lng = None
            if request.location:
                lat_lng = await self._geocode_location(request.location)

            # Perform the appropriate search in threadpool
            if lat_lng:
                search_result = await self._run_blocking(
                    self.client.places_nearby,
                    location=lat_lng,
                    keyword=request.query,
                    radius=request.radius
                )
            else:
                search_result = await self._run_blocking(
                    self.client.places,
                    query=request.query
                )

            raw_results = search_result.get("results", []) if isinstance(search_result, dict) else []
            if not raw_results:
                logger.info("No results found for query: %s", request.query)
                return PlaceSearchResponse(query=request.query, results=[], count=0)

            places = self._format_place_results(raw_results)
            logger.info("Found %d results for query=%s", len(places), request.query)
            return PlaceSearchResponse(query=request.query, results=places, count=len(places))

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Search error")
            raise HTTPException(status_code=500, detail="Search failed")

    async def get_place_details(self, place_id: str) -> PlaceDetailsResponse:
        """
        Get detailed information about a specific place (async-safe).
        """
        try:
            logger.info("Fetching details for place_id=%s", place_id)
            place_details = await self._run_blocking(
                self.client.place,
                place_id=place_id,
                fields=[
                    "name", "formatted_address", "formatted_phone_number",
                    "international_phone_number", "website", "rating",
                    "user_ratings_total", "price_level", "opening_hours",
                    "geometry", "types"
                ]
            )

            result = place_details.get("result", {}) if isinstance(place_details, dict) else {}
            if not result:
                logger.warning("Place not found: %s", place_id)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Place not found: {place_id}")

            location = result.get("geometry", {}).get("location", {})
            opening_hours = None
            if "opening_hours" in result:
                opening_hours = {
                    "open_now": result["opening_hours"].get("open_now"),
                    "weekday_text": result["opening_hours"].get("weekday_text", [])
                }

            return PlaceDetailsResponse(
                name=result.get("name", "Unknown"),
                formatted_address=result.get("formatted_address", "N/A"),
                formatted_phone_number=result.get("formatted_phone_number"),
                international_phone_number=result.get("international_phone_number"),
                website=result.get("website"),
                rating=result.get("rating"),
                user_ratings_total=result.get("user_ratings_total"),
                price_level=result.get("price_level"),
                opening_hours=opening_hours,
                location=PlaceLocation(
                    lat=location.get("lat"),
                    lng=location.get("lng")
                ),
                types=result.get("types", []),
                google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Error fetching place details")
            raise HTTPException(status_code=500, detail="Failed to fetch place details")

    async def get_directions(self, request: DirectionsRequest) -> DirectionsResponse:
        """
        Get directions between two locations (async-safe).
        """
        try:
            logger.info("Getting directions: %s -> %s (%s)", request.origin, request.destination, request.mode)
            directions = await self._run_blocking(
                self.client.directions,
                origin=request.origin,
                destination=request.destination,
                mode=request.mode
            )

            if not directions:
                logger.warning("No route found from %s to %s", request.origin, request.destination)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No route found")

            route = directions[0]
            leg = route.get("legs", [])[0]

            steps = [
                DirectionsStep(
                    instruction=step.get("html_instructions"),
                    distance=step.get("distance", {}).get("text"),
                    duration=step.get("duration", {}).get("text"),
                )
                for step in leg.get("steps", [])
            ]

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
                    summary=route.get("summary", "Route"),
                    distance=leg.get("distance", {}).get("text"),
                    duration=leg.get("duration", {}).get("text"),
                    start_address=leg.get("start_address"),
                    end_address=leg.get("end_address"),
                    steps=steps
                ),
                google_maps_url=google_maps_url
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Directions error")
            raise HTTPException(status_code=500, detail="Failed to get directions")

    async def geocode_address(self, request: GeocodeRequest) -> GeocodeResponse:
        """
        Convert an address to geographic coordinates (async-safe).
        """
        try:
            logger.info("Geocoding address: %s", request.address)
            geocode_result = await self._run_blocking(
                self.client.geocode,
                request.address
            )

            if not geocode_result:
                logger.warning("Geocoding returned no results for %s", request.address)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not geocode address")

            results = [
                GeocodeLocation(
                    formatted_address=res.get("formatted_address"),
                    location=PlaceLocation(
                        lat=res.get("geometry", {}).get("location", {}).get("lat"),
                        lng=res.get("geometry", {}).get("location", {}).get("lng")
                    ),
                    location_type=res.get("geometry", {}).get("location_type"),
                    place_id=res.get("place_id")
                )
                for res in geocode_result[:5]
            ]

            return GeocodeResponse(address=request.address, results=results, count=len(results))

        except HTTPException:
            raise
        except Exception:
            logger.exception("Geocoding error")
            raise HTTPException(status_code=500, detail="Geocoding failed")

    # Private helper methods

    async def _geocode_location(self, location: str) -> dict:
        """
        Geocode a location string to coordinates (async-safe).
        """
        try:
            geocode_result = await self._run_blocking(self.client.geocode, location)
            if geocode_result:
                lat_lng = geocode_result[0].get("geometry", {}).get("location", {})
                logger.info("Geocoded location: %s", lat_lng)
                return lat_lng
            else:
                logger.warning("Could not find location: %s", location)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not find location: {location}")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Geocoding error in helper")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid location")

    def _format_place_results(self, raw_results: List[dict]) -> List[PlaceResult]:
        """
        Format raw Google Maps place results.

        Args:
            raw_results: Raw results from Google Maps API

        Returns:
            List of formatted PlaceResult objects
        """
        places: List[PlaceResult] = []
        max_results = getattr(self.settings, "max_results", 10)
        for place in raw_results[:max_results]:
            location = place.get("geometry", {}).get("location", {})
            place_id = place.get("place_id", "")

            places.append(PlaceResult(
                name=place.get("name", "Unknown"),
                address=place.get("vicinity") or place.get("formatted_address", "N/A"),
                place_id=place_id,
                rating=place.get("rating"),
                user_ratings_total=place.get("user_ratings_total"),
                location=PlaceLocation(
                    lat=location.get("lat"),
                    lng=location.get("lng")
                ),
                types=place.get("types", []),
                google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            ))

        return places
