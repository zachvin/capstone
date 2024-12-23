import serial
import json
import sys
import csv

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)

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
