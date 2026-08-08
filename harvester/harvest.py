import getpass
import os 
import sys
import socket
from getmac import get_mac_address as gma
import datetime

user_account = str(getpass.getuser())
device_name = str(socket.gethostname())
try:
    device_mac = str(gma())
except:
    device_mac = "Null"

device_ip = str(socket.gethostbyname(device_name))
sys_version = str(sys.version)
osname = "Windows "+ str(os.name)
playform_version = str(sys.getwindowsversion().platform_version)
last_used = str(datetime.datetime.now())
disabled = 0

def get_mac():
    device_mac = str(gma())
    return device_mac

def get_credentials():
    credentials = (user_account,device_name,device_mac,device_ip,disabled,last_used)
    return credentials

def get_specs():
    specs = (device_mac,device_ip,sys_version,osname,playform_version)
    return specs

def update_credentials():
    credentials = (device_ip,last_used,device_mac)
    return credentials