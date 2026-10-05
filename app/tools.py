# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import json
import os
import uuid
import urllib.request
import urllib.parse
import datetime
from zoneinfo import ZoneInfo
from google import genai
from google.genai import types
from google.cloud import firestore, storage
from google.adk.tools import ToolContext

# Hardcoded constants as requested for Firestore and Cloud Storage bucket
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-fbbc64cbc886"
GCS_BUCKET_NAME = "travel-concierge-assets-03fbbc"


def _get_firestore_client() -> firestore.Client:
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


async def generate_destination_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates a custom travel postcard or destination image using gemini-3.1-flash-lite-image in the global region.

    Saves the image artifact to ADK ToolContext and uploads the raw image bytes to the public Cloud Storage bucket.

    Args:
        prompt: Description of the destination scene or postcard image to generate (e.g. "Kyoto bamboo grove in morning light").
        tool_context: ADK ToolContext automatically provided by the agent framework.

    Returns:
        Public HTTPS URL of the generated image stored in Cloud Storage.
    """
    try:
        # Initialize GenAI client specifically for global region
        client = genai.Client(location="global")

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        # Extract generated image part and binary bytes
        part = response.candidates[0].content.parts[0]
        mime_type = part.inline_data.mime_type if part.inline_data else "image/jpeg"
        image_bytes = part.inline_data.data if part.inline_data else b""

        ext = "png" if "png" in mime_type.lower() else "jpg"
        filename = f"postcard_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact with tool_context for Playground Artifacts panel
        await tool_context.save_artifact(filename=filename, artifact=part)

        # 2. Upload image bytes directly to public GCS bucket (without writing local file)
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating image: {str(e)}"


async def generate_destination_video(prompt: str, tool_context: ToolContext) -> str:
    """Generates a short travel promo or destination scene video using gemini-omni-flash-preview in the global region.

    Saves the video artifact to ADK ToolContext and uploads the raw video bytes to the public Cloud Storage bucket.

    Args:
        prompt: Description of the destination scene or promo video to generate (e.g. "Scenic 3-second promo video of Kyoto bamboo forest").
        tool_context: ADK ToolContext automatically provided by the agent framework.

    Returns:
        Public HTTPS URL of the generated video stored in Cloud Storage.
    """
    try:
        # Initialize GenAI client specifically for global region
        client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")

        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            response_format={"modalities": ["VIDEO"]},
        )

        output_video = getattr(interaction, "output_video", None)
        if not output_video or not output_video.data:
            return "Error: No video data returned from model."

        mime_type = output_video.mime_type or "video/mp4"
        data_str = output_video.data
        if isinstance(data_str, str):
            video_bytes = base64.b64decode(data_str)
        else:
            video_bytes = data_str

        ext = "mp4" if "mp4" in mime_type.lower() else "mov"
        filename = f"video_{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save artifact with tool_context for Playground Artifacts panel
        part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=part)

        # 2. Upload video bytes directly to public GCS bucket (without writing local file)
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating video: {str(e)}"


def fetch_live_exchange_rates(from_currency: str = "USD", to_currencies: str = "EUR,JPY,GBP,IDR,ISK") -> str:
    """Fetches real live currency exchange rates from a public exchange rate API (Frankfurter API).

    Args:
        from_currency: Base 3-letter currency code (e.g. "USD", "EUR", "GBP").
        to_currencies: Comma-separated target 3-letter currency codes (e.g. "EUR,JPY,GBP,IDR,ISK").

    Returns:
        JSON string containing live exchange rates and base date metadata.
    """
    base = from_currency.upper().strip()
    targets = ",".join([c.strip().upper() for c in to_currencies.split(",") if c.strip()])

    # Optionally read custom API key or custom endpoint from environment if set
    custom_key = os.getenv("EXCHANGE_RATE_API_KEY", "")

    try:
        url = f"https://api.frankfurter.app/latest?from={base}&to={targets}"
        req = urllib.request.Request(url, headers={"User-Agent": "TravelConciergeAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return json.dumps(data, indent=2)
            else:
                return json.dumps({"error": f"Public Exchange Rate API returned HTTP status {response.status}"})
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch live exchange rates: {str(e)}"})


def get_destination_local_time(city: str) -> str:
    """Retrieves the current local time and timezone for a travel destination city.

    Args:
        city: City name (e.g., "Tokyo", "Paris", "Bali", "Reykjavik", "Kyoto").

    Returns:
        Formatted local time string.
    """
    c = city.lower().strip()
    if "tokyo" in c or "kyoto" in c or "japan" in c:
        tz_name = "Asia/Tokyo"
    elif "bali" in c or "indonesia" in c:
        tz_name = "Asia/Makassar"
    elif "paris" in c or "france" in c:
        tz_name = "Europe/Paris"
    elif "reykjavik" in c or "iceland" in c:
        tz_name = "Atlantic/Reykjavik"
    elif "london" in c or "uk" in c:
        tz_name = "Europe/London"
    elif "new york" in c or "ny" in c:
        tz_name = "America/New_York"
    elif "san francisco" in c or "sf" in c:
        tz_name = "America/Los_Angeles"
    else:
        tz_name = "UTC"

    now = datetime.datetime.now(ZoneInfo(tz_name))
    return f"The current local time in {city} ({tz_name}) is {now.strftime('%Y-%m-%d %H:%M:%S %Z (UTC%z)')}."


def get_destinations_from_firestore(category: str = "all") -> str:
    """Reads travel destinations directly from the Firestore database.

    Args:
        category: Filter destinations by category ("culture", "beach", "adventure", "romance", or "all").

    Returns:
        JSON string containing matching destination documents from Firestore.
    """
    try:
        db = _get_firestore_client()
        collection_ref = db.collection("destinations")
        category_clean = category.lower().strip()

        if category_clean == "all":
            docs = collection_ref.stream()
        else:
            docs = collection_ref.where("category", "==", category_clean).stream()

        results = [doc.to_dict() for doc in docs]
        if not results and category_clean != "all":
            # Fallback to all stream if no exact category match
            all_docs = collection_ref.stream()
            results = [doc.to_dict() for doc in all_docs]

        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch destinations from Firestore: {str(e)}"})


def add_destination_to_firestore(
    destination_id: str,
    name: str,
    category: str,
    description: str,
    best_season: str,
    avg_daily_cost_usd: float,
    top_attractions: str
) -> str:
    """Writes a new travel destination document into the Firestore 'destinations' collection.

    Args:
        destination_id: Unique string identifier for the document (e.g., "kyoto", "sydney", "maui").
        name: Full display name of destination (e.g. "Sydney, Australia").
        category: Category type ("culture", "beach", "adventure", "romance", "nature").
        description: Engaging summary of the destination.
        best_season: Recommended time of year to visit.
        avg_daily_cost_usd: Estimated average daily cost per person in USD.
        top_attractions: Comma-separated list of top attraction highlights.

    Returns:
        JSON string confirmation of saved document.
    """
    try:
        db = _get_firestore_client()
        doc_ref = db.collection("destinations").document(destination_id.lower().strip())
        
        attractions_list = [attr.strip() for attr in top_attractions.split(",") if attr.strip()]
        doc_data = {
            "id": destination_id.lower().strip(),
            "name": name,
            "category": category.lower().strip(),
            "description": description,
            "best_season": best_season,
            "avg_daily_cost_usd": avg_daily_cost_usd,
            "top_attractions": attractions_list,
        }
        
        doc_ref.set(doc_data)
        return json.dumps({"status": "success", "message": f"Successfully added '{name}' to Firestore.", "data": doc_data}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to add destination to Firestore: {str(e)}"})


def save_trip_itinerary(
    trip_name: str,
    destination: str,
    num_days: int,
    total_budget_usd: float,
    notes: str = ""
) -> str:
    """Saves a planned travel itinerary to the Firestore 'trips' collection.

    Args:
        trip_name: Descriptive name for the trip (e.g. "Tokyo 7-Day Adventure").
        destination: Destination location name.
        num_days: Duration of the trip in days.
        total_budget_usd: Estimated total trip cost in USD.
        notes: Additional itinerary details, flight notes, or hotel selections.

    Returns:
        JSON string confirmation of saved trip.
    """
    try:
        db = _get_firestore_client()
        doc_id = trip_name.lower().replace(" ", "_")
        doc_ref = db.collection("trips").document(doc_id)
        
        trip_data = {
            "trip_name": trip_name,
            "destination": destination,
            "num_days": num_days,
            "total_budget_usd": total_budget_usd,
            "notes": notes,
        }
        
        doc_ref.set(trip_data)
        return json.dumps({"status": "success", "message": f"Successfully saved trip '{trip_name}' to Firestore.", "data": trip_data}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to save trip itinerary to Firestore: {str(e)}"})


def get_weather(location: str) -> str:
    """Retrieves current weather forecast summary for a travel location.

    Args:
        location: City or region name.

    Returns:
        Weather forecast string.
    """
    loc = location.lower()
    if "tokyo" in loc or "japan" in loc:
        return "Tokyo: 68°F (20°C), Partly Cloudy, mild breeze."
    elif "bali" in loc or "indonesia" in loc:
        return "Bali: 84°F (29°C), Tropical & Sunny, humidity 72%."
    elif "paris" in loc or "france" in loc:
        return "Paris: 62°F (17°C), Light Rain showers, pleasant."
    elif "reykjavik" in loc or "iceland" in loc:
        return "Reykjavik: 42°F (5°C), Crisp & Clear, high chance of Northern Lights tonight."
    elif "kyoto" in loc:
        return "Kyoto: 66°F (19°C), Clear skies, ideal for temple walks."
    else:
        return f"{location}: 72°F (22°C), Sunny with light clouds."


def calculate_trip_budget(num_days: int, num_travelers: int, daily_budget_per_person: float, flight_cost_per_person: float) -> str:
    """Calculates total trip budget breakdown and cost per traveler.

    Args:
        num_days: Duration of the trip in days.
        num_travelers: Number of people traveling.
        daily_budget_per_person: Estimated daily spending per person in USD (accommodation, food, activities).
        flight_cost_per_person: Round-trip flight cost per person in USD.

    Returns:
        Formatted trip budget summary string.
    """
    total_flights = flight_cost_per_person * num_travelers
    total_daily = daily_budget_per_person * num_days * num_travelers
    total_cost = total_flights + total_daily
    cost_per_person = total_cost / num_travelers if num_travelers > 0 else total_cost

    return json.dumps({
        "num_days": num_days,
        "num_travelers": num_travelers,
        "flight_cost_total": f"${total_flights:,.2f}",
        "daily_spending_total": f"${total_daily:,.2f}",
        "grand_total_usd": f"${total_cost:,.2f}",
        "cost_per_traveler_usd": f"${cost_per_person:,.2f}"
    }, indent=2)
