"""
Start a discord bot that will stay persistently online, getting new invite links for a server
    every REFRESH_RATE, each lasting INVITE_LENGTH_DURATION. Does this forever with error resilience.

Every updated link, it will restart the flask server to use that as a redirect URL for "/".

This means that we end up with a URL that automatically redirects to a working link.

So if we have a QR code going to that link, then it will automatically give a working invite link.
"""
import discum
from flask import Flask, redirect
from utils.loop_utils import persistent
from utils.output_utils import silent
import time
from timeout_decorator import timeout, TimeoutError
from datetime import datetime
import pytz

DAY = 3600*24
pst = pytz.timezone('US/Pacific')

REFRESH_RATE = 1*DAY
INVITE_LENGTH_DURATION = 7*DAY

channel = "1121926027740979231"
token = open("DISCORD_KEY","r").read()

@persistent(interval=DAY/2)
def main():
    # Main. everything goes in here. Shouldn't crash, but if it does, will restart clean
    #   in half a day.
    # 
    # Initialise bot. 
    with silent():
        # SHADDDAPPP
        bot = discum.Client(token=token)
        bot.log = {"console":False, "file":"log.txt","encoding":"utf-8"}

    
    def update_invite_link():
        # Get the invite link and format it.
        resp = bot.createInvite(channel, max_age_seconds=INVITE_LENGTH_DURATION)
        invite_link = f"https://discord.gg/{resp.json()['code']}"
        print(f"\tInvite Link Generated: {invite_link}")
        return invite_link

    @timeout(REFRESH_RATE) # so app.run will stop after a day so we can refresh
    def start_redirect_server(redirect_url):
        app = Flask(__name__)

        @app.route('/')
        def index():
            return redirect(redirect_url)

        print(f"\tStarting Redirect Server with URL: {redirect_url}")
        with silent():
            app.run(debug=False)

    # MAIN LOOP
    # Every day, get new invite link and restart the server with the new link.
    # We do this every day rather than every 7 days because of Murphy's Law.
    @persistent(interval=REFRESH_RATE) # handles timeout errors too ;)
    def update_redirect_with_invite():
        now = datetime.now(pst)
        print(f"{now.strftime('%A, %B %d, %I:%M%p')} PST")
        invite_link = update_invite_link()
        try:
            start_redirect_server(invite_link)
        except TimeoutError: pass


    update_redirect_with_invite()

main()


