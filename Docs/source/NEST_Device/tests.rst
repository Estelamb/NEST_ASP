Testing and Validation
======================

To ensure the reliability of the NEST system, each hardware peripheral underwent a dedicated **Unitary Testing** phase. This process verified that both the physical wiring and the specific software drivers worked correctly before integration into the main FreeRTOS multitasking firmware.

Hardware Unitary Tests
----------------------

The following procedures were executed to validate each component of the ecosystem:

* **DHT22 (Temperature and Humidity)**:
    * **Objective**: Data consistency and single-bus timing.
    * **Method**: Measured ambient conditions and verified output accuracy.
    * **Reference**: `ESP32 with DHT22 Guide <https://randomnerdtutorials.com/esp32-dht11-dht22-temperature-humidity-sensor-arduino-ide/>`_

* **Load Cell (HX711)**:
    * **Objective**: Accuracy and calibration of weight sensing for egg detection.
    * **Method**: Applied known weights and verified results in the Serial Monitor.
    * **Reference**: `ESP32 Load Cell and HX711 Tutorial <https://randomnerdtutorials.com/esp32-load-cell-hx711/>`_

* **RFID (MFRC522)**:
    * **Objective**: Successful UID identification and SPI bus stability.
    * **Method**: Scanned multiple tags to ensure unique hex strings were captured correctly.
    * **Reference**: `RFID MFRC522 Video Guide <https://www.youtube.com/watch?v=mZ-6WCRlwQs>`_

* **Servos (SG90)**:
    * **Objective**: Precision of movement and power stability under load.
    * **Method**: Commanded open and closed positions to simulate door operation.
    * **Reference**: `Servo Control Video Tutorial <https://www.youtube.com/watch?v=tTXw5qxRL04>`_

* **RGB LED**:
    * **Objective**: Color mixing and PWM duty cycle validation.
    * **Method**: Executed a test cycle to display Red, Green, and Blue colors for local feedback.

System Integration Results
--------------------------

After the unitary tests, a **System Integration Test** was conducted to confirm the end-to-end data pipeline. As shown in the local feedback logs, the system successfully transitions through states (e.g., from ``WAITING_FOR_HEN`` to ``HEN_INSIDE``) based on real-time sensor inputs. 

All telemetry data—including temperature, humidity, weight, and UID—is successfully synchronized with the **ThingsBoard** dashboard via secure MQTT.