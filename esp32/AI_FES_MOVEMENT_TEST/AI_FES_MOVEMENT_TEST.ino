#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <math.h>
#include <ArduinoJson.h>

// WiFi credentials
const char *ssid = "REDACTED";
const char *password = "REDACTED";

// WebSocket server
const char *websockets_server_host = "1.1.1.1";
const uint16_t websockets_server_port = 8000;
const char *websockets_path = "/ws/robotcontrol";

using namespace websockets;
WebsocketsClient client;

// Motor pins
#define M1_FORWARD_PIN 21   // front-left
#define M1_BACKWARD_PIN 22  // front-left
#define M2_FORWARD_PIN 18
#define M2_BACKWARD_PIN 19
#define M3_FORWARD_PIN 26
#define M3_BACKWARD_PIN 25

int currentGlobalSpeed = 255;

// --- Movement functions ---
void moveXY(float x, float y);
void setMotor(int forwardPin, int backwardPin, int speed);

void moveBackward() {
  moveXY(0, -1);
}
void moveForward() {
  moveXY(0, 1);
}
void turnLeft() {
  moveXY(1, 0);
}
void turnRight() {
  moveXY(-1, 0);
}
void stop() {
  moveXY(0, 0);
}

void rotateClockwise() {
  int speed = currentGlobalSpeed;
  setMotor(M1_FORWARD_PIN, M1_BACKWARD_PIN, speed);
  setMotor(M2_FORWARD_PIN, M2_BACKWARD_PIN, speed);
  setMotor(M3_FORWARD_PIN, M3_BACKWARD_PIN, speed);
}

void rotateCounterClockwise() {
  int speed = currentGlobalSpeed;
  setMotor(M1_FORWARD_PIN, M1_BACKWARD_PIN, -speed);
  setMotor(M2_FORWARD_PIN, M2_BACKWARD_PIN, -speed);
  setMotor(M3_FORWARD_PIN, M3_BACKWARD_PIN, -speed);
}

// --- WebSocket event handlers ---
void onMessageCallback(WebsocketsMessage message) {
  String data = message.data();
  data.trim();
  Serial.print("Received command: ");
  Serial.println(data);

  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, data);

  // Test if parsing succeeds.
  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return;
  }

  float x = doc["x"];
  float y = doc["y"];

  // if x=99, y=99, then rotate clockwise
  if (x == 99 && y == 99) {
    Serial.println("Rotating clockwise");
    rotateClockwise();
    return;
  }

  if (x == -99 && y == -99) {
    Serial.println("Rotating counter-clockwise");
    rotateCounterClockwise();
    return;
  }

  // flip magnitude of x (if x is positive, make it negative, if x is negative, make it positive)
  if (x > 0) {
    x = -x;
  } else {
    x = abs(x);
  }

  moveXY(x, y);
  return;
}

void connectWebSocket() {
  String ws_url = String("ws://") + websockets_server_host + ":" + String(websockets_server_port) + websockets_path;
  Serial.print("Connecting to WebSocket: ");
  Serial.println(ws_url);

  while (!client.connect(ws_url)) {
    Serial.println("WebSocket connection failed, retrying in 2s...");
    delay(2000);
  }
  Serial.println("WebSocket connected!");
  client.onMessage(onMessageCallback);
}

// --- Arduino setup/loop ---
void setup() {
  Serial.begin(115200);

  // Motor pins
  pinMode(M1_FORWARD_PIN, OUTPUT);
  pinMode(M1_BACKWARD_PIN, OUTPUT);
  pinMode(M2_FORWARD_PIN, OUTPUT);
  pinMode(M2_BACKWARD_PIN, OUTPUT);
  pinMode(M3_FORWARD_PIN, OUTPUT);
  pinMode(M3_BACKWARD_PIN, OUTPUT);

  currentGlobalSpeed = 100;

  // WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());

  // WebSocket
  connectWebSocket();
}

void loop() {
  if (client.available()) {
    client.poll();
  } else {
    Serial.println("WebSocket disconnected, reconnecting...");
    connectWebSocket();
  }
  delay(10);  // Small delay to avoid watchdog resets
}

// --- Movement code (unchanged) ---
void moveXY(float x, float y) {
  float magnitude = sqrt(x * x + y * y);
  if (magnitude > 1.0) {
    x /= magnitude;
    y /= magnitude;
  }
  float w1 = -0.5 * x + (sqrt(3) / 2) * y;
  float w2 = -0.5 * x - (sqrt(3) / 2) * y;
  float w3 = x;

  int m1_speed = int(w1 * currentGlobalSpeed);
  int m2_speed = int(w2 * currentGlobalSpeed);
  int m3_speed = int(w3 * currentGlobalSpeed);

  Serial.print("moveXY called with x: ");
  Serial.print(x, 3);
  Serial.print(", y: ");
  Serial.print(y, 3);
  Serial.print(" | m1_speed: ");
  Serial.print(m1_speed);
  Serial.print(", m2_speed: ");
  Serial.print(m2_speed);
  Serial.print(", m3_speed: ");
  Serial.println(m3_speed);

  setMotor(M1_FORWARD_PIN, M1_BACKWARD_PIN, m1_speed);
  setMotor(M2_FORWARD_PIN, M2_BACKWARD_PIN, m2_speed);
  setMotor(M3_FORWARD_PIN, M3_BACKWARD_PIN, m3_speed);
}

void setMotor(int forwardPin, int backwardPin, int speed) {
  if (speed > 0) {
    analogWrite(forwardPin, abs(speed));
    analogWrite(backwardPin, 0);
  } else if (speed < 0) {
    analogWrite(forwardPin, 0);
    analogWrite(backwardPin, abs(speed));
  } else {
    analogWrite(forwardPin, 0);
    analogWrite(backwardPin, 0);
  }
}