# HeyPico Maps - Local LLM with Google Maps Integration

AI assistant powered by Llama 3.3 70B that can search for places, restaurants, and locations using Google Maps API.

## Features

- 🤖 Local LLM processing (complete privacy)
- 🗺️ Google Maps integration
- 📍 Place search with ratings
- 🧭 Turn-by-turn directions
- 🔒 Secure API key management
- 🐳 Docker Compose deployment

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd heypico-maps

# Copy environment template
cp .env.example .env

# Add your Google Maps API keys to .env

# Start services
docker compose up -d

# Pull LLM model
docker exec -it heypico-ollama ollama pull llama3.3:70b

# Access UI
open http://localhost:3000
```

## Documentation

- [Setup Guide](docs/SETUP.md)
- [API Documentation](docs/API_USAGE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation Plan](plan/00-OVERVIEW.md)

## Technology Stack

- **LLM**: Llama 3.3 70B via Ollama
- **Frontend**: Open WebUI
- **Backend**: FastAPI (Python)
- **APIs**: Google Maps Platform
- **Deployment**: Docker Compose

## License

MIT

## Author

HeyPico Team
