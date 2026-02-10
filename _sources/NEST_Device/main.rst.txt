NEST Device Firmware
====================

The **NEST (Next-generation Edge System for Tracking)** firmware is an ESP32-based IoT application designed for smart poultry farming. It integrates environmental monitoring, access control, and weight measurement using a multitasking approach powered by **FreeRTOS**.

Main Features
-------------

* **Real-time Environmental Monitoring**: Periodic reading of temperature and humidity via DHT22.
* **Access Control**: High-frequency RFID scanning (MFRC522) for hen and farmer identification.
* **Weight Measurement**: High-precision egg detection using a load cell and HX711 amplifier.
* **Remote Commanding**: Bidirectional communication with ThingsBoard for actuator control (Servos and RGB LED).
* **Fault Tolerance**: Concurrent error tracking for sensors and network connectivity.

Firmware Architecture
---------------------

The firmware utilizes **FreeRTOS** to manage two core concurrent tasks, ensuring that high-speed events (like RFID detection) do not interfere with periodic telemetry.

Task Management
^^^^^^^^^^^^^^^

* **taskTelemetry (Periodic)**: Executes every 10 seconds (default). It performs data fusion from all sensors and publishes a comprehensive JSON payload to the MQTT broker.
* **taskRFID (Async)**: Executes every 250ms. It provides "Instant Publish" capabilities, sending a telemetry update immediately upon detecting a new card to minimize latency for door operations.

Resource Synchronization
^^^^^^^^^^^^^^^^^^^^^^^^

To prevent race conditions and hardware conflicts, the system implements the following **Mutexes**:

* ``mqttMutex``: Synchronizes access to the Shared MQTT client and WiFi radio.
* ``spiMutex``: Manages the SPI bus contention between the MFRC522 RFID reader and other peripherals.

Technical Reference
-------------------

.. cpp:function:: String checkRFID()

   Scans for the presence of an RFID tag. It includes a forced Wakeup sequence to ensure tags are detected even if held continuously in front of the reader.
   
   :return: The UID of the detected card in Hex format, or an empty string if none.

.. cpp:function:: void setLedColor(String color)

   Updates the color of the Common Anode RGB LED.
   
   :param color: The target color name (off, red, green, blue, on).

.. cpp:function:: void operateDoor(String command)

   Drives two SG90 servomotors to specific angles to simulate a physical door opening or closing.
   
   :param command: "open" to trigger the entry position, otherwise "closed".

.. cpp:function:: void mqttCallback(char* topic, byte* payload, unsigned int length)

   Processes incoming JSON messages from ThingsBoard. It extracts **Shared Attributes** to remotely update the door state, LED feedback, or the telemetry reporting frequency.

