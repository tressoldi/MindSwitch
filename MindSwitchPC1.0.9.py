# MINDSWITCH OPEN SOURCE SOFTWARE
# Created by Luca Semenzato; luca.semenzato@unipd.it
# All rights reserved to Patrizio Tressoldi; email: patrizio.tressoldi@unipd.it

# This Software allow to test the performance of the Frequency monobit test and the Runs Test
# in detecting the randomness of strings of random series of 0 and 1 obtained from a TrueRNG

import os
import errno
import serial
import binascii
import winsound
import datetime
import configparser
import numpy as np
import time
import scipy.special as spc
from functools import reduce
from serial.tools import list_ports
import fnmatch
import os.path

file_conf = 'Calibration.ini'
file_analysis = 'MindSwitchDataAnalysis.csv'
file_dir = 'MindSwitch'
version = '1.0.9'

# Default configuration data
# Number of bits/sec from the TrueRNG (>400000 bit/sec)
bit_sec = 100
# Number of data samples (T)
tot_samples = 300
# Time Interval for data analyses in seconds(y)
int_time = 1
# Cut-off value for the Frequency Monobit Test (default=0.01)
cutoff_ft = 0.01
# Cut-off value for the Runs Test (default=0.01)
cutoff_rt = 0.01

csv_len = len(fnmatch.filter(os.listdir(os.path.dirname(os.path.realpath(__file__))), '*.csv'))
# Add hash to a file to create an always new file. Hash based on timestamp
def addhashtofile(file):
    import hashlib
    d = str(datetime.datetime.now())
    h = int(hashlib.sha256(d.encode('utf-8')).hexdigest(), 16) % 10**8
    file = str(csv_len) + "_" + file.split('.')[0] + '_' + str(h) + '.' + file.split('.')[1]
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
            print("Exception! Error: %s" % str(e1))
            dict1[option] = None
    return dict1


# Print our Principal Header
print('============= '+file_dir+' '+version+' ================')
print('==================================================')

config = configparser.ConfigParser()
try:
    # Extract the Variables from the Calibration file
    config.read(file_conf)
except Exception as e:
    print('Can\'t load calibration.ini. Error: %s' % str(e))
    print('Do you have permissions set to read the file?')
    exit(errno.ENOENT)
try:
    # Number of bits/sec from the TrueRNG (>400000 bit/sec)
    bit_sec = int(configsectionmap("Time")['bit_sec'])

    # Time Interval for data analyses in seconds(y)
    int_time = int(configsectionmap("Time")['int_time'])

    # Number of data samples (T)
    tot_samples = int(configsectionmap("Time")['tot_samples'])

    # Cut-off value for the Frequency Monobit Test (default=0.01)
    cutoff_ft = float(configsectionmap("Cutoff")['cutoff_ft'])

    # Cut-off value for the Runs Test (default=0.01)
    cutoff_rt = float(configsectionmap("Cutoff")['cutoff_rt'])
except Exception as e:
    print('Can\'t convert configuration values. Data format error? Error: %s' % str(e))
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

# Print which port we're using
print('Using com port:  ' + str(rng_com_port))


# The length of the bit string
n = bit_sec*int_time
# Size of block for each loop
blocksize = int(n / 8)

# Number of loops (default=1)
numloops = blocksize

# time delay for each byte pick
delay_time = 1/(bit_sec/8)

measure1 = time.time()
measure2 = time.time()

count = 0

nRead = 0


# adding hash to out file
csv_len += 1
file_analysis = addhashtofile(file_analysis)
print('Analysis file: %s' % str(file_analysis))
out_file = None
try:
    # Write on "MinSwitchDataAnalysis.txt" the output information about the tests
    out_file = open(file_analysis, 'w')
except Exception as e:
            print('Can\'t open %s. Error: %s' % (file_analysis, str(e)))
            exit(errno.ENOENT)

