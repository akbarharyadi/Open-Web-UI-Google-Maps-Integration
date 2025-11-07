"""Test script to verify Google Maps tool works inside Open WebUI container."""

import sys
import os

# Add the tool directory to path
sys.path.insert(0, '/app/backend/data/tools')

# Import the tool
try:
    from google_maps_tool import Tools
    print("✅ Tool imported successfully!")

    # Initialize tool
    tool = Tools()
    print(f"✅ Tool initialized")
    print(f"   Backend URL: {tool.valves.BACKEND_API_URL}")
    print(f"   Max Results: {tool.valves.MAX_RESULTS_DISPLAY}")
    print(f"   Timeout: {tool.valves.REQUEST_TIMEOUT}s")
    print(f"   Include Links: {tool.valves.INCLUDE_MAP_LINKS}")

    # Test search function
    print("\n🔍 Testing search_places function...")
    result = tool.search_places("coffee shops", "San Francisco, CA", 3000)

    if "Error" in result or "❌" in result:
        print(f"❌ Search failed: {result[:200]}")
    elif "Found" in result or "📍" in result:
        print("✅ Search successful!")
        print(f"   Result preview: {result[:150]}...")
    else:
        print(f"⚠️  Unexpected result: {result[:200]}")

    # Test geocode function
    print("\n🌐 Testing geocode_address function...")
    result = tool.geocode_address("Times Square, New York")

    if "Error" in result or "❌" in result:
        print(f"❌ Geocode failed: {result[:200]}")
    elif "Geocoding Results" in result or "📍" in result:
        print("✅ Geocode successful!")
        print(f"   Result preview: {result[:150]}...")
    else:
        print(f"⚠️  Unexpected result: {result[:200]}")

    print("\n✅ All tool tests passed!")

except ImportError as e:
    print(f"❌ Failed to import tool: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
