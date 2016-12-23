#!/usr/bin/env python2
#HEAD#########################################################
#
# Katana Framework | API functions                         
# Last Modified: 23/12/2016
#
#########################################################HEAD#

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
from Design import *
from lib.adb.adb import adb_commands
import xml.etree.ElementTree as ET

import fcntl        ,struct   ,readline,rlcompleter,subprocess
import threading    ,StringIO ,httplib ,commands   ,random ,re , json
import logging      ,urllib   ,socket  ,time       ,sys

from Internal import (
	Maquetar,
	saveRegister,
	MakeTable,
	KTFVAR
	)

AGENT_ARRAY=[]
File_Agent_Open=False
NUMBER_AGENTS=0
ap_list = []

### API EXECUTE FUNCTION ####################################################################################################
def Executefunction(query):
	try:

		if query[len("f::"):len("get_aps")+len("f::")] == "get_aps": 
			query = query[len("f::")+len("get_aps"):].replace("(","").replace(")","").split(",")
			get_aps(str(query[0]),int(query[1]))

		elif query[len("f::"):len("start_monitor")+len("f::")]== "start_monitor":
			query = query[len("f::")+len("start_monitor"):].replace("(","").replace(")","").split(",")
		    
			if start_monitor(query[0]):printAlert(3,query[0]+" now is in monitor mode.")
			else:NoDeviceFound(query[0]) 

		elif query[len("f::"):len("get_interfaces")+len("f::")]    == "get_interfaces":    print " ",get_interfaces()
		elif query[len("f::"):len("get_monitors_mode")+len("f::")] == "get_monitors_mode": print " ",get_monitors_mode()
		elif query[len("f::"):len("get_local_ip")+len("f::")]      == "get_local_ip":      print " ",get_local_ip()
		elif query[len("f::"):len("get_external_ip")+len("f::")]   == "get_external_ip":   print " ",get_external_ip()
		elif query[len("f::"):len("get_gateway")+len("f::")]       == "get_gateway":       print " ",get_gateway()

		else:functionNotFound()                                                                                 
	except:printAlert(6,"Check Again your Functions command.")
##############################################################################################################################

### PING ###
def isLive(defaulthost, defaultport):
	if True:
		
		redTEST=socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
		redTEST.connect((defaulthost, int(defaultport))) 
		redTEST.close()
		return True
	return False


### LIST DEVICES CONNECTED (ADB) ###
def ListDevicesConnectADB():
	try:
		NumberDevice=0
		LIST = ""
		for d in adb_commands.AdbCommands.Devices():
			NumberDevice+=1
			LIST += (' %s) %s\t device\t%s' % (NumberDevice, d.serial_number, ','.join(str(p) for p in d.port_path)))
		return LIST
	except:N=2

