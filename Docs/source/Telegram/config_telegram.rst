System Configuration
====================

The ``config`` module serves as the central repository for constants, credentials, and environment-specific settings. It defines the mapping between the physical IoT nodes and the logical representations used by the Telegram bot.

Component Overview
------------------

This module is structured into three main segments:

1. **Authentication Secrets**: Contains the Telegram Bot API token. It is the primary credential for the BotFather interface.
2. **Device Registry**: A static dictionary named ``NESTS`` that defines the hardware available in the system. Each entry links a human-readable display name to its internal UUID (``device_id``) and its private ``access_token``.
3. **Connectivity Settings**: Defines the URI structure for the backend platform, distinguishing between the standard Device API (v1) and the Plugins API for telemetry and authentication.

Session Variables
-----------------

The module also declares placeholders for runtime data such as ``USER_TOKEN``, ``USERNAME``, and ``CURRENT_NEST``. These variables are updated dynamically during the bot's execution to maintain the state of the user session.

Module Documentation
--------------------

.. automodule:: config
   :members:
   :undoc-members:
   :show-inheritance: