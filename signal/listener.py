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
    def fetch_group_data(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def create_group_mapping(group_data):
        group_mapping = TripletStore()
        for group in group_data:
            id = group.get('id', '')
            internal_id = group.get('internal_id', '')
            name = group.get('name', '')
            group_mapping.insert(id, internal_id, name)
        return group_mapping

    @staticmethod
    def fetch_messages(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error: {e}")
            return None

    def parse_messages(self, data):
        READ_TEMPLATE = ["envelope", "receiptMessage","isRead"]

        messages = []
        for item in data:
            envelope = item.get('envelope', {})
            source_name = envelope.get('sourceName', '')
            try:
                group_internal_id = envelope.get('dataMessage', {}).get('groupInfo', {}).get('groupId', {})
                group_name = MessageFetcher.group_mapping.get(group_internal_id)[-1]
            except:
                group_name = "?"
            timestamp = envelope.get('timestamp', 0)
            human_readable_timestamp = datetime.fromtimestamp(timestamp / 1000).strftime('%b %d, %I:%M%p')
            message_text = envelope.get('dataMessage', {}).get('message', '')

            messages.append(Message(source_name, message_text, human_readable_timestamp, group_name, item))
        return messages

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

class Message:
    def __init__(self, timestamp, group, user, msg, data):
        self.timestamp = timestamp
        self.group = group
        self.user = user
        self.msg = msg
        self.data = data

        # Parse out from attributes the type of message
        self.is_delivered = self.group == "$delivered"
        self.is_read = self.group == "$read"
        self.is_viewed = self.group == "$viewed"
        self.is_typing = self.group == "$typing"
        self.is_dm = self.group == "$msg"
        self.is_deleted = self.group == "$deleted"
        self.is_unknown = self.group == "$unknown"

        # Otherwise is group message

    def __eq__(self, other):
        # If everything is the same but it came like a few seconds later (duplicate checking) then its equal.
        return self.group == other.group and\
               self.user == other.user and\
               self.msg == other.msg and\
               self.is_delivered == other.is_delivered and\
               self.is_read == other.is_read and\
               self.is_viewed == other.is_viewed and\
               self.is_typing == other.is_typing and\
               self.is_dm == other.is_dm and\
               self.is_deleted == other.is_deleted and\
               self.is_unknown == other.is_unknown

    def print(self):
        """
        Print out differently according to type of message
            don't print if certain flags are set.
        :return:
        """
        # Constructing the color-coded message
        timestamp_color = Fore.YELLOW
        groupname_color = Fore.CYAN
        username_color = Fore.GREEN
        flag_color = Fore.MAGENTA
        deleted_color = Fore.RED
        message_color = Fore.WHITE
        debug_color = Fore.RED
        s = f"{timestamp_color}{self.timestamp} "

        if self.is_delivered:
            s += f"{username_color}{self.user}: {flag_color} Received Message"
        elif self.is_read:
            s += f"{username_color}{self.user}: {flag_color} Read Message"
        elif self.is_viewed:
            s += f"{username_color}{self.user}: {flag_color} Viewed Message"
        elif self.is_typing:
            s += f"{username_color}{self.user}: {flag_color} Typing Message"
        elif self.is_deleted:
            s += f"{username_color}{self.user}: {deleted_color} Deleted Message"
        elif self.is_dm:
            s += f"{username_color}{self.user}: {message_color}{self.msg}"
        elif self.is_unknown:
            s += f"{debug_color}UNKNOWN FORMAT: {message_color}{self.data}"
        else: # group msg
            s += f"{groupname_color}{self.group} - {username_color}{self.user}: {message_color}{self.msg}"

        if DEBUG:
            s += f" {debug_color}DEBUG: {self.data}"

        if not RECEIPTS:
            if self.is_delivered or self.is_read or self.is_viewed:
                return

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
