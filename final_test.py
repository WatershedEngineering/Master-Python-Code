######## main seabright dam code ############
# Last revised by PLK 6/1/2014 10:30
# Still to do: write plotly code for generators and temps
# alarm functions


import datetime
import time
import sys  
import smtplib  
import pymysql
import serial
import minimalmodbus
import plotly.plotly as py
import plotly.tools as tls 
from plotly.graph_objs import Stream
from plotly.graph_objs import Figure, Data, Layout, Scatter


#initializations
config_file_loc = "/opt/seabright/config.txt"

#all functions are below
  
def readconfigfile(filelocation):

#This function takes the location of config.txt as input and 
#returns a dictionary called configdict, with config variables
#as keys and the values as their values. configdict also
#includes the key 'returncode', whose value is a 0 if config.txt
#can't be found, a 1 if keys are missing from the dictionary,
#and a 2 if everything works. config.txt should be a text file,
#with each line formatted like this: 
#key : value 
    
    def configreadline(var_line, configdict): #reads a line of the config file and adds it to configdict
        #global configdict #makes configdict global
        var_line = var_line.replace(" ", "") #remove spaces from var_line
        var_line = var_line.strip('\n') #removes newline characters from var_line
        var_list = var_line.split(":") #changes var_line from a string into a two-part list, splitting it on either side of the colon
        configdict[var_list[0]] = var_list[1] #adds var_list to configdict, with var_list[0] as the key and var_list[1] the value
        return configdict
        
    configdict = {}  #dictionary to store config values
    
    try:
        f = open(config_file_loc, "r") #open the file config.txt in the cwd
    except:
        print "Can't find config file - error", 0 #if the file can't be found
        configdict['returncode'] = 0
    
    with open(config_file_loc,'r') as f: #run configreadline() on each line of config.txt and stop after the last line
        while True:
            line=f.readline()
            if not line: break
            configdict = configreadline(line, configdict)
    
    #make sure all they keys are in the dictionary that should be
    if ('db_host'in configdict and
        'db_passwd' in configdict and
        'db_user' in configdict and
        'db' in configdict and
        'plotly_username' in configdict and
        'plotly_pw' in configdict and
        'alarm_user_email' in configdict and
        'alarm_user_cell_email' in configdict and
        'gmail_user' in configdict and
        'gmail_pw' in configdict and
        'EKM1' in configdict and
        'EKM2' in configdict and
        'streaming_code_1' in configdict and
        'streaming_code_2' in configdict and
        'streaming_code_3' in configdict and 
        'streaming_code_4' in configdict and
        'streaming_code_5' in configdict and
        'streaming_code_6' in configdict and
        'streaming_code_7' in configdict and
        'streaming_code_8' in configdict and
        'streaming_code_9' in configdict and
        'streaming_code_10' in configdict and
        'streaming_code_11' in configdict and
        'streaming_code_12' in configdict and
        'streaming_code_13' in configdict and
        'streaming_code_14' in configdict and
        'upper_depth_offset' in configdict and
        'lower_depth_offset' in configdict and
        'abovedam_depth_up_alarm' in configdict and
        'abovedam_depth_down_alarm' in configdict and
        'belowdam_depth_up_alarm' in configdict and
        'rpm_port_1' in configdict and
        'rpm_port_2' in configdict and
        'EKM_port' in configdict and
        'depth_port' in configdict):
            
        print configdict 
        configdict['returncode'] = 2
        print 'all good -', 2
    else:
        print configdict    
        print "you're missing stuff - error", 1
        configdict['returncode'] = 1
    return configdict
    f.close() #close the file
    
    
# function to read depth. pass the serial port and the single digit address for the depth 
def readDepth(port,address):
    sensor = minimalmodbus.Instrument(port, address) # port name, slave address (in decimal) 
    #sensor1.debug = True # PRINT out hex chars sent and received
    sensor.serial.baudrate = 9600 #default is 19.2k so need to set this to 9600
    PReg = 2 # addr of Pressure 32bit fp 
    #TReg = 8 # addr of Temp signed 32bit fp
    
    #print sensor1   # print out all serial port paramters for debug
    
    Pressure = sensor.read_float(PReg) 
    #Temperature = sensor.read_float(TReg)
    
    #print "Pressure: " + str(Pressure) + " bar"
    #print "Temp: " + str(Temperature) + " degC"
    
    Depth = Pressure * 31.54 #1 bar = 33.54 feet of water
    #print Depth
    return Depth
    
