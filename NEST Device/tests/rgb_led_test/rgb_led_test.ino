#include <Arduino.h>

// Define GPIO pins
const int RED_PIN = 25;   // Connect to Red cathode through resistor
const int GREEN_PIN = 26; // Connect to Green cathode through resistor
const int BLUE_PIN = 27;  // Connect to Blue cathode through resistor

void setup() {
  Serial.begin(9600);
  Serial.println("ESP32 RGB Common Anode LED Demo");

  // Configure pins as outputs
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  // Initial state: OFF (In common anode, HIGH is OFF)
  digitalWrite(RED_PIN, HIGH);
  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(BLUE_PIN, HIGH);
}

void loop() {
  Serial.println("Red ON");
  digitalWrite(RED_PIN, LOW);    // LOW = ON for Common Anode
  delay(1000);
  digitalWrite(RED_PIN, HIGH);   // HIGH = OFF

  Serial.println("Green ON");
  digitalWrite(GREEN_PIN, LOW);
  delay(1000);
  digitalWrite(GREEN_PIN, HIGH);

  Serial.println("Blue ON");
  digitalWrite(BLUE_PIN, LOW);
  delay(1000);
  digitalWrite(BLUE_PIN, HIGH);

  Serial.println("White (All ON)");
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, LOW);
  delay(1000);
  
  // Reset all to OFF
  digitalWrite(RED_PIN, HIGH);
  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(BLUE_PIN, HIGH);
  delay(1000);
}