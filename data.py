import serial
import json
import sys
import csv
from mpu6050 import mpu6050

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

imu = mpu6050(0x68)

with open('reader.log', 'a') as f:
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            data = json.loads(line)
            print(f'Finger 1: {data["finger1"]}')
            print(f'Finger 2: {data["finger2"]}')
            print(f'Finger 3: {data["finger3"]}')
            print(f'Finger 4: {data["finger4"]}')
            print(f'Finger 5: {data["finger5"]}\n')

        #print(f'Accelerometer: {imu.get_accel_data()}')
        data = imu.get_gyro_data()
        x = data['x']
        y = data['y']
        z = data['z']
        #print(f'x: {x:08.4f}\ty: {y:08.4f}\tz: {z:08.4f}')