#function to read the ekm data. Pass the ekm serial port and the sequence including id
def readEKM(EKMport, sequence):
	def parse_EKM(response): #takes the response and parses it
	

		d= {"Address":0, 
		"Total kWh":0.0,   
		"T1 kWh" : 0.0, 
		"T2 kWh" : 0.0,
		"T3 kWh": 0.0,
		"Tot Rev kWh" : 0.0,
		"T1 Rev kWh" : 0.0,
		"T2 Rev kWh" : 0.0,
		"T3 Rev kWh" : 0.0, 
		"V1" :0.0, 
		"V2" : 0.0,
		"V3": 0.0,
		"A1": 0.0,
		"A2": 0.0,
		"A3" : 0.0,
		"P1": 0.0,
		"P2" : 0.0,
		"P3" : 0.0,
		"Total Power":0.0,
		"Gen Status" : 0.0}

		def floatize8(string): #function for turning string
			length = len(string) #calculates the length of the string
			newstring = string[:-2] + "." + string[length-2:length] #inserts decimal point
			return newstring 
		def floatize4(string): #function for turning string
			length = len(string) #calculates the length of the string
			newstring = string[:-1] + "." + string[length-1:length] #inserts decimal point
			return newstring 
			
		if response == "":
			return d
		else:
			d["Address"]= response[11:16] #12
			d["Total kWh"] = floatize8(response[16:24]) #8
			d["T1 kWh"] = floatize8(response[24:32]) #8
			d["T2 kWh"] = floatize8(response[32:40]) #8
			d["T3 kWh"] = floatize8(response[40:48]) #8
			d["Tot Rev kWh"] = floatize8(response[56:64]) #8
			d["T1 Rev kWh"] = floatize8(response[64:72]) #8
			d["T2 Rev kWh"] = floatize8(response[72:80]) #8
			d["T3 Rev kWh"] = floatize8(response[80:88]) #8
			d["V1"] = floatize4(response[96:100]) #4
			d["V2"] = floatize4(response[100:104]) #4
			d["V3"] = floatize4(response[104:108]) #4
			d["A1"] = floatize4(response[108:113]) #5
			d["A2"] = floatize4(response[113:118]) #5
			d["A3"] = floatize4(response[118:123]) #5
			d["P1"] = response[123:130] #7
			d["P2"] = response[130:137] #7
			d["P3"] = response[137:144]
			d["Total Power"] = response[144:151] #7
			d["Gen Status"] = 1
			return d #returns the dictionary

	ser=serial.Serial(EKMport,baudrate=9600,parity=serial.PARITY_EVEN,bytesize=serial.SEVENBITS, timeout = 1) #setting up serial
	ser.write(sequence) #writes the request sequence
	response = ser.readline() #assigns the response a variable
	print response
	return parse_EKM(response) #returns the dictionary
	print d
	
#function to get RPM from a generator. Pass the serial port address 
#needs pyserial module
#only works if generator is running: DO NOT CALL if gen not running
def get_RPM(serial_port):
#Function to parse the RPM Data	
	def parse_RPM(string):
		new_string = string[11:15] #gets the digits need to get the RPM from the string
		rpm = float(new_string)/10 #makes string into a float		print rpm
		return rpm
	#Main code	
	ser = serial.Serial(serial_port, baudrate=9600,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,timeout=1) #assigns the serial
	print "opening "+serial_port
	data = ser.read(16)
	print "raw data from serial port:"+data
	ser.close()
	RPM = parse_RPM(data) #performs the parse RPM function
	print "generator rpm: "+str(RPM)
	return RPM
	

#function to send email 
def send_email(TO, GMAIL_USER, GMAIL_PASS, SUBJECT, TEXT):
	print("Sending email/text")
	smtpserver = smtplib.SMTP("smtp.gmail.com",587)
	smtpserver.ehlo()
	smtpserver.starttls()
	smtpserver.ehlo
	smtpserver.login(GMAIL_USER, GMAIL_PASS)
	header = 'To:' + TO + '\n' + 'From: ' + GMAIL_USER
	header = header + '\n' + 'Subject:' + SUBJECT + '\n'
	print header
	msg = header + '\n' + TEXT + ' \n\n'
	smtpserver.sendmail(GMAIL_USER, TO, msg)
	smtpserver.close() #function to send email 
	print("Sending email/text")
	smtpserver = smtplib.SMTP("smtp.gmail.com",587)
	smtpserver.ehlo()
	smtpserver.starttls()
	smtpserver.ehlo
	smtpserver.login(GMAIL_USER, GMAIL_PASS)
	header = 'To:' + TO + '\n' + 'From: ' + GMAIL_USER
	header = header + '\n' + 'Subject:' + SUBJECT + '\n'
	print header
	msg = header + '\n' + TEXT + ' \n\n'
	smtpserver.sendmail(GMAIL_USER, TO, msg)
	smtpserver.close()
	
	
