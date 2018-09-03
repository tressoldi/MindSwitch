#MINDSWITCH OPEN SOURCE SOFTWARE
#Created by Andrea Pagnin; email: andrepagnin31@gmail.com
#All rights reserved to Patrizio Tressoldi; email: patrizio.tressoldi@unipd.it

#This Software allow to test the performance of the Frequency monobit test and the Runs Test
# in detecting the randomness of strings of random series of 0 and 1 obtained from a TrueRNG

import serial
import binascii
import mpmath
import time
import datetime



from serial.tools import list_ports


#Print our Principal Header
print('MIND SWITCH - 1.0.0')
print('==================================================')



#Extract the Variables from the "Calibration.txt"
cal = open('Calibration.txt', 'r')


cal.readline()

#Number of bits/sec from the TrueRNG (>400000 bit/sec)
v = int(cal.readline())

cal.readline()

#Amount of Time of data acquisition in seconds (T)
T = int(cal.readline())

cal.readline()

#Time Interval for data analyses in seconds(y)
y = int(cal.readline())

cal.readline()

#Cut-off value for the Frequency Monobit Test (default=0.01)
cutofffr = float(cal.readline())

cal.readline()

#Cut-off value for the Runs Test (default=0.01)
cutoffru = float(cal.readline())


# Create ports variable as dictionary
ports=dict()  

# Call list_ports to get com port info 
ports_avaiable = list(list_ports.comports())

# Set default of None for com port
rng_com_port = None

# Loop on all available ports to find TrueRNG
for temp in ports_avaiable:
    if temp[1].startswith("TrueRNG"):
        print('Found:           ' + str(temp))
        if rng_com_port == None:        # always chooses the 1st TrueRNG found
            rng_com_port=str(temp[0])

# Print which port we're using
print('Using com port:  ' + str(rng_com_port))



#FREQUENCY MONOBIT TEST


#The length of the bit string
n = 0

measure1 = time.time()
measure2 = time.time()

count = 0

r = 0

C = T/y


#Variables set for calculate the total Random or Not Random Reads
randomf = 0

nrandomf = 0

randomr = 0

nrandomr = 0


#Write on "MinSwitchDataAnalisis.txt" the output information about the tests
out_file = open('MindSwitchDataAnalisis.txt','w')



