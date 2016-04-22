#!/usr/bin/python
import os, time
import usb.core
import usb.util
import pygtk
pygtk.require('2.0')
import gtk
from sys import exit
import math

def main():
    try:
        dev = connect_to_scale()

        interface = 0
        if dev.is_kernel_driver_active(interface) is True:
            print("Detaching kernel driver...")
            dev.detach_kernel_driver(interface)
            dev.set_configuration() #default configs
            usb.util.claim_interface(dev, interface) #hostile takeover

        #read away!
        read_from_scale(dev)
            
    except KeyboardInterrupt as e:
            print "\nQuitting.."
            exit()

def connect_to_scale():
    # DYMO M25
    VENDOR_ID = 0x0922
    PRODUCT_ID = 0x8003
    
    print("Attempting to connect to scale...")
    dev = usb.core.find(idVendor=VENDOR_ID,
                       idProduct=PRODUCT_ID)
    
    if dev is None:
        time.sleep(5.0)
        return connect_to_scale()
    else:
        return dev

def read_from_scale(dev):
    DATA_MODE_GRAMS = 2
    DATA_MODE_OUNCES = 11
        
    previous_weight = 0
    weight = 0
    
    print "listening for weight..."

    while True:
        time.sleep(.5)

        weight = 0
        print_weight = ""

        data = read_scale_weight(dev)

        if data == "ERROR":
            print("Device lost, disconnecting")
            main() #restart the program!
            break
        
        if data != None:
            weight = data[4] + data[5] * 256
        
        if weight == previous_weight:
            continue

        previous_weight = weight
        
        if data[2] == DATA_MODE_OUNCES:
            weight = math.ceil((weight * 0.1))
        elif data[2] == DATA_MODE_GRAMS:
            weight = math.ceil(weight)

        process_scale_weight(data[2], weight)


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
                data = None
                #if e.args == ('Operation timed out',):
                #    print("IM HERE")
                #    attempts -= 1
                #    print "timed out... trying again"
                #    continue
                #else:
                #    print(e.args)
                #Assume any exception is bad and just tick up the attempts
                return "ERROR"

        return data
    except usb.core.USBError as e:
        print "USBError: " + str(e.args)
    except IndexError as e:
        print "IndexError: " + str(e.args)

def process_scale_weight(mode, weight):
    DATA_EMPTY_POT_WEIGHT_GRAMS = 10 #1950 #technically 1938 - but a little rounding for that half cup won't hurt
    DATA_EMPTY_POT_WEIGHT_OUNCES = 20 #19.5 technically - but the math.ceil will account for this!
    
    DATA_MODE_GRAMS = 2
    DATA_MODE_OUNCES = 11

    if weight == 0:
        print("No coffee pot on the scale")
    else:
        empty_pot = False
        weight_type = None
        remaining_coffee = 0
        if mode == DATA_MODE_OUNCES:
            empty_pot = weight <= DATA_EMPTY_POT_WEIGHT_OUNCES
            weight_type = "ounces"
            remaining_coffee = weight - DATA_EMPTY_POT_WEIGHT_OUNCES
        elif mode == DATA_MODE_GRAMS:
            empty_pot  = weight <= DATA_EMPTY_POT_WEIGHT_GRAMS
            weight_type = "grams"
            remaining_coffee = weight - DATA_EMPTY_POT_WEIGHT_GRAMS
            
        if empty_pot is True:
            print("No more coffee")
            
        else:
            print "{} {} of coffee remaining".format(remaining_coffee, weight_type)

main()