def depth_alarm(depth, alarmdepth, highlow):
#pass the current depth wherever you're checking(above or below the dam) as depth
#pass the minimum or maximum depth that should set off an alarm (from the config file) as alarmdepth. 
#If a high water level should set off the alarm, enter "high" as highlow
#If a low water level should set off the alarm, enter "low" as highlow
#If the alarm level has been reached, this function returns a 1
#If the water level is acceptable, it returns a 2
#If the depth is neither above, below, or equal to the alarm value (I guess if it wasn't an integer or float)
#   It returns a zero. I don't know if this could ever happen.
#if highlow isn't either "high" or "low", it returns a 3.
    depth = float(alarmdepth)
    if highlow == 'high':
        
    	if depth >= alarmdepth:
            print "The water level is too high!"            
            return 1
        elif depth < alarmdepth:
            print "The water level isn't too high."            
            return 2
        else: 
            print "something's wrong with the depth"
            return 0
    elif highlow == 'low':
        if depth <= alarmdepth:
            print "The water level is too low!"
            print "depth =" + str(depth)
            print "alarmdepth = " + str(alarmdepth)
            return 1
        elif depth > alarmdepth:
            print "The water level isn't too low."            
            return 2
        else:
            print "something's wrong with the depth"            
            return 0
    else:
        print "depth_alarm() should be called with highlow as either 'high' or 'low.'"
        return 3


#write to database function 


       	
def saveToDatabase(data, db):
	ekm1 = data["ekmd1"]
	ekm2 = data["ekmd2"]
	now = datetime.now()
	time = str(now.hour) + ":" + str(now.minute) 
	date = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
	#insert_string = """INSERT INTO seabright_data (Date, Time, `Temp 1`, `Temp 2`, `RPM 1`, `Depth 1`, `Depth 2`, A1, A2, A3, `KWH 1`, `KWH 2`,`KWH 3`, V1, V2, V3, TotalKWH, Totrev, T1, T2, T3, P1, P2, P3, Power,`Gen Status`) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""" % (date,time,Temp1, Temp2, RPM1, Depth1, Depth2, A1, A2, A3, KWH1, KWH2, KWH3, V1, V2, V3, TotalKWH, Totrev, T1, T2, T3, P1, P2, P3, Power, GenStatus)
	insert_string1 = """INSERT INTO seabright_data (Date, Time, Temp1, Temp2, RPM1, RPM2, Depth1, Depth2, A1, A2, A3, KWH1, KWH2,KWH3, V1, V2, V3, TotalKWH, Totrev, T1, T2, T3, P1, P2, P3, Power, GenStatus) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""  % ('Date', 'Time', data["Temp1"],data["Temp2"], data["RPM1"], data["RPM2"],data["topDepth"],data["bottomDepth"],ekm1["A1"], ekm1["A2"], ekm1["A3"], ekm1["T1_kWh"], ekm1["T2_kWh"], ekm1["T3_kWh"], ekm1["V1"], ekm1["V2"],ekm1["V3"], ekm1["Total_kWh"], ekm1["Tot_Rev_kWh"], ekm1["T1_Rev_kWh"], ekm1["T2_Rev_kWh"], ekm1["T3_Rev_kWh"], ekm1["P1"], ekm1["P2"], ekm1["P3"], ekm1["Total_Power"], ekm1["Gen_Status"])
	insert_string2 = """INSERT INTO seabright_data2 (Date, Time, Temp1, Temp2, RPM1, RPM2, Depth1, Depth2, A1, A2, A3, KWH1, KWH2,KWH3, V1, V2, V3, TotalKWH, Totrev, T1, T2, T3, P1, P2, P3, Power, GenStatus) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""  % ('Date', 'Time', data["Temp1"],data["Temp2"], data["RPM1"], data["RPM2"],data["topDepth"],data["bottomDepth"],ekm2["A1"], ekm2["A2"], ekm2["A3"], ekm2["T1_kWh"], ekm1["T2_kWh"], ekm2["T3_kWh"], ekm2["V1"], ekm2["V2"],ekm2["V3"], ekm2["Total_kWh"], ekm2["Tot_Rev_kWh"], ekm2["T1_Rev_kWh"], ekm2["T2_Rev_kWh"], ekm2["T3_Rev_kWh"], ekm2["P1"], ekm2["P2"], ekm2["P3"], ekm2["Total_Power"], ekm2["Gen_Status"])
	print insert_string 
	cursor = db.cursor()
	try:
		cursor.execute(insert_string1)
		db.commit()
		print "added to data base"
	except:     
		db.rollback()
		print "exception occured"
 		
	try:
		cursor.execute(insert_string2)
		db.commit()
		print "added to data base"
	except:
		db.rollback()
		print "exception occured"

	
	