### AP's SCAN ###
def get_aps(mon,timeout):
	commands.getoutput('rm '+FOLDER_KATANA+'tmp/*.netxml')
	printAlert(0,"Scanning Access Points in Interface '"+mon+"', Please wait "+str(timeout)+"seg")
	Subprocess("airodump-ng "+mon+" -w '"+FOLDER_KATANA+"tmp/ktf.wifi' --wps --output-format netxml --write-interval "+str(timeout))
	time.sleep(timeout+1)
	APCOUNTER    = 0
	CLCOUNTER    = 0
	ESSIDs       = []
	BSSIDs       = []
	MANUs        = []
	CHANNELs     = []
	ENCRYPTAIONs = []
	PWRs         = []
	CLIENTMACs   = []
	CLIENTMANs   = []
	CLIENTESSs   = []
	tree = ET.parse(FOLDER_KATANA+'tmp/ktf.wifi-01.kismet.netxml')
	root = tree.getroot()
	try:
		Space()
		b =  [["#","MAC","CH","PWR","ENCRYPTION","VENDOR","ESSID"]]

		for network in root.findall('wireless-network'):
			if network.get('type')=="infrastructure":
				for essid in network.findall('SSID'):

					APCOUNTER += 1

					if essid.find('essid') is not None:
						ESSIDs.append(essid.find('essid').text)
					else:
						ESSIDs.append("NULL")

					if essid.find('encryption') is not None:
						ENCRYPTAIONs.append(essid.find('encryption').text)
					else:
						ENCRYPTAIONs.append("NULL")

		for network in root.findall('wireless-network'):
			if network.get('type')=="infrastructure":	
				BSSIDs.append(network.find('BSSID').text)
				MANUs.append(network.find('manuf').text)
				CHANNELs.append(network.find('channel').text)

		for network in root.findall('wireless-network'):
			if network.get('type')=="infrastructure":
				for essid in network.findall('snr-info'):
					PWRs.append(essid.find('last_signal_rssi').text)

		for network in root.findall('wireless-network'):
			if network.get('type')=="probe":
				for probe in network.findall('wireless-client'):
					CLCOUNTER+=1
					CLIENTMACs.append(probe.find('client-mac').text)
					CLIENTMANs.append(probe.find('client-manuf').text)

					for essid in probe.findall('SSID'):
						if essid.find('ssid') is not None:
							CLIENTESSs.append(essid.find('ssid').text)
						else:
							CLIENTESSs.append("NULL")
		LIST=0
		while LIST < APCOUNTER:
			b += [[str(LIST),str(BSSIDs[LIST]),str(CHANNELs[LIST]),str(PWRs[LIST]),str(ENCRYPTAIONs[LIST]),str(MANUs[LIST]),str(ESSIDs[LIST])]]
			LIST+=1

		b +=  [["","","","","","",""]]
		b +=  [["#","MAC","","","","VENDOR","PROBE"]]
		b +=  [["","","","","","",""]]


		LIST=0
		while LIST < CLCOUNTER:
			b += [[str(LIST),str(CLIENTMACs[LIST]),"","","",str(CLIENTMANs[LIST]),str(CLIENTESSs[LIST])]]
			LIST+=1

		Maquetar(b)
		commands.getoutput('killall airodump-ng')
	except:FAIL=1292
	
### PING PORT ###
def isPortOpen(defaulthost, defaultport):
	if True:
		try:
			redTEST=socket.socket(socket.AF_INET, socket.SOCK_STREAM)   
			redTEST.settimeout(5)
			redTEST.connect((defaulthost, int(defaultport))) 
			redTEST.close()
			return True
		except:return False
	return False

### START MONITOR INTERFACE ###
def start_monitor(interface):
	commands.getoutput("airmon-ng check kill")
	if checkDevice(interface):
		state=commands.getoutput("airmon-ng start "+interface)
		if state:return True
	return False

### CHECK IF INTERFACE SUPPORT AP MODE ###
def CheckAPmode():
	output = commands.getoutput('iw list | grep "* AP"')
	if len(output) > 0 : return True
	printAlert(1,"You device not support AP mode.")
	return False

### MY LOCAL IP ### 
def get_local_ip():
	SocCKet = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try: 
		SocCKet.connect(("google.com",80))
		if True:
			IP_Address=SocCKet.getsockname()[0]
			SocCKet.close()
			return IP_Address
	except:
		SocCKet.close()
		return "NULL"

### GET EXTANAL IP ###
def get_external_ip():
	try:	
	    site = urllib.urlopen("http://checkip.dyndns.org/").read()
	    grab = re.findall('([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', site)
	    address = grab[0]
	    return address
	except:
		return "NULL"

### INTERFACES SCANNING ###
def get_interfaces():
	Interfaces=commands.getoutput("netstat -i | awk '{print $1}'")
	Interfaces=Interfaces.replace("\n",",")
	Interfaces=Interfaces.replace("Kernel,Iface,","")
	Interfaces=Interfaces.split(",")
	if len(Interfaces) >= 0:
		return Interfaces
	return "NULL"

### CHECK DEVICE ###
def checkDevice(device):
	devices=commands.getoutput("netstat -i | awk '{print $1}'")
	devices=devices.split("\n")
	for interface in devices:
		if device == interface : return True
	NoDeviceFound(device)
	return False

### GET MONITORS INTERFACE ###
def get_monitors_mode():
	Monitor=commands.getoutput("airmon-ng | grep 'mon' | awk '{print $2}'")
	Monitor=Monitor.split("\n")
	if len(Monitor) >= 0:
		return Monitor
	return "NULL"


### VALIDATE MAC ###
def checkMAC(mac):
	if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()): return True
	printAlert(1,"is not MAC address")

