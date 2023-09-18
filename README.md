# MQTT to OPC UA Bridge

This Python script serves as a bridge between MQTT (Message Queuing Telemetry Transport) and OPC UA (OLE for Process Control Unified Architecture). It allows you to route data from MQTT topics to OPC UA nodes.

## Dependencies

- Paho MQTT
- AsyncUA

You can install these using pip:

```bash
pip install -r requirements.txt
```

## Configuration

The script reads settings from a JSON file (default is `settings.json`). The settings should include the MQTT host and port, the OPC UA endpoint, and the list of topics to be bridged with their corresponding node IDs and types.

Example `settings.json`:

```json
{
  "mqtt": {
    "host": "mqtt_host",
    "port": 1883
  },
  "opcua": {
    "endpoint": "opc.tcp://localhost:4840/freeopcua/server/"
  },
  "topics": [
    {
      "topic": "mqtt/topic1",
      "nodeid": "ns=2;i=2",
      "type": "Int32"
    },
    {
      "topic": "mqtt/topic2",
      "nodeid": "ns=2;i=3",
      "type": "Double"
    }
  ]
}
```

## Usage

Run the script from the command line:

```bash
python mqtt2opcua.py [path_to_settings.json]
```

If you don't provide a settings path, it will default to `settings.json`.

## How it Works

- The MQTT client subscribes to the specified topics and listens for incoming messages.
- Upon receiving a message, it writes the value to the corresponding node in the OPC UA server.
- The OPC UA server can be accessed from other OPC UA clients to read the values.