####### Plotly functions below ##########      
  
#plotly setup function
def setup_plotly(config):       
	tls.set_credentials_file(username=config["plotly_username"], 
                         api_key=config["plotly_pw"]) #set up plotly credentials
	# Read credentials
	creds = tls.get_credentials_file() 
	#Sign in to Plotly from API
	py.sign_in(creds['username'], creds['api_key'])
	tls.set_credentials_file(stream_ids=[config["streaming_code_1"],config["streaming_code_2"],
		config["streaming_code_3"],config["streaming_code_4"],config["streaming_code_5"],
		config["streaming_code_6"],config["streaming_code_7"],config["streaming_code_8"],
		config["streaming_code_9"],config["streaming_code_10"],config["streaming_code_11"],
		config["streaming_code_12"]])   #replace with your stream_id

	return tls.get_credentials_file()['stream_ids']
	
#plotly depth code
def plot_depth(stream_ids,data,AT):
	#grab two streaming codes
	depth1_stream_id = stream_ids[0]
	depth2_stream_id = stream_ids[1]

	#set the streaming codes for each plot
	depth1_stream = Stream(token=depth1_stream_id) 
	depth2_stream = Stream(token=depth2_stream_id)
	
	#configure the plots
	depth1 = Scatter(x=[], y=[], mode='lines+markers', stream=depth1_stream)
	depth2 = Scatter(x=[], y=[], mode='lines+markers', stream=depth2_stream)
	depth_data = Data([depth1,depth2])
	depth_layout = Layout(title='Depth')
	depth_fig = Figure(data=depth_data, layout=depth_layout)

	unique_url = py.plot(depth_fig, filename='Seabright Depth Data')
	s1 = py.Stream(depth1_stream_id)
	s2 = py.Stream(depth2_stream_id)

	# Open the streams
	s1.open()
	s2.open()
	time.sleep(5)  # delay start of stream by 5 seconds
	s1.write(dict(x=AT,y=data["topDepth"],text=data["topDepth"]))  #  write to Plotly stream
	s2.write(dict(x=AT,y=data["bottomDepth"],text=data["bottomDepth"]))
	print "writing to stream"
	s1.close()  
	s2.close()  
   
###################   main code    #####################

#read the config.txt file and update the configuration dictionary
config = readconfigfile(config_file_loc) #read the config file

#set up the plotly graphs by calling the setup_plotly function
stream_ids = setup_plotly(config)

#connect to database
db = pymysql.connect( host = config["db_host"],
      passwd = config["db_passwd"], user = config['db_user'], db=config["db"])
print("connected to database")


