NEST Device Profile Configuration
=================================

The **NEST Device Profile** acts as a technical blueprint within ThingsBoard, ensuring that all physical and simulated nodes follow a standardized set of rules and communication protocols. It centralizes the logic for alarm generation and data transport security.

Technical Specifications
------------------------

* **Transport Protocol:** The profile is configured to use **MQTT** as the primary transport stack.
* **Data Format:** All incoming telemetry and outgoing commands are structured using **JSON**.
* **Provisioning Strategy:** It uses the **Allow Create New Devices** strategy, enabling the automated deployment of simulated nodes via the ``run_all.bat`` workflow.

Alarm Rules and Operational Logic
---------------------------------

The profile contains specialized rules to transform raw telemetry into actionable alerts for the farmer:

1. Environmental Bounds
~~~~~~~~~~~~~~~~~~~~~~~
* **Temperature Alarm:** Automatically triggers a "Warning" or "Critical" alarm if the temperature deviates from the optimal incubation range.
* **Humidity Alarm:** Monitors ambient moisture levels to protect egg quality, triggering alerts if values fall outside predefined thresholds.

2. Security and Productivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* **Unauthorized Access:** Generates an alarm if a tag is scanned that does not match an authorized Hen or Farmer UID.
* **System Inactivity:** Includes a "Device Inactivity" rule that alerts the farmer if a NEST node stops sending telemetry, indicating a potential hardware or connectivity failure.

3. Edge Status Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~
* **Attribute Sync:** Tracks the synchronization of **Shared Attributes** (such as the door state or RGB LED color) to ensure the Digital Twin accurately reflects the physical state of the nest.

Integration with Service Platforms
----------------------------------

The profile is linked to the **NEST Rule Chain**. This ensures that as soon as telemetry is received, it is processed to determine if an automated action is required, such as notifying the user via **Telegram** when a critical alarm is created.