### IP's SCANNING LAN ###
def get_lan_ips(output):
	test=isConect()
	count=0
	if test!=False:
		array_ip=[]
		commands.getoutput('nmap -sn '+test+'/24 -oX tmp/ips.xml > null')
		xmldoc = minidom.parse('tmp/ips.xml')
		itemlist = xmldoc.getElementsByTagName('address')
		for s in itemlist:
		    ip=s.attributes['addr'].value
		    if ip!=test:
		    	array_ip.append(ip)

	if output==1 and test!=False:
		for ip in array_ip:
			
			if ip.find(":") <= 0 :
				mac=ip
				if get_gateway(2)==mac:
					mac+="]["+colors.B+"GATEWAY"+colors.W
			else:
				count=count+1
				print " [ "+str(count),"] Host's up  : ["+mac+"]["+ip+"]"
		commands.getoutput('rm tmp/ips.xml > null')
	else:
		return False

### STATUS CMD ###
def status_cmd(cmd):
	status_1=subprocess.call(cmd+' >/dev/null 2>&1', shell=True)
	if status_1==0:
		return "[\033[1m"+colors[2]+"OK"+colors[0]+"]"+colors[0]
	else:
		return "["+colors[1]+"\033[1mERROR"+colors[0]+"]"+colors[0]+"["+colors[3]+"\033[1mWARNING"+colors[0]+"]"


### GET GATEWAY ###
def get_gateway():
	ip_r_l=subprocess.Popen("ip r l",shell=True,stdout=subprocess.PIPE).communicate()[0]
	s = StringIO.StringIO(ip_r_l)
	for line in s:
		if "default" in line:
			gateway = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',line).group(0)
			return gateway
	return "NULL"

### am I Connected? ###
def isConect():
	ip_r_l=subprocess.Popen("ip r l",shell=True,stdout=subprocess.PIPE).communicate()[0]
	s = StringIO.StringIO(ip_r_l)
	for line in s:
		if "default" in line:
			return True
	printAlert(1,"you not is connected to a network.\n")
	return False


### GET MY MAC ADRRESS ###
def get_my_mac_address():
	if isConect()!=False:
	    my_macs = [get_if_hwaddr(i) for i in get_if_list()]
	    for maca in my_macs:
	        if(maca != "00:00:00:00:00:00"):
	            return maca
	return "NULL"

