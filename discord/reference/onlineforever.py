import sys
import json
import time
import requests
import websocket

status = "online"

custom_status = "" #If you don't need a custom status on your profile, just put "" instead of "youtube.com/@SealedSaucer"

#usertoken = "MTE1NDUxODA3OTY1MzU1NjI1NQ.GqLmgT.5-viN9Csg9EsEfnY0wYaqkY9Bzmohy8dYOf-D4"

usertoken = "MTE1NDUxODA3OTY1MzU1NjI1NQ.G9x_AS.YZVHs3YzWJCKVh0mlY_VBNENF0wU1g18kc35b4"

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

validate = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
if validate.status_code != 200:
  print("[ERROR] Your token might be invalid. Please check it again.")
  sys.exit()

userinfo = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

def onliner(token, status):
    ws = websocket.WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
    start = json.loads(ws.recv())
    heartbeat = start["d"]["heartbeat_interval"]
    auth = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "Windows 10",
                "$browser": "Google Chrome",
                "$device": "Windows",
            },
            "presence": {"status": status, "afk": False},
        },
        "s": None,
        "t": None,
    }
    ws.send(json.dumps(auth))
    cstatus = {
        "op": 3,
        "d": {
            "since": 0,
            "activities": [
                {
                    "type": 4,
                    "state": f"{time.time()}",
                    "name": "Custom Status",
                    "id": "custom",
                    #Uncomment the below lines if you want an emoji in the status
                    #"emoji": {
                        #"name": "emoji name",
                        #"id": "emoji id",
                        #"animated": False,
                    #},
                }
            ],
            "status": status,
            "afk": False,
        },
    }
    ws.send(json.dumps(cstatus))
    online = {"op": 1, "d": "None"}
    time.sleep(heartbeat / 1000)
    ws.send(json.dumps(online))

def run_onliner():
  print(f"Logged in as {username}#{discriminator} ({userid}).")
  while True:
    onliner(usertoken, status)
    time.sleep(30)
    print("Updating status")

run_onliner()