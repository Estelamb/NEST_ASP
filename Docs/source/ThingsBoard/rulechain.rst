NEST Rule-Chain
===============

NEST Rule Chain Logic
=====================

The **NEST Rule Chain** acts as the central intelligence of the system within ThingsBoard. It processes all incoming data from the nodes (physical or simulated), manages the "Digital Twin" state, and automates responses based on environmental and security conditions.

Core Workflow
-------------

1. Data Validation and Filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* **Telemetry Check:** The system first filters incoming messages to ensure they contain essential keys such as ``temperature``, ``humidity``, ``weight``, and ``uid``.
* **Message Type Switching:** The rule chain distinguishes between standard telemetry (sensor data), attribute updates (device settings), and RPC (Remote Procedure Call) requests.

2. Edge Intelligence & Digital Twin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The rule chain manages the state of the nest autonomously:

* **Incubation Monitoring:** It evaluates temperature and humidity against predefined thresholds to ensure the health of the eggs.
* **Weight & Identity Logic:** A critical logic flow correlates **Weight** (egg detection) with **UID** (hen identification). If an egg is detected and the hen leaves the nest, the system automatically updates the ``servo`` and ``lock`` attributes to secure the nest.
* **Attribute Synchronization:** Any change in the "Server-side Attributes" is automatically pushed to the physical ESP32 or the simulation node, ensuring the hardware stays in sync with the cloud logic.

3. Alarm Management
~~~~~~~~~~~~~~~~~~~
* **Dynamic Thresholds:** The system compares incoming data against high and low limits. If a value (like temperature) exceeds these limits, an alarm is created or updated.
* **Alarm Life Cycle:** The logic handles the creation of alarms and ensures they are cleared once the telemetry returns to normal operating ranges.

4. External Notifications
~~~~~~~~~~~~~~~~~~~~~~~~~
The rule chain includes integration for external alerts:

* **Telegram Integration:** When a critical event is detected (e.g., a security breach or extreme temperature), the rule chain triggers a notification to the farmer via a Telegram Bot, providing real-time updates outside the dashboard.

Technical Nodes
---------------
The implementation relies on several specialized nodes:

* **Script Nodes:** Used for parsing complex JSON data and calculating the nest status.
* **Save Timeseries:** To store historical data for the dashboard charts.
* **Rule Chain Transitions:** Complex branching based on "Success", "True/False", and "Failure" results to ensure robust error handling.


.. literalinclude:: nest_rulechain.json
   :language: json