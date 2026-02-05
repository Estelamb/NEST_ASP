import logging
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
)

from api_client import APIClient
from config import (
    TELEGRAM_TOKEN, API_BASE_URL, 
    NESTS
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize API client
api_client = APIClient(API_BASE_URL)

# --- HELPER FUNCTIONS ---

def get_current_nest_info(context=None):
    """
    Retrieves the currently selected NEST information from the user data.

    :param context: The context object provided by the telegram.ext handler.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE, optional
    :return: A tuple containing the (nest_id, nest_info_dict) or (None, None) if not found.
    :rtype: tuple
    """
    if context and context.user_data and 'current_nest' in context.user_data:
        nest_id = context.user_data['current_nest']
        if nest_id in NESTS:
            return nest_id, NESTS[nest_id]
    
    return None, None

def require_nest_selected(func):
    """
    Decorator that ensures a NEST has been selected before executing a command.
    If no NEST is selected, it prompts the user to select one using /nest.

    :param func: The asynchronous function to be wrapped.
    :type func: callable
    :return: The wrapped asynchronous function.
    :rtype: callable
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        nest_id, nest_info = get_current_nest_info(context)
        
        if not nest_info:
            if update.callback_query:
                query = update.callback_query
                if query.data.startswith("nest_"):
                    parts = query.data.split("_")
                    if len(parts) >= 2:
                        potential_nest_id = parts[1]
                        if potential_nest_id in NESTS:
                            nest_id = potential_nest_id
                            nest_info = NESTS[nest_id]
            
            if not nest_info:
                await update.message.reply_text(
                    "⚠️ *First select a NEST*\n\n"
                    "Use: `/nest` or /select_nest",
                    parse_mode='Markdown'
                )
                return
        
        if context:
            context.user_data['current_nest'] = nest_id
        
        return await func(update, context, nest_info)
    
    return wrapper

def require_login(func):
    """
    Decorator that checks if the user is authenticated with the API client.
    If not logged in, it sends an alert for callback queries or a warning message.

    :param func: The asynchronous function to be wrapped.
    :type func: callable
    :return: The wrapped asynchronous function.
    :rtype: callable
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not api_client.is_logged_in():
            if update.callback_query:
                await update.callback_query.answer("You must login first!", show_alert=True)
            else:
                await update.message.reply_text(
                    "🔒 *Login required*\n\n"
                    "You must login first with `/login username password`",
                    parse_mode='Markdown'
                )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

# --- NEST SELECTION COMMANDS ---

async def select_nest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows a menu with available NEST devices for the user to select.

    :param update: The update object representing the incoming command.
    :type update: telegram.Update
    :param context: The context for the current conversation.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    keyboard = []
    
    nest_keys = list(NESTS.keys())
    for i in range(0, len(nest_keys), 2):
        row = []
        if i < len(nest_keys):
            nest1 = nest_keys[i]
            row.append(InlineKeyboardButton(
                NESTS[nest1]['display_name'], 
                callback_data=f"select_{nest1}"
            ))
        if i + 1 < len(nest_keys):
            nest2 = nest_keys[i + 1]
            row.append(InlineKeyboardButton(
                NESTS[nest2]['display_name'], 
                callback_data=f"select_{nest2}"
            ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❓ NESTS Information", callback_data="nest_info")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏠 *Select a NEST:*\n\n"
        "Choose the device you want to control:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Routes all callback query data from inline buttons to their respective handlers.

    :param update: The update object containing the callback query.
    :type update: telegram.Update
    :param context: The context for the current conversation.
    :type context: telegram.ext.ContextTypes.DEFAULT_TYPE
    """
    query = update.callback_query
    await query.answer()
    
    if query.data == "nest_info":
        info_text = "📋 *NESTS Information:*\n\n"
        for nest_id, nest_info in NESTS.items():
            info_text += f"*{nest_info['display_name']}*\n"
        
        info_text += "Tap a NEST to select it."
        
        await query.edit_message_text(
            info_text,
            parse_mode='Markdown',
            reply_markup=query.message.reply_markup
        )
        return
    
    if query.data.startswith("select_"):
        nest_id = query.data.replace("select_", "")
        
        if nest_id in NESTS:
            context.user_data['current_nest'] = nest_id
            nest_info = NESTS[nest_id]
            
            await show_nest_main_menu(query, nest_id, nest_info)
        return
    
    if query.data.startswith("menu_"):
        nest_id = query.data.split("_")[1]
        action = query.data.split("_")[2]
        
        if nest_id in NESTS:
            nest_info = NESTS[nest_id]
            context.user_data['current_nest'] = nest_id
            
            if action == "telemetry":
                await handle_telemetry_button(query, context, nest_info)
            elif action == "door":
                await handle_door_button(query, context, nest_info)
            elif action == "temperature":
                await handle_temperature_button(query, context, nest_info)
            elif action == "humidity":
                await handle_humidity_button(query, context, nest_info)
            elif action == "rgb":
                await handle_rgb_button(query, context, nest_info)
            elif action == "eggs":
                await handle_eggs_button(query, context, nest_info)
            elif action == "location":
                await handle_location_button(query, context, nest_info)
            elif action == "status":
                await handle_status_button(query, context, nest_info)
            elif action == "back":
                await select_nest_command_from_query(query)
    
    if query.data.startswith("door_"):
        nest_id = query.data.split("_")[1]
        action = query.data.split("_")[2]
        
        if nest_id in NESTS:
            nest_info = NESTS[nest_id]
            await handle_door_action(query, context, nest_info, action)
    
    if query.data.startswith("egg_"):
        nest_id = query.data.split("_")[1]
        egg_type = query.data.split("_")[2]
        
        if nest_id in NESTS:
            nest_info = NESTS[nest_id]
            context.user_data['current_nest'] = nest_id
            await handle_egg_type_selection(query, context, nest_info, egg_type)

async def show_nest_main_menu(query, nest_id, nest_info):
    """
    Generates and displays the main feature menu for a selected NEST.

    :param query: The callback query to edit with the menu.
    :type query: telegram.CallbackQuery
    :param nest_id: The ID of the current NEST.
    :type nest_id: str
    :param nest_info: Metadata dictionary for the NEST.
    :type nest_info: dict
    """
    keyboard = [
        [InlineKeyboardButton("📊 Telemetry", callback_data=f"menu_{nest_id}_telemetry")],
        [InlineKeyboardButton("🚪 Door Control", callback_data=f"menu_{nest_id}_door")],
        [InlineKeyboardButton("🌡️ Temperature", callback_data=f"menu_{nest_id}_temperature")],
        [InlineKeyboardButton("💧 Humidity", callback_data=f"menu_{nest_id}_humidity")],
        [InlineKeyboardButton("🎨 RGB", callback_data=f"menu_{nest_id}_rgb")],
        [InlineKeyboardButton("🥚 Eggs", callback_data=f"menu_{nest_id}_eggs")],
        [InlineKeyboardButton("📍 Location", callback_data=f"menu_{nest_id}_location")],
        [
            InlineKeyboardButton("🔄 Change NEST", callback_data=f"menu_{nest_id}_back"),
            InlineKeyboardButton("📋 Status", callback_data=f"menu_{nest_id}_status")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *{nest_info['display_name']} Selected*\n\n"
        f"Choose an option:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def select_nest_command_from_query(query):
    """
    Redraws the NEST selection menu from an existing callback query (Back button logic).

    :param query: The callback query to edit.
    :type query: telegram.CallbackQuery
    """
    keyboard = []
    
    nest_keys = list(NESTS.keys())
    for i in range(0, len(nest_keys), 2):
        row = []
        if i < len(nest_keys):
            nest1 = nest_keys[i]
            row.append(InlineKeyboardButton(
                NESTS[nest1]['display_name'], 
                callback_data=f"select_{nest1}"
            ))
        if i + 1 < len(nest_keys):
            nest2 = nest_keys[i + 1]
            row.append(InlineKeyboardButton(
                NESTS[nest2]['display_name'], 
                callback_data=f"select_{nest2}"
            ))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❓ NESTS Information", callback_data="nest_info")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏠 *Select a NEST:*\n\n"
        "Choose the device you want to control:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# --- BUTTON HANDLERS ---

async def handle_telemetry_button(query, context, nest_info):
    """
    Handles the telemetry view when triggered from an inline button.

    :param query: The callback query.
    :param context: The context object.
    :param nest_info: The current NEST information dictionary.
    """
    if not api_client.is_logged_in():
        await query.answer("You must login first!", show_alert=True)
        return
    
    await query.edit_message_text(f"📡 Getting telemetry from {nest_info['display_name']}...")
    
    telemetry_data = api_client.get_telemetry(nest_info['device_id'])
    
    if telemetry_data:
        response_text = f"📊 *Telemetry Data - {nest_info['display_name']}:*\n\n"
        
        for key, values in telemetry_data.items():
            if values:
                latest = values[-1]
                timestamp = latest.get('ts', '')
                value = latest.get('value', 'N/A')
                
                time_str = ""
                if timestamp:
                    try:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        time_str = str(timestamp)
                
                emoji = "📊"
                if key == 'temperature':
                    emoji = "🌡️"
                elif key == 'humidity':
                    emoji = "💧"
                elif key == 'uid':
                    emoji = "🆔"
                elif key == 'weight':
                    emoji = "⚖️"
                
                response_text += f"{emoji} *{key.capitalize()}*: `{value}`\n"
                if time_str:
                    response_text += f"   🕐 _Last update: {time_str}_\n"
                response_text += "\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"❌ *Error getting telemetry from {nest_info['display_name']}*\n\n"
            "Could not retrieve data.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_door_button(query, context, nest_info):
    """
    Handles the door control menu display.

    :param query: The callback query.
    :param context: The context object.
    :param nest_info: The current NEST information.
    """
    keyboard = [
        [InlineKeyboardButton("🚪 Get Status", callback_data=f"door_{context.user_data['current_nest']}_get")],
        [InlineKeyboardButton("🔓 Open Door", callback_data=f"door_{context.user_data['current_nest']}_open")],
        [InlineKeyboardButton("🔒 Close Door", callback_data=f"door_{context.user_data['current_nest']}_close")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🚪 *Door Control - {nest_info['display_name']}*\n\n"
        "Choose an action:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_door_action(query, context, nest_info, action):
    """
    Sends door control commands to the API and updates the UI with the result.

    :param query: The callback query.
    :param context: The context object.
    :param nest_info: The current NEST information.
    :param action: The string action ('get', 'open', 'close').
    :type action: str
    """
    if action == "get":
        await query.edit_message_text(f"🚪 Getting door status from {nest_info['display_name']}...")
        
        door_data = api_client.get_door_status(nest_info['access_token'])
        
        if door_data and 'shared' in door_data and 'door' in door_data['shared']:
            door_status = door_data['shared']['door']
            
            emoji = "🔓" if door_status in ["open", "opened"] else "🔒"
            status_text = "OPEN" if door_status in ["open", "opened"] else "CLOSED"
            
            response_text = (
                f"{emoji} *Door Status - {nest_info['display_name']}:*\n\n"
                f"• **Status:** `{status_text}`\n"
                f"• **Value:** `{door_status}`\n"
            )
        else:
            response_text = f"❌ *Error getting door status from {nest_info['display_name']}*\n\nCould not retrieve status."
    
    elif action in ["open", "close"]:
        if not api_client.is_logged_in():
            await query.answer("You must login first!", show_alert=True)
            return
        
        door_status = "open" if action == "open" else "closed"
        emoji = "🔓" if action == "open" else "🔒"
        
        await query.edit_message_text(
            f"{emoji} {'Opening' if action == 'open' else 'Closing'} door on {nest_info['display_name']}...\n"
            f"⏳ Verifying change..."
        )
        
        success, message = api_client.set_door_status(nest_info['access_token'], door_status)
        
        if success:
            response_text = f"✅ *DOOR {'OPENED' if action == 'open' else 'CLOSED'} - {nest_info['display_name']}*\n\n{message}"
        else:
            response_text = f"❌ *Error updating door status on {nest_info['display_name']}*\n\n{message}"
    
    keyboard = [
        [InlineKeyboardButton("🚪 Door Control", callback_data=f"menu_{context.user_data['current_nest']}_door")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        response_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_temperature_button(query, context, nest_info):
    """
    Displays current temperature thresholds and instructions to modify them.
    """
    await query.edit_message_text(f"🌡️ Getting temperature settings from {nest_info['display_name']}...")
    
    temp_data = api_client.get_temperature_attributes(nest_info['access_token'])
    
    if temp_data:
        max_temp = temp_data.get('maxTemp', 'NaN')
        min_temp = temp_data.get('minTemp', 'NaN')
        
        response_text = (
            f"🌡️ *Temperature Settings - {nest_info['display_name']}:*\n\n"
            f"• **Max Temperature:** `{max_temp}°C`\n"
            f"• **Min Temperature:** `{min_temp}°C`\n\n"
            "*Use commands to modify:*\n"
            "`/temperature max VALUE`\n"
            "`/temperature min VALUE`\n\n"
            "*Requires login*"
        )
    else:
        response_text = f"❌ *Error getting temperature settings from {nest_info['display_name']}*\n\nCould not retrieve data."
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        response_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_humidity_button(query, context, nest_info):
    """
    Displays current humidity thresholds.
    """
    await query.edit_message_text(f"💧 Getting humidity settings from {nest_info['display_name']}...")
    
    hum_data = api_client.get_humidity_attributes(nest_info['access_token'])
    
    if hum_data:
        max_hum = hum_data.get('maxHum', 'NaN')
        min_hum = hum_data.get('minHum', 'NaN')
        
        response_text = (
            f"💧 *Humidity Settings - {nest_info['display_name']}:*\n\n"
            f"• **Max Humidity:** `{max_hum}%`\n"
            f"• **Min Humidity:** `{min_hum}%`\n\n"
            "*Use commands to modify:*\n"
            "`/humidity max VALUE`\n"
            "`/humidity min VALUE`\n\n"
            "*Requires login*"
        )
    else:
        response_text = f"❌ *Error getting humidity settings from {nest_info['display_name']}*\n\nCould not retrieve data."
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        response_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_rgb_button(query, context, nest_info):
    """
    Displays the current RGB light status.
    """
    await query.edit_message_text(f"🎨 Getting RGB status from {nest_info['display_name']}...")
    
    current_rgb = api_client.get_rgb_attribute(nest_info['access_token'])
    
    if current_rgb:
        emoji_map = {'off': '⚫', 'red': '🔴', 'green': '🟢', 'blue': '🔵'}
        emoji = emoji_map.get(current_rgb.lower(), '🎨')
        
        response_text = (
            f"{emoji} *Current RGB Status - {nest_info['display_name']}:*\n\n"
            f"• **Value:** `{current_rgb}`\n"
        )
    else:
        response_text = f"❌ *Could not get RGB status from {nest_info['display_name']}*\n\nThe attribute might not be configured."
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        response_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_eggs_button(query, context, nest_info):
    """
    Displays egg counter and weight information, with options to change egg type.
    """
    await query.edit_message_text(f"🥚 Getting eggs information from {nest_info['display_name']}...")
    
    eggs_value = api_client.get_eggs_attribute(nest_info['access_token'])
    egg_type = api_client.get_egg_type(nest_info['access_token'])
    weight_data = api_client.get_weight_attributes(nest_info['access_token'])
    
    if eggs_value is not None:
        response_text = (
            f"🥚 *Eggs Information - {nest_info['display_name']}:*\n\n"
            f"• **Count:** `{eggs_value}`\n"
        )
        
        if egg_type != "Unknown":
            response_text += f"• **Egg Type:** `{egg_type}`\n"
        
        if weight_data:
            avg_weight = weight_data.get('avgWeight', 'NaN')
            min_weight = weight_data.get('minWeight', 'NaN')
            response_text += f"• **Avg Weight:** `{avg_weight}g`\n"
            response_text += f"• **Min Weight:** `{min_weight}g`\n"
        
        response_text += "\n"
        
        if api_client.is_logged_in():
            response_text += "*Change egg type:*"
            keyboard = [
                [
                    InlineKeyboardButton("🐔 Hen (63g avg)", callback_data=f"egg_{context.user_data['current_nest']}_hen"),
                    InlineKeyboardButton("🐦 Quail (11g avg)", callback_data=f"egg_{context.user_data['current_nest']}_quail")
                ],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]
            ]
        else:
            response_text += "*Login required to change egg type*"
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
        
    else:
        response_text = f"❌ *Could not get eggs information from {nest_info['display_name']}*\n\nThe 'eggs' attribute might not be configured."
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        response_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_egg_type_selection(query, context, nest_info, egg_type):
    """
    Updates the weight attributes based on selected egg type (Hen/Quail).
    """
    if not api_client.is_logged_in():
        await query.answer("You must login first!", show_alert=True)
        return
    
    egg_weights = {
        'hen': {'avg': 63, 'min': 50},
        'quail': {'avg': 11, 'min': 8}
    }
    
    weights = egg_weights.get(egg_type)
    if not weights:
        await query.answer("Invalid egg type!", show_alert=True)
        return
    
    await query.edit_message_text(
        f"🥚 Setting egg type to **{egg_type.capitalize()}** for {nest_info['display_name']}...\n\n"
        f"• Avg Weight: `{weights['avg']}g`\n"
        f"• Min Weight: `{weights['min']}g`\n\n"
        f"⏳ Verifying changes..."
    )
    
    success, message = api_client.set_weight_attributes(
        nest_info['access_token'], 
        weights['avg'], 
        weights['min']
    )
    
    if success:
        await query.edit_message_text(f"✅ *Egg type set to {egg_type.capitalize()}!*\n\n{message}", parse_mode='Markdown')
        await asyncio.sleep(1)
        await handle_eggs_button(query, context, nest_info)
    else:
        keyboard = [
            [
                InlineKeyboardButton("🐔 Hen", callback_data=f"egg_{context.user_data['current_nest']}_hen"),
                InlineKeyboardButton("🐦 Quail", callback_data=f"egg_{context.user_data['current_nest']}_quail")
            ],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ *Update issue for {egg_type.capitalize()} eggs*\n\n{message}\n\n"
            f"Please try again or check device connection.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_location_button(query, context, nest_info):
    """
    Displays current GPS coordinates and a Google Maps link.
    """
    await query.edit_message_text(f"📍 Getting location from {nest_info['display_name']}...")
    
    location_data = api_client.get_location_attributes(nest_info['access_token'])
    
    if location_data:
        lat = location_data.get('latitude', 'NaN')
        lon = location_data.get('longitude', 'NaN')
        
        map_link = ""
        try:
            if lat != 'NaN' and lon != 'NaN' and lat != 'Not defined' and lon != 'Not defined':
                lat_float = float(lat)
                lon_float = float(lon)
                map_url = f"https://maps.google.com/?q={lat_float},{lon_float}"
                map_link = f"\n\n[📍 View on Google Maps]({map_url})"
        except:
            pass
        
        response_text = (
            f"📍 *Device Location - {nest_info['display_name']}:*\n\n"
            f"• **Latitude:** `{lat}`\n"
            f"• **Longitude:** `{lon}`"
            f"{map_link}\n\n"
            f"*To update location, use:*\n"
            f"`/location set` - Share GPS location\n"
            f"`/location coordinates LAT LON` - Manual coordinates"
        )
    else:
        response_text = f"❌ *Error getting location from {nest_info['display_name']}*\n\nThe device doesn't have location configured."
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        response_text,
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def handle_status_button(query, context, nest_info):
    """
    Provides a quick summary of the device connection and session state.
    """
    status_text = f"📡 *System Status - {nest_info['display_name']}:*\n\n"
    
    if api_client.is_logged_in():
        status_text += "✅ *API Session:* **Active**\n"
        if context.user_data and 'username' in context.user_data:
            status_text += f"   👤 User: `{context.user_data['username']}`\n"
    else:
        status_text += "❌ *API Session:* **Inactive**\n"
        status_text += "   Use `/login` to start session\n"
    
    door_data = api_client.get_door_status(nest_info['access_token'])
    if door_data and 'shared' in door_data and 'door' in door_data['shared']:
        door_status = door_data['shared']['door']
        emoji = "🔓" if door_status in ["open", "opened"] else "🔒"
        status_text += f"{emoji} *Door:* `{door_status}`\n"
    else:
        status_text += "🚪 *Door:* Not available\n"
    
    current_rgb = api_client.get_rgb_attribute(nest_info['access_token'])
    if current_rgb:
        emoji_map = {'off': '⚫', 'red': '🔴', 'green': '🟢', 'blue': '🔵'}
        emoji = emoji_map.get(current_rgb.lower(), '🎨')
        status_text += f"{emoji} *RGB:* `{current_rgb}`\n"
    else:
        status_text += "🎨 *RGB:* Not available\n"
    
    status_text += f"\n📱 *Device:*\n"
    status_text += f"   • Name: {nest_info['display_name']}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data=f"select_{context.user_data['current_nest']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        status_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def back_to_nest_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Navigation handler for returning to the main list of devices.
    """
    await select_nest_command(update, context)

# --- TEXT COMMANDS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Standard /start command to welcome users.
    """
    welcome_text = """
    🏠 *IoT Bot - NESTS Control*
    
    *First select a NEST:*
    /nest - Select NEST device
    
    *General commands:*
    /login username password - Login to API
    /logout - Logout
    /status - Connection status
    /help - Complete help
    
    *Once a NEST is selected:*
    • Telemetry, door, temperature, etc.
    
    *Available:* 4 different NESTS
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays the complete command manual.
    """
    help_text = """
    📚 *Help - IoT Bot*
    
    *Commands:*
    
    1. *Authentication:*
       • `/login username password` - Login
       • `/logout` - Logout
       • `/status` - Connection status
    
    2. *NEST Selection:*
       • `/nest` - Select a NEST device
       • `/back` - Return to NEST selection
    
    3. *Device data (require NEST selection):*
       • `/telemetry` - Humidity, temperature, uid, weight (requires login)
       • `/door get` - Door status
       • `/eggs` - Eggs count
       • `/rgb` - RGB status
    
    4. *Temperature control:*
       • `/temperature get` - Get min/max temperatures
       • `/temperature max VALUE` - Set max temperature (requires login)
       • `/temperature min VALUE` - Set min temperature (requires login)
    
    5. *Humidity control:*
       • `/humidity get` - Get min/max humidity
       • `/humidity max VALUE` - Set max humidity (requires login)
       • `/humidity min VALUE` - Set min humidity (requires login)
    
    6. *Location control:*
       • `/location get` - Get current location
       • `/location set` - Send GPS location (requires login)
       • `/location coordinates LAT LON` - Send coordinates manually (requires login)
    
    *Examples:*
    ```
    /login admin password123
    /nest
    [Select NEST2]
    /telemetry
    /door get
    /temperature get
    ```
    
    *API:* https://srv-iot.diatel.upm.es
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Authenticates the user using CLI-style arguments.
    """
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ *Usage:* `/login username password`\n\n"
            "*Example:* `/login admin password123`",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0]
    password = context.args[1]
    
    logger.info(f"Login attempt for user: {username}")
    
    await update.message.reply_text(f"🔐 Logging in as *{username}*...", parse_mode='Markdown')
    
    token = api_client.login(username, password)
    
    if token:
        context.user_data['username'] = username
        
        await update.message.reply_text(
            f"✅ *Login successful!*\n\n"
            f"• User: `{username}`\n"
            f"• You can now use protected commands.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Login failed*\n\n"
            "Please check your username and password.",
            parse_mode='Markdown'
        )

@require_nest_selected
@require_login
async def telemetry_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Command handler for retrieving device telemetry.
    """
    await update.message.reply_text(f"📡 Getting telemetry from {nest_info['display_name']}...")
    
    telemetry_data = api_client.get_telemetry(nest_info['device_id'])
    
    if telemetry_data:
        response_text = f"📊 *Telemetry Data - {nest_info['display_name']}:*\n\n"
        
        for key, values in telemetry_data.items():
            if values:
                latest = values[-1]
                timestamp = latest.get('ts', '')
                value = latest.get('value', 'N/A')
                
                time_str = ""
                if timestamp:
                    try:
                        dt = datetime.fromtimestamp(timestamp / 1000)
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        time_str = str(timestamp)
                
                emoji = "📊"
                if key == 'temperature':
                    emoji = "🌡️"
                elif key == 'humidity':
                    emoji = "💧"
                elif key == 'uid':
                    emoji = "🆔"
                elif key == 'weight':
                    emoji = "⚖️"
                
                response_text += f"{emoji} *{key.capitalize()}*: `{value}`\n"
                if time_str:
                    response_text += f"   🕐 _Last update: {time_str}_\n"
                response_text += "\n"
        
        await update.message.reply_text(response_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"❌ *Error getting telemetry from {nest_info['display_name']}*\n\n"
            "Could not retrieve data.",
            parse_mode='Markdown'
        )

@require_nest_selected
async def door_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Command handler for door operations.
    """
    if not context.args:
        await update.message.reply_text(
            f"🚪 *Door Control - {nest_info['display_name']}*\n\n"
            "*Commands:*\n"
            "• `/door get` - Get status\n"
            "• `/door open` - Open door (login)\n"
            "• `/door close` - Close door (login)",
            parse_mode='Markdown'
        )
        return
    
    command = context.args[0].lower()
    
    if command not in ['get', 'open', 'close']:
        await update.message.reply_text(
            "❌ *Invalid command*\n\n"
            "Allowed: `get`, `open`, `close`",
            parse_mode='Markdown'
        )
        return
    
    if command == 'get':
        await update.message.reply_text(f"🚪 Getting door status...")
        
        door_data = api_client.get_door_status(nest_info['access_token'])
        
        if door_data and 'shared' in door_data and 'door' in door_data['shared']:
            door_status = door_data['shared']['door']
            emoji = "🔓" if door_status in ["open", "opened"] else "🔒"
            status_text = "OPEN" if door_status in ["open", "opened"] else "CLOSED"
            
            await update.message.reply_text(
                f"{emoji} *Door Status - {nest_info['display_name']}:*\n\n"
                f"• **Status:** `{status_text}`\n"
                f"• **Value:** `{door_status}`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ *Error getting door status from {nest_info['display_name']}*",
                parse_mode='Markdown'
            )
        return
    
    if not api_client.is_logged_in():
        await update.message.reply_text(
            "🔒 *Login required*\n\n"
            "Use: `/login username password`",
            parse_mode='Markdown'
        )
        return
    
    door_status = "open" if command == "open" else "closed"
    emoji = "🔓" if command == "open" else "🔒"
    
    await update.message.reply_text(
        f"{emoji} {'Opening' if command == 'open' else 'Closing'} door...\n"
        f"⏳ Verifying change..."
    )
    
    success, message = api_client.set_door_status(nest_info['access_token'], door_status)
    
    if success:
        await update.message.reply_text(
            f"✅ *Door {'opened' if command == 'open' else 'closed'} successfully!*\n\n{message}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ *Error updating door status*\n\n{message}",
            parse_mode='Markdown'
        )

@require_nest_selected
async def temperature_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Command handler for temperature configuration.
    """
    if not context.args:
        await update.message.reply_text(
            f"🌡️ *Temperature Control - {nest_info['display_name']}*\n\n"
            "*Commands:*\n"
            "• `/temperature get` - Get temperatures\n"
            "• `/temperature max VALUE` - Set max (login)\n"
            "• `/temperature min VALUE` - Set min (login)",
            parse_mode='Markdown'
        )
        return
    
    command = context.args[0].lower()
    
    if command == 'get':
        await update.message.reply_text(f"🌡️ Getting temperature settings...")
        
        temp_data = api_client.get_temperature_attributes(nest_info['access_token'])
        
        if temp_data:
            max_temp = temp_data.get('maxTemp', 'NaN')
            min_temp = temp_data.get('minTemp', 'NaN')
            
            await update.message.reply_text(
                f"🌡️ *Temperature Settings - {nest_info['display_name']}:*\n\n"
                f"• **Max:** `{max_temp}°C`\n"
                f"• **Min:** `{min_temp}°C`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ *Error getting temperature*", parse_mode='Markdown')
        return
    
    if command in ['max', 'min']:
        if not api_client.is_logged_in():
            await update.message.reply_text("🔒 *Login required*", parse_mode='Markdown')
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(f"❌ *Missing value*\nUsage: `/temperature {command} VALUE`", parse_mode='Markdown')
            return
        
        try:
            value = float(context.args[1])
            attribute = 'maxTemp' if command == 'max' else 'minTemp'
            
            await update.message.reply_text(
                f"🌡️ Setting {command} temperature to {value}°C...\n"
                f"⏳ Verifying change..."
            )
            
            success, message = api_client.set_temperature_attribute(nest_info['access_token'], attribute, value)
            
            if success:
                await update.message.reply_text(f"✅ *{command.capitalize()} temperature updated to {value}°C!*\n\n{message}", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"⚠️ *Update issue*\n\n{message}", parse_mode='Markdown')
                
        except ValueError:
            await update.message.reply_text("❌ *Invalid value. Use a number.*", parse_mode='Markdown')

@require_nest_selected
async def humidity_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Command handler for humidity configuration.
    """
    if not context.args:
        await update.message.reply_text(
            f"💧 *Humidity Control - {nest_info['display_name']}*\n\n"
            "*Commands:*\n"
            "• `/humidity get` - Get humidity\n"
            "• `/humidity max VALUE` - Set max (login)\n"
            "• `/humidity min VALUE` - Set min (login)",
            parse_mode='Markdown'
        )
        return
    
    command = context.args[0].lower()
    
    if command == 'get':
        await update.message.reply_text(f"💧 Getting humidity settings...")
        
        hum_data = api_client.get_humidity_attributes(nest_info['access_token'])
        
        if hum_data:
            max_hum = hum_data.get('maxHum', 'NaN')
            min_hum = hum_data.get('minHum', 'NaN')
            
            await update.message.reply_text(
                f"💧 *Humidity Settings - {nest_info['display_name']}:*\n\n"
                f"• **Max:** `{max_hum}%`\n"
                f"• **Min:** `{min_hum}%`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ *Error getting humidity*", parse_mode='Markdown')
        return
    
    if command in ['max', 'min']:
        if not api_client.is_logged_in():
            await update.message.reply_text("🔒 *Login required*", parse_mode='Markdown')
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(f"❌ *Missing value*\nUsage: `/humidity {command} VALUE`", parse_mode='Markdown')
            return
        
        try:
            value = float(context.args[1])
            attribute = 'maxHum' if command == 'max' else 'minHum'
            
            await update.message.reply_text(
                f"💧 Setting {command} humidity to {value}%...\n"
                f"⏳ Verifying change..."
            )
            
            success, message = api_client.set_humidity_attribute(nest_info['access_token'], attribute, value)
            
            if success:
                await update.message.reply_text(f"✅ *{command.capitalize()} humidity updated to {value}%!*\n\n{message}", parse_mode='Markdown')
            else:
                await update.message.reply_text(f"⚠️ *Update issue*\n\n{message}", parse_mode='Markdown')
                
        except ValueError:
            await update.message.reply_text("❌ *Invalid value. Use a number.*", parse_mode='Markdown')

@require_nest_selected
async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Command handler for manual or GPS location updates.
    """
    if not context.args:
        await update.message.reply_text(
            f"📍 *Location Control - {nest_info['display_name']}*\n\n"
            "*Commands:*\n"
            "• `/location get` - Get location\n"
            "• `/location set` - Send GPS location (login)\n"
            "• `/location coordinates LAT LON` - Manual (login)",
            parse_mode='Markdown'
        )
        return
    
    command = context.args[0].lower()
    
    if command == 'get':
        await update.message.reply_text(f"📍 Getting location...")
        
        location_data = api_client.get_location_attributes(nest_info['access_token'])
        
        if location_data:
            lat = location_data.get('latitude', 'NaN')
            lon = location_data.get('longitude', 'NaN')
            
            map_link = ""
            try:
                if lat != 'NaN' and lon != 'NaN':
                    map_url = f"https://maps.google.com/?q={lat},{lon}"
                    map_link = f"\n[📍 View on Google Maps]({map_url})"
            except:
                pass
            
            await update.message.reply_text(
                f"📍 *Location - {nest_info['display_name']}:*\n\n"
                f"• **Lat:** `{lat}`\n"
                f"• **Lon:** `{lon}`"
                f"{map_link}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text("❌ *Error getting location*", parse_mode='Markdown')
        return
    
    if command in ['set', 'coordinates']:
        if not api_client.is_logged_in():
            await update.message.reply_text("🔒 *Login required*", parse_mode='Markdown')
            return
        
        if command == 'coordinates':
            if len(context.args) < 3:
                await update.message.reply_text("❌ *Usage: `/location coordinates LAT LON`*", parse_mode='Markdown')
                return
            
            try:
                lat = float(context.args[1])
                lon = float(context.args[2])
                
                await update.message.reply_text(
                    f"📍 Setting location to ({lat}, {lon})...\n"
                    f"⏳ Verifying..."
                )
                
                success, message = api_client.set_location_attributes(nest_info['access_token'], lat, lon)
                
                if success:
                    map_url = f"https://maps.google.com/?q={lat},{lon}"
                    await update.message.reply_text(
                        f"✅ *Location updated!*\n\n{message}\n\n"
                        f"[📍 View on Google Maps]({map_url})",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                else:
                    await update.message.reply_text(f"⚠️ *Update issue*\n\n{message}", parse_mode='Markdown')
                    
            except ValueError:
                await update.message.reply_text("❌ *Invalid coordinates*", parse_mode='Markdown')
        else:
            keyboard = [
                [KeyboardButton("📍 Share my location", request_location=True)],
                ["❌ Cancel"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(
                "📱 *Please share your location:*\n\n"
                "Tap the '📍 Share my location' button below",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

@require_nest_selected
async def eggs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Retrieves egg-related information via text command.
    """
    await update.message.reply_text(f"🥚 Getting eggs information from {nest_info['display_name']}...")
    
    eggs_value = api_client.get_eggs_attribute(nest_info['access_token'])
    egg_type = api_client.get_egg_type(nest_info['access_token'])
    weight_data = api_client.get_weight_attributes(nest_info['access_token'])
    
    if eggs_value is not None:
        response_text = (
            f"🥚 *Eggs Information - {nest_info['display_name']}:*\n\n"
            f"• **Count:** `{eggs_value}`\n"
        )
        
        if egg_type != "Unknown":
            response_text += f"• **Egg Type:** `{egg_type}`\n"
        
        if weight_data:
            avg_weight = weight_data.get('avgWeight', 'NaN')
            min_weight = weight_data.get('minWeight', 'NaN')
            response_text += f"• **Avg Weight:** `{avg_weight}g`\n"
            response_text += f"• **Min Weight:** `{min_weight}g`\n"
        
        response_text += f"\n*Use buttons in /nest menu to change egg type*"
        
        await update.message.reply_text(response_text, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"❌ *Could not get eggs count from {nest_info['display_name']}*\n\n"
            "The 'eggs' attribute might not be configured.",
            parse_mode='Markdown'
        )

async def rgb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command handler for RGB status.
    """
    nest_id, nest_info = get_current_nest_info(context)
    
    if not nest_info:
        await update.message.reply_text("⚠️ *First select a NEST*", parse_mode='Markdown')
        return
    
    await update.message.reply_text(f"🎨 Getting RGB status from {nest_info['display_name']}...")
    
    current_rgb = api_client.get_rgb_attribute(nest_info['access_token'])
    
    if current_rgb:
        emoji_map = {'off': '⚫', 'red': '🔴', 'green': '🟢', 'blue': '🔵'}
        emoji = emoji_map.get(current_rgb.lower(), '🎨')
        
        await update.message.reply_text(
            f"{emoji} *Current RGB Status - {nest_info['display_name']}:*\n\n"
            f"• **Value:** `{current_rgb}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ *Could not get RGB status from {nest_info['display_name']}*",
            parse_mode='Markdown'
        )

@require_nest_selected
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, nest_info):
    """
    Shows detailed connection status for the current NEST.
    """
    status_text = f"📡 *System Status - {nest_info['display_name']}:*\n\n"
    
    if api_client.is_logged_in():
        status_text += "✅ *API Session:* **Active**\n"
        if context.user_data and 'username' in context.user_data:
            status_text += f"   👤 User: `{context.user_data['username']}`\n"
    else:
        status_text += "❌ *API Session:* **Inactive**\n"
        status_text += "   Use `/login` to start session\n"
    
    door_data = api_client.get_door_status(nest_info['access_token'])
    if door_data and 'shared' in door_data and 'door' in door_data['shared']:
        door_status = door_data['shared']['door']
        emoji = "🔓" if door_status in ["open", "opened"] else "🔒"
        status_text += f"{emoji} *Door:* `{door_status}`\n"
    else:
        status_text += "🚪 *Door:* Not available\n"
    
    current_rgb = api_client.get_rgb_attribute(nest_info['access_token'])
    if current_rgb:
        emoji_map = {'off': '⚫', 'red': '🔴', 'green': '🟢', 'blue': '🔵'}
        emoji = emoji_map.get(current_rgb.lower(), '🎨')
        status_text += f"{emoji} *RGB:* `{current_rgb}`\n"
    else:
        status_text += "🎨 *RGB:* Not available\n"
    
    status_text += f"\n📱 *Device:*\n"
    status_text += f"   • Name: {nest_info['display_name']}\n"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Closes the session and clears local user data.
    """
    if api_client.is_logged_in():
        api_client.logout()
        context.user_data.clear()
        await update.message.reply_text("👋 *Session closed successfully*", parse_mode='Markdown')
    else:
        await update.message.reply_text("ℹ️ *No active session*", parse_mode='Markdown')

async def location_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Intercepts location shares from Telegram and updates the API.
    """
    location = update.message.location
    
    if location:
        nest_id, nest_info = get_current_nest_info(context)
        
        if nest_info and api_client.is_logged_in():
            lat = location.latitude
            lon = location.longitude
            
            await update.message.reply_text(
                f"📍 Setting location to ({lat:.6f}, {lon:.6f})...\n"
                f"⏳ Verifying..."
            )
            
            success, message = api_client.set_location_attributes(nest_info['access_token'], lat, lon)
            
            if success:
                map_url = f"https://maps.google.com/?q={lat},{lon}"
                await update.message.reply_text(
                    f"✅ *Location updated!*\n\n{message}\n\n"
                    f"[📍 View on Google Maps]({map_url})",
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(f"⚠️ *Update issue*\n\n{message}", parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Catches and logs unhandled exceptions within handlers.
    """
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ An error occurred. Please try again.")

# --- MAIN FUNCTION ---

def main():
    """
    The main entry point: configures the application and starts the polling service.
    """
    print(f"🤖 Starting IoT Bot...")
    print(f"🔑 Token: {TELEGRAM_TOKEN[:20]}...")
    print(f"🌐 API: {API_BASE_URL}")
    print(f"🏠 Available NESTS: {len(NESTS)}")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Text Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("logout", logout_command))
    
    # NEST Management
    application.add_handler(CommandHandler(["nest", "select_nest", "nests"], select_nest_command))
    application.add_handler(CommandHandler("back", back_to_nest_selection))
    
    # Feature Handlers
    application.add_handler(CommandHandler("telemetry", telemetry_command))
    application.add_handler(CommandHandler("door", door_command))
    application.add_handler(CommandHandler("temperature", temperature_command))
    application.add_handler(CommandHandler("humidity", humidity_command))
    application.add_handler(CommandHandler("location", location_command))
    application.add_handler(CommandHandler("eggs", eggs_command))
    application.add_handler(CommandHandler("rgb", rgb_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Interactive Handlers
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.LOCATION, location_message_handler))
    
    # Global Error Handler
    application.add_error_handler(error_handler)
    
    print("✅ Bot ready. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()