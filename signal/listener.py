import requests
import json
import base64
from datetime import datetime
import time
from colorama import Fore, Style, init
from utils.ai_utils import *
# Initialize Colorama
init(autoreset=True)
SYSTEM_PROMPT = """
You are a helpful assistant who is trying to be helpful while also being way too concerned that people think you are a robot and not a human.
You must do your best to hide the fact (humorously) that you are an AI and not a human.
Your job is to respond to the prompts given as if you were a human, and give humorous and evasive responses whenever
you are asked about your human-ness or you think someone is trying to test if you are a human.

KEEP RESPONSES SHORT! DO ONE SENTENCE ONLY.
If asked for your name, tell them your name is Blue Hephaestus. Good luck, and have fun!
"""
SYSTEM_NUMBER = "+18647109821"
DEBUG = False
RECEIPTS = False

class TripletStore:
    def __init__(self):
        self.map1 = {}
        self.map2 = {}
        self.map3 = {}

    def insert(self, item1, item2, item3):
        self.map1[item1] = (item2, item3)
        self.map2[item2] = (item1, item3)
        self.map3[item3] = (item1, item2)

    def get(self, item):
        if item in self.map1:
            return self.map1[item]
        if item in self.map2:
            return self.map2[item]
        if item in self.map3:
            return self.map3[item]
        return None

class MessageFetcher:
    group_mapping = TripletStore()

    def __init__(self, group_url, message_url):
        self.group_url = group_url
        self.message_url = message_url
        self.update_group_mapping()

    def update_group_mapping(self):
        group_data = self.fetch_group_data(self.group_url)
        if group_data:
            MessageFetcher.group_mapping = self.create_group_mapping(group_data)


    @staticmethod
    def create_group_mapping(group_data):
        group_mapping = TripletStore()
        for group in group_data:
            id = group.get('id', '')
            internal_id = group.get('internal_id', '')
            name = group.get('name', '')
            group_mapping.insert(id, internal_id, name)
        return group_mapping

    """
    a 
        b: c
        d: 
            e: f
            g: h
        i: j
    
    """

    def items_recursive(self, dic):
        for key, val in dic.items():
            if type(val) is dict:
                for ikey, ival in self.items_recursive(val):
                    yield ikey, ival
            else:
                yield key, val

    def flatten_dict(self, dic):
        # return 1-d dict from multidimensional dict
        return {k:v for k,v in self.items_recursive(dic)}

    def parse(self, data):
        """
        Parse data into message, with variety of formats for data.
        Flattens dictionary and gets whatever attributes are possible, to keep things simple.
        """
        data = self.flatten_dict(data)

        # Get unified attributes
        timestamp = datetime.fromtimestamp(data.get("timestamp",0) / 1000).strftime('%b %d, %I:%M%p')
        group = ""
        user = data.get("sourceName", "?")
        msg = ""


        # Check for flag messages
        # Store in group since these messages don't have a group ID so we just use it as indicator.
        if data.get("isDelivery",False):
            # Message delivered notification
            group = "$delivered"

        elif data.get("isRead", False) or data.get("readMessages", False):
            # Message read notification (the second type is our own read message)
            group = "$read"

        elif data.get("isViewed", False):
            # Message viewed notification
            group = "$viewed"

        elif data.get("action", False):
            # Message typing notification
            group = "$typing"

        elif data.get("message", False) is None:
            # react or delete

            # If react, add suffix to username
            if data.get("emoji", False):
                user = user + " (REACTED)"
                msg = data.get("emoji", "?")
                group = "$msg"
            else:
                # Message deleted notification
                group = "$deleted"

        # Check for new message
        elif data.get("message", False):
            # New Message, group or DM
            msg = data.get("message", "?")

            # If edited, add suffix to username
            if data.get("targetSentTimestamp", False):
                user = user + " (EDITED)"


            group = "$msg"

            if data.get("groupId", False):
                # Group message, use its name
                group = MessageFetcher.group_mapping.get(data.get("groupId","?"))[-1]

        else:
            # Unknown
            group = "$unknown"


        # Now initialize object with all values used.
        return Message(timestamp, group, user, msg, data)


    def send_message(self, response, group_name):
        try:
            group_id, group_internal_id = MessageFetcher.group_mapping.get(group_name)
        except:
            print(f"Failed to identify group. Not sending message to {group_name}")
            return

        # Id and internal identified, send message
        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'message': response,
            'number': SYSTEM_NUMBER,
            'recipients': [group_id],
        }
        response = requests.post('http://localhost:8080/v2/send', headers=headers, data=json.dumps(data))

        try:
            response.raise_for_status()
            print("Message sent successfully")
        except:
            print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
            return





    def main_loop(self):
        bot = ChatGPT(id="autoblue", system_prompt=SYSTEM_PROMPT)
        print("Beginning message loop.")
        while True:
            # self.send_message("kek", "Lonely Dreamers")
            #return
            data = self.fetch_messages(self.message_url)
            if data:
                prev = None # avoid dupes
                for item in data:
                    msg = self.parse(item)

                    # Avoid dupes, sometimes happens
                    if prev is not None and prev == msg: continue
                    prev = msg

                    msg.print()
                    try:
                        pass
                        #if len(msg.message_text) < 3: continue
                        #if not "Lonely" in msg.group_name: continue
                        #print(msg)
                        # print("Generating response")
                        # response = bot.cumulative_ask(msg.message_text)
                        # print(f"Response: {response}")
                        # print(f"Sending Response...")
                        #self.send_message(response, msg.group_name)
                    except: continue
            else:
                # print("Failed to fetch messages or no messages found.")
                pass
            time.sleep(1)

        print(s)


# class Message:
#     def __init__(self, source_name, message_text, timestamp, group_name, raw_msg):
#         self.source_name = source_name
#         self.message_text = message_text
#         self.timestamp = timestamp
#         self.group_name = group_name
#         self.raw_msg = raw_msg
#
#     def __str__(self):
#         #return f"Group {self.group_name}, Name: {self.source_name}, Message: {self.message_text}, Timestamp: {self.timestamp}"
#         if self.group_name == "?" or len(self.message_text) < 5:
#             # Output raw message, unknown format.
#             return (f"{timestamp_color}{self.timestamp} "
#                     f"{groupname_color}{self.group_name} - "
#                     f"{username_color}{self.source_name}: "
#                     f"{message_color}{self.raw_msg}")
#
#         else:
#             return (f"{timestamp_color}{self.timestamp} "
#                     f"{groupname_color}{self.group_name} - "
#                     f"{username_color}{self.source_name}: "
#                     f"{message_color}{self.message_text}")


# Usage
group_url = f'http://127.0.0.1:8080/v1/groups/{SYSTEM_NUMBER}'
message_url = f'http://127.0.0.1:8080/v1/receive/{SYSTEM_NUMBER}'
message_fetcher = MessageFetcher(group_url, message_url)
message_fetcher.main_loop()


"""
OI FUTURE SELF
next steps are to use multiple messages for processing rather than individuals.
this means simply keeping track of old messages in a structure, saving them to disk automatically,
and then referencing them to get info when people make edits or deletes or reacts or other things.

also need to do attachments at some point.

"""
