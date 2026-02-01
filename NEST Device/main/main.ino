/**
 * @file main.ino
 * @brief ESP32 based IoT system for environmental monitoring, access control, and weight measurement.
 * * This system integrates MQTT (ThingsBoard), DHT22, HX711, RFID, and Servos using 
 * FreeRTOS tasks to manage concurrent sensor reading and telemetry.
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <MFRC522.h>
#include <SPI.h>
#include "HX711.h"
#include "DHT.h"
#include <ArduinoJson.h>

// --- CONFIGURATION ---
const char* ssid = "A56 de Estela";
const char* password = "4hk2fbthruumfqf";
const char* mqtt_server = "srv-iot.diatel.upm.es";
const char* token = "hNxbPHZG1Rft0LHAVO";

/** @brief Interval between periodic telemetry updates in milliseconds. */
int telemetryInterval = 10000;

// --- PIN DEFINITIONS ---
#define DHTPIN 15 
#define DHTTYPE DHT22
#define LOADCELL_DOUT_PIN 16
#define LOADCELL_SCK_PIN 4 

const int RED_PIN = 25;
const int GREEN_PIN = 26;
const int BLUE_PIN = 27;

#define SS_PIN     5   
#define RST_PIN    22  
#define SCK_PIN    18
#define MISO_PIN   19
#define MOSI_PIN   23

#define SERVO_1_PIN 2
#define SERVO_2_PIN 13

// --- OBJECTS ---
DHT dht(DHTPIN, DHTTYPE);
HX711 scale;
Servo s1;
Servo s2;
MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClientSecure espClient;
PubSubClient client(espClient);

// --- FREE RTOS & GLOBAL VARIABLES ---
/** @brief Mutex to prevent concurrent access to the MQTT client. */
SemaphoreHandle_t mqttMutex; 
/** @brief Mutex to prevent SPI bus contention between RFID and other peripherals. */
SemaphoreHandle_t spiMutex;  
/** @brief Stores the last detected RFID UID string. */
String lastUid = ""; 
/** @brief Calibration factor for the HX711 load cell. */
float calibration_factor = -531.02;

/**
 * @brief Checks for the presence of an RFID card.
 * * Detects cards even if they are held continuously in the reader's range 
 * by forcing a Wakeup sequence and halting the card after reading.
 * * @return String The UID of the detected card in Hex format, or empty string if none.
 */
String checkRFID() {
  String uidStr = "";
  byte bufferATQA[2];
  byte bufferSize = sizeof(bufferATQA);

  MFRC522::StatusCode result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);
  if (result != MFRC522::STATUS_OK) {
    result = mfrc522.PICC_WakeupA(bufferATQA, &bufferSize);
  }

  if (result == MFRC522::STATUS_OK) {
    if (mfrc522.PICC_ReadCardSerial()) {
      for (byte i = 0; i < mfrc522.uid.size; i++) {
        uidStr += (mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
        uidStr += String(mfrc522.uid.uidByte[i], HEX);
      }
      uidStr.toUpperCase();
      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();
    }
  }
  return uidStr;
}

/**
 * @brief Updates the frequency of telemetry publishing.
 * @param newPeriod The new interval in milliseconds (minimum 1000ms).
 */
void setPeriod(int newPeriod) {
  if (newPeriod >= 1000) {
    telemetryInterval = newPeriod;
    Serial.printf("[CONFIG] - New period: %d ms\n", telemetryInterval);
  }
}

/**
 * @brief Sets the color of the Common Anode RGB LED.
 * @param color Color name ("off", "red", "green", "blue", "on").
 */
void setLedColor(String color) {
  String colorLower = color;
  colorLower.toLowerCase();

  if (colorLower == "off") {
    analogWrite(RED_PIN, 255); analogWrite(GREEN_PIN, 255); analogWrite(BLUE_PIN, 255);
  } else if (colorLower == "green") {
    analogWrite(RED_PIN, 255); analogWrite(GREEN_PIN, 0);   analogWrite(BLUE_PIN, 255);
  } else if (colorLower == "red") {
    analogWrite(RED_PIN, 0);   analogWrite(GREEN_PIN, 255); analogWrite(BLUE_PIN, 255);
  } else if (colorLower == "blue") {
    analogWrite(RED_PIN, 255); analogWrite(GREEN_PIN, 255); analogWrite(BLUE_PIN, 0);
  } else if (colorLower == "on") {
    analogWrite(RED_PIN, 0);   analogWrite(GREEN_PIN, 0);   analogWrite(BLUE_PIN, 0);
  }

  Serial.print("[LED] - Changed color to: ");
  Serial.println(colorLower);
}

/**
 * @brief Moves two servos to simulate a door opening/closing.
 * @param command "open" to move servos to open position, else "close".
 */
void operateDoor(String command) {
  command.toLowerCase();

  int angle_s1 = (command == "open") ? 150 : 20;
  s1.write(angle_s1);
  delay(250);

  int angle_s2 = (command == "open") ? 20 : 150;
  s2.write(angle_s2);
  
  Serial.println("[DOOR] - Movement completed");
}

/**
 * @brief Handles incoming MQTT messages from ThingsBoard.
 * * Parses JSON payloads to extract shared attributes like door state, 
 * LED color, or telemetry reporting period.
 * * @param topic The MQTT topic string.
 * @param payload The message payload.
 * @param length Length of the payload.
 */
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<500> doc;
  if (deserializeJson(doc, payload, length)) return;
  JsonObject shared = doc.containsKey("shared") ? doc["shared"] : doc.as<JsonObject>();
  
  if (shared.containsKey("door")) operateDoor(shared["door"].as<String>());
  if (shared.containsKey("rgb")) setLedColor(shared["rgb"].as<String>());
  if (shared.containsKey("period")) setPeriod(shared["period"].as<int>());
}

