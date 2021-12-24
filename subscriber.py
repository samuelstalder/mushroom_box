import sqlite3
import json

import paho.mqtt.client as mqtt
import time

DB = "frontend/mushroom.db" # TODO

INSERT_TEMP = """INSERT INTO 
			temperatur
			(
				box, time, value
			)
		VALUES
			( ?, ?, ? );
			
		"""

INSERT_HUMI = """INSERT INTO 
			humidity 
			(
				box, time, value, inner
			)
		VALUES
			( ?, ?, ?, ? );
			
		"""

INNER_BOX = 0
OUTER_BOX = 1

def _insert(query, data):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(query, data)
    con.commit()
    cur.close()
    con.close()


def insert_inner(data):
    temp = data["temp"]
    humi = data["humi"]
    box = data["id"]
    time = data["time"]
    _insert(INSERT_TEMP, (box, time, temp))
    _insert(INSERT_HUMI, (box, time, humi, INNER_BOX))
     

def insert_outer(data):
    humi = data["humi"]
    box = data["id"]
    time = data["time"]
    _insert(INSERT_HUMI, (box, time, humi, OUTER_BOX))



def on_message(client, userdata, message):
    data = json.loads(message.payload.decode("utf-8"))
    if data["inner"]:
        insert_inner(data)
    else:
        insert_outer(data)

    print("received message: ", data)

mqttBroker ="172.16.32.107"

client = mqtt.Client("Smartphone")
client.connect(mqttBroker) 

client.subscribe("DATA")
client.on_message=on_message 

client.loop_forever()