#Main LOOP
while True:

	#get the date and time
	AT = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
	data = {}
	# get gen 1 ekm data        
	data["ekmd1"] = readEKM(config["EKM_port"],config["EKM1"]) 
	print "checkpoint: got ekm1"
	print data["ekmd1"]

	# get gen 2 ekm data
	data["ekmd2"] = readEKM(config["EKM_port"],config["EKM2"])
	print "checkpoint: got ekm2"
	print data["ekmd2"]

	#check to see if gen is running before querying RPM
	if data["ekmd1"]["V1"] == 0:
		data["RPM1"]=0	
	else:
		data["RPM1"] = get_RPM(config["rpm1_port"])
	print "checkpoint: got RPM1"
	print "RPM1: " + str(data["RPM1"])

	if data["ekmd2"]["V1"] == 0:
		data["RPM2"] = 0
	else:
		data["RPM2"] = get_RPM(config["rpm2_port"])
	print "checkpoint: got RPM2"
	print "RPM2: " + str(data["RPM2"])

	# read depth, apply depth offset
	data["topDepth"] = readDepth(config["depth_port"],2)
	data["topDepth"] += float(config["upper_depth_offset"])
	data["topDepth"]=round(data["topDepth"],2)
	print "Top Depth: " + str(data["topDepth"])

	# read bottom depth
	data["bottomDepth"] = readDepth(config["depth_port"],1)
	data["bottomDepth"] += float(config["lower_depth_offset"])
	data["bottomDepth"]=round(data["bottomDepth"],2)
	print "Bottom Depth: " + str(data["bottomDepth"])

	#read temp
	data["Temp1"] = ""
	data["Temp2"] = ""

	print data
	
	#write to database function call here
	
	######### Warning section ############
	#RPM1 alarm
	if data["RPM1"] > 0 and data["RPM1"] < 600:
		send_email(config["alarm_user_email"],config["gmail_user"],config["gmail_pw"],"GEN 1 RPM ALARM","Gen 1 RPM is "+str(data["RPM1"])+" which is below the alarm threshold")	
		send_email(config["alarm_user_cell_email"],config["gmail_user"],config["gmail_pw"],"GEN 1 RPM ALARM","Gen 1 RPM is "+str(data["RPM1"])+" which is below the alarm threshold")	
	#RPM2 alarm
	if data["RPM2"] > 0 and data["RPM2"] < 600:
		send_email(config["alarm_user_email"],config["gmail_user"],config["gmail_pw"],"GEN 2 RPM ALARM","Gen 1 RPM is "+str(data["RPM2"])+" which is below the alarm threshold")	
		send_email(config["alarm_user_cell_email"],config["gmail_user"],config["gmail_pw"],"GEN 2 RPM ALARM","Gen 1 RPM is "+str(data["RPM2"])+" which is below the alarm threshold")	
	
	#depth alarm 
	high_up_alarm = depth_alarm(data["topDepth"], config["abovedam_depth_up_alarm"], "high")
	low_up_alarm = depth_alarm(data["topDepth"], config["abovedam_depth_down_alarm"], "low")
	high_down_alarm = depth_alarm(data["bottomDepth"], config["belowdam_depth_up_alarm"], "high")
	
	print "high up alarm =" + str(high_up_alarm)
	print "low up alarm = " + str(low_up_alarm)
	print "high down alarm =" + str(high_down_alarm)
	
	#depth alarm conditions: above dam, high limit
	if high_up_alarm == 1:
		send_email(config["alarm_user_email"],config["gmail_user"],config["gmail_pw"],"WATER LEVEL ALARM", "Water level above dam is "+str(data["topDepth"])+" which is above the alarm threshold")	
		send_email(config["alarm_user_cell_email"],config["gmail_user"],config["gmail_pw"],"WATER LEVEL ALARM", "Water level above dam is "+str(data["topDepth"])+" which is above the alarm threshold")
	
	#depth alarm conditions: above dam, low limit	
	if low_up_alarm == 1:
		send_email(config["alarm_user_email"],config["gmail_user"],config["gmail_pw"],"WATER LEVEL ALARM", "Water level above dam is "+str(data["topDepth"])+" which is below the alarm threshold")	
		send_email(config["alarm_user_cell_email"],config["gmail_user"],config["gmail_pw"],"WATER LEVEL ALARM", "Water level above dam is "+str(data["topDepth"])+" which is below the alarm threshold")	
	
	#depth alarm conditions: below dam, high limit
	if high_down_alarm == 1:
		send_email(config["alarm_user_email"],config["gmail_user"],config["gmail_pw"],"WATER LEVEL ALARM", "Water level below dam is "+ str(data["topDepth"])+" which is above the alarm threshold")	
		send_email(config["alarm_user_cell_email"],config["gmail_user"],config["gmail_pw"],"WATER LEVEL ALARM", "Water level above dam is "+str(data["topDepth"])+" which is above the alarm threshold")
	######### Plotting section ############
	
	print "plotting depth"
	plot_depth(stream_ids,data,AT)
	print "waiting 1 minute"
	
	
	time.sleep(60)
	########## end of main loop ###############
