import sys
sys.path.insert(1, './btferret')
import serial
import json
import btfpy
import numpy as np
import time
from mpu6050 import mpu6050


# ********** Bluetooth keyboard **********
# From https://github.com/petzval/btferret
#   Build btfpy.so module - instructions in README file
#
# Download
#   keyboard.py
#   keyboard.txt
# 
# Edit keyboard.txt to set ADDRESS=
# to the address of the local device
# that runs this code
#
# Run
#   sudo python3 keyboard.py
#
# Connect from phone/tablet/PC to "HID" device
#
# All keystrokes go to connecting device
# F10 sends "Hello" plus Enter
# ESC stops the server 
#
# To add a battery level service:
# uncomment all battery level labelled
# code in keyboard.txt and here.
# F10 will then also send a battery level notification
#
# Note: This code uses the lowest level of security.
# Do not use it if you need high security.
#
# Non-GB keyboards
# Even if the keyboard of this device is non-GB
# it must be specified as "gb" in the boot info as follows:
#
# Edit /etc/default/keyboard to include the line:
# XKBLAYOUT="gb"
#
# It is the receiving device that decides which
# characters correspond to which keys. See discussion
# in the HID Devices section of the documentation.
#
# This code sets an unchanging random address.
# If connection is unreliable try changing the address.
#
# See HID Devices section in documentation for 
# more infomation.
#
# ********************************    

#/*********  keyboard.txt DEVICES file ******
# DEVICE = My Pi   TYPE=Mesh  node=1  ADDRESS = DC:A6:32:04:DB:56
#  PRIMARY_SERVICE = 1800
#    LECHAR=Device Name   SIZE=4   Permit=02 UUID=2A00  
#    LECHAR=Appearance    SIZE=2   Permit=02 UUID=2A01  
#  PRIMARY_SERVICE = 180A
#    LECHAR= PnP ID       SIZE=7 Permit=02 UUID=2A50  
#  PRIMARY_SERVICE = 1812
#    LECHAR=Protocol Mode   SIZE=1  Permit=06  UUID=2A4E  
#    LECHAR=HID Info        SIZE=4  Permit=02  UUID=2A4A  
#    LECHAR=HID Ctl Point   SIZE=8  Permit=04  UUID=2A4C  
#    LECHAR=Report Map      SIZE=47 Permit=02  UUID=2A4B  
#    LECHAR=Report1         SIZE=8  Permit=92  UUID=2A4D  
#        ; Report1 must have Report ID = 1 
#        ;   0x85, 0x01 in Report Map
#        ; uuid = [0x2A,0x4D]
#        ; index = btfpy.Find_ctic_index(btfpy.Localnode(),btfpy.UUID_2,uuid)
#        ; Send data: btfpy.Write_ctic(btfpy.Localnode(),index,data,0)
#
# ;  *** Optional battery level ***
# ;  PRIMARY_SERVICE = 180F
# ;    LECHAR=Battery Level   SIZE=1 Permit=12  UUID=2A19   
#
# ********

# **** KEYBOARD REPORT MAP *****
# 0x05, 0x01 Usage Page (Generic Desktop)
# 0x09, 0x06 Usage (Keyboard)
# 0xa1, 0x01 Collection (Application)
# 0x85, 0x01 Report ID = 1
# 0x05, 0x07 Usage Page (Keyboard)
# 0x19, 0xe0 Usage Minimum (Keyboard LeftControl)
# 0x29, 0xe7 Usage Maximum (Keyboard Right GUI)
# 0x15, 0x00 Logical Minimum (0)
# 0x25, 0x01 Logical Maximum (1)
# 0x75, 0x01 Report Size (1)  
# 0x95, 0x08 Report Count (8)
# 0x81, 0x02 Input (Data, Variable, Absolute) Modifier byte
# 0x95, 0x01 Report Count (1)
# 0x75, 0x08 Report Size (8)
# 0x81, 0x01 Input (Constant) Reserved byte
# 0x95, 0x06 Report Count (6)
# 0x75, 0x08 Report Size (8)
# 0x15, 0x00 Logical Minimum (0)
# 0x25, 0x65 Logical Maximum (101)
# 0x05, 0x07 Usage Page (Key Codes)
# 0x19, 0x00 Usage Minimum (Reserved (no event indicated))
# 0x29, 0x65 Usage Maximum (Keyboard Application)
# 0x81, 0x00 Input (Data,Array) Key arrays (6 bytes)
# 0xc0 End Collection
#*******************

    # NOTE the size of reportmap (47 in this case) must appear in keyboard.txt as follows:
    #   LECHAR=Report Map      SIZE=47 Permit=02  UUID=2A4B  
