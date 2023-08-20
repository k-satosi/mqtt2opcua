from paho.mqtt import client as mqtt_client
from asyncua import Server as opcua_server, ua
import asyncio
import json
import logging
import sys

_logger = logging.getLogger(__name__)

opc_server = {}
opc_client = {}
settings = {}

async def write_to_opcua(nodeid, value):
  _logger.debug(f"Writing to {nodeid}")
  global opc_server
  var = opc_server.get_node(nodeid)
  await var.write_value(float(value))

def mqtt_on_connect(client, userdata, flags, rc):
  _logger.info("MQTT Connected")

def mqtt_on_message(client, userdata, msg):
  _logger.info(f"Receive `{msg.payload.decode()}` from `{msg.topic}` topic")

  for topic in settings["topics"]:
    if topic["topic"] == msg.topic:
      loop = asyncio.new_event_loop()
      loop.run_until_complete(write_to_opcua(topic["nodeid"], msg.payload.decode()))

def load_setting(path):
  with open(path) as f:
    global settings
    settings = json.load(f)
  
async def run_mqtt_client():
  mqtt_host = settings["mqtt"]["host"]
  mqtt_port = settings["mqtt"]["port"]

  client = mqtt_client.Client()
  client.on_connect = mqtt_on_connect
  client.on_message = mqtt_on_message
  client.connect(mqtt_host, mqtt_port)
  for t in settings["topics"]:
    client.subscribe(t["topic"])
  client.loop_start()
  while True:
    await asyncio.sleep(1)

async def run_opcua_server():
  endpoint = settings["opcua"]["endpoint"]

  global opc_server
  opc_server = opcua_server()
  await opc_server.init()
  opc_server.set_endpoint(endpoint)

  uri = "http://examples.freeopcua.github.io"
  idx = await opc_server.register_namespace(uri)

  objects = opc_server.get_objects_node()
  myobj = await objects.add_object(idx, "Object")
  for t in settings["topics"]:
    nodeid = ua.NodeId.from_string(t["nodeid"])
    myvar = await myobj.add_variable(nodeid, nodeid.Identifier, 0.0)
    _logger.info(await myvar.read_browse_name())
    await myvar.set_writable()
    await myvar.write_value(0.0)

  async with opc_server:
    while True:
      await asyncio.sleep(1)

async def run(path="settings.json"):
  load_setting(path)

  task1 = asyncio.create_task(run_opcua_server())
  task2 = asyncio.create_task(run_mqtt_client())
  await task1
  await task2

if __name__ == "__main__":
  args = sys.argv
  if len(args) < 2:
    asyncio.run(run())
  else:
    asyncio.run(run(args[1]))