out_file.write('DEBUG;')
out_file.write('Read;')
out_file.write('Frequency test;')
out_file.write('Runs test;')
out_file.write('Accuracy;')
out_file.write('Zero count;')
out_file.write('One count;')
out_file.write('Onset time;')
out_file.write('Timestamp')
out_file.write('\n')

while count < tot_samples:

    dtn = datetime.datetime.now()
    onset_time = measure2 - measure1

    print('TimeStamp: %s ' % str(dtn))
    print('Onset read time: %s' % str(onset_time))

    nRead = nRead + 1

    print('Read n. %d of %d' % (nRead, tot_samples))
    print('')

    count += 1

    # Print General Information
    print('==================================================')
    print('Total number of cycles:             %d ' % tot_samples)
    print('Interval Time for every read:       %d seconds' % int_time)
    print('Length of the bit string:           %d bit per read' % n)
    print('Number of loops:                    %d loops per read' % numloops)
    print('Total size:                         %d Bytes per read' % blocksize)
    print('One byte read every:                %s seconds' % delay_time)
    print('==================================================')

    ser = None
    # Try to setup and open the comport
    try:
        ser = serial.Serial(port=rng_com_port, timeout=10)  # timeout set at 10 seconds in case the read fails
    except Exception as e:
        print('Port Not Usable!Error: %s' % str(e))
        print('Do you have permissions set to read port: "%s" ?' % rng_com_port)
        debug_rand = True

    # Open the serial port if it isn't open
    if not ser.isOpen():
        try:
            ser.open()
        except Exception as e:
            print('Serial port NOT opened! Error: %s' % str(e))
            print('Do you have permissions set to read port: "%s" ?' % rng_com_port)
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
    zeroN = 0
    oneN = 0


    for _ in range(numloops):

        # Try to read the port
        # noinspection PyBroadException
        try:
            if not debug_rand:
                bytes_read = ser.read(1)  # read bytes from serial port
            else:
                bytes_read = os.urandom(int(1))

            # Convert bytes to bit
            hexadecimal = binascii.hexlify(bytes_read)
            decimal = int(hexadecimal, 16)
            binary = bin(decimal)[2:].zfill(8)
            data += "%s" % binary
            zeroN += binary.count('0')
            oneN += binary.count('1')

        except Exception as e:
            print('Read bytes failed! Error: %s' % str(e))
            break
        time.sleep(delay_time)
        # Debugging data byte to byte
        # print('Delay time: ' + str(time.time()-measure1))
        # print('Data: ' + str(data))

    print('Read Complete.')
    print('Total bytes read: %d' % len(bytes_read))
    print('')

    # Close the serial port
    ser.close()

    # Debugging data
    # print('Data: ' + str(data))

    # Starting test phase

    pValMB = monobitfrequencytest(data)
    print('P-Value = %.4f' % pValMB)
    pValRT = runstest(data)
    print('P-Value  = %.4f' % pValRT)
    accuracy = 2

    print('')
    print('The Results: ')
    print('')
    if pValMB < cutoff_ft or pValRT < cutoff_rt:
        accuracy = 1
        print('Since one or more P-Value < cutoff declared, accept the sequence as Not Random')
        if pValMB < cutoff_ft and pValRT < cutoff_rt:
            accuracy = 0
    else:
        print('Since all P-Value >= cutoff declared, accept the sequence as Random')
    print('')

    out_file.write(str(debug_rand) + ';')
    out_file.write(str(nRead) + ';')
    out_file.write(str(pValMB) + ';')
    out_file.write(str(pValRT) + ';')
    out_file.write(str(accuracy) + ';')
    out_file.write(str(zeroN) + ';')
    out_file.write(str(oneN) + ';')
    out_file.write(str(onset_time) + ';')
    out_file.write(str(dtn))
    out_file.write('\n')

    measure2 = time.time()

out_file.close()

print(' ')

print('FINISHED!')

print(' ')

# Final beep sound
frequency = 1400  # Set Frequency
duration = 1000  # Set Duration in ms
winsound.Beep(frequency, duration)
