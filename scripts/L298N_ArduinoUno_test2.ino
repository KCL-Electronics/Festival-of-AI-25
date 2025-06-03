// --- Pin Definitions (UNO - CHANGE THESE TO MATCH YOUR WIRING!) ---
// IMPORTANT: Enable pins (ENA, ENB) MUST be connected to PWM-capable pins on the Uno (~3, ~5, ~6, ~9, ~10, ~11)

// Motor 1 Pins
const int MOTOR1_EN = 3;  // Enable Pin (PWM ~) - often labeled ENA or EN1
const int MOTOR1_IN1 = 2; // Input 1
const int MOTOR1_IN2 = 4; // Input 2

// Motor 2 Pins
const int MOTOR2_EN = 5;  // Enable Pin (PWM ~) - often labeled ENB or EN2
const int MOTOR2_IN1 = 7; // Input 3 (or IN1 on a second L298N board)
const int MOTOR2_IN2 = 8; // Input 4 (or IN2 on a second L298N board)

// Motor 3 Pins
// Using pins from a second L298N board (or another set of free pins)
// NOTE: Uno has limited PWM pins. If using 3 motors, you might need creative wiring
// or accept on/off control for one motor, or use a dedicated motor shield.
// Assuming a PWM pin is available for the third motor:
const int MOTOR3_EN = 6;  // Enable Pin (PWM ~) - e.g., ENA on board 2
const int MOTOR3_IN1 = 12; // Input 1 on board 2
const int MOTOR3_IN2 = 13; // Input 2 on board 2

// --- Test Parameters ---
const int TEST_SPEED = 150; // Speed for testing (0-255). Start low! Adjust as needed.
const int TEST_DURATION_MS = 2000; // How long to run each motor direction (milliseconds)
const int PAUSE_DURATION_MS = 1000; // Pause between tests

// --- Helper Function to Control a Motor ---
void controlMotor(int enPin, int in1Pin, int in2Pin, int speed, bool forward) {
  // Set direction
  if (forward) {
    digitalWrite(in1Pin, HIGH);
    digitalWrite(in2Pin, LOW);
    Serial.println(" Direction: Forward");
  } else {
    digitalWrite(in1Pin, LOW);
    digitalWrite(in2Pin, HIGH);
    Serial.println(" Direction: Backward");
  }
  // Set speed
  analogWrite(enPin, speed); // Use analogWrite for PWM speed control
  Serial.print(" Speed: ");
  Serial.println(speed);
}

// --- Helper Function to Stop a Motor (Coast) ---
void stopMotor(int enPin, int in1Pin, int in2Pin) {
  digitalWrite(in1Pin, LOW);
  digitalWrite(in2Pin, LOW);
  analogWrite(enPin, 0); // Speed to 0
  Serial.println(" Motor Stopped (Coast)");
}

// --- Setup Function ---
void setup() {
  Serial.begin(9600); // Start serial communication (9600 is common for Uno)
  while (!Serial); // Wait for serial connection (especially useful on some boards)
  Serial.println("Arduino Uno L298N Motor Test");

  // Set all motor control pins as outputs
  pinMode(MOTOR1_EN, OUTPUT);
  pinMode(MOTOR1_IN1, OUTPUT);
  pinMode(MOTOR1_IN2, OUTPUT);

  pinMode(MOTOR2_EN, OUTPUT);
  pinMode(MOTOR2_IN1, OUTPUT);
  pinMode(MOTOR2_IN2, OUTPUT);

  pinMode(MOTOR3_EN, OUTPUT);
  pinMode(MOTOR3_IN1, OUTPUT);
  pinMode(MOTOR3_IN2, OUTPUT);

  // Ensure all motors are stopped initially
  stopMotor(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
  stopMotor(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);
  stopMotor(MOTOR3_EN, MOTOR3_IN1, MOTOR3_IN2);

  Serial.println("Setup complete. Ensure 12V Battery is connected.");
  Serial.println("Starting tests in 3 seconds...");
  delay(3000); // Pause before starting
}

// --- Main Loop Function ---
void loop() {
  // --- Test Motor 1 ---
  Serial.println("\n--- Testing Motor 1 ---");
  // Forward
  controlMotor(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2, TEST_SPEED, true);
  delay(TEST_DURATION_MS);
  // Stop
  stopMotor(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
  delay(PAUSE_DURATION_MS);
  // Backward
  controlMotor(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2, TEST_SPEED, false);
  delay(TEST_DURATION_MS);
  // Stop
  stopMotor(MOTOR1_EN, MOTOR1_IN1, MOTOR1_IN2);
  delay(PAUSE_DURATION_MS * 2); // Longer pause before next motor

  // --- Test Motor 2 ---
  Serial.println("\n--- Testing Motor 2 ---");
   // Forward
  controlMotor(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2, TEST_SPEED, true);
  delay(TEST_DURATION_MS);
  // Stop
  stopMotor(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);
  delay(PAUSE_DURATION_MS);
  // Backward
  controlMotor(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2, TEST_SPEED, false);
  delay(TEST_DURATION_MS);
  // Stop
  stopMotor(MOTOR2_EN, MOTOR2_IN1, MOTOR2_IN2);
  delay(PAUSE_DURATION_MS * 2); // Longer pause before next motor

  // --- Test Motor 3 ---
  Serial.println("\n--- Testing Motor 3 ---");
   // Forward
  controlMotor(MOTOR3_EN, MOTOR3_IN1, MOTOR3_IN2, TEST_SPEED, true);
  delay(TEST_DURATION_MS);
  // Stop
  stopMotor(MOTOR3_EN, MOTOR3_IN1, MOTOR3_IN2);
  delay(PAUSE_DURATION_MS);
  // Backward
  controlMotor(MOTOR3_EN, MOTOR3_IN1, MOTOR3_IN2, TEST_SPEED, false);
  delay(TEST_DURATION_MS);
  // Stop
  stopMotor(MOTOR3_EN, MOTOR3_IN1, MOTOR3_IN2);
  delay(PAUSE_DURATION_MS * 2); // Longer pause before next motor

  Serial.println("\n--- Test Cycle Complete. Repeating in 5 seconds... ---");
  delay(5000); // Wait before repeating the whole cycle
}
