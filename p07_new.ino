#define D7 13
#define D6 12
#define D5 11
#define D4 10
#define RS 9
#define EN 8

#define DEG 0xDF
#define HEATER 4
#define TEMP A0
#define TUP 45
#define TDW 35

#include <LiquidCrystal.h>
LiquidCrystal lcd(RS, EN, D4, D5, D6, D7);
float T = 0;
bool stHeater = false;

void setup() {
  pinMode(HEATER, OUTPUT);
  lcd.begin(16, 2);
  lcd.print("Temperature:");
}

void loop() {
  // Read the temperature from the sensor
  T = analogRead(TEMP);
  T = T * (5.0 / 10.23);  // Corrected floating-point division

  // Display the temperature on the LCD
  lcd.setCursor(0, 1);
  lcd.print(T, 1);
  lcd.write(DEG);
  lcd.print("C  ");

  // Control the heater based on the temperature
  if (T <= TDW)
    stHeater = HIGH;
  if (T >= TUP)
    stHeater = LOW;

  digitalWrite(HEATER, stHeater);

  // Delay for stable readings
  delay(500);  // Increased the delay to 500 ms
}
