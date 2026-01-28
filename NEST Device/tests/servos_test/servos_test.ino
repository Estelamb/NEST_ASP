#include <ESP32Servo.h>

#define SERVO_1_PIN 2
#define SERVO_2_PIN 13

Servo s1;
Servo s2;

// --- AJUSTE PARA 3.3V ---
// A 3.3V el servo es más lento. 

void setup() {
  Serial.begin(115200);

  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);

  s1.setPeriodHertz(50);
  s2.setPeriodHertz(50);

  s1.attach(SERVO_1_PIN, 500, 2400); 
  s2.attach(SERVO_2_PIN, 500, 2400);

  
  delay(1000);
}

void openDoor() {
  Serial.println("Abriendo a 3.3V...");

  s1.write(160);
  delay(500);
  s2.write(20);
}

void closeDoor() {
  Serial.println("Cerrando a 3.3V...");

  s1.write(20); 
  delay(500);
  s2.write(125);
}


void loop() {
  openDoor();
  delay(2000);
  closeDoor();
  delay(2000);
}