#!/usr/bin/python
import os, time
import usb.core
import usb.util
import pygtk
pygtk.require('2.0')
import gtk
from sys import exit
import math

DATA_MODE_GRAMS = 2
DATA_MODE_OUNCES = 12

# DYMO S400
VENDOR_ID = 0x0922
PRODUCT_ID = 0x8009

IS_CONNECTED_TO_SCALE = False

def main():
    try:
        dev = connect_to_scale()
        hostile_takeover_scale(dev)
        
        #read away!
        read_from_scale(dev)
            
    except KeyboardInterrupt as e:
            print "\nQuitting.."
            exit()

def hostile_takeover_scale(dev):
    interface = 0
    if dev.is_kernel_driver_active(interface) is True:
        print("Detaching kernel driver...")
        dev.detach_kernel_driver(interface)
        dev.set_configuration() #default configs
        usb.util.claim_interface(dev, interface) #hostile takeover

def connect_to_scale():
    print("Attempting to connect to scale...")
    dev = usb.core.find(idVendor=VENDOR_ID,
                       idProduct=PRODUCT_ID)
    
    if dev is None:
        time.sleep(5.0)
        return connect_to_scale()
    else:
        return dev

def read_from_scale(dev):
    sleep_time = .5
    stable_sleep_time = 3
    previous_weight = 0
    weight = 0

    total_time_at_weight = 0
    
    print "listening for weight..."

    while True:
        time.sleep(sleep_time)

        weight = 0

        data = read_scale_weight(dev)

        if data is None:
            print("Device lost, disconnecting")
            main() #restart the program!
            break
        
        if data != None:
            weight = data[4] + data[5] * 256
        
        if weight == previous_weight:
            total_time_at_weight += sleep_time
            if total_time_at_weight == stable_sleep_time:
                process_scale_weight(data[2], weight, True)
            continue
        else:
            total_time_at_weight = 0
            preview_weight = weight
            process_scale_weight(data[2], weight, False)

        #only process weights that arent the same as the previ
        previous_weight = weight


def read_scale_weight(dev):
    try:
        # first endpoint
        endpoint = dev[0][(0,0)][0]

        # read a data packet
        attempts = 0
        data = None
        
        while data is None and attempts < 10:
            try:
                data = dev.read(endpoint.bEndpointAddress,
                                   endpoint.wMaxPacketSize)
            except usb.core.USBError as e:
                print(str(e))
                data = None

        return data
    except usb.core.USBError as e:
        print "USBError: " + str(e.args)
    except IndexError as e:
        print "IndexError: " + str(e.args)

def process_scale_weight(mode, weight, stable):
    weight = weight * .1
    formatted_weight_mode = "pounds" if mode == DATA_MODE_OUNCES else "kilograms"
    print("STABLE = " + str(stable) + " Weight is currently: " + str(weight) + " " + formatted_weight_mode)

main()