### STATUS HTTP ###
def checkStatusHTTP(host, port, filerequest):
	connection = httplib.HTTPConnection(host,port)
	connection.request("GET", "/"+filerequest)
	response = connection.getresponse()
	code = response.status
	description = ["unknowk","unknowk"]
	if code == 200 : description = [ "OK"                                       , "Suf" ]
	if code == 201 : description = [ "Created"                                  , "Suf" ]
	if code == 202 : description = [ "Accepted"                                 , "Suf" ]
	if code == 203 : description = [ "Non/Authoritative Information (HTTP/1.1)" , "Suf" ]
	if code == 204 : description = [ "No Content"                               , "Suf" ]
	if code == 205 : description = [ "Reset Content"                            , "Suf" ]
	if code == 206 : description = [ "Partial Content"                          , "Suf" ]
	if code == 207 : description = [ "Multi/Status (Multi/Status, WebDAV)"      , "Suf" ]
	if code == 208 : description = [ "Already Reported (WebDAV)"                , "Suf" ]
	if code == 300 : description = [ "Multiple Choices"                         , "Inf:Redirection" ]
	if code == 301 : description = [ "Moved Permanently"                        , "Inf:Redirection" ]
	if code == 302 : description = [ "Found"                                    , "Inf:Redirection" ]
	if code == 303 : description = [ "See Other (from HTTP/1.1)"                , "Inf:Redirection" ]
	if code == 304 : description = [ "Not Modified"                             , "Inf:Redirection" ]
	if code == 305 : description = [ "Use Proxy (desde HTTP/1.1)"               , "Inf:Redirection" ]
	if code == 306 : description = [ "Switch Proxy"                             , "Inf:Redirection" ]
	if code == 307 : description = [ "Temporary Redirect (desde HTTP/1.1)"      , "Inf:Redirection" ]
	if code == 308 : description = [ "Permanent Redirect"                       , "Inf:Redirection" ]                
	if code == 400 : description = [ "Bad Request"                              , "Inf:Redirection" ]
	if code == 401 : description = [ "Unauthorized"                             , "Err:Client" ]
	if code == 402 : description = [ "Payment Required"                         , "Err:Client" ]
	if code == 403 : description = [ "Forbidden"                                , "Err:Client" ]
	if code == 404 : description = [ "Not Found"                                , "Err:Client" ]
	if code == 405 : description = [ "Method Not Allowed"                       , "Err:Client" ]
	if code == 406 : description = [ "Not Acceptable"                           , "Err:Client" ]
	if code == 407 : description = [ "Proxy Authentication Required"            , "Err:Client" ]
	if code == 408 : description = [ "Request Timeout"                          , "Err:Client" ]
	if code == 409 : description = [ "Conflict"                                 , "Err:Client" ]
	if code == 410 : description = [ "Gone"                                     , "Err:Client" ]
	if code == 411 : description = [ "Length Required"                          , "Err:Client" ]
	if code == 412 : description = [ "Precondition Failed"                      , "Err:Client" ]
	if code == 413 : description = [ "Request Entity Too Large"                 , "Err:Client" ]
	if code == 414 : description = [ "Request/URI Too Long"                     , "Err:Client" ]
	if code == 415 : description = [ "Unsupported Media Type"                   , "Err:Client" ]
	if code == 416 : description = [ "Requested Range Not Satisfiable"          , "Err:Client" ]
	if code == 417 : description = [ "Expectation Failed"                       , "Err:Client" ]
	if code == 418 : description = [ "I'm a teapot"                             , "Err:Client" ]
	if code == 422 : description = [ "Unprocessable Entity (WebDAV / RFC 4918)" , "Err:Client" ]
	if code == 423 : description = [ "Locked (WebDAV / RFC 4918)"               , "Err:Client" ]
	if code == 424 : description = [ "Failed Dependency (WebDAV) (RFC 4918)"    , "Err:Client" ]
	if code == 425 : description = [ "Unassigned"                               , "Err:Client" ]
	if code == 426 : description = [ "Upgrade Required (RFC 7231)"              , "Err:Client" ]
	if code == 428 : description = [ "Precondition Required"                    , "Err:Client" ]
	if code == 429 : description = [ "Too Many Requests"                        , "Err:Client" ]
	if code == 431 : description = [ "Request Header Fileds Too Large)"         , "Err:Client" ]
	if code == 451 : description = [ "Unavailable for Legal Reasons"            , "Err:Client" ]
	if code == 500 : description = [ "Internal Server Error"                    , "Err:Server" ]
	if code == 501 : description = [ "Not Implemented"                          , "Err:Server" ]
	if code == 502 : description = [ "Bad Gateway"                              , "Err:Server" ]
	if code == 503 : description = [ "Service Unavailable"                      , "Err:Server" ]
	if code == 504 : description = [ "Gateway Timeout"                          , "Err:Server" ]
	if code == 505 : description = [ "HTTP Version Not Supported"               , "Err:Server" ]
	if code == 506 : description = [ "Variant Also Negotiates (RFC 2295)"       , "Err:Server" ]
	if code == 507 : description = [ "Insufficient Storage (WebDAV / RFC 4918)" , "Err:Server" ]
	if code == 508 : description = [ "Loop Detected (WebDAV)"                   , "Err:Server" ]
	if code == 510 : description = [ "Not Extended (RFC 2774)"                  , "Err:Server" ]
	if code == 511 : description = [ "Network Authentication Required"          , "Err:Server" ]
	if (description[1]=="Err:Server"):
		printAlert(1,"Connection : "+description[0])
		return False
	if (description[1]=="Err:Client"):
		printAlert(6,"Connection : "+description[0])
		return False
	if (description[1]=="Suf")       :
		printAlert(3,"Connection : "+description[0])
		return True

### USER-AGENT GENERATOR ###
def RamdonAgent():
	global NUMBER_AGENTS,File_Agent_Open
	NUMBER_AGENTS=0
	if File_Agent_Open==False:
		with open(AGENTS_BROWSER,'r') as AGENT_LIST:
			for AGENT in AGENT_LIST:
				NUMBER_AGENTS=1+NUMBER_AGENTS
				AGENT_ARRAY.append(AGENT.replace("\n",""))
	File_Agent_Open=True
	Generate = 0
	Generate = random.randint(0, NUMBER_AGENTS)
	return AGENT_ARRAY[Generate]
