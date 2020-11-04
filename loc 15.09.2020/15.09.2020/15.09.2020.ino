#include <IOXhop_FirebaseESP32.h>
//#include <IOXhop_FirebaseStream.h>

#include <WiFi.h>
//#include <WiFiClient.h>
//#include <WiFiServer.h>
//#include <WiFiUdp.h>



#include <NTPClient.h>
#include <WiFiUdp.h>


// Define NTP Client to get time
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP);

// Variables to save date and time
String formattedDate;
String dayStamp;
String timeStamp;
String miniute;
//String miniutee;
String hour;
long mincount = 0;
String day;
String dayy;
String path;
String path1;
String location;
String lastlocation = "Room 1";
int i , j ;
volatile int seconds = 0 , miniutee = 0; //make it volatile because it is used inside the interrupt








#define FIREBASE_HOST "esp-app-10.firebaseio.com"
#define FIREBASE_AUTH "23GPfDbYlNaRnkPKkew4GkFe8nMlrvMwEEaErNH1"
#define WIFI_SSID "Dialog 4G"
#define WIFI_PASSWORD "778T4GM99AE"

String fireStatus = ""; 


volatile int interruptCounter;
int totalInterruptCounter;
 
hw_timer_t * timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;


void IRAM_ATTR onTimer() {
  portENTER_CRITICAL_ISR(&timerMux);
  interruptCounter++;
  portEXIT_CRITICAL_ISR(&timerMux);

  miniutee = 1;
 
}





#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

int scanTime = 5; //In seconds
BLEScan* pBLEScan;

class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
      Serial.printf("Advertised Device: %s \n", advertisedDevice.toString().c_str());
    }
};





void setup() {



  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 5000000, true);
  timerAlarmEnable(timer);


 Serial.begin(9600);
  delay(1000);
  pinMode(2, OUTPUT);                
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);                                  
  Serial.print("Connecting to ");
  Serial.print(WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  
}

  Serial.println();

  Serial.print("Connected to ");

  Serial.println(WIFI_SSID);

  Serial.print("IP Address is : ");

  Serial.println(WiFi.localIP());                                                      //print local IP address

  Firebase.begin(FIREBASE_HOST, FIREBASE_AUTH);                                       // connect to firebase

 // Firebase.setString("ROOM 1", "Date");                                          //send initial string of led status

  
  timeClient.begin();
//   Set offset time in seconds to adjust for your timezone, for example:
//   GMT +1 = 3600
 //  GMT +8 = 28800
//   GMT -1 = -3600
//   GMT 0 = 0
  timeClient.setTimeOffset(19800);




  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true); //active scan uses more power, but get results faster
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(99);  // less or equal setInterval value
  
  
  
  


}


void loop() {


 if( miniutee > 0 ){


  BLEScanResults foundDevices = pBLEScan->start(scanTime, false);
  Serial.print("Devices found: ");
  Serial.println(foundDevices.getCount());
  Serial.println("Scan done!");
  pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory
  delay(1000);

  while(!timeClient.update()) {
    timeClient.forceUpdate();
  }
  // The formattedDate comes with the following format:
  // 2018-05-28T16:00:13Z
  // We need to extract date and time
  formattedDate = timeClient.getFormattedDate();
  Serial.println(formattedDate);

  // Extract date
  int splitT = formattedDate.indexOf("T");
  dayStamp = formattedDate.substring(0, splitT);
//  Serial.print("DATE: ");
//Serial.println(dayStamp);
  // Extract time
  timeStamp = formattedDate.substring(splitT+1, formattedDate.length()-1);
//  Serial.print("HOUR: ");
//  Serial.println(timeStamp);

  miniute = timeStamp.substring(3,5);
  hour = timeStamp.substring(0,2);
 // Serial.println(hour);
  day = dayStamp.substring(5,7) + "_" + dayStamp.substring(8,10);
 // Serial.println(miniute);
 // Serial.println(day);

  timeStamp = dayStamp + " " + timeStamp;

  mincount = hour.toInt()*60+ miniute.toInt();
 // Serial.println(mincount);






  path1 = "Sensor/" +  day + "/" + String(mincount) + "/D";

  
 Serial.println(timeStamp);
 
   
 //Firebase.setString(path1, timeStamp );    // Send Location and time to database 

  path = "Sensor/" + day + "/" + String(mincount) + "/R";

  i = random(1 , 6);
  j = random(1 , 5);
  Serial.println(i);
  Serial.println(j);
  
  switch (i){
    
    case 1: location = "Room 1";
    break;
    case 2: location = "Room 2";
    break;
    case 3: location = "Washroom";
    break;
    case 4: location = "Dining Room";
    break;
    case 5: location = "Living Room";
    break;
    default: location = "Living Room";
    
    }

 //   Serial.println(location);
  
   if (j >  3){
    
 //   Firebase.setString(path, location ); 
    lastlocation = location;
    
    }

    else{
    
//  Firebase.setString(path, lastlocation );    // Send Location and time to database
    
    
    }
  
  delay(500);


  Serial.println(location);
  miniutee = 0;

 // mincount++;

 

  

  delay(500);
   
//  fireStatus = Firebase.getString(path1);                     // get led status input from firebase

  if (fireStatus == timeStamp) {                // compare the input of led status received from firebase

    Serial.println("Data Logging Success");                 

    digitalWrite(2, HIGH);   // make output led ON
    delay(500);
    
    digitalWrite(2, LOW);   // make output led ON

  }

  else {

  //  Serial.println("Wrong Credential! Please send ON/OFF");

        Serial.println("Data Logging Faild");

    digitalWrite(2, LOW);

  }

 }

}
