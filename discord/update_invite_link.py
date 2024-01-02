import discum
from utils.loop_utils import persistent
from utils.output_utils import silent

channel = "322499026908086294"
token = open("DISCORD_KEY","r").open()

with silent():
    # SHADDDAPPP
    bot = discum.Client(token=token)
    bot.log = {"console":False, "file":"log.txt","encoding":"utf-8"}

@persistent(interval=3)# wait a day between each run
def update_invite_link():
    resp = bot.createInvite(channel, max_age_seconds=3600*24*7)# Max refresh rate, 7 days
    invite_link = f"https://discord.gg/{resp.json()['code']}"
    print(invite_link)
    return invite_link


if __name__=="__main__":
    update_invite_link()
