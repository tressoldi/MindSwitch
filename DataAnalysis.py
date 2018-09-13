#Input File
fp = open('DataFilterinput.txt', 'r')

fp.readline()

#First data of the interval
intf = str(fp.readline())

fp.readline()

#Second data of the interval
ints = str(fp.readline())

fp.readline()

T = int(fp.readline())


fp.readline()

y = int(fp.readline())


C = T/y

V = C*2

fp.close()

#File to Analized
out_file = open('MindSwitchDataAnalisis.txt','r')

#Output file
fo = open('DataFilteroutput.txt', 'w')

i = 0

count = 0

#First Loop to search the date and time info 
while i <= V:
        
    out_file.readline()
    out_file.readline()
    out_file.readline()

    dtnf = str(out_file.readline())

    #Read the position of the first data (intf) in the file
    if dtnf == intf:

        s = out_file.tell()
        f = s - 55

    #Count 
    if dtnf <= ints and dtnf >= intf:

        count = count + 1

        
    out_file.readline()
    
    i = i + 1


#Set the position of the out_file to start the writing 
out_file.seek(f)


i = 0

#Write only the data of the interval in the output file
while i < count:


    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
    fo.write(out_file.readline())
        
        
    
    
    i = i + 1


    
out_file.close()
fo.close()
