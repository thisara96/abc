/*
   Based on Neil Kolban example for IDF: https://github.com/nkolban/esp32-snippets/blob/master/cpp_utils/tests/BLE%20Tests/SampleScan.cpp
   Ported to Arduino ESP32 by Evandro Copercini
*/

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

int scanTime = 5; //In seconds
BLEScan* pBLEScan;
int rssinow,rssi1,rssi2,rssi3;
int myArray[4], room, maxVal;
String pServerAddress;


class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      Serial.printf("Advertised Device: %s \n", advertisedDevice.toString().c_str());

       if (advertisedDevice.haveRSSI()){
        Serial.printf("Rssi: %d \n", (int)advertisedDevice.getRSSI());
        rssinow = advertisedDevice.getRSSI();
        Serial.println(advertisedDevice.getAddress().toString().c_str());
        //Serial.println(rssinow);

        pServerAddress = advertisedDevice.getAddress().toString().c_str();

        if( pServerAddress == "d4:36:39:d8:ca:c6" ){
          
          Serial.println("HM10");
          rssi1 = rssinow;
          
          }
        if( pServerAddress == "24:62:ab:d7:52:62" ){
          
          Serial.println("ESP33");
         rssi2 = rssinow;
          
          }
        if( pServerAddress == "3c:71:bf:42:1a:3a" ){
          
          Serial.println("ESP32");
          rssi3 = rssinow;
          
         }

        else{
          
          Serial.println("No Dev");
          
          }         

      }
      else Serial.printf("\n");

        Serial.println(rssi1);
        Serial.println(rssi2);
        Serial.println(rssi3);
      }
};

void setup() {
  Serial.begin(115200);
  Serial.println("Scanning...");

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true); //active scan uses more power, but get results faster
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);  // less or equal setInterval value
}

void loop() {
  // put your main code here, to run repeatedly:
  BLEScanResults foundDevices = pBLEScan->start(scanTime, false);
  Serial.print("Devices found: ");
  Serial.println(foundDevices.getCount());
  Serial.println("Scan done!");
  pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory
  myArray[0] = -150;
  myArray[1] = rssi1;
  myArray[2] = rssi2;
  myArray[3] = rssi3;

 
 

 maxVal = myArray[0];  // just to start it off
for (byte n = 0; n < 4; n++) {

  
   if (myArray[n] > maxVal) {
        maxVal = myArray[n];
        
   }
}

for (byte n = 0; n < 4; n++) {
   if (maxVal == myArray[n]){
    
       room = n;
       
    }

  }

  switch (room){
    
    case 0: Serial.println("room1");
    break;
    case 1: Serial.println("room2");
    break;
    case 2: Serial.println("room3");
    break;
    case 3: Serial.println("room4");
    break;
    
    
    }

  delay(2000);
}
