# My agent: Travel Concierge (Wanderlust AI)
One-liner: A conversational agent that helps travelers plan personalized trips with a catalog of curated destinations, hotels, and itineraries.

Tool coverage:
- Memory: Remembers user travel preferences (budget vs. luxury, dietary constraints, preferred airlines, past trips visited).
- Tools: Searches destinations, looks up hotel/attraction options, and fetches weather and local time.
- Catalog/UI: Renders destination cards, hotel/attraction option lists, and day-by-day itinerary tables using A2UI.
- Image gen: Generates custom destination preview postcards and scenic spot images using gemini-3.1-flash-lite-image.
- Sandbox: Runs Python calculations for total trip budget estimation, daily expense splitting, and currency conversions.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for budget calculations, Google Maps API integration, Cloud Trace for observability.
