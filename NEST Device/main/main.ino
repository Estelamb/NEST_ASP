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
const char* token = "hNxbPHZG1A1Rft0LHAVO";
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
Servo s1, s2;
MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClientSecure espClient;
PubSubClient client(espClient);

// --- FREE RTOS & GLOBAL VARIABLES ---
SemaphoreHandle_t mqttMutex; 
SemaphoreHandle_t spiMutex;  
String lastUid = ""; 
float calibration_factor = -531.02;

// --- RFID HELPER FUNCTION ---

/**
 * Enhanced checkRFID: Detects cards even if they are held 
 * continuously in the reader's range by forcing a Wakeup sequence.
 */
String checkRFID() {
  String uidStr = "";
  byte bufferATQA[2];
  byte bufferSize = sizeof(bufferATQA);

  // Attempt to wake up any card (Request A)
  MFRC522::StatusCode result = mfrc522.PICC_RequestA(bufferATQA, &bufferSize);

  // If not found, try WakeupA (to find cards in HALT state)
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
      
      // Essential: Halt and stop crypto to allow re-detection in next loop
      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();
    }
  }
  return uidStr;
}

// --- CONTROL FUNCTIONS ---

void setPeriod(int newPeriod) {
  if (newPeriod >= 1000) {
    telemetryInterval = newPeriod;
    Serial.printf("[CONFIG] - New period: %d ms\n", telemetryInterval);
  }
}

void setLedColor(String color) {
  String colorLower = color;
  colorLower.toLowerCase();

  Serial.print("[LED] - Changing color to: ");
  Serial.println(colorLower);

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
}

void operateDoor(String command) {
  Serial.print(command);
  Serial.println(" door");
  int angle = (command == "open") ? 0 : 90;
  s1.write(angle);
  delay(250); 
  s2.write(angle);
  Serial.println("[DOOR] - Movement completed");
}

// --- MQTT MANAGEMENT ---

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("[MQTT] - Message arrived: ");
  StaticJsonDocument<500> doc;
  if (deserializeJson(doc, payload, length)) return;
  JsonObject shared = doc.containsKey("shared") ? doc["shared"] : doc.as<JsonObject>();
  if (shared.containsKey("door")) operateDoor(shared["door"].as<String>());
  if (shared.containsKey("rgb")) setLedColor(shared["rgb"].as<String>());
  if (shared.containsKey("period")) setPeriod(shared["period"].as<int>());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.println("[MQTT] - Connecting...");
    if (client.connect(token, token, NULL)) {
      Serial.println("[MQTT] - Connected");
      client.subscribe("v1/devices/me/attributes");
      client.publish("v1/devices/me/attributes/request/1", "{}");
    } else {
      vTaskDelay(5000 / portTICK_PERIOD_MS);
    }
  }
}

// --- FreeRTOS TASKS ---

/**
 * Task: Periodic Telemetry
 * Sends all sensors + UID (if present). If no card is present, sends NULL.
 */
void taskTelemetry(void * pvParameters) {
  for(;;) {
    String instantUid = "";
    if (xSemaphoreTake(spiMutex, portMAX_DELAY)) {
      instantUid = checkRFID();
      xSemaphoreGive(spiMutex);
    }

    if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
      if (!client.connected()) reconnectMQTT();
      client.loop(); 

      float h = dht.readHumidity();
      float t = dht.readTemperature();
      float w = scale.get_units(5);

      StaticJsonDocument<256> data;
      data["temperature"] = isnan(t) ? 0 : t;
      data["humidity"] = isnan(h) ? 0 : h;
      data["weight"] = w;

      // Telemetry logic: Check instant detection first, then buffer, else null
      if (instantUid != "") {
        data["uid"] = instantUid;
      } else if (lastUid != "") {
        data["uid"] = lastUid;
      } else {
        data["uid"] = "None"; 
      }
      
      lastUid = ""; // Reset buffer after periodic transmission

      char buffer[256];
      serializeJson(data, buffer);
      Serial.print("[TELEMETRY] - Periodic publish: ");
      Serial.println(buffer);
      client.publish("v1/devices/me/telemetry", buffer);
      
      xSemaphoreGive(mqttMutex);
    }
    vTaskDelay(telemetryInterval / portTICK_PERIOD_MS);
  }
}

/**
 * Task: Asynchronous Instant RFID Detection
 * Detects card and publishes immediately to ThingsBoard.
 */
void taskRFID(void * pvParameters) {
  String previousDetected = "";

  for(;;) {
    String currentDetected = "";
    
    if (xSemaphoreTake(spiMutex, portMAX_DELAY)) {
      currentDetected = checkRFID();
      xSemaphoreGive(spiMutex);
    }

    // ONLY publish if a card is detected AND it's a new event
    if (currentDetected != "" && currentDetected != previousDetected) {
      
      if (xSemaphoreTake(mqttMutex, portMAX_DELAY)) {
        if (client.connected()) {
          StaticJsonDocument<100> rfidDoc;
          rfidDoc["uid"] = currentDetected;
          char rfidBuffer[100];
          serializeJson(rfidDoc, rfidBuffer);
          Serial.print("[RFID] - Instant Publish: ");
          Serial.println(currentDetected);
          client.publish("v1/devices/me/telemetry", rfidBuffer);
        }
        xSemaphoreGive(mqttMutex);
      }
    }
    
    previousDetected = currentDetected;
    vTaskDelay(250 / portTICK_PERIOD_MS); // Yield CPU
  }
}

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

  dht.begin();
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare();
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN); 
  mfrc522.PCD_Init();

  ESP32PWM::allocateTimer(0);
  s1.setPeriodHertz(50);
  s2.setPeriodHertz(50);
  s1.attach(SERVO_1_PIN, 500, 2400);
  s2.attach(SERVO_2_PIN, 500, 2400);

  xTaskCreate(taskTelemetry, "TelemetryTask", 8192, NULL, 1, NULL);
  xTaskCreate(taskRFID, "RFIDTask", 4096, NULL, 1, NULL);
}

void loop() {}