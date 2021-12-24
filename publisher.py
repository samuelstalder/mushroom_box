import paho.mqtt.client as mqtt 
from random import randrange, uniform
import time
import grovepi
import json
import math
# Connect the Grove Temperature & Humidity Sensor Pro to digital port D4
# This example uses the blue colored sensor.
# SIG,NC,VCC,GND
sensor = 4  # The Sensor goes on digital port 4.

# Connect the Grove Moisture Sensor to analog port A0
# SIG,NC,VCC,GND
analog_sensor = 0

white = 1   # The White colored sensor.
blue = 0
BOX_ID = 1
INNER = False

grovepi.pinMode(analog_sensor,"INPUT")

mqttBroker ="172.16.32.107" 

client = mqtt.Client("Temperature_Inside")
client.connect(mqttBroker) 



while True:
    [temp,humidity] = grovepi.dht(sensor,white)
    #resistance = (float)(1023 - light_value) * 10 / light_value
    #moisture = grovepi.analogRead(analog_sensor)
    if math.isnan(temp) == False and math.isnan(humidity) == False:
        print("temp = %.02f C humidity =%.02f%%"%(temp, humidity))
        val = grovepi.analogRead(0)
        print(val)

    if INNER:
        corpus = {
        "temp": temp,
        "humi": humidity,
        "id": BOX_ID,
        "inner": INNER,
        "time": int(time.time()) # unix time
        }
    else: 
        corpus = {
        "humi": humidity,
        "id": BOX_ID,
        "inner": INNER,
        "time": int(time.time()) # unix time
        }

    client.publish("DATA", json.dumps(corpus))
    time.sleep(1)
