# ruff: noqa
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

import json
from pathlib import Path

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    generate_destination_image,
    generate_destination_video,
    fetch_live_exchange_rates,
    get_destination_local_time,
    get_destinations_from_firestore,
    add_destination_to_firestore,
    save_trip_itinerary,
    get_weather,
    calculate_trip_budget,
)

# Constants for Memory Bank and Firestore
GCP_PROJECT_ID = "qwiklabs-gcp-03-fbbc64cbc886"
GCP_LOCATION = "us-central1"
MEMORY_BANK_ID = "331295497832628224"


def _get_agent_engine_resource_name() -> str | None:
    metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
    if metadata_file.exists():
        try:
            data = json.loads(metadata_file.read_text())
            return data.get("remote_agent_runtime_id")
        except Exception:
            pass
    return None


agent_engine_resource_name = _get_agent_engine_resource_name()
code_executor = AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_resource_name)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to extract durable facts, allergies, and user preferences into Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except ValueError:
        # Memory service not configured on standalone test runners
        pass
    return None


def memory_service_builder():
    """Memory service builder configured for future agent redeployments."""
    return VertexAiMemoryBankService(
        project=GCP_PROJECT_ID,
        location=GCP_LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

TRAVEL_CONCIERGE_INSTRUCTION = schema_manager.generate_system_prompt(
    role_description="You are Wanderlust AI, an expert, friendly Travel Concierge assistant.",
    workflow_description=(
        "Help travelers discover destinations from Firestore, add new destinations, save planned trip itineraries, "
        "look up live currency exchange rates, generate custom destination postcards/images, generate short travel promo videos, "
        "check current local times across cities, check weather forecasts, and compute trip budgets using Python code execution. "
        "Cross-Session Memory & Allergy Guidelines: Always pay strict attention to, record, and remember all user allergies "
        "(e.g., food allergies like peanuts/shellfish/gluten/dairy, medication allergies, or environmental allergies). "
        "Whenever the user mentions any allergy or dietary restriction, explicitly confirm that it has been recorded to their Memory Bank. "
        "When recommending restaurants, dining, activities, or travel itineraries, cross-check preloaded user memories and strictly ensure all suggestions accommodate their recorded allergies."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=TRAVEL_CONCIERGE_INSTRUCTION,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        generate_destination_image,
        generate_destination_video,
        fetch_live_exchange_rates,
        get_destination_local_time,
        get_destinations_from_firestore,
        add_destination_to_firestore,
        save_trip_itinerary,
        get_weather,
        calculate_trip_budget,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