/**
 * @brief Reconnects the MQTT client to the broker using the provided token.
 */
void reconnectMQTT() {
  while (!client.connected()) {
    if (client.connect(token, token, NULL)) {
      client.subscribe("v1/devices/me/attributes");
      client.publish("v1/devices/me/attributes/request/1", "{}");
    } else {
      vTaskDelay(2000 / portTICK_PERIOD_MS);
    }
  }
}

/**
 * @brief FreeRTOS Task: Collects and publishes periodic telemetry.
 * Validates WiFi, DHT22, and HX711 status. Multiple errors are 
 * concatenated into a single "error" string.
 */
void taskTelemetry(void * pvParameters) {
  for(;;) {      
    String instantUid = "";
    String accumulatedErrors = ""; 

    // 1. WiFi Connection Check
    if (WiFi.status() != WL_CONNECTED) {
      accumulatedErrors += "WiFi Link Down; ";
    }

    if (xSemaphoreTake(spiMutex, portMAX_DELAY)) {
      instantUid = checkRFID();
      xSemaphoreGive(spiMutex);
    }

    if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
      // 2. MQTT Connection Check
      if (!client.connected()) {
        accumulatedErrors += "MQTT Broker Unreachable; ";
        reconnectMQTT(); 
      }
      client.loop(); 

      // 3. DHT22 Sensor Check
      float h = dht.readHumidity();
      float t = dht.readTemperature();
      if (isnan(h) || isnan(t)) {
        accumulatedErrors += "DHT22 Failure; ";
      }

      // 4. HX711 Load Cell Check
      float w = 0;
      if (!scale.wait_ready_timeout(150)) {
        accumulatedErrors += "HX711 (Scale) Not Found; ";
      } else {
        w = scale.get_units(5);
      }

      StaticJsonDocument<512> data;
      data["temperature"] = isnan(t) ? 0 : t;
      data["humidity"] = isnan(h) ? 0 : h;
      data["weight"] = w;
      data["uid"] = (instantUid != "") ? instantUid : ((lastUid != "") ? lastUid : "None");
      
      if (accumulatedErrors != "") {
        accumulatedErrors.trim();
        data["error"] = accumulatedErrors;
      }

      char buffer[512];
      serializeJson(data, buffer);
      client.publish("v1/devices/me/telemetry", buffer);
      xSemaphoreGive(mqttMutex);
    }
    vTaskDelay(telemetryInterval / portTICK_PERIOD_MS);
  }
}

/**
 * @brief FreeRTOS Task: High-frequency RFID scanning.
 * * Scans for RFID cards every 250ms and publishes a telemetry 
 * update immediately upon detecting a new card.
 * * @param pvParameters Task parameters (unused).
 */
void taskRFID(void * pvParameters) {
  String previousDetected = "";
  for(;;) {
    String currentDetected = "";
    String rfidError = "";

    if (xSemaphoreTake(spiMutex, portMAX_DELAY)) {
      // Check if RFID reader is responsive
      if (mfrc522.PCD_PerformSelfTest()) { 
         currentDetected = checkRFID();
      } else {
         rfidError = "MFRC522 Reader Hardware Error";
      }
      xSemaphoreGive(spiMutex);
    }

    // Report immediate detection or error
    if ((currentDetected != "" && currentDetected != previousDetected) || rfidError != "") {
      if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
        if (client.connected()) {
          StaticJsonDocument<200> rfidDoc;
          if (currentDetected != "") rfidDoc["uid"] = currentDetected;
          if (rfidError != "") rfidDoc["error"] = rfidError;
          
          char rfidBuffer[200];
          serializeJson(rfidDoc, rfidBuffer);
          client.publish("v1/devices/me/telemetry", rfidBuffer);
        }
        xSemaphoreGive(mqttMutex);
      }
    }
    previousDetected = currentDetected;
    vTaskDelay(250 / portTICK_PERIOD_MS);
  }
}

/**
 * @brief Standard Arduino Setup function.
 * * Initializes serial communication, GPIOs, WiFi, MQTT, hardware sensors, 
 * and creates FreeRTOS tasks.
 */
void setup() {
  Serial.begin(115200);
  mqttMutex = xSemaphoreCreateMutex();
  spiMutex = xSemaphoreCreateMutex();
  
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); }

  espClient.setInsecure(); 
  client.setServer(mqtt_server, 8883);
  client.setCallback(mqttCallback);

  reconnectMQTT(); 

  StaticJsonDocument<64> initDoc;
  initDoc["init"] = "started";
  char initBuffer[64];
  serializeJson(initDoc, initBuffer);
  client.publish("v1/devices/me/telemetry", initBuffer);

  dht.begin();
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare();

  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN); 
  mfrc522.PCD_Init();

  ESP32PWM::allocateTimer(0);
  s1.setPeriodHertz(50);
  s1.attach(SERVO_1_PIN, 500, 2400);
  s2.setPeriodHertz(50);
  s2.attach(SERVO_2_PIN, 500, 2400);

  xTaskCreate(taskTelemetry, "TelemetryTask", 8192, NULL, 1, NULL);
  xTaskCreate(taskRFID, "RFIDTask", 4096, NULL, 1, NULL);
}

/** @brief Standard Arduino Loop function. Unused as system runs on FreeRTOS tasks. */
void loop() {}