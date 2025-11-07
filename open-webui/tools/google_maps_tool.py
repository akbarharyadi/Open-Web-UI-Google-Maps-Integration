"""
title: Google Maps Integration
author: Chat Team
version: 2.0.0
description: Search for places, get directions, and view locations using Google Maps API with embedded interactive maps. Displays results with inline Google Maps showing markers, routes, and locations directly in chat. Provides intelligent place search, detailed location information, turn-by-turn directions, and geocoding services.
requirements: requests
"""

from pydantic import BaseModel, Field
import requests
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime


class Tools:
    """Google Maps tool for Open WebUI."""

    class Valves(BaseModel):
        """Configuration for Google Maps tool.

        Environment Variables:
        - BACKEND_API_URL: Backend API URL for tool-to-backend communication (Docker hostname)
        - BROWSER_API_URL: Browser-accessible API URL for maps display (localhost)
        """

        BACKEND_API_URL: str = Field(
            default="http://fastapi-backend:8000/api/maps",
            description="Backend API URL for tool-to-backend communication (uses Docker hostname)"
        )
        BROWSER_API_URL: str = Field(
            default="http://localhost:8000/api/maps",
            description="Browser-accessible API URL for maps display (uses localhost for image access)"
        )
        MAX_RESULTS_DISPLAY: int = Field(
            default=5,
            description="Maximum number of results to display to user (1-20 recommended)"
        )
        REQUEST_TIMEOUT: int = Field(
            default=15,
            description="API request timeout in seconds (5-30 recommended)"
        )
        INCLUDE_MAP_LINKS: bool = Field(
            default=True,
            description="Include clickable Google Maps links in responses"
        )
        SHOW_MAP_IMAGES: bool = Field(
            default=True,
            description="Include static map images in responses (displays directly in chat)"
        )
        SHOW_INTERACTIVE_MAPS: bool = Field(
            default=True,
            description="Include interactive map embeds with fallback links"
        )
        MAP_WIDTH: int = Field(
            default=600,
            description="Width of map images in pixels (400-800 recommended)"
        )
        MAP_HEIGHT: int = Field(
            default=400,
            description="Height of map images in pixels (300-600 recommended)"
        )

    def __init__(self):
        """Initialize Google Maps tool with configuration."""
        self.valves = self.Valves()
        # Enable citation to show tool context in responses
        self.citation = True

    def update_valves(self, **kwargs):
        """Update valves configuration from Open WebUI interface."""
        for key, value in kwargs.items():
            if hasattr(self.valves, key):
                setattr(self.valves, key, value)

    def _backend_embed_src(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Build a backend proxy URL for embed/static endpoints.
        endpoint: endpoint name under BACKEND_API_URL (e.g., 'embed' or 'static')
        params: dict of query params
        Returns the backend endpoint to be used as image URL.
        """
        # Build query string
        from urllib.parse import urlencode

        # Use appropriate base URL depending on endpoint type
        if endpoint in ["static-image", "embed-redirect"]:
            # These need to be accessible from browser - use BROWSER_API_URL (localhost)
            base = self.valves.BROWSER_API_URL.rstrip("/")
        elif endpoint == "embed":
            # For embed, call API from tool (Docker hostname)
            base = self.valves.BACKEND_API_URL.rstrip("/")
        else:
            # API calls from tool to backend - use BACKEND_API_URL (Docker hostname)
            base = self.valves.BACKEND_API_URL.rstrip("/")

        query = urlencode(params)
        return f"{base}/{endpoint}?{query}"

    def _generate_map_image(self, places: List[Dict], center_location: Optional[str] = None) -> str:
        """Generate a static map image showing multiple locations via backend proxy (no key in client)."""
        if not self.valves.SHOW_MAP_IMAGES or not places:
            return ""

        # Center on first place if available, else center_location string
        first_place = places[0]
        center_lat = first_place['location']['lat']
        center_lng = first_place['location']['lng']
        center = f"{center_lat},{center_lng}"

        # Build markers param correctly for Google Static Maps API
        # Format: markers=color:red|label:1|lat,lng&markers=color:red|label:2|lat,lng&...
        marker_params = []
        for i, place in enumerate(places[:self.valves.MAX_RESULTS_DISPLAY], 1):
            loc = place['location']
            # Create each marker parameter without encoding (backend will handle encoding)
            marker_param = f"markers=color:red|label:{i}|{loc['lat']},{loc['lng']}"
            marker_params.append(marker_param)

        # Join all marker params with '&' (this creates the full markers string for the URL)
        markers_param = "&".join(marker_params)

        # Build backend static map URL (server will add key)
        params = {
            "markers": markers_param,
            "width": self.valves.MAP_WIDTH,
            "height": self.valves.MAP_HEIGHT,
            "q": center  # fallback center param
        }
        # Use the image endpoint directly (no need to call both static and static-image)
        image_url = self._backend_embed_src("static-image", params)
        # Also provide a direct Google Maps link as fallback
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={center}"

        return f"\n![Map showing search results]({image_url})\n\n🔗 [**View on Google Maps**](https://www.google.com/maps/search/?api=1&query={center})\n"

    def _generate_directions_image(self, origin: str, destination: str, route_data: Dict) -> str:
        """Generate a static map image showing route via backend proxy."""
        if not self.valves.SHOW_MAP_IMAGES:
            return ""

        start_loc = route_data.get('start_location', {})
        end_loc = route_data.get('end_location', {})
        if not start_loc or not end_loc:
            return ""

        # Build markers and optional path param (encode path as "lat,lng|lat,lng")
        marker_params = [
            f"markers=color:green|label:A|{start_loc['lat']},{start_loc['lng']}",
            f"markers=color:red|label:B|{end_loc['lat']},{end_loc['lng']}"
        ]
        # Join marker params with '&' (backend will handle URL encoding)
        markers_param = "&".join(marker_params)
        # Build path param as simple start|end (server can render polyline)
        path_param = f"{start_loc['lat']},{start_loc['lng']}|{end_loc['lat']},{end_loc['lng']}"

        params = {
            "markers": markers_param,
            "path": path_param,
            "width": self.valves.MAP_WIDTH,
            "height": self.valves.MAP_HEIGHT,
            "q": f"{start_loc['lat']},{start_loc['lng']}"
        }
        src = self._backend_embed_src("static", params)
        # Use direct image endpoint for better Open WebUI compatibility
        image_url = self._backend_embed_src("static-image", params)
        return f"\n![Route map from {origin} to {destination}]({image_url})\n"

    def _generate_location_image(self, lat: float, lng: float, label: str = "") -> str:
        """Generate a static map image showing a single location via backend proxy."""
        if not self.valves.SHOW_MAP_IMAGES:
            return ""

        params = {
            "q": f"{lat},{lng}",
            "width": self.valves.MAP_WIDTH,
            "height": self.valves.MAP_HEIGHT
        }
        label_text = f" - {label}" if label else ""
        # Use the image endpoint directly (no need to call both static and static-image)
        image_url = self._backend_embed_src("static-image", params)
        return f"\n![Location map{label_text}]({image_url})\n"

    def _generate_location_embed(self, lat: float, lng: float, label: str = "") -> str:
        """Generate a clickable Google Maps link."""
        # Create a direct Google Maps URL
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        label_text = f" - {label}" if label else ""

        return f'\n🔗 [**View on Google Maps**{label_text}]({google_maps_url})\n'

    def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000,
        __event_emitter__=None
    ) -> str:
        """
        Search for places like restaurants, cafes, gas stations, attractions, etc.

        Use this function when the user asks to find, search, or locate places.
        Examples:
        - "Find pizza restaurants in Brooklyn"
        - "Where can I get coffee near Times Square?"
        - "Show me gas stations within 2 miles of Central Park"
        - "What are the best sushi places in San Francisco?"

        IMPORTANT: The output contains formatted markdown with static map images and clickable links.
        You MUST return the complete output exactly as provided, including all markdown
        formatting and emojis. Do NOT summarize or rewrite.

        :param query: What to search for (e.g., "pizza restaurants", "coffee shops", "hospitals")
        :param location: Center location for search (e.g., "New York, NY", "Times Square")
        :param radius: Search radius in meters (default: 5000, max: 50000)
        :return: Formatted list of places with names, addresses, ratings, embedded map, and Google Maps links
        """
        try:
            # Prepare request
            payload = {
                "query": query,
                "location": location,
                "radius": radius
            }

            # Call backend API
            api_url = f"{self.valves.BACKEND_API_URL}/search"
            try:
                response = requests.post(
                    api_url,
                    json=payload,
                    timeout=self.valves.REQUEST_TIMEOUT
                )
            except requests.exceptions.RequestException as e:
                return f"❌ Network error connecting to backend: {str(e)}\nAPI URL: {api_url}\nBackend URL: {self.valves.BACKEND_API_URL}"

            # Handle errors
            if response.status_code != 200:
                try:
                    error_detail = response.json().get('detail', 'Unknown error')
                except:
                    error_detail = response.text[:200]
                return f"❌ Error searching for places (HTTP {response.status_code}): {error_detail}"

            # Parse response
            data = response.json()
            places = data.get('results', [])

            if not places:
                location_text = f" near {location}" if location else ""
                return f"🔍 No results found for '{query}'{location_text}. Try a different search term or location."

            # Format output
            location_text = f" near {location}" if location else ""
            output = [f"📍 **Found {data['count']} places for '{query}'{location_text}:**\n"]

            # Limit display results
            display_count = min(len(places), self.valves.MAX_RESULTS_DISPLAY)

            for i, place in enumerate(places[:display_count], 1):
                # Rating display
                rating_text = ""
                if place.get('rating'):
                    stars = "⭐" * int(round(place['rating']))
                    rating_text = f" {stars} {place['rating']}/5"
                    if place.get('user_ratings_total'):
                        rating_text += f" ({place['user_ratings_total']} reviews)"

                # Format place entry
                place_entry = f"\n**{i}. {place['name']}**{rating_text}\n"
                place_entry += f"   📍 {place['address']}\n"

                # Add coordinates
                loc = place['location']
                place_entry += f"   🗺️ Coordinates: {loc['lat']:.6f}, {loc['lng']:.6f}\n"

                # Add Google Maps link
                if self.valves.INCLUDE_MAP_LINKS and place.get('google_maps_url'):
                    place_entry += f"   🔗 [View on Google Maps]({place['google_maps_url']})\n"

                # Add place types
                if place.get('types'):
                    types = ', '.join(place['types'][:3])
                    place_entry += f"   🏷️ Types: {types}\n"

                output.append(place_entry)

            # Add footer
            if len(places) > display_count:
                output.append(f"\n_({len(places) - display_count} more results available)_\n")

            # Add static map view
            map_image = self._generate_map_image(places[:display_count], location)
            if map_image:
                output.append("\n## 🗺️ Map View\n")
                output.append(map_image)

            # Note: Static map with markers and clickable links are provided above

            return "".join(output)

        except requests.Timeout:
            return f"⏱️ Request timed out after {self.valves.REQUEST_TIMEOUT} seconds. Please try again."
        except requests.RequestException as e:
            return f"❌ Network error: {str(e)}"
        except Exception as e:
            return f"❌ Unexpected error searching places: {str(e)}"

    def get_place_details(self, place_id: str) -> str:
        """
        Get detailed information about a specific place using its Google Place ID.

        Use this function when the user wants more information about a specific place.
        You should use this after search_places to get complete details.

        :param place_id: Google Maps Place ID (obtained from search_places)
        :return: Detailed information including phone, website, hours, reviews, etc.
        """
        try:
            # Call backend API
            response = requests.get(
                f"{self.valves.BACKEND_API_URL}/place/{place_id}",
                timeout=self.valves.REQUEST_TIMEOUT
            )

            if response.status_code == 404:
                return f"❌ Place not found with ID: {place_id}"
            elif response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                return f"❌ Error fetching place details: {error_detail}"

            # Parse response
            place = response.json()

            # Format output
            output = [f"📍 **{place['name']}**\n"]

            # Address
            output.append(f"\n**Address:**\n{place['formatted_address']}\n")

            # Rating
            if place.get('rating'):
                stars = "⭐" * int(round(place['rating']))
                output.append(f"\n**Rating:** {stars} {place['rating']}/5")
                if place.get('user_ratings_total'):
                    output.append(f" ({place['user_ratings_total']} reviews)")
                output.append("\n")

            # Price level
            if place.get('price_level'):
                price = "$" * place['price_level']
                output.append(f"\n**Price Level:** {price}\n")

            # Contact information
            if place.get('formatted_phone_number'):
                output.append(f"\n**Phone:** {place['formatted_phone_number']}\n")

            if place.get('website'):
                output.append(f"\n**Website:** {place['website']}\n")

            # Opening hours
            if place.get('opening_hours'):
                hours = place['opening_hours']
                if 'open_now' in hours:
                    status = "🟢 Open now" if hours['open_now'] else "🔴 Closed now"
                    output.append(f"\n**Status:** {status}\n")

                if hours.get('weekday_text'):
                    output.append("\n**Hours:**\n")
                    for day_hours in hours['weekday_text']:
                        output.append(f"  {day_hours}\n")

            # Coordinates
            loc = place['location']
            output.append(f"\n**Coordinates:** {loc['lat']:.6f}, {loc['lng']:.6f}\n")

            # Types
            if place.get('types'):
                types = ', '.join(place['types'][:5])
                output.append(f"\n**Categories:** {types}\n")

            # Google Maps link
            if self.valves.INCLUDE_MAP_LINKS and place.get('google_maps_url'):
                output.append(f"\n🔗 [View on Google Maps]({place['google_maps_url']})\n")

            return "".join(output)

        except requests.Timeout:
            return f"⏱️ Request timed out. Please try again."
        except Exception as e:
            return f"❌ Error getting place details: {str(e)}"

    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> str:
        """
        Get turn-by-turn directions between two locations.

        Use this function when the user asks for directions, routes, or how to get somewhere.
        Examples:
        - "How do I get from JFK Airport to Times Square?"
        - "Give me directions from Brooklyn to Manhattan"
        - "Show me the walking route from Central Park to MoMA"

        IMPORTANT: The output contains formatted markdown and embedded HTML route map.
        You MUST return the complete output exactly as provided, including all markdown
        formatting, emojis, and HTML iframe elements. Do NOT summarize or rewrite.

        :param origin: Starting point (address, place name, or coordinates)
        :param destination: Ending point (address, place name, or coordinates)
        :param mode: Travel mode - "driving", "walking", "bicycling", or "transit"
        :return: Turn-by-turn directions with distance, duration, embedded route map, and Google Maps link
        """
        try:
            # Validate mode
            valid_modes = ['driving', 'walking', 'bicycling', 'transit']
            if mode.lower() not in valid_modes:
                return f"❌ Invalid travel mode '{mode}'. Use: {', '.join(valid_modes)}"

            # Prepare request
            payload = {
                "origin": origin,
                "destination": destination,
                "mode": mode.lower()
            }

            # Call backend API
            response = requests.post(
                f"{self.valves.BACKEND_API_URL}/directions",
                json=payload,
                timeout=self.valves.REQUEST_TIMEOUT
            )

            if response.status_code == 404:
                return f"❌ No route found from {origin} to {destination}"
            elif response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                return f"❌ Error getting directions: {error_detail}"

            # Parse response
            data = response.json()
            route = data['route']

            # Format output
            mode_emoji = {
                'driving': '🚗',
                'walking': '🚶',
                'bicycling': '🚴',
                'transit': '🚇'
            }

            output = [
                f"{mode_emoji.get(mode, '📍')} **Directions: {origin} → {destination}**\n",
                f"**Mode:** {mode.capitalize()}\n\n"
            ]

            # Route summary
            output.append("**Route Summary:**\n")
            output.append(f"  📏 Distance: {route['distance']}\n")
            output.append(f"  ⏱️ Duration: {route['duration']}\n")
            output.append(f"  🏁 Start: {route['start_address']}\n")
            output.append(f"  🎯 End: {route['end_address']}\n")

            # Turn-by-turn directions
            output.append(f"\n**Turn-by-Turn Directions** ({len(route['steps'])} steps):\n\n")

            for i, step in enumerate(route['steps'][:20], 1):  # Limit to 20 steps
                # Clean HTML from instructions
                instruction = step['instruction']
                instruction = instruction.replace('<b>', '**').replace('</b>', '**')
                instruction = instruction.replace('<div>', '').replace('</div>', '')

                output.append(f"{i}. {instruction}\n")
                output.append(f"   📏 {step['distance']} • ⏱️ {step['duration']}\n\n")

            if len(route['steps']) > 20:
                output.append(f"_({len(route['steps']) - 20} more steps...)_\n\n")

            # Google Maps link
            if self.valves.INCLUDE_MAP_LINKS and data.get('google_maps_url'):
                output.append(f"🗺️ [View full route on Google Maps]({data['google_maps_url']})\n")

            # Add route map image
            map_image = self._generate_directions_image(origin, destination, route)
            if map_image:
                output.append("\n## 🗺️ Route Map\n")
                output.append(map_image)

            return "".join(output)

        except requests.Timeout:
            return f"⏱️ Request timed out. Please try again."
        except Exception as e:
            return f"❌ Error getting directions: {str(e)}"

    def geocode_address(self, address: str) -> str:
        """
        Convert an address or place name to geographic coordinates (latitude/longitude).

        Use this function when the user asks for coordinates of a location.
        Examples:
        - "What are the coordinates of the Eiffel Tower?"
        - "Give me the latitude and longitude of Times Square"

        IMPORTANT: The output contains formatted markdown and embedded HTML location map.
        You MUST return the complete output exactly as provided, including all markdown
        formatting, emojis, and HTML iframe elements. Do NOT summarize or rewrite.

        :param address: Address or place name to geocode
        :return: Formatted address with coordinates, embedded location map, and Google Maps link
        """
        try:
            # Prepare request
            payload = {"address": address}

            # Call backend API
            response = requests.post(
                f"{self.valves.BACKEND_API_URL}/geocode",
                json=payload,
                timeout=self.valves.REQUEST_TIMEOUT
            )

            if response.status_code == 404:
                return f"❌ Could not find location: {address}"
            elif response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                return f"❌ Error geocoding address: {error_detail}"

            # Parse response
            data = response.json()
            results = data.get('results', [])

            if not results:
                return f"🔍 No results found for: {address}"

            # Format output
            output = [f"📍 **Geocoding Results for '{address}':**\n"]

            for i, result in enumerate(results[:3], 1):  # Show top 3 results
                loc = result['location']
                output.append(f"\n**{i}. {result['formatted_address']}**\n")
                output.append(f"   🌐 Latitude: {loc['lat']:.6f}\n")
                output.append(f"   🌐 Longitude: {loc['lng']:.6f}\n")
                output.append(f"   🎯 Type: {result['location_type']}\n")

                # Google Maps link
                maps_url = f"https://www.google.com/maps?q={loc['lat']},{loc['lng']}"
                if self.valves.INCLUDE_MAP_LINKS:
                    output.append(f"   🔗 [View on Map]({maps_url})\n")

            # Note: Individual map links are already provided in each result above

            return "".join(output)

        except requests.Timeout:
            return f"⏱️ Request timed out. Please try again."
        except Exception as e:
            return f"❌ Error geocoding address: {str(e)}"
