#!/usr/bin/python
import os, time
import usb.core
import usb.util
import pygtk
pygtk.require('2.0')
import gtk
from sys import exit
import math

#Configurations!
#Modes for the Dymo M25 g/oz
DATA_MODE_GRAMS = 2
DATA_MODE_OUNCES = 11

#Device IDs - lsusb to verify this is corrects
# DYMO M25
VENDOR_ID = 0x0922
PRODUCT_ID = 0x8003

TIME_RECONNECT = 5

#Take the measurements for the pot and give them here!
DATA_EMPTY_POT_WEIGHT_GRAMS = 10 #1950 #technically 1938 - but a little rounding for that half cup won't hurt
#could be more accurate for ounces - probably will be in the future
DATA_EMPTY_POT_WEIGHT_OUNCES = 20 #19.5 technically - but the math.ceil will account for this!

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
        listen_on_scale(dev)
            
    except KeyboardInterrupt as e:
            print "\nQuitting.."
            exit()

def connect_to_scale():
    print("Attempting to connect to scale...")
    dev = usb.core.find(idVendor=VENDOR_ID,
                       idProduct=PRODUCT_ID)
    
    if dev is None:
        time.sleep(TIME_RECONNECT)
        return connect_to_scale()
    else:
        return dev

def listen_on_scale(dev):
    previous_weight = 0
    weight = 0
    total_time_same_weight = 0
    
    print "Listening for weight..."

    while True:
        time.sleep(.5)

        weight = 0
        print_weight = ""

        data = read_scale_weight(dev)

        if data == "ERROR":
            print("Device lost, will attempt to reconnect...")
            main() #restart the program!
            break
        
        if data != None:
            weight = data[4] + data[5] * 256
        
        #Once it's the same weight for 3 seconds - we'll process that as "stable" and do some operations
        if weight == previous_weight:
            total_time_same_weight += 0.5
            if total_time_same_weight == 3.0:
                #get converted weight
                converted_weight = convert_scale_weight(weight, data[2])

                #log and process
                print "Stable weight: {} {}".format(converted_weight, ("grams" if data[2] == DATA_MODE_GRAMS else "ounces"))
                process_stable_weight(data[2], converted_weight)
            
            continue
        else:
            total_time_same_weight = 0

            #Data recording! Record the different weight fluctuations!
            print "Unstable weight: {} {}".format(convert_scale_weight(weight, data[2]), ("grams" if data[2] == DATA_MODE_GRAMS else "ounces"))

        previous_weight = weight

def convert_scale_weight(raw_weight, mode):
    if mode == DATA_MODE_OUNCES:
        #return math.ceil((raw_weight * 0.1))
        return raw_weight * 0.1
    elif mode == DATA_MODE_GRAMS:
        #return math.ceil(raw_weight)
        return raw_weight
        
    return weight #failsafe


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

def process_stable_weight(mode, weight):
    if weight == 0:
        #nothing on the scale state
        #print("No pot on the scale, must be getting refilled (or it better be!")
        math = 1
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
            
        #if empty_pot is True:
            #empty coffee state - do something about it
        #else:
            #remaining coffee state
            #print "{} {} of coffee remaining".format(remaining_coffee, weight_type)
            

main()
