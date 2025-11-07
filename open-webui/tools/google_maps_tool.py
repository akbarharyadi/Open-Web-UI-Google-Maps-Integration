"""
title: Google Maps Integration
author: HeyPico Team
version: 1.0.0
description: Search for places, get directions, and view locations using Google Maps API. Provides intelligent place search, detailed location information, turn-by-turn directions, and geocoding services.
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
        """Configuration for Google Maps tool."""

        BACKEND_API_URL: str = Field(
            default="http://fastapi-backend:8000/api/maps",
            description="FastAPI backend URL for Google Maps API"
        )
        MAX_RESULTS_DISPLAY: int = Field(
            default=5,
            description="Maximum number of results to display to user"
        )
        REQUEST_TIMEOUT: int = Field(
            default=15,
            description="API request timeout in seconds"
        )
        INCLUDE_MAP_LINKS: bool = Field(
            default=True,
            description="Include clickable Google Maps links in responses"
        )

    def __init__(self):
        """Initialize Google Maps tool with configuration."""
        self.valves = self.Valves(
            **{
                "BACKEND_API_URL": os.getenv(
                    "BACKEND_API_URL",
                    "http://fastapi-backend:8000/api/maps"
                )
            }
        )
        # Enable citation to show tool context in responses
        self.citation = True

    def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        radius: int = 5000
    ) -> str:
        """
        Search for places like restaurants, cafes, gas stations, attractions, etc.

        Use this function when the user asks to find, search, or locate places.
        Examples:
        - "Find pizza restaurants in Brooklyn"
        - "Where can I get coffee near Times Square?"
        - "Show me gas stations within 2 miles of Central Park"
        - "What are the best sushi places in San Francisco?"

        :param query: What to search for (e.g., "pizza restaurants", "coffee shops", "hospitals")
        :param location: Center location for search (e.g., "New York, NY", "Times Square")
        :param radius: Search radius in meters (default: 5000, max: 50000)
        :return: Formatted list of places with names, addresses, ratings, and Google Maps links
        """
        try:
            # Prepare request
            payload = {
                "query": query,
                "location": location,
                "radius": radius
            }

            # Call backend API
            response = requests.post(
                f"{self.valves.BACKEND_API_URL}/search",
                json=payload,
                timeout=self.valves.REQUEST_TIMEOUT
            )

            # Handle errors
            if response.status_code != 200:
                error_detail = response.json().get('detail', 'Unknown error')
                return f"❌ Error searching for places: {error_detail}"

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
                output.append(f"\n_({len(places) - display_count} more results available)_")

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

        :param origin: Starting point (address, place name, or coordinates)
        :param destination: Ending point (address, place name, or coordinates)
        :param mode: Travel mode - "driving", "walking", "bicycling", or "transit"
        :return: Turn-by-turn directions with distance, duration, and Google Maps link
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

        :param address: Address or place name to geocode
        :return: Formatted address with coordinates and Google Maps link
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

            return "".join(output)

        except requests.Timeout:
            return f"⏱️ Request timed out. Please try again."
        except Exception as e:
            return f"❌ Error geocoding address: {str(e)}"
