NEST Telegram Controller
========================

This module implements a high-level Telegram interface for the NEST IoT system. It acts as a bridge between the end-user and the physical or simulated NEST nodes, providing real-time telemetry, door control, and environmental configuration.

Operational Logic
-----------------

The bot operates using an **asynchronous event-driven architecture** managed by the `python-telegram-bot` library. It maintains a stateful session for each user via `user_data` to ensure commands are executed against the correct device.

* **Authentication Flow**: Users must authenticate via the ``/login`` command. The module uses a decorator-based system to restrict access to protected API endpoints.
* **Contextual Nest Selection**: Before interacting with sensors or actuators, a user must select a "Current NEST" from the available registry. This context is persisted across the session.
* **Menu Navigation**: The system uses a nested **Inline Keyboard** structure, allowing users to navigate from a global list of nests to specific device sub-menus (Telemetry, Door, Eggs, etc.).
* **Validation Decorators**: 
    * ``@require_login``: Ensures an active API token exists before sending PUT/POST requests.
    * ``@require_nest_selected``: Ensures a Target Device ID is present in the context.

Command Hierarchy
-----------------

The bot implements several command categories to manage the IoT ecosystem:

1.  **System Commands**: ``/start``, ``/help``, and ``/status`` for connectivity health checks.
2.  **Actuator Control**: 
    * **Door**: Toggle states between `open` and `closed`.
    * **RGB**: Visual status feedback control.
3.  **Environmental Tuning**: 
    * Set min/max thresholds for **Temperature** and **Humidity** to trigger automated alerts on the physical hardware.
4.  **Production Logging**: 
    * Update **Egg Types** (Hen vs. Quail) to adjust weight calculation logic for production metrics.

Code Documentation
------------------

.. automodule:: bot
   :members:
   :undoc-members:
   :show-inheritance: