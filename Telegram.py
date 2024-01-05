import requests
from parsers import *
from Message import Message
import asyncio
import os
from telethon import TelegramClient, events, sync

SYSTEM_NUMBER = "+18647109821"
API_ID = os.environ["TELEGRAM_API_ID"]
API_HASH = os.environ["TELEGRAM_API_HASH"]



#async def main():

#client.loop.run_until_complete(main())

class Telegram:
    # telegram bot interface

    def __init__(self):
        print("Initializing Telegram Bot...")
        self.client = TelegramClient('session_name', API_ID, API_HASH)


        # Message event listener
        @self.client.on(events.NewMessage())
        async def new_message(event):
            msg = Message(self, platform="telegram")
            await msg.parse(event)
            await self.callback(msg) # send to host


    async def run(self, interval, callback):
        # We do not use interval for this one, since it's event-driven not polling loop.
        # Start the client before using it
        await self.client.start(SYSTEM_NUMBER)

        # Get all channels and messages
        dialogs = await self.client.get_dialogs()

        # Convert to simple ID -> Name mapping
        self.group_mapping = {d.id:d.name for d in dialogs}

        # Get all users from these grouops, make simple ID -> Name mapping
        self.user_mapping = {}
        for d in dialogs:
            try:
                users = await self.client.get_participants(d)
                for u in users:
                    self.user_mapping[u.id] = u.username
            except: continue

        self.callback = callback
        print("Telegram Bot Initialized. Awaiting Messages...")
        await self.client.send_message('BlueHephaestus', 'Cabeiri now running.')

        # Run the client
        await self.client.run_until_disconnected()
