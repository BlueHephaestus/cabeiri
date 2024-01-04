import requests
from parsers import *
from Message import Message
import time

SYSTEM_NUMBER = "+18647109821"
GROUP_URL = f'http://127.0.0.1:8080/v1/groups/{SYSTEM_NUMBER}'
MESSAGE_URL = f'http://127.0.0.1:8080/v1/receive/{SYSTEM_NUMBER}'

class Signal:
    # signal bot interface

    def __init__(self):
        # Initialize by getting group info for our account.
        group_data = self.get_request_json(GROUP_URL)
        if group_data:
            self.group_mapping = TripletStore() # 3 way hashmap
            for group in group_data:
                id = group.get('id', '')
                internal_id = group.get('internal_id', '')
                name = group.get('name', '')
                self.group_mapping.insert(id, internal_id, name)

    @staticmethod
    def get_request_json(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    def run(self, interval):
        # Initialize the group mapping
        # TODO make this async and return to host program each message after parsing.
        print("Initializing Signal bot...")
        while True:
            data = self.get_request_json(MESSAGE_URL)
            if data:
                for item in data:
                    msg = Message(self, platform="signal")
                    msg.parse(item)
                    msg.print()
            time.sleep(interval)

