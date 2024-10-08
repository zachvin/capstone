from mpu6050 import mpu6050

imu = mpu6050(0x68)

while(1):
    print(f"ACCELERATION: {imu.get_accel_data()}")
    print(f"GYRO: {imu.get_gyro_data()}")
    print(f"TEMP: {imu.get_temp()}")
