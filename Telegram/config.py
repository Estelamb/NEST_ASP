"""
Configuration module for the NEST IoT Telegram Bot.

This module contains the sensitive credentials, API endpoints, and 
the static registry of NEST devices used by the system.
"""

import os

# --- Telegram Bot Configuration ---
#: The unique authentication token provided by BotFather.
TELEGRAM_TOKEN = "8560879729:AAEHgMY-NWSmXSejZ07uWvmfoxJfSWEWbCw"

# --- API Endpoints ---
#: Root URL for the IoT Platform API.
API_BASE_URL = "https://srv-iot.diatel.upm.es"

#: Base URL for Device API v1 (Attributes and RPC).
API_V1_BASE_URL = f"{API_BASE_URL}/api/v1"

#: Base URL for Plugin-based APIs (Telemetry and Auth).
API_PLUGINS_BASE_URL = f"{API_BASE_URL}/api"

# --- NEST Device Registry ---
#: Dictionary mapping NEST identifiers to their technical credentials and display names.
#: Each entry contains a 'device_id' (UUID) and an 'access_token' (Secret).
NESTS = {
    'NEST1': {
        'device_id': "b5697430-f455-11f0-b5e6-d92120c3d6c8",
        'access_token': "hNxbPHZG1A1Rft0LHAVO",
        'display_name': "🥚NEST 1"
    },
    'NEST2': {
        'device_id': "e838eeb0-f458-11f0-b5e6-d92120c3d6c8",
        'access_token': "HUyaoCGGK6Pmu8nH3AWr",
        'display_name': "🥚NEST 2"
    },
    'NEST3': {
        'device_id': "ec94f5d0-f458-11f0-b5e6-d92120c3d6c8",
        'access_token': "XAWy4XST70V5WmEHwV7h",
        'display_name': "🥚NEST 3"
    },
    'NEST4': {
        'device_id': "f62effa0-f458-11f0-b5e6-d92120c3d6c8",
        'access_token': "kPfpX4EumVHdRR2icNjP",
        'display_name': "🥚NEST 4"
    }
}

# --- Runtime Session Variables ---
#: Stores the active JWT session token after a successful login.
USER_TOKEN = None

#: Stores the username of the currently authenticated user.
USERNAME = None

#: Stores the ID of the NEST device currently being controlled by the user.
CURRENT_NEST = None