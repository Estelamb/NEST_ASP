ThingsBoard Dashboard Overview
==============================

The NEST dashboard serves as the primary interface for the real-time monitoring and management of poultry farm nodes. It integrates telemetry data, geospatial information, and remote control capabilities into a single cohesive view.

Main Components and Functionalities
-----------------------------------

1. Geospatial Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~
The dashboard utilizes an **OpenStreetMap** widget to track the physical location of each nest. By mapping ``latitude`` and ``longitude`` attributes, the system provides a clear geographical overview of the distributed nodes across the facility.

2. Environmental & Production Telemetry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Real-time data visualization is provided for critical environmental and production metrics:

* **Climate Monitoring:** Continuous tracking of **Temperature** and **Humidity** levels to ensure optimal conditions for the hens and eggs.
* **Production Detection:** Monitoring of the **Weight** sensor, which is the primary indicator of a new egg being laid.
* **Power Management:** Tracking of **Battery** levels for physical ESP32 nodes to prevent downtime.

3. Edge Control & Actuators
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The dashboard enables direct interaction with the hardware through **Shared Attributes** widgets:

* **Access Control:** Real-time status and manual override of the **RFID Lock**.
* **Door Automation:** Control and monitoring of the **Servo** motor that operates the nest entrance.
* **Digital Twin Logic:** Visualization of the autonomous edge logic, showing when a nest is "Locked" or "Unlocked" based on the presence of an egg and the absence of the hen.

4. Data Analysis & History
~~~~~~~~~~~~~~~~~~~~~~~~~~
* **Latest Values:** High-visibility cards showing the most recent telemetry received.
* **Time-Series Charts:** Historical graphs (e.g., weight trends or temperature fluctuations over the last 24 hours) to assist in long-term farm management and analysis.

5. Scalability & Entity Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Through the use of **Entity Aliases** (such as "Actual NEST"), the dashboard can dynamically switch between different physical devices or simulated Python nodes, allowing the system to scale easily as more nests are added to the farm.

