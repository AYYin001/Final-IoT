#include <TinyGPS++.h>
#include <HardwareSerial.h>
#include <WiFi.h>
#include <HttpClient.h>

// WiFi credentials
const char* ssid = "Yihan";
const char* password = "cvdl7342";

// Server info
const char kHostname[] = "18.219.120.109";  // your EC2 public IP (no http://)
const int kPort = 5000;                   // Flask app runs on this port

TinyGPSPlus gps;
#define GPS_RX 32
#define GPS_TX 33
#define GPS_BAUD 9600
HardwareSerial gpsSerial(1);

void setup() {
  Serial.begin(9600);
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX, GPS_TX);

  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.println("IP: " + WiFi.localIP().toString());
}

void loop() {
  while (gpsSerial.available() > 0) {
    char c = gpsSerial.read();
    gps.encode(c);
  }

  if (gps.location.isUpdated()) {
    float lat = gps.location.lat();
    float lng = gps.location.lng();
    float spd = gps.speed.kmph();

    Serial.printf("Lat: %.6f, Lng: %.6f, Speed: %.2f\n", lat, lng, spd);

    // Format the GET request path

    int hourUTC = gps.time.hour();
    int hourLocal = (hourUTC - 7 + 24) % 24; 

    char path[150];
    snprintf(path, sizeof(path),
  "/gps?lat=%.6f&lng=%.6f&speed=%.2f&date=%02d-%02d-%04d&time=%02d:%02d:%02d",
      lat, lng, spd,
      gps.date.day(), gps.date.month(), gps.date.year(),
      hourLocal, gps.time.minute(), gps.time.second()
    );
    
    Serial.print("📤 Sending path: ");
    Serial.println(path);

    // Setup HTTP connection using HttpClient
    WiFiClient client;
    HttpClient http(client);

    int err = http.get(kHostname, kPort, path);
    if (err == 0) {
      Serial.println("Request sent");

      int status = http.responseStatusCode();
      Serial.print("HTTP Status Code: ");
      Serial.println(status);

      http.skipResponseHeaders();
      while (http.available()) {
        char c = http.read();
        Serial.print(c);  // Print response
      }
    } else {
      Serial.print("❌ HTTP GET failed: ");
      Serial.println(err);
    }

    http.stop();
    Serial.println("🔌 Connection closed\n");

    delay(1000); // Wait before sending next reading
  }
}
