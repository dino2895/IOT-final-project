#include <ArduinoBLE.h>
#include <LSM6DS3.h>
#include <Wire.h>

// 建立 IMU 物件
LSM6DS3 myIMU(I2C_MODE, 0x6A); // I2C 位址

// 建立 BLE 服務與特徵值（改用 binary characteristic）
BLEService imuService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLECharacteristic imuBinaryChar("19B10002-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 24); // 6 floats = 24 bytes

void setup() {
  Serial.begin(9600);
  while (!Serial);

  // 初始化 IMU
  if (myIMU.begin() != 0) {
    Serial.println("IMU Device error");
    while (1);
  } else {
    Serial.println("IMU ready. Binary streaming started.");
  }

  // 初始化 BLE
  if (!BLE.begin()) {
    Serial.println("BLE initialization failed!");
    while (1);
  }

  BLE.setLocalName("nRF52-IMU-BIN");
  BLE.setAdvertisedService(imuService);
  imuService.addCharacteristic(imuBinaryChar);
  BLE.addService(imuService);
  BLE.setConnectionInterval(6, 12); // 建議連線間隔 7.5ms~15ms

  BLE.advertise();
  Serial.println("BLE advertising started");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    while (central.connected()) {
      // 讀取感測器資料
      float accelX = myIMU.readFloatAccelX();
      float accelY = myIMU.readFloatAccelY();
      float accelZ = myIMU.readFloatAccelZ();
      float gyroX  = myIMU.readFloatGyroX();
      float gyroY  = myIMU.readFloatGyroY();
      float gyroZ  = myIMU.readFloatGyroZ();

      // 建立 binary buffer
      uint8_t buffer[24]; // 6 個 float 各佔 4 bytes
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

      delay(5); // 控制頻率，可視需求調整
    }

    Serial.println("Central disconnected");
  }
}
