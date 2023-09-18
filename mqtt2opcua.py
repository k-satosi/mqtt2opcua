from paho.mqtt import client as mqtt_client
from asyncua import Server as opcua_server, ua
import asyncio
import json
import logging
import sys

_logger = logging.getLogger(__name__)

type_list = {
  "Int32": { "uatype": ua.VariantType.Int32, "default": 0 },
  "Double": { "uatype": ua.VariantType.Double, "default": 0.0 },
  "Boolean": { "uatype": ua.VariantType.Boolean, "default": False},
  "String": { "uatype": ua.VariantType.String, "default": ""}
}

class MQTT2OPCUA:
  def __init__(self, config_path="settings.json"):
    self.config_path = config_path
    self.load_setting()
    self.opc_server = None

  async def write_to_opcua(self, nodeid, value):
    _logger.debug(f"Writing to {nodeid}")
    var = self.opc_server.get_node(nodeid)
    await var.write_value(value)

  def mqtt_on_connect(self, client, userdata, flags, rc):
    _logger.info("MQTT Connected")

  def mqtt_on_message(self, client, userdata, msg):
    _logger.info(f"Receive `{msg.payload.decode()}` from `{msg.topic}` topic")

    for topic in self.settings["topics"]:
      if topic["topic"] == msg.topic:
        val = msg.payload.decode()
        if not "type" in topic:
          val = float(val)
        elif topic["type"] == "Boolean":
          val =  True if val == "True" else False
        elif topic["type"] == "Int32":
          val = int(val)
        elif topic["type"] == "Double":
          val = float(val)
        elif topic["type"] == "String":
          val = str(val)
        else:
          val = float(val)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.write_to_opcua(topic["nodeid"], val))

  def load_setting(self):
    with open(self.config_path) as f:
      self.settings = json.load(f)
  
  async def run_mqtt_client(self):
    mqtt_host = self.settings["mqtt"]["host"]
    mqtt_port = self.settings["mqtt"]["port"]

    client = mqtt_client.Client()
    client.on_connect = self.mqtt_on_connect
    client.on_message = self.mqtt_on_message
    client.connect(mqtt_host, mqtt_port)
    for t in self.settings["topics"]:
      client.subscribe(t["topic"])
    client.loop_start()
    while True:
      await asyncio.sleep(1)

  async def run_opcua_server(self):
    endpoint = self.settings["opcua"]["endpoint"]

    self.opc_server = opcua_server()
    await self.opc_server.init()
    self.opc_server.set_endpoint(endpoint)

    uri = "http://examples.freeopcua.github.io"
    idx = await self.opc_server.register_namespace(uri)

    objects = self.opc_server.get_objects_node()
    myobj = await objects.add_object(idx, "Object")
    for t in self.settings["topics"]:
      nodeid = ua.NodeId.from_string(t["nodeid"])
      myvar = {}
      if not "type" in t:
        myvar = await myobj.add_variable(nodeid, nodeid.Identifier, 0.0)
      else:
        ty = t["type"]
        vtype = type_list[ty]
        myvar = await myobj.add_variable(nodeid, t["topic"], vtype["default"], vtype["uatype"])
      await myvar.set_writable()
      _logger.info(await myvar.read_browse_name())

    async with self.opc_server:
      while True:
        await asyncio.sleep(1)

  async def run(self):
    task1 = asyncio.create_task(self.run_opcua_server())
    task2 = asyncio.create_task(self.run_mqtt_client())
    await task1
    await task2

if __name__ == "__main__":
  args = sys.argv
  if len(args) < 2:
    bridge = MQTT2OPCUA()
  else:
    bridge = MQTT2OPCUA(config_path=args[1])
  asyncio.run(bridge.run())