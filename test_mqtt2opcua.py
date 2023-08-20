import unittest
import mqtt2opcua as m2o

from paho.mqtt import client as mqtt_client
from asyncua import Client as opcua_client
import asyncio
import json

async def publish_mqtt(host, port, topic, value):
  client = mqtt_client.Client()
  client.connect(host, port)
  client.publish(topic, value)

async def read_opcua_node(endpoint, nodeid):
  url = endpoint
  async with opcua_client(url=url) as client:
    var = client.get_node(nodeid)
    value = await var.read_value()
    return value

class M2OTest(unittest.IsolatedAsyncioTestCase):
  async def test_normal(self):
    settings = {
      "mqtt": {
        "host": "localhost",
        "port": 1883
      },
      "opcua": {
        "endpoint": "opc.tcp://localhost:4840"
      },
      "topics": [
        {
          "topic": "test1",
          "nodeid": "ns=2;s=Var1"
        },
        {
          "topic": "test2",
          "nodeid": "ns=2;s=Var2",
          "type": "Double"
        },
        {
          "topic": "testBoolean",
          "nodeid": "ns=2;s=BoolVar",
          "type": "Boolean"
        },
        {
          "topic": "testString",
          "nodeid": "ns=2;s=StringVar",
          "type": "String"
        }
      ]
    }
    with open("test.json", "w") as f:
      json.dump(settings, f)

    host = settings["mqtt"]["host"]
    port = settings["mqtt"]["port"]
    endpoint = settings["opcua"]["endpoint"]
    task1 = asyncio.create_task(m2o.run("test.json"))

    async def publish_and_read(topic, expected):
      await publish_mqtt(host, port, topic["topic"], expected)
      actual = await read_opcua_node(endpoint, topic["nodeid"])
      self.assertEqual(actual, expected)

    await asyncio.sleep(1)
    await publish_and_read(settings["topics"][0], 2.3)
    await publish_and_read(settings["topics"][1], -0.7)
    await publish_and_read(settings["topics"][2], True)
    await publish_and_read(settings["topics"][3], "Hello")
    
    task1.cancel()

if __name__ == "__main__":
  unittest.main()