while count < C:

    

    if measure2 - measure1 >= y:

        out_file.write('\n')
        out_file.write('\n')
        out_file.write('FREQUENCY MONOBIT TEST')
        out_file.write('\n')


        #Increment of n.bit read at a certain speed (over 350kbit/sec)
        n = n + (v*y)
        

        # Print our header
        print(' ')
        print(' ')
        print('Frequency (Monobit) Test - 1.0.0')
        print('==================================================')

       
        r = r + 1

        readn = 'Read n.'  +  str(r) 
        
        print(readn)
        print('')
        
        dtn = datetime.datetime.now()
        print(dtn)
        
        
        measure1 = measure2
        measure2 = time.time()
        count += 1

        # Size of block for each loop 
        blocksize = n/8


        # Number of loops (default=1)
        numloops=1 
        

        print('==================================================')


        # Print General Information
        
        print('Total Time for data acquiring:      ' + str(T) + ' Seconds')
        print('Interval Time for every read:       ' + str(y) + ' Seconds')
        print('Cut-Off Value =                     ' + str(cutofffr))  
        print('Length of the bit string:           ' + str(n) + ' Bit' )
        print('Number of loops:                    ' + str(numloops))
        print('Total size:                         ' + str(blocksize * numloops) + ' Bytes')
        print('Writing to:                         random.bin')
        print('==================================================')

        # Open/create the file random.bin in the current directory with 'write binary'
        fp=open('random.bin','wb')

        # Print an error if we can't open the file
        if fp==None:
            print('Error Opening File!')
    
        # Try to setup and open the comport
        try:
            ser = serial.Serial(port=rng_com_port,timeout=10)  # timeout set at 10 seconds in case the read fails
        except:
            print('Port Not Usable!')
            print('Do you have permissions set to read ' + rng_com_port + ' ?')
    
        # Open the serial port if it isn't open
        if(ser.isOpen() == False):
            ser.open()

        # Set Data Terminal Ready to start flow
        ser.setDTR(True)   
    
        # This clears the receive buffer so we aren't using buffered data
        ser.flushInput()    

        # Keep track of total bytes read
        totalbytes=0

        # Loop 
        for _ in range(numloops):

            # Try to read the port
            try:
       
                x=ser.read(blocksize)   # read bytes from serial port 
        
            except:
                print('Read Failed!!!')
                break

            # Update total bytes read
            totalbytes +=len(x)

            # If we were able to open the file, write to disk
            if fp !=0:
                fp.write(x)
        
        print('Read Complete:')
        print('')

        

        # Close the serial port
        ser.close()


        # If the file is open then close it
        if fp != 0:
            fp.close()

        
        # Convert the file to real binary data
        fp_ = open('random.bin', 'rb')
        with fp_:
            byte = fp_.read()
            hexadecimal = binascii.hexlify(byte)
            decimal = int(hexadecimal, 16)
            binary = bin(decimal)[2:].zfill(8)
            data = "%s" % (binary)
            
            
        fp.close()


        #Calculate Sn 
        i = 0
        dig = 0
        sum = 0
        Co=0
        x=0


        num = int(data)


        for x in str(num):

            if x=='0':
    
                Co = Co + 1
                

        while(num > 0):

        
            dig = int(num%10)
            sum = sum+dig
            num = num/10
    

        Sn = sum - Co

        print('S' + str(n) + ' = '  + str(Sn)) 


        


        #Calculate S(obs)

        So = abs(Sn)/mpmath.sqrt(n)

        print('S' + '(obs) = ' + str(So))    
        


        #Inizialize the P-Value
        pv = mpmath.erfc(So/mpmath.sqrt(2))


        print('==================================================')

        print('The Results: ')
        print('')
        print('P-Value = ' + str(pv))


        
        if pv >= cutofffr:

            print('Since P-Value >=' + str(cutofffr) + ', accept the sequence as Random')
            
            read = readn + str(' = R')
            out_file.write(read + '       ' + str(dtn))
            out_file.write('\n')

            randomf = randomf + 1
            
        else:


            print('Since P-Value <' + str(cutofffr) + ', accept the sequence as Not Random')
            
            read = readn + str(' = NR')
            out_file.write(read + '       ' + str(dtn))
            out_file.write('\n')

            nrandomf = nrandomf + 1


      

        print(' ')
        print(' ')


        out_file.write('\n')
        out_file.write('\n')
        out_file.write('RUNS TEST')
        out_file.write('\n')


        #RUNS TEST


        # Print our header
        print('Runs Test - 1.0.0')
        print('==================================================')

        
        print(readn)
        print('')

        dtn = datetime.datetime.now()
        print(dtn)
        
        

        print('==================================================')


        # Print General Information
        
        print('Total Time for data acquiring:      ' + str(T) + ' Seconds')
        print('Interval Time for every read:       ' + str(y) + ' Seconds')
        print('Total Reads:                        ' + str(C))
        print('Cut-Off Value =                     ' + str(cutoffru))  
        print('Length of the bit string:           ' + str(n) + ' Bit' )
        print('Number of loops:                    ' + str(numloops))
        print('Total size:                         ' + str(blocksize * numloops) + ' Bytes')
        print('Writing to:                         random.bin')
        print('==================================================')
    
                
        
        print('Read Complete:')
        print('')

        

        #Calculate  Pi(i)
        i = 0
        dig = 0
        sum = 0

        num = int(data)

    
        while(num > 0):
        
            dig = int(num%10)
            sum = sum+dig
            num = num/10
    

        p=float(sum)/n

        print('Pi = ' + str(p))



        #Calculate Vn(obs)

        c = float(n)/10
        V = sum + c

        print('V' + str(n) + '(obs) = '  + str(V))    
        


        #Inizialize the P-Value

        w = mpmath.sqrt(2*n)
        a = abs(V-2*n*p*(1-p))
        x = 2*w*p*(1-p)
        pv = mpmath.erfc(a/x)


        print('==================================================')

        print('The Results: ')
        print('')
        print('P-Value = ' + str(pv))
        

        

        if pv >= cutoffru:

            print('Since P-Value >=' + str(cutoffru) + ', accept the sequence as Random')

            read = readn + str(' = R')
            out_file.write(read + '       ' + str(dtn))
            out_file.write('\n')

            randomr = randomr + 1 

        else:


            print('Since P-Value <' + str(cutoffru) + ', accept the sequence as Not Random')
    
            read = readn + str(' = NR')
            out_file.write(read + '       ' + str(dtn))
            out_file.write('\n')

            nrandomr = nrandomr + 1


        
            
            

    else:
        measure2 = time.time()


out_file.write('\n')
out_file.write('\n')
out_file.write('\n')
out_file.write('\n')
out_file.write('FREQUENCY MONOBIT TEST')
out_file.write('\n')
out_file.write('Total Reads:  '+ str(C))
out_file.write('\n')
out_file.write('Total Random Reads: '+ str(randomf))
out_file.write('\n')
out_file.write('Total Non Random Reads: '+ str(nrandomf))
out_file.write('\n')
out_file.write('\n')
out_file.write('RUNS TEST')
out_file.write('\n')
out_file.write('Total Reads:  '+ str(C))
out_file.write('\n')
out_file.write('Total Random Reads: '+ str(randomr))
out_file.write('\n')
out_file.write('Total Non Random Reads: '+ str(nrandomr))
out_file.write('\n')        
out_file.close()
cal.close()         





print(' ')

print('FINISHED!')

print(' ')
