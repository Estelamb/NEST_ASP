#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>

// Standard ESP32 pins for VSPI
#define SS_PIN    5   
#define RST_PIN   22  // Reset pin
#define SCK_PIN   18
#define MISO_PIN  19
#define MOSI_PIN  23

MFRC522 mfrc522(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  
  // Initialize SPI bus with specific ESP32 pins
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, SS_PIN); 
  
  // Initialize MFRC522
  mfrc522.PCD_Init();
  
  Serial.println("--- RFID RC522 Ready ---");
  Serial.println("Scan a card or keychain...");
}

void loop() {
  // Look for new cards
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }
  
  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }
    
  // Display UID
  Serial.print("Card UID:");
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      Serial.print(" 0");
    } else {
      Serial.print(" ");
    }
    Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  
  Serial.println();
  
  // Stop encryption on PCD (Proximity Coupling Device)
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}