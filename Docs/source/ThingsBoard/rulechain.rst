NEST Rule Chain Logic
=====================

The **NEST Rule Chain** acts as the central intelligence of the system within ThingsBoard. It processes incoming sensor data, manages a **Finite State Machine (FSM)** for the nest's life cycle, and automates physical responses and external notifications.

Core Workflow
-------------

1. Message Classification and Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* **Message Type Switching:** The system first differentiates between ``Post telemetry``, ``Post attributes``, and other message types via the **Check Message Type** node.
* **Telemetry Validation:** The **Check Telemetry Message** node ensures incoming data contains necessary keys such as ``temperature``, ``humidity``, ``weight``, ``uid``, ``error``, or ``init``.
* **Hardware Error Handling:** If an ``error`` key is detected, the **Hardware Error** node creates a **CRITICAL** severity alarm including error details and a timestamp.

2. Digital Twin and FSM Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The system manages the nest's state autonomously through specialized logic:

* **Finite State Machine (FSM):** Using the ``state`` shared attribute, the **Check FSM State** and **Change FSM State** nodes control transitions between:
    * ``Waiting for Hen``: Remains until the UID matches the ``henUID``.
    * ``Hen Inside``: Active while the hen is detected.
    * ``Eggs Inside``: Triggered when the hen leaves and weight is detected; it calculates estimated eggs (``weight / avgWeight``) and sets the door to ``closed``.
    * ``Recolecting Eggs``: Allows access to the farmer (``validUID``) to reset the cycle.
* **Access Control (UID):** The **Open Door** node validates if the incoming ``uid`` matches the ``validUID``. If it matches, it toggles the ``door`` attribute and sets the LED ``rgb`` to **Green**. Unrecognized UIDs trigger the **Reject Door Use** node, setting the LED to **Red**.

3. Environmental Monitoring and Alarms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* **Dynamic Thresholds:** The **TempRange** and **HumRange** nodes fetch client attributes (``maxTemp``, ``minTemp``, etc.) to use as bounds.
* **Alarm Life Cycle:**
    * If temperature or humidity exceeds limits, **Temperature/Humidity Out of Bounds** alarms are created.
    * Alarms are automatically cleared when telemetry returns to the safe range.
* **Egg Notification:** The **Eggs Inside** filter triggers a specific alarm when the egg count is greater than zero.

4. External Notifications
~~~~~~~~~~~~~~~~~~~~~~~~~
* **Telegram Integration:** The rule chain connects to the Telegram API to send updates to chat ID ``1624527516``.
* **Real-time Alerts:** Notifications are sent for created/cleared environmental alarms and when eggs are detected or collected.

Technical Nodes
---------------
* **TBEL Scripting:** Extensively used for FSM transitions, egg estimation logic, and RGB status management.
* **Attribute Enrichment:** The **Get Attributes** nodes (TempRange, HumRange, UIDs, FSM) load configuration parameters into metadata before evaluation.
* **REST API Call:** Executes POST requests to the Telegram Bot.
* **Data Persistence:** Sensor data is saved via **Save Timeseries**, and device states are pushed to **SHARED_SCOPE** to sync with the physical hardware.