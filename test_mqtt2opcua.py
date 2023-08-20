import unittest
import mqtt2opcua as m2o

from paho.mqtt import client as mqtt_client
from asyncua import Client as opcua_client
import asyncio
import json

async def publish_mqtt(host, port, topic, value):
  await asyncio.sleep(1)
  client = mqtt_client.Client()
  client.connect(host, port)
  client.publish(topic, value)

async def read_opcua_node(endpoint, nodeid):
  await asyncio.sleep(2)
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
          "nodeid": "ns=2;s=Var2"
        }
      ]
    }
    with open("test.json", "w") as f:
      json.dump(settings, f)

    expected = 2.3
    topic1 = settings["topics"][0]
    topic2 = settings["topics"][1]
    host = settings["mqtt"]["host"]
    port = settings["mqtt"]["port"]
    endpoint = settings["opcua"]["endpoint"]
    task1 = asyncio.create_task(m2o.run("test.json"))
    
    task2 = asyncio.create_task(publish_mqtt(host, port, topic1["topic"], expected))
    task3 = asyncio.create_task(read_opcua_node(endpoint, topic1["nodeid"]))

    await task2
    value = await task3
    self.assertEqual(value, expected)

    expected = -0.7
    task2 = asyncio.create_task(publish_mqtt(host, port, topic2["topic"], expected))
    task3 = asyncio.create_task(read_opcua_node(endpoint, topic2["nodeid"]))

    await task2
    value = await task3
    self.assertEqual(value, expected)

    task1.cancel()

if __name__ == "__main__":
  unittest.main()
