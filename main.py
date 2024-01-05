from Signal import *
from Telegram import *
import asyncio

class Cabeiri:
    def __init__(self):
        self.signal_bot = Signal()
        self.telegram_bot = Telegram()

    async def new_message(self, msg):
        # Event listener for new messages from various bots
        msg.print()

    async def run(self):
        t1 = asyncio.create_task(self.signal_bot.run(5, self.new_message))
        t2 = asyncio.create_task(self.telegram_bot.run(-1, self.new_message))

        await asyncio.gather(t1, t2)

if __name__ == "__main__":
    cabeiri = Cabeiri()
    # asyncio.run(cabeiri.telegram_bot.run(1, cabeiri.new_message))
    asyncio.run(cabeiri.run())