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

from google.cloud import firestore

# Hardcode project ID to ensure compatibility on Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-fbbc64cbc886"

SEED_DESTINATIONS = [
    {
        "id": "tokyo",
        "name": "Tokyo, Japan",
        "category": "culture",
        "description": "Vibrant metropolis blending futuristic skyscrapers with historic temples and world-class culinary experiences.",
        "best_season": "Spring / Autumn",
        "avg_daily_cost_usd": 150,
        "top_attractions": ["Shinjuku Gyoen", "Senso-ji Temple", "Shibuya Crossing", "Tsukiji Outer Market"],
    },
    {
        "id": "kyoto",
        "name": "Kyoto, Japan",
        "category": "culture",
        "description": "Ancient imperial capital famous for classical Buddhist temples, gardens, imperial palaces, and wooden houses.",
        "best_season": "Spring / Autumn",
        "avg_daily_cost_usd": 130,
        "top_attractions": ["Fushimi Inari Shrine", "Kinkaku-ji (Golden Pavilion)", "Arashiyama Bamboo Grove"],
    },
    {
        "id": "bali",
        "name": "Bali, Indonesia",
        "category": "beach",
        "description": "Tropical paradise featuring volcanic mountains, iconic rice paddies, beaches, and coral reefs.",
        "best_season": "May to October",
        "avg_daily_cost_usd": 75,
        "top_attractions": ["Ubud Monkey Forest", "Uluwatu Temple", "Tegallalang Rice Terraces", "Seminyak Beach"],
    },
    {
        "id": "paris",
        "name": "Paris, France",
        "category": "romance",
        "description": "Global center for art, fashion, gastronomy, and culture with iconic architecture and historic landmarks.",
        "best_season": "Spring / Summer",
        "avg_daily_cost_usd": 200,
        "top_attractions": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Montmartre"],
    },
    {
        "id": "reykjavik",
        "name": "Reykjavik, Iceland",
        "category": "adventure",
        "description": "Gateway to geothermal wonders, stunning glaciers, volcanic landscapes, and Northern Lights.",
        "best_season": "Winter (Northern Lights) / Summer (Midnight Sun)",
        "avg_daily_cost_usd": 220,
        "top_attractions": ["Golden Circle", "Blue Lagoon", "Hallgrimskirkja", "Black Sand Beach"],
    },
]


def seed_firestore():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("destinations")

    for dest in SEED_DESTINATIONS:
        doc_id = dest["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(dest)
        print(f"Seeded document 'destinations/{doc_id}': {dest['name']}")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed_firestore()
