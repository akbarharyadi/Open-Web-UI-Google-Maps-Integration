# Embedded Maps Setup Guide

## Overview

The Google Maps tool now supports embedding interactive maps directly in Open WebUI chat responses! Users can view locations, directions, and search results without leaving the chat interface.

## Features

When configured, the tool will automatically embed interactive Google Maps for:

1. **Place Search** - Shows map with markers for all found locations
2. **Directions** - Displays the complete route with turn-by-turn navigation
3. **Geocoding** - Shows the exact location on a map

## Setup Instructions

### Step 1: Get a Google Maps Embed API Key

The embedded maps use the Google Maps Embed API, which requires a separate API key from the backend API key.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Enable **Maps Embed API**:
   - Go to **APIs & Services** → **Library**
   - Search for "Maps Embed API"
   - Click **Enable**

4. Create an API Key:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **API Key**
   - Copy the generated key

5. Restrict the API Key (Recommended):
   - Click on the key you just created
   - Under **API restrictions**, select **Restrict key**
   - Choose **Maps Embed API**
   - Under **Website restrictions**, add:
     - `http://localhost:3000/*`
     - Your production domain if deploying
   - Click **Save**

### Step 2: Configure the Tool in Open WebUI

1. Open Open WebUI at http://localhost:3000
2. Go to **Workspace** → **Tools**
3. Find **Google Maps Integration** tool
4. Click the **Settings** or **Valves** icon
5. Set the following configuration:

```
EMBED_MAPS: true
GOOGLE_MAPS_EMBED_API_KEY: your-embed-api-key-here
MAP_HEIGHT: 400
```

6. Click **Save**

### Step 3: Test the Embedded Maps

Try these prompts to test the embedded maps:

1. **Place Search:**
   ```
   Find pizza restaurants in Brooklyn, New York
   ```
   Expected: List of restaurants + embedded map showing all locations

2. **Directions:**
   ```
   How do I get from JFK Airport to Times Square?
   ```
   Expected: Turn-by-turn directions + embedded map with route

3. **Geocoding:**
   ```
   What are the coordinates of the Statue of Liberty?
   ```
   Expected: Coordinates + embedded map showing the location

## Configuration Options

### Valves (Tool Settings)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `BACKEND_API_URL` | string | `http://fastapi-backend:8000/api/maps` | FastAPI backend URL |
| `MAX_RESULTS_DISPLAY` | int | `5` | Maximum number of results to show |
| `REQUEST_TIMEOUT` | int | `15` | API request timeout in seconds |
| `INCLUDE_MAP_LINKS` | bool | `true` | Include Google Maps links |
| `EMBED_MAPS` | bool | `true` | Enable embedded maps |
| `MAP_HEIGHT` | int | `400` | Height of embedded maps in pixels |
| `GOOGLE_MAPS_EMBED_API_KEY` | string | `""` | API key for embedded maps |

## Troubleshooting

### Maps Not Showing

**Problem**: Embedded maps don't appear in chat responses

**Solutions**:
1. Verify `EMBED_MAPS` is set to `true`
2. Ensure `GOOGLE_MAPS_EMBED_API_KEY` is correctly configured
3. Check that Maps Embed API is enabled in Google Cloud Console
4. Verify API key restrictions allow your domain

### "This page can't load Google Maps correctly"

**Problem**: Map iframe shows an error message

**Solutions**:
1. Check that the API key is valid
2. Verify Maps Embed API is enabled (not just JavaScript API)
3. Check API key restrictions:
   - Ensure your domain is whitelisted
   - Ensure API restriction includes Maps Embed API
4. Check billing is enabled on Google Cloud project

### Maps Show Wrong Location

**Problem**: Map displays incorrect location

**Solutions**:
1. Verify the search query is specific enough
2. Try including city/state in location parameter
3. Check the coordinates returned by the backend API

## API Key Security

### Best Practices

1. **Use Separate Keys**: Use different API keys for:
   - Backend API (server-side, unrestricted)
   - Embed API (client-side, domain-restricted)

2. **Restrict Access**:
   - Backend key: IP restrictions
   - Embed key: HTTP referrer restrictions

3. **Monitor Usage**:
   - Set up billing alerts in Google Cloud
   - Monitor API usage regularly
   - Set quota limits to prevent abuse

4. **Rotate Keys**:
   - Rotate keys periodically
   - Immediately rotate if key is exposed

## Alternative: Disable Embedded Maps

If you prefer to show only links without embedded maps:

1. Set `EMBED_MAPS` to `false` in tool settings
2. Users will still get clickable Google Maps links
3. No Embed API key required

## Cost Considerations

### Google Maps Embed API Pricing

- **Free Tier**:
  - Maps Embed API: Free (no charge)
  - Unlimited map loads per month

- **Note**: The backend APIs (Places, Directions, Geocoding) have separate pricing

### Cost Optimization Tips

1. **Use Embed API Only**: It's free!
2. **Optimize Backend Calls**: These count toward paid quotas
   - Cache frequent searches
   - Limit MAX_RESULTS_DISPLAY
3. **Monitor Usage**: Set up billing alerts

## Examples

### Example 1: Restaurant Search with Map

**User**: "Find Italian restaurants near Times Square"

**Response**:
```
📍 Found 5 places for 'Italian restaurants' near Times Square:

1. Carmine's Italian Restaurant ⭐⭐⭐⭐⭐ 4.5/5 (3,245 reviews)
   📍 200 W 44th St, New York, NY 10036
   ...

## 🗺️ View on Map
[Interactive map showing all 5 restaurants with numbered markers]
```

### Example 2: Directions with Route Map

**User**: "How do I get from Central Park to Brooklyn Bridge?"

**Response**:
```
🚗 Directions: Central Park → Brooklyn Bridge
Mode: Driving

Route Summary:
📏 Distance: 8.2 miles
⏱️ Duration: 24 mins
...

## 🗺️ View Route on Map
[Interactive map showing the complete route]
```

## Support

For issues or questions:
1. Check logs: `docker compose logs fastapi-backend`
2. Verify backend health: http://localhost:8000/health
3. Review tool configuration in Open WebUI
4. Check Google Cloud Console for API errors

## Related Documentation

- [TOOL_USAGE.md](./TOOL_USAGE.md) - General tool usage guide
- [Phase 4 Plan](../plan/04-OPEN-WEBUI-TOOL.md) - Tool development details
- [Phase 5 Plan](../plan/05-FRONTEND-MAP-VIEWER.md) - Map viewer implementation
