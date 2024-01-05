"""
Unified message class for all platforms, so that it can be parsed and stored here in this consistent form.

1. Id - Identifier of this message.
2. Unix Timestamp
3. Human Timestamp
4. Platform - one of the above
5. Group(or channel) - Possible group or channel the message belongs to.
6. Sender - Person who sent the data, either in a DM or a group.
7. Referred - Message being referred to in this message, like responding to a thread or reacting to a message
8. Attachment(s) - Possible attachment or attachments for a message.
9. Content - Actual text content of the message.
10. Type - Type of the message. May be a TON of different things, including:
   1. Message (normal)
   2. Group Message
   3. Edit
   4. Delete
   5. React
   6. Read Receipt
   7. Delivery Receipt
   8. Typing Notification
"""
import typing
import json
from colorama import Fore, Style, init
from telethon.utils import get_display_name
import asyncio
import threading

from parsers import *
DEBUG = False
RECEIPTS = False

class Message:
    def __init__(self, bot, platform):
        self.bot = bot # bot this is part of

        # Define necessary attributes and init to defaults
        self.id: typing.Any = None
        self.unix_timestamp: int = 0
        self.human_timestamp: str = ""
        self.platform: str = platform
        self.group: str = ""
        self.sender: str = ""
        self.ref: str = ""
        self.attachments: typing.List[str] = []
        self.msg: str = ""
        self.type: str = ""
        #self.data = {}


        # self.user = user
        # self.msg = msg
        # self.data = data
        #
        # # Parse out from attributes the type of message
        # self.is_delivered = self.group == "$delivered"
        # self.is_read = self.group == "$read"
        # self.is_viewed = self.group == "$viewed"
        # self.is_typing = self.group == "$typing"
        # self.is_dm = self.group == "$msg"
        # self.is_deleted = self.group == "$deleted"
        # self.is_unknown = self.group == "$unknown"

        # Otherwise is group message

    async def parse(self, data):
        """
        Parse out based on platform, populate this message class with the data.
        """
        if self.platform == "signal":
            self.parse_signal(data)

        elif self.platform == "telegram":
            await self.parse_telegram(data)

    def parse_signal(self, data):
        """
        Parse out the data from signal message into this class's attributes
        """
        # Flattens dictionary and gets whatever attributes are possible, to keep things simple.
        data = flatten_dict(data)

        # Get unified attributes
        self.unix_timestamp = data.get("timestamp", 0)
        self.human_timestamp = to_human_timestamp(self.unix_timestamp)
        self.sender = data.get("sourceName", "?")
        self.type = "message"

        # Check for flag messages
        """
           1. Message (normal)
           2. Group Message
           3. Edit
           4. Delete
           5. React
           6. Read Receipt
           7. Delivery Receipt
           8. Typing Notification
        """
        # pretty print json data for debugging
        # print(json.dumps(data, indent=4, sort_keys=True))
        if data.get("isDelivery",False):
            # Message delivered notification
            self.type = "delivery"

        elif data.get("isRead", False) or data.get("readMessages", False):
            # Message read notification (the second type is our own read message)
            self.type = "read"

        elif data.get("isViewed", False):
            # Message viewed notification
            self.type = "view"

        elif data.get("action", False):
            # Message typing notification
            self.type = "typing"

        elif data.get("message", False) is None and data.get("emoji", False):
            # react to message
            self.type = "react"
            self.msg = data.get("emoji", "?")

        elif data.get("message", False) is None:
            # Message deleted notification
            self.type = "delete"

        # New message
        elif data.get("message", False):
            # New Message, group or DM
            self.msg = data.get("message", "?")

            # If edited, mark type and refer to original message
            if data.get("targetSentTimestamp", False):
                self.type = "edit"
                self.ref = data.get("targetSentTimestamp", 0)

            if data.get("groupId", False):
                # Group message, use its name
                self.type = "group"
                self.group = self.bot.group_mapping.get(data.get("groupId","?"))[-1]

        else:
            # Unknown
            #group = "$unknown"
            pass

    async def parse_telegram(self, data):
        """
        Parse out the data from telegram message into this class's attributes
            so much easier than signal, oh my god.
        """
        """
        event.chat_id (or event.id)
        event.message.date.timestamp()
        event.message.date.convert(usual)
        "telegram"
        event.chat.title
        event.chat.username
        ??
        event.message.media
        event.message.message

        """
        self.id = data.chat_id
        # Get datetime object in this timezone
        date = to_local_timezone(data.message.date)
        self.unix_timestamp = date.timestamp()
        # self.human_timestamp = to_human_timestamp(self.unix_timestamp)
        self.human_timestamp = date.strftime(STRFTIME_FMT)
        self.platform = "telegram"

        if data.is_group or data.is_channel or data.is_private:
            self.type = "group"
            #self.group = asyncio.run(data.get_chat()).title
            # Try to get from object, otherwise lookup
            if hasattr(data.chat, "title"):
                self.group = data.chat.title
            else:
                self.group = self.bot.group_mapping.get(data.chat_id, "?")
            # self.group = self.run_async_in_thread(data.get_chat())
        else:
            self.type = "message"

        if hasattr(data.message.sender, "username") and data.message.sender.username is not None:
            self.sender = data.message.sender.username
        else:
            self.sender = self.bot.user_mapping.get(data.message.sender_id, "?")

        self.attachments = data.message.media
        self.msg = data.message.message

    def __eq__(self, other):
        # If everything is the same but it came like a few seconds later (duplicate checking) then its equal.
        return self == other
        # return self.group == other.group and \
        #        self. == other.user and \
        #        self.msg == other.msg and \
        #        self.is_delivered == other.is_delivered and \
        #        self.is_read == other.is_read and \
        #        self.is_viewed == other.is_viewed and \
        #        self.is_typing == other.is_typing and \
        #        self.is_dm == other.is_dm and \
        #        self.is_deleted == other.is_deleted and \
        #        self.is_unknown == other.is_unknown

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
        s = f"{timestamp_color}{self.human_timestamp} "

        if self.platform == "signal":
            s += f"📡 "
        elif self.platform == "telegram":
            s += f"🐱 "
        elif self.platform == "text":
            s += f"☎ ️️"




        if self.type == "delivery":
            s += f"{username_color}{self.sender}: {flag_color} Received Message"
        elif self.type == "read":
            s += f"{username_color}{self.sender}: {flag_color} Read Message"
        elif self.type == "view":
            s += f"{username_color}{self.sender}: {flag_color} Viewed Message"
        elif self.type == "typing":
            s += f"{username_color}{self.sender}: {flag_color} Typing Message"
        elif self.type == "deleted":
            s += f"{username_color}{self.sender}: {deleted_color} Deleted Message"
        elif self.type == "message" or self.type == "react" or self.type == "edit":
            s += f"{username_color}{self.sender}: {message_color}{self.msg}"
        elif self.type == "group":# group msg
            s += f"{groupname_color}{self.group} - {username_color}{self.sender}: {message_color}{self.msg}"
        else:
            # s += f"{debug_color}UNKNOWN FORMAT: {message_color}{self.data}"
            pass

        if DEBUG:
            # s += f" {debug_color}DEBUG: {self.data}"
            pass

        if not RECEIPTS:
            if self.type in ["delivery", "read", "view"]:
                return

        print(s)

