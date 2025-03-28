#include <Servo.h>

#define SERVO_PIN 9
Servo steeringServo;

// Custom angle configuration
const int RIGHT_BOUND = 135;   // Full right position
const int LEFT_BOUND = 45;   // Full left position
const int CENTER_ANGLE = 90;  // Middle position
int currentAngle = CENTER_ANGLE;

void setup() {
  Serial.begin(9600);
  steeringServo.attach(SERVO_PIN);
  
  // Move to center position at startup
  steeringServo.write(map(CENTER_ANGLE, LEFT_BOUND, RIGHT_BOUND, 0, 180));
  delay(500);

  Serial.println("Arduino Nano Ready");
  Serial.println("Send commands: S<angle>");
  Serial.println("Example: S15 (center), S30 (full right), S-15 (full left)");
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();
    
    if (command == 'S') {
      int angle = Serial.parseInt();
      angle = constrain(angle, LEFT_BOUND, RIGHT_BOUND);

      // Smooth transition logic
      int step = (angle > currentAngle) ? 1 : -1;
      while(currentAngle != angle) {
        currentAngle += step;
        int mappedAngle = map(currentAngle, LEFT_BOUND, RIGHT_BOUND, 0, 180);
        steeringServo.write(mappedAngle);
        delay(30);  // Adjust this for faster/slower movement
      }

      Serial.print("Servo mapped to physical angle: ");
      Serial.println(map(currentAngle, LEFT_BOUND, RIGHT_BOUND, 0, 180));
      Serial.print("Your logical angle set to: ");
      Serial.println(currentAngle);
    }
  }
}