reportmap = [0x05,0x01,0x09,0x06,0xA1,0x01,0x85,0x01,0x05,0x07,0x19,0xE0,0x29,0xE7,0x15,0x00,\
             0x25,0x01,0x75,0x01,0x95,0x08,0x81,0x02,0x95,0x01,0x75,0x08,0x81,0x01,0x95,0x06,\
             0x75,0x08,0x15,0x00,0x25,0x65,0x05,0x07,0x19,0x00,0x29,0x65,0x81,0x00,0xC0]

    # NOTE the size of report (8 in this case) must appear in keyboard.txt as follows:
    #   LECHAR=Report1         SIZE=8  Permit=92  UUID=2A4D  
report = [0,0,0,0,0,0,0,0]

name = "HID"
appear = [0xC2,0x03]  # 03C2 = mouse icon appears on connecting device 
pnpinfo = [0x02,0x6B,0x1D,0x46,0x02,0x37,0x05]
protocolmode = [0x01]
hidinfo = [0x01,0x11,0x00,0x02]
battery = [100] 
reportindex = -1
# reportindex2 = -1
node = 0

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
count = 0
def read_from_serial():
  global count
  if ser.in_waiting > 0:
      count += 1
      try:
          line = ser.readline().decode('utf-8').rstrip()
          return json.loads(line)
      except:
          print(f'Bad json data {count}')
          count = 0
          pass
  return None

imu = mpu6050(0x68)

def process_data(finger_data):
  global imu
  button = 0
  closed_thresh = 580
  thresh = 600
  open_thresh = 620

  bit_array = 0
    for i, num in enumerate(finger_data):
        if num > thresh:
            bit_array |= (1 << i)

  # If hand is in a fist return no mouse movement or button
  if bit_array == 0b10000 or bit_array == 0b00000
    return 0, 0, 0, 0, 1

  else:
    # get imu data
    imu_data = imu.get_gyro_data()
    dx = -int(imu_data['x']) if abs(int(imu_data['x'])) > 5 else 0
    dy = int(imu_data['y']) if abs(int(imu_data['y'])) > 5 else 0

    # scroll
    # elif finger_data.get('finger4') > thresh and finger_data.get('finger3') > thresh and finger_data.get('finger2') < thresh and finger_data.get('finger1') < thresh:
  elif bit_array == 0b01100: 
        # 6 = page up
        # 7 = page down
        print("SCROLL")
        return 0,0,0, 'a', 2
        if dy > 0:
            return 0,0,0, 6, 2
        else:
            return 0,0,0, 7, 2
			
    # click
    elif bit_array == 0b01000:
        print("CLICK")
        return 0, 0, 1, 0, 1

    return dx, dy, button, 0, 1

def lecallback(clientnode,op,cticn):
  global xydel
      
  if(op == btfpy.LE_CONNECT): 
    print("Connected OK. X stops server.")

  if(op == btfpy.LE_TIMER):
    data = read_from_serial()
    dx,dy = 0,0
    mode = 0
    key = 0
    if data:
      for key in data.keys():
          print(data[key], end='\t')
      print()
      if len(data.keys()) < 5:
          print('Not all data received.')
          return btfpy.SERVER_CONTINUE

      dx, dy, but, key, mode = process_data(data)
    else:
      print('No data from flex sensor')
      
    if mode == 1:
      try:
        send_key_mouse(dx,dy,but)
      except:
        print('Error in sending mouse')
        return(btfpy.SERVER_CONTINUE)
    else:
      try:
        send_key_keyboard(key)
      except:
        print('Error in sending keyboard')
        return(btfpy.SERVER_CONTINUE)

  if(op == btfpy.LE_DISCONNECT):
    return(btfpy.SERVER_EXIT)
  return(btfpy.SERVER_CONTINUE)

#*********** SEND KEY *****************
def send_key_mouse(x,y,but):
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

def send_key_keyboard(key):
  global reportindex2
  global node
  print("In keyboard func: " + key)
  
  hidcode = btfpy.Hid_key_code(key)
  if(hidcode == 0):
    return

  buf = [0,0,0,0,0,0,0,0] 
        
  # send key press to Report1
  buf[0] = (hidcode >> 8) & 0xFF  # modifier
  buf[2] = hidcode & 0xFF         # key code
  btfpy.Write_ctic(node,reportindex2,buf,0)
  # send no key pressed - all zero
  buf[0] = 0
  buf[2] = 0
  btfpy.Write_ctic(node,reportindex2,buf,0) 
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

uuid = [0x2A,0x4D]
btfpy.Write_ctic(node,btfpy.Find_ctic_index(node,btfpy.UUID_2,uuid) + 1,report2,0)

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

btfpy.Keys_to_callback(btfpy.KEY_ON,0)   # enable LE_KEYPRESS calls in lecallback
                                         # 0 = GB keyboard  

btfpy.Set_le_wait(20000)  # Allow 20 seconds for connection to complete
                                         
btfpy.Le_pair(btfpy.Localnode(),btfpy.JUST_WORKS,0)  # Easiest option, but if client requires
                                                     # passkey security - remove this command  

btfpy.Le_server(lecallback,1)
  
btfpy.Close_all()
