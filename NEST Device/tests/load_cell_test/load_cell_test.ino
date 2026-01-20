#include <Arduino.h>
#include "HX711.h"

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 16;
const int LOADCELL_SCK_PIN = 4;

HX711 scale;

// --- CALIBRATION FACTOR ---
// For a 5kg load cell, this value is usually around 400.0 to 1000.0 
// depending on the specific sensor. You will need to adjust this.
float calibration_factor = -471.497; 

void setup() {
  Serial.begin(9600); 
  setCpuFrequencyMhz(80); 
  
  Serial.println("\n--- HX711 Weight Scale (Grams / mg precision) ---");
  Serial.println("Sensor Capacity: 5kg");

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

  // Safety check: if the scale is not ready, it's a wiring issue
  if (scale.wait_ready_timeout(2000)) {
    Serial.println("HX711 found and ready.");
  } else {
    Serial.println("Error: HX711 not found. Check your connections (VCC, GND, DT, SCK).");
    while (1); // Halt program if sensor is not found
  }

  scale.set_scale(calibration_factor); 
  Serial.println("Taring... Please do not place any weight on the scale.");
  scale.tare(); 
  
  Serial.println("Tare complete. Ready to weigh.");
}

void loop() {
  // Check if sensor is still responding
  if (scale.is_ready()) {
    float weight_g = scale.get_units(1);      // Single reading
    float average_g = scale.get_units(10);    // Average of 10 readings

    Serial.print("Current Weight: ");
    // 3 decimal places = milligram precision (0.001g)
    Serial.print(weight_g, 3); 
    Serial.print(" g\t| Stable Average: ");
    Serial.print(average_g, 3);
    Serial.println(" g");
  } else {
    Serial.println("HX711 not found. Check wiring.");
  }

  delay(500); 
}