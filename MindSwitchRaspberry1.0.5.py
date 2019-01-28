# MINDSWITCH OPEN SOURCE SOFTWARE
# Edited by Luca Semenzato; luca.semenzato@unipd.it
# All rights reserved to Patrizio Tressoldi; email: patrizio.tressoldi@unipd.it

# This Software must be installed in the Raspberry micro controller

import RPi.GPIO as GPIO
import errno
import serial
import binascii
import time
import datetime
import configparser
import numpy as np
import scipy.special as spc
from functools import reduce
from serial.tools import list_ports
import os, sys
import os.path
import fnmatch


GPIO.setmode(GPIO.BOARD)
GPIO.setup(3, GPIO.OUT)  # led --> finish
GPIO.setup(7, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(16, GPIO.OUT)  # audio


file_conf = 'CalibrationRaspberry.ini'
file_analysis = 'MindSwitchDataAnalysis.csv'
file_dir = 'MindSwitch'
version = '1.0.5'
csv_len = len(fnmatch.filter(os.listdir(os.path.dirname(os.path.realpath(__file__))), '*.csv'))

# detectiong USB flash to save data
media_path = '/media/pi'
dirs = os.listdir( media_path )
usbFind = False
for dirUSB in dirs:
    if os.path.exists(media_path+"/"+dirUSB+"/"+file_dir):
        usbFind = True
        csv_len = len(fnmatch.filter(os.listdir(media_path+"/"+dirUSB+"/"+file_dir), '*.csv'))
        file_analysis = str(media_path+"/"+dirUSB+"/"+file_dir+"/"+str(csv_len)+"_"+file_analysis)
        print("USB flash device properly detected.\nAnalysis file stored in: "+file_analysis)
if not usbFind:
    file_analysis = str(csv_len) + "_" + file_analysis
# Default configuration data
# Number of bits/sec from the TrueRNG (>400000 bit/sec)
bit_sec = 100
# A mount of Time of data acquisition in seconds (T)
tot_time = 10
# Time Interval for data analyses in seconds(y)
int_time = 1
# Cut-off value for the Frequency Monobit Test (default=0.01)
cutoff_ft = 0.01
# Cut-off value for the Runs Test (default=0.01)
cutoff_rt = 0.01
# Activate or deactivate the timer
light_switch = 1
# Timer for Led light automatic switching-off;
light_duration = 2


# Add hash to a file to create an always new file. Hash based on timestamp
def addhashtofile(file):
    import hashlib
    d = str(datetime.datetime.now())
    h = int(hashlib.sha256(d.encode('utf-8')).hexdigest(), 16) % 10**8
    file = file.split('.')[0] + '_' + str(h) + '.' + file.split('.')[1]
    return file


def sum_i(xi): return 2 * xi - 1


def su(xu, yu): return xu + yu


def sus(xu): return (xu - 0.5) ** 2


def sq(xq): return int(xq) ** 2


def logo(xo): return xo * np.log(xo)


def runstest(binin):

    print('==================================================')
    print('== Runs Test =====================================')
    print('==================================================')
    ss = [int(el) for el in binin]
    len_binin = len(binin)
    # sn = reduce(su, sc)
    sn = 0
    for i in ss:
        sn = sn + i
    pi = 1.0 * sn / len_binin
    vobs = len(binin.replace('0', ' ').split()) + len(binin.replace('1', ' ').split())
    pval = spc.erfc(abs(vobs-2*len_binin*pi*(1-pi)) / (2 * pi * (1 - pi) * np.sqrt(2*len_binin)))
    return pval


def monobitfrequencytest(binin):
    print('==================================================')
    print('== Monobit Frequency Test ========================')
    print('==================================================')
    ss = [int(el) for el in binin]
    # sc = map(sum_i, ss)
    sc = []
    for i in ss:
        sc.append(sum_i(i))
    # sn = reduce(su, sc)
    sn = 0
    for i in sc:
        sn = sn+i
    sobs = np.abs(sn) / np.sqrt(len(binin))
    pval = spc.erfc(sobs / np.sqrt(2))
    return pval


def configsectionmap(section):

    dict1 = {}
    options = config.options(section)
    for option in options:
        # noinspection PyBroadException
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except Exception as e1:
            print("Exception! Error:" + str(e1))
            dict1[option] = None
    return dict1


# Print our Principal Header
print('============= '+file_dir+' '+version+' ==================')
print('==================================================')

config = configparser.ConfigParser()
try:
    # Extract the Variables from the Calibration file
    config.read(file_conf)
except Exception as e:
    print('Can\'t load configuration.ini. Error: ' + str(e))
    print('Do you have permissions set to read the file?')
    exit(errno.ENOENT)
try:
    # Number of bits/sec from the TrueRNG (>400000 bit/sec)
    bit_sec = int(configsectionmap("Time")['bit_sec'])
    # A mount of Time of data acquisition in seconds (T)
    tot_time = int(configsectionmap("Time")['tot_time'])

    # Time Interval for data analyses in seconds(y)
    int_time = int(configsectionmap("Time")['int_time'])

    # Cut-off value for the Frequency Monobit Test (default=0.01)
    cutoff_ft = float(configsectionmap("Cutoff")['cutoff_ft'])

    # Cut-off value for the Runs Test (default=0.01)
    cutoff_rt = float(configsectionmap("Cutoff")['cutoff_rt'])

    # Activate or deactivate the timer
    light_switch = int(configsectionmap("Light")['light_switch'])

    # Timer for Led light automatic switching-off;
    light_duration = int(configsectionmap("Light")['light_duration'])

except Exception as e:
    print('Can\'t convert configuration values. Data format error? Error: ' + str(e))
    print('Do you write the configuration properly?')
    exit(errno.ENOEXEC)


# Create ports variable as dictionary
ports = dict()

# Call list_ports to get com port info
ports_available = list(list_ports.comports())

# Set default of None for com port
rng_com_port = None

# Debug random if rng_com_port is not allowable
debug_rand = False

# Loop on all available ports to find TrueRNG
for temp in ports_available:
    if temp[1].startswith("TrueRNG"):
        print('Found:           ' + str(temp))
        if not rng_com_port:  # always chooses the 1st TrueRNG found
            rng_com_port = str(temp[0])
    else:
        print ('Others ports:' + str(temp))
# Print which port we're using
print('Using com port:  ' + str(rng_com_port))

# The length of the bit string
n = bit_sec * int_time
# Size of block for each loop
blocksize = int(n / 8)
# Number of loops (default=1)
numloops = blocksize
# time delay for each byte pick
delay_time = 1/bit_sec

measure1 = time.time()
measure2 = time.time()

count = 0

nRead = 0

C = tot_time / int_time

# adding hash to out file
file_analysis = addhashtofile(file_analysis)

out_file = None
try:
    # Write on "MinSwitchDataAnalysis.txt" the output information about the tests
    out_file = open(file_analysis, 'w')
except Exception as e:
    print('Can\'t open ' + file_analysis + '. Error: ' + str(e))
    exit(errno.ENOENT)

out_file.write('DEBUG;')
out_file.write('Read;')
out_file.write('Frequency test;')
out_file.write('Runs test;')
out_file.write('Accuracy;')
out_file.write('Onset time;')
out_file.write('Timestamp')
out_file.write('\n')


GPIO.output(12, GPIO.HIGH)

while count < C and measure2 - measure1 < tot_time:

    if count * int_time <= measure2 - measure1 < tot_time:

        dtn = datetime.datetime.now()
        onset_time = measure2 - measure1

        print('TimeStamp_ ' + str(dtn))
        print('Onset read time: ' + str(onset_time))

        nRead = nRead + 1

        print('Read n. ' + str(nRead))
        print('')

        count += 1

        GPIO.output(7, GPIO.HIGH)

        # Print General Information
        print('==================================================')
        print('Total Time for data acquiring:      ' + str(tot_time) + ' Seconds')
        print('Interval Time for every read:       ' + str(int_time) + ' Seconds')
        print('Length of the bit string:           ' + str(n) + ' bit per read')
        print('Number of loops:                    ' + str(numloops))
        print('Total size:                         ' + str(blocksize) + ' Bytes')
        print('One byte read every:                %s seconds' % delay_time)
        print('==================================================')

        ser = None
        # Try to setup and open the comport
        try:
            ser = serial.Serial(port=rng_com_port, timeout=10)  # timeout set at 10 seconds in case the read fails
        except Exception as e:
            print('Port Not Usable!Error: ' + str(e))
            print('Do you have permissions set to read port: "' + str(rng_com_port) + '" ?')
            debug_rand = True

        # Open the serial port if it isn't open
        if not ser.isOpen():
            try:
                ser.open()
            except Exception as e:
                print('Serial port NOT opened! Error: ' + str(e))
                print('Do you have permissions set to read port: "' + str(rng_com_port) + '" ?')
                print('Continue in DEBUG MODE ON')
                debug_rand = True

        # Set Data Terminal Ready to start flow
        if not debug_rand:
            ser.setDTR(True)

        # This clears the receive buffer so we aren't using buffered data
        if not debug_rand:
            ser.flushInput()

        # Keep track of total bytes read
        totalbytes = 0

        # Loop
        bytes_read = bytes(0)
        hexadecimal = None
        decimal = None
        binary = None
        data = ""
        for _ in range(numloops):

            # Try to read the port
            # noinspection PyBroadException
            try:
                if not debug_rand:
                    bytes_read = ser.read(blocksize)  # read bytes from serial port
                else:
                    bytes_read = os.urandom(int(blocksize))

                # Convert bytes to bit
                hexadecimal = binascii.hexlify(bytes_read)
                decimal = int(hexadecimal, 16)
                binary = bin(decimal)[2:].zfill(8)
                data += "%s" % binary
            except Exception as e:
                print('Read bytes failed! Error: ' + str(e))
                break
            time.sleep(delay_time)
            # Debugging data byte to byte
            # print('Data: ' + str(data))

        print('Read Complete:')
        print('Total bytes read: ' + str(len(bytes_read)))
        print('')

        # Close the serial port
        ser.close()

        GPIO.output(7, GPIO.LOW)

        # Debugging data
        # print('Data: ' + str(data))

        # Starting test phase

        pValMB = monobitfrequencytest(data)
        print('P-Value = ' + str(pValMB))

        pValRT = runstest(data)
        print('P-Value  = ' + str(pValRT))

        accuracy = 0

        GPIO.output(12, GPIO.LOW)

        print('')
        print('The Results: ')
        print('')

        if pValMB >= cutoff_ft or pValRT >= cutoff_rt:
            accuracy = 1
            GPIO.output(3, GPIO.LOW)

        if pValMB >= cutoff_ft and pValRT >= cutoff_rt:
            accuracy = 2
            GPIO.output(3, GPIO.LOW)
            print('Since all P-Value >= cutoff declared, accept the sequence as Random')
        else:
            if light_switch == 1:
                GPIO.output(3, GPIO.HIGH)
                time.sleep(light_duration)
                GPIO.output(3, GPIO.LOW)
            else:
                GPIO.output(3, GPIO.HIGH)
            print('Since one or more P-Value < cutoff declared, accept the sequence as Not Random')

        out_file.write(str(debug_rand) + ';')
        out_file.write(str(nRead) + ';')
        out_file.write(str(pValMB) + ';')
        out_file.write(str(pValRT) + ';')
        out_file.write(str(accuracy) + ';')
        out_file.write(str(onset_time) + ';')
        out_file.write(str(dtn))
        out_file.write('\n')

    else:
        measure2 = time.time()

GPIO.output(3, GPIO.HIGH)
GPIO.output(7, GPIO.LOW)
GPIO.output(12, GPIO.LOW)
GPIO.output(16, GPIO.HIGH)
time.sleep(0.1)
GPIO.output(16, GPIO.LOW)

out_file.close()

print(' ')

print('FINISHED!')

print(' ')
