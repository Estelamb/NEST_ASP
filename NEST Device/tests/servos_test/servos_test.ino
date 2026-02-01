#include <ESP32Servo.h>

#define SERVO_1_PIN 2
#define SERVO_2_PIN 13

Servo s1;
Servo s2;

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
  s1.write(150);
  delay(250);
  s2.write(20);
}

void closeDoor() {
  s1.write(20); 
  delay(250);
  s2.write(150);
}


void loop() {
  openDoor();
  delay(2000);
  closeDoor();
  delay(2000);
}