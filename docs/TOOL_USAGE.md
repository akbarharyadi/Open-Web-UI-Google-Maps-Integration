# Google Maps Tool - Usage Guide

## Overview

The Google Maps Integration tool allows the LLM to search for places, get directions, and geocode addresses using natural language.

## Functions

### 1. search_places()

**Purpose**: Find restaurants, shops, attractions, services, etc.

**When to use**:
- "Find [place type] in [location]"
- "Where can I get [item/service]?"
- "Show me [place type] near [landmark]"

**Examples**:
- "Find pizza restaurants in New York"
- "Coffee shops near Times Square"
- "Hotels in San Francisco"

**Parameters**:
- `query` (required): What to search for
- `location` (optional): Center point for search
- `radius` (optional): Search radius in meters (default: 5000)

**Returns**:
- Place name with rating
- Address
- Coordinates
- Google Maps link
- Place types/categories

### 2. get_place_details()

**Purpose**: Get detailed information about a specific place.

**When to use**:
- After search_places to get more info
- When you have a Place ID

**Returns**:
- Full address
- Phone number
- Website
- Rating and reviews
- Opening hours
- Price level

**Parameters**:
- `place_id` (required): Google Place ID from search results

### 3. get_directions()

**Purpose**: Get turn-by-turn directions between two locations.

**When to use**:
- "How do I get from [A] to [B]?"
- "Directions to [place]"
- "Show me the route"

**Modes**:
- `driving` (default): Car directions
- `walking`: Pedestrian directions
- `bicycling`: Bike routes
- `transit`: Public transportation

**Parameters**:
- `origin` (required): Starting point
- `destination` (required): Ending point
- `mode` (optional): Travel mode

**Returns**:
- Total distance and duration
- Turn-by-turn steps
- Start/end addresses
- Google Maps link with full route

### 4. geocode_address()

**Purpose**: Convert address to coordinates.

**When to use**:
- "What are the coordinates of [place]?"
- "Where is [address] located?"
- "Latitude/longitude of [place]"

**Returns**:
- Formatted address
- Latitude
- Longitude
- Location type
- Google Maps link

**Parameters**:
- `address` (required): Address or place name

## Best Practices

### For Users

1. **Be specific**: "Pizza in Brooklyn" is better than "food"
2. **Include location**: Helps narrow down results
3. **Use landmarks**: "near Times Square" works well
4. **Ask naturally**: Tool understands conversational language

### For Developers

1. **Docstrings**: LLM reads these - be detailed!
2. **Error handling**: Always try/except
3. **Format output**: Use markdown, emojis, links
4. **Citations**: Set `self.citation = True`
5. **Validation**: Use Pydantic for config

## Troubleshooting

### "No results found"
- Try broader search term
- Check spelling of location
- Increase search radius

### "Invalid location"
- Use full city/state
- Try landmark instead of address
- Verify location exists

### "Request timed out"
- Backend may be slow
- Check FastAPI container running
- Increase timeout in Valves

### "API key not configured"
- Check Docker secret exists
- Verify backend can read secret
- Restart containers

### Tool not being called by LLM
- Ensure tool is enabled for the model
- Check docstrings are descriptive
- Try explicitly asking: "Use the Google Maps tool to..."
- Verify using a capable model (70B+ recommended)

## Configuration (Valves)

Admin can configure:
- `BACKEND_API_URL`: FastAPI backend URL (default: http://fastapi-backend:8000/api/maps)
- `MAX_RESULTS_DISPLAY`: How many results to show (default: 5)
- `REQUEST_TIMEOUT`: API timeout in seconds (default: 15)
- `INCLUDE_MAP_LINKS`: Show clickable links (default: true)

## Installation

### 1. Upload Tool to Open WebUI

1. Access Open WebUI at http://localhost:3000
2. Log in as admin
3. Go to **Admin Panel** → **Tools**
4. Click **+ Create Tool**
5. Paste the entire `google_maps_tool.py` content
6. Click **Save**

### 2. Enable Tool

1. In Tools list, find "Google Maps Integration"
2. Toggle **Enabled** switch to ON
3. Verify all 4 functions appear

### 3. Enable for Model

1. Go to main chat interface
2. Click **Models** dropdown
3. Click **gear icon** next to model name
4. Find "Google Maps Integration" in **Tools & Functions**
5. Toggle **Enable** to ON
6. Click **Save**

### 4. Verify Installation

1. Start new chat
2. Type: `/tools`
3. Verify "Google Maps Integration" appears in list

## Manual Testing

Before using with LLM, test each function:

1. Go to **Admin Panel** → **Tools** → **Google Maps Integration**
2. Click **Test** tab
3. Select function
4. Enter parameters (JSON format)
5. Click **Run**
6. Verify output

Example test for `search_places`:
```json
{
  "query": "coffee shops",
  "location": "San Francisco, CA",
  "radius": 3000
}
```

## Examples

See [test_prompts.md](./test_prompts.md) for comprehensive examples and test cases.

## Architecture

```
User → Open WebUI → LLM → Tool Functions → FastAPI Backend → Google Maps API
                     ↓
                  Format & Display Result
```

## Security

- API keys stored in Docker secrets
- Backend acts as secure proxy
- No direct API access from frontend
- Request timeouts prevent hanging
- Input validation via Pydantic

## Performance

- Average response time: 1-3 seconds
- Caching: Not implemented (future enhancement)
- Rate limiting: Managed by Google Maps API
- Concurrent requests: Supported

## Limitations

- Maximum 50km search radius
- Up to 5 results displayed by default (configurable)
- Turn-by-turn directions limited to 20 steps display
- Geocoding returns top 3 matches
- Requires internet connectivity

## Future Enhancements

- [ ] Caching frequent searches
- [ ] Save favorite places
- [ ] Route comparison (multiple modes)
- [ ] Real-time traffic data
- [ ] Street view integration
- [ ] Place photos
- [ ] Reviews display
- [ ] Nearby search from current location

## Support

For issues or questions:
1. Check logs: `docker compose logs fastapi-backend`
2. Test backend directly: `curl http://localhost:8000/health`
3. Verify containers running: `docker compose ps`
4. Review plan documentation in `plan/04-OPEN-WEBUI-TOOL.md`
