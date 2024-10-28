#!/usr/bin/python3
import serial
import json
import btfpy
import numpy as np
from mpu6050 import mpu6050

# ********** Bluetooth mouse **********
# From https://github.com/petzval/btferret
#   Build btfpy.so module - instructions in README file
#
# Download
#   mouse.py
#   mouse.txt
# 
# Edit mouse.txt to set ADDRESS=
# to the address of the local device
# that runs this code
#
# Run
#   sudo python3 mouse.py
#
# Connect from phone/tablet/PC to "HID" device
#
# Arrow keys move cursor. ESC stops server
# Button press  F1 = Left   F2 = Middle   F3 = Right
# Pg Up/Pg Dn  Increase/Decrease cursor step distance per key press
#
# This code sets an unchanging random address.
# If connection is unreliable try changing the address.
#
# See HID Devices section in documentation for 
# more infomation.
#
# ********************************    


#*********  mouse.txt DEVICES file ******
#DEVICE = My Pi   TYPE=Mesh  node=1  ADDRESS = DC:A6:32:04:DB:56
#  PRIMARY_SERVICE = 1800
#    LECHAR=Device Name   SIZE=4   Permit=02 UUID=2A00  
#    LECHAR=Appearance    SIZE=2   Permit=02 UUID=2A01  
#  PRIMARY_SERVICE = 180A
#    LECHAR= PnP ID       SIZE=7 Permit=02 UUID=2A50  
#  PRIMARY_SERVICE = 1812
#    LECHAR=Protocol Mode   SIZE=1  Permit=06  UUID=2A4E  
#    LECHAR=HID Info        SIZE=4  Permit=02  UUID=2A4A  
#    LECHAR=HID Ctl Point   SIZE=8  Permit=04  UUID=2A4C  
#    LECHAR=Report Map      SIZE=52 Permit=02  UUID=2A4B  
#    LECHAR=Report1         SIZE=3  Permit=92  UUID=2A4D  
#        ; Report1 must have Report ID = 1 
#        ;   0x85, 0x01 in Report Map
#        ; unsigned char uuid[2]={0x2A,0x4D};
#        ; index = find_ctic_index(localnode(),UUID_2,uuid);
#        ; Send data: write_ctic(localnode(),index,data,0);
#********/


#**** MOUSE REPORT MAP *****
# From Appendix E.10 in the following:
# https://www.usb.org/sites/default/files/documents/hid1_11.pdf
# Report ID = 1 has been added (0x85,0x01)
# NOTE the size of reportmap (52 in this case) must appear in mouse.txt as follows:
#    LECHAR=Report Map      SIZE=52 Permit=02  UUID=2A4B  
reportmap = [0x05,0x01,0x09,0x02,0xA1,0x01,0x85,0x01,0x09,0x01,0xA1,0x00,0x05,0x09,0x19,0x01,\
             0x29,0x03,0x15,0x00,0x25,0x01,0x95,0x03,0x75,0x01,0x81,0x02,0x95,0x01,0x75,0x05,\
             0x81,0x01,0x05,0x01,0x09,0x30,0x09,0x31,0x15,0x81,0x25,0x7F,0x75,0x08,0x95,0x02,\
             0x81,0x06,0xC0,0xC0]

   # NOTE the size of report (3 in this case) must appear in keyboard.txt as follows:
   #   LECHAR=Report1         SIZE=3  Permit=92  UUID=2A4D  
report = [0,0,0]

name = "HID"
appear = [0xC2,0x03]  # 03C2 = mouse icon appears on connecting device 
pnpinfo = [0x02,0x6B,0x1D,0x46,0x02,0x37,0x05]
protocolmode = [0x01]
hidinfo = [0x01,0x11,0x00,0x02]
reportindex = -1
node = 0
xydel = 8   # cursor step size

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
def read_from_serial():
  global ser
  if ser.in_waiting > 0:
      line = ser.readline().decode('utf-8').rstrip()
      return json.loads(line)
  return None

imu_baseline = {'x': 0, 'y': 0, 'z': 0}
imu = mpu6050(0x68)
def process_data(finger_data):
  thresh = 1000
  # calibrate IMU when hand is open
  if all([finger_data[f] for f in finger_data.keys()]) > thresh or imu_baseline is None:
    imu_baseline = imu.get_gyro_data()
    return 0, 0
  
  # use IMU when hand is closed
  elif all([finger_data[f] for f in finger_data.keys()]) < thresh:
    imu_data = imu.get_gyro_data()
    dx = int(imu_baseline['x'] - imu_data.x)
    dy = int(imu_baseline['x'] - imu_data.y)
    return dx, dy
  
  else:
    return 0, 0


def lecallback(clientnode,op,cticn):
  global xydel
      
  if(op == btfpy.LE_CONNECT): 
    print("Connected OK. X stops server.")

  if(op == btfpy.LE_TIMER):
    data = read_from_serial()
    dx,dy = 0,0
    if data:
      dx,dy = process_data(data)
    
    send_key(dx,dy,0) # 0 constant since we won't use keyboard

  if(op == btfpy.LE_DISCONNECT):
    return(btfpy.SERVER_EXIT)
  return(btfpy.SERVER_CONTINUE)

#*********** SEND KEY *****************

def send_key(x,y,but):
  global reportindex
  global node

  # convert signed xy to signed byte
  if(x < 0):
    ux = x + 256
  else:
    ux = x
    
  if(y < 0):
    uy = y + 256
  else:
    uy = y
           
  # send to Report1
  btfpy.Write_ctic(node,reportindex,[but,ux,uy],0)
  if(but != 0):
    # send no button pressed - all zero
    btfpy.Write_ctic(node,reportindex,[0,0,0],0) 
  return


############ START ###########
   
if(btfpy.Init_blue("mouse.txt") == 0):
  exit(0)

if(btfpy.Localnode() != 1):
  print("ERROR - Edit mouse.txt to set ADDRESS = " + btfpy.Device_address(btfpy.Localnode()))
  exit(0)
      
node = btfpy.Localnode()    

# look up Report1 index
uuid = [0x2A,0x4D]
reportindex = btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid)
if(reportindex < 0):
  print("Failed to find Report characteristic")
  exit(0)

  # Write data to local characteristics  node=local node
uuid = [0x2A,0x00]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),name,0) 

uuid = [0x2A,0x01]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),appear,0) 

uuid = [0x2A,0x4E]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),protocolmode,0)

uuid = [0x2A,0x4A]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),hidinfo,0)

uuid = [0x2A,0x4B]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),reportmap,0)

uuid = [0x2A,0x4D]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),report,0)

uuid = [0x2A,0x50]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid),pnpinfo,0)
                            
  # Set unchanging random address by hard-coding a fixed value.
  # If connection produces an "Attempting Classic connection"
  # error then choose a different address.
  # If set_le_random_address() is not called, the system will set a
  # new and different random address every time this code is run.  
 
  # Choose the following 6 numbers
  # 2 hi bits of first number must be 1
randadd = [0xD3,0x56,0xD3,0x15,0x32,0xA0]
btfpy.Set_le_random_address(randadd)
     
btfpy.Set_le_wait(20000)  # Allow 20 seconds for connection to complete
                                         
btfpy.Le_pair(btfpy.Localnode(),btfpy.JUST_WORKS,0)  # Easiest option, but if client requires
                                                     # passkey security - remove this command  

btfpy.Le_server(lecallback,1)
  
btfpy.Close_all()
