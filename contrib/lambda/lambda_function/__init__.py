import requests

VERSION = "0.1.0"

IDIOTIC_API = "https://idiotic.hackafe.net"
IDIOTIC_ITEMS = IDIOTIC_API + "/api/items"
IDIOTIC_SCENES = IDIOTIC_API + "/api/scenes"
MANUFACTURER = "idiotic"

TURN_ON = 'turnOn'
TURN_OFF = 'turnOff'
SET_VALUE = 'setTargetTemperature'
INC_VALUE = 'incrementTargetTemperature'
DEC_VALUE = 'decrementTargetTemperature'
SET_PERCENT = 'setPercentage'
DEC_PERCENT = 'decrementPercentage'
INC_PERCENT = 'incrementPercentage'

COMMAND_MAP = {
    'TurnOnRequest': ("on", [], {}),
    'TurnOffRequest': ("off", [], {}),
    'SetTargetTemperatureRequest': ("set", [], {"val": "targetTemperature"}),
    'IncrementTargetTemperatureRequest': ("add", [], {"amount": "deltaTemperature"}),
    'DecrementTargetTemperatureRequest': ("sub", [], {"amount": "deltaTemperature"}),
    'SetPercentageRequest': ("set", [], {"val": "percentageState"}),
    'IncrementPercentageRequest': ("up", [], {"step": "deltaPercentage"}),
    'DecrementPercentageRequest': ("down", [], {"step": "deltaPercentage"}),
}

def lambda_handler(event, context):
    access_token = event['payload']['accessToken']
 
    if event['header']['namespace'] == 'Alexa.ConnectedHome.Discovery':
        return handleDiscovery(context, event)
 
    elif event['header']['namespace'] == 'Alexa.ConnectedHome.Control':
        return handleControl(context, event)

def convertItem(item):
    base = {
        "applianceId": item.get("id", item["name"]),
        "manufacturerName": MANUFACTURER,
        "modelName": MANUFACTURER + "." + item["type"],
        "version": VERSION,
        "friendlyName": item["name"],
        "friendlyDescription": item.get("description", item["name"]),
        "isReachable": True,
    }

    commands = item.get("commands", {})
    actions = []
    if "on" in commands:
        actions.append(TURN_ON)

    if "off" in commands:
        actions.append(TURN_OFF)

    if "set" in commands:
        actions += [
            SET_VALUE,
            INC_VALUE,
            DEC_VALUE
        ]

    if "down" in commands or "up" in commands:
        actions.append(SET_PERCENT)

    if "down" in commands:
        actions.append(DEC_PERCENT)

    if "up" in commands:
        actions.append(INC_PERCENT)

    base["actions"] = actions

    return base

def convertScene(scene):
    return {
        # We should really return ID on scenes
        "applianceId": ''.join((x for x in scene["name"].lower().replace(" ", "_") if x.isalnum() or x=='_')) if scene["name"] else "",
        "manufacturerName": MANUFACTURER,
        "modelName": MANUFACTURER + ".scene",
        "version": VERSION,
        "friendlyName": scene["name"],
        "friendlyDescription": scene["name"],
        "isReachable": True,
        "actions": [TURN_ON, TURN_OFF],
    }

def handleDiscovery(context, event):
    payload = ''
    header = {
        "namespace": "Alexa.ConnectedHome.Discovery",
        "name": "DiscoverAppliancesResponse",
        "payloadVersion": "2"
        }
 
    if event['header']['name'] == 'DiscoverAppliancesRequest':
        items = requests.get(IDIOTIC_ITEMS).json()['result']
        scenes = requests.get(IDIOTIC_SCENES).json()['result']
        payload = {
            "discoveredAppliances": [
                convertItem(item) for item in items
            ] + [
                convertScene(scene) for scene in scenes
            ]
        }

    return {'payload': payload, 'header': header}
 
def handleControl(context, event):
    payload = ''
    device_id = event['payload']['appliance']['applianceId']
    message_id = event['header']['messageId']

    args = []
    kwargs = {}
    request = event['header']['name']

    if request in COMMAND_MAP:
        cmd, arg_template, kwarg_template = COMMAND_MAP[request]

        args = [event['payload'][k]["value"] for k in arg_template]
        kwargs = {k: event['payload'][v]['value'] for k, v in kwarg_template.items()}
 
        header = {
            "namespace":"Alexa.ConnectedHome.Control",
            "name": request.replace('Request', 'Confirmation'),
            "payloadVersion":"2",
            "messageId": message_id
        }

    return {'header': header, 'payload': {}}
