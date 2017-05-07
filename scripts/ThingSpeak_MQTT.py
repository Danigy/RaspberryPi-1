# ThingSpeak Update Using MQTT
# Copyright 2016, MathWorks, Inc

# Modified by: M. Gries
# Created 1st: 2017-04-29
# Last Change: 2017-05-07

# This is an example of publishing to multiple fields simultaneously.
# Connections over standard TCP, websocket or SSL are possible by setting
# the parameters below.
#
# CPU and RAM usage is collected every 20 seconds and published to a
# ThingSpeak channel using an MQTT Publish
#
# This example requires the Paho MQTT client package which
# is available at: http://eclipse.org/paho/clients/python

from __future__ import print_function
from time import localtime, strftime
from subprocess import check_output
from re import findall
import paho.mqtt.publish as publish
import psutil
import os       


###   Start of user configuration   ###   

#  ThingSpeak Channel Settings

# The ThingSpeak Channel ID
# Replace this with your Channel ID
channelID = "265640"

# The Write API Key for the channel
# Replace this with your Write API key
apiKey = "XV28FE37W2ZRUDHU"

#  MQTT Connection Methods

# Set intervall MQTT messages will be send
tIntervall = 20

# Set useUnsecuredTCP to True to use the default MQTT port of 1883
# This type of unsecured MQTT connection uses the least amount of system resources.
useUnsecuredTCP = False

# Set useUnsecuredWebSockets to True to use MQTT over an unsecured websocket on port 80.
# Try this if port 1883 is blocked on your network.
useUnsecuredWebsockets = False

# Set useSSLWebsockets to True to use MQTT over a secure websocket on port 443.
# This type of connection will use slightly more system resources, but the connection
# will be secured by SSL.
useSSLWebsockets = True

###   End of user configuration   ###



# The Hostname of the ThinSpeak MQTT service
mqttHost = "mqtt.thingspeak.com"

# Set up the connection parameters based on the connection type
if useUnsecuredTCP:
    tTransport = "tcp"
    tPort = 1883
    tTLS = None

if useUnsecuredWebsockets:
    tTransport = "websockets"
    tPort = 80
    tTLS = None

if useSSLWebsockets:
    import ssl
    tTransport = "websockets"
    tTLS = {'ca_certs':"/etc/ssl/certs/ca-certificates.crt",'tls_version':ssl.PROTOCOL_TLSv1}
    tPort = 443
        
# Create the topic string
topic = "channels/" + channelID + "/publish/" + apiKey

def get_snr():
    # example line: Serial		: 0000000084d82aad
    snr = check_output(["cat /proc/cpuinfo | grep Serial | cut -d' ' -f2"], shell=True)
    return(snr)

print("Serial No:", get_snr())

def get_temp():
    # example line: temp=56.4'C
    temp = check_output(["vcgencmd","measure_temp"]).decode("UTF-8")
    return(findall("\d+\.\d+",temp)[0])

print("CPU temperature:", get_temp())

def get_tasks():
    # example line: Tasks: 173 total,   1 running, 171 sleeping,   1 stopped,   0 zombie
    tasks = check_output(["top -bn1 | grep 'Tasks'"], shell=True)
    return(findall("\d+",tasks)[0])

print("RPi3 current tasks:", get_tasks(), "\n")

def get_rssi():
    # example line: -55 dBm 
    rssi = check_output(["iwconfig wlan0 | egrep 'Signal' | cut -d= -f3"], shell=True)
    return(rssi)

print("Signal level:", get_rssi(), "\n")

# Run a loop which calculates the system performance every
#   tIntervall seconds and published that to a ThingSpeak channel
#   using MQTT.

print (strftime("%a, %d %b %Y %H:%M:%S starting loop ...", localtime()))

while(True):
    
    # get the system performance data
    cpuPercent = psutil.cpu_percent(interval = tIntervall)
    ramPercent = psutil.virtual_memory().percent
    msgTime = strftime("%H:%M:%S ", localtime())
    cpuTemp = get_temp()
    RPi3Tasks = get_tasks()
    rssiStr = get_rssi()
    RPi3rssi = "-" + str(findall("\d+",rssiStr)[0])
    print (msgTime, \
           "  CPU =",cpuPercent, \
           "  RAM =",ramPercent, \
           "  Temp =",cpuTemp, \
           "  Tasks =",RPi3Tasks, \
           "  RSSI =",RPi3rssi)

    # build the payload string
    tPayload = "field1=" + str(cpuPercent) + \
               "&field2=" + str(ramPercent) + \
               "&field3=" + str(cpuTemp) + \
               "&field4=" + str(RPi3Tasks) + \
               "&field5=" + str(RPi3rssi)

    # attempt to publish this data to the topic 
    try:
        publish.single(topic, payload=tPayload, hostname=mqttHost, port=tPort, tls=tTLS, transport=tTransport)

    except (KeyboardInterrupt):
        break

    except:
        print ("There was an error while publishing the data.")
