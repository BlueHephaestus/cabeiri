from Signal import *
import asyncio

class Cabeiri:
    def __init__(self):
        self.signal_bot = Signal()
        self.telegram_bot = Signal()

    async def new_message(self, msg):
        # Event listener for new messages from various bots
        msg.print()

    async def run(self):
        asyncio.create_task(self.signal_bot.run(5, self.new_message))
        asyncio.create_task(self.telegram_bot.run(1, self.new_message))

if __name__ == "__main__":
    cabeiri = Cabeiri()
    asyncio.run(cabeiri.run())