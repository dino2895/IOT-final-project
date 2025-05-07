#include <ArduinoBLE.h>
#include <LSM6DS3.h>
#include <Wire.h>

// IMU 初始化
LSM6DS3 myIMU(I2C_MODE, 0x6A); // I2C 位址

// BLE 服務與特徵
BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic imuBinaryChar("19B10002-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 24); // 6 floats = 24 bytes

// 板載藍燈 D14
const int ledPin = 14;
bool ledState = false;
unsigned long lastBlinkTime = 0;
const unsigned long blinkInterval = 300;

void startBLE() {
  BLE.stopAdvertise();
  BLE.advertise();
  Serial.println("BLE advertising restarted");
}

void setup() {
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);

  Serial.begin(9600);
  delay(100);
  Serial.println("Starting...");

  if (myIMU.begin() != 0) {
    Serial.println("IMU Device error");
    while (1); // 停止執行
  }

  if (!BLE.begin()) {
    Serial.println("BLE init failed");
    while (1); // 停止執行
  }

  BLE.setLocalName("nRF52-IMU-BIN-02");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuBinaryChar);
  BLE.addService(imuService);

  startBLE();
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    digitalWrite(ledPin, HIGH); // 綠燈恆亮

    while (central.connected()) {
      // 讀取感測器資料
      float accelX = myIMU.readFloatGyroX();
      float accelY = myIMU.readFloatGyroY();
      float accelZ = myIMU.readFloatGyroZ();
      float gyroX  = myIMU.readFloatAccelX();
      float gyroY  = myIMU.readFloatAccelY();
      float gyroZ  = myIMU.readFloatAccelZ();
      // 建立 binary buffer
      uint8_t buffer[24] = {0}; // 6 個 float 各佔 4 bytes
      memcpy(buffer,      &accelX, 4);
      memcpy(buffer + 4,  &accelY, 4);
      memcpy(buffer + 8,  &accelZ, 4);
      memcpy(buffer + 12, &gyroX,  4);
      memcpy(buffer + 16, &gyroY,  4);
      memcpy(buffer + 20, &gyroZ,  4);
      // 傳送 binary 資料
      imuBinaryChar.writeValue(buffer, sizeof(buffer));

      // 印出數據到 Serial Monitor（方便開發時 debug）
      Serial.println("---- IMU Data (float) ----");
      Serial.print("Accel : ");
      Serial.print(accelX, 2); Serial.print(", ");
      Serial.print(accelY, 2); Serial.print(", ");
      Serial.println(accelZ, 2);

      Serial.print("Gyro  : ");
      Serial.print(gyroX, 2); Serial.print(", ");
      Serial.print(gyroY, 2); Serial.print(", ");
      Serial.println(gyroZ, 2);
      Serial.println("--------------------------\n");

      delay(20);
    }

    Serial.println("Central disconnected");
    digitalWrite(ledPin, LOW); // 離線後重新進入閃爍狀態
    startBLE();
  }

  // 尚未連線時閃綠燈
  if (!BLE.connected()) {
    unsigned long currentMillis = millis();
    if (currentMillis - lastBlinkTime >= blinkInterval) {
      ledState = !ledState;
      digitalWrite(ledPin, ledState ? HIGH : LOW);
      lastBlinkTime = currentMillis;
    }
  }
}
