import discord
from discord import Interaction, Game, Status, Embed
from discord.ext import commands, tasks
import sys, os, json
import logging
import subprocess
import requests


DIR = sys.path[0]
SETTING = json.load(open(f"{DIR}/setting.json", "r"))
TOKEN = SETTING["TOKEN"]
GUILD_IDS = SETTING["GUILD_IDS"]


bot = commands.Bot()


class NoTokenLogFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return 'token' not in message


logger = logging.getLogger(__name__)
logger.addFilter(NoTokenLogFilter())
formatter = '%(asctime)s$%(filename)s$%(lineno)d$%(funcName)s$%(levelname)s:%(message)s'
logging.basicConfig(format=formatter, filename=f'{DIR}/niranet_statusbot.log', level=logging.INFO)


async def getServiceStatus():
    subprocess_result = subprocess.run(args="systemctl status apache2", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return subprocess_result.returncode


async def getWebpageStatus():
    try:
        r = requests.get(f"https://nira.f5.si/")
        return r.status_code
    except:
        return None


async def changeStatus():
    service: int = await getServiceStatus()
    webpage: int = await getWebpageStatus()
    if service != 0:
        return (Game(name="停止中: Service", type=1), Status.dnd, 1, service, webpage)
    else:
        if webpage != 200:
            return (Game(name="停止中: Network", type=1), Status.dnd, 2, service, webpage)
        else:
            return (Game(name="稼働中: OK", type=1), Status.online, 0, service, webpage)


@tasks.loop(seconds=10)
async def changeBotStatus():
    status = await changeStatus()
    await bot.change_presence(activity=status[0], status=status[1])


@bot.event
async def on_ready():
    print(f"""\
Launched.
NANE: {bot.user.name}#{bot.user.discriminator}
ID: {bot.user.id}
GUILD_IDS: {GUILD_IDS}""")
    await bot.change_presence(activity=Game(name="接続中...: Loading", type=1), status=Status.dnd)
    changeBotStatus.start()


@bot.slash_command(name="status", description="Niranet Status")
async def status_slash(interaction: Interaction):
    await interaction.response.defer()
    status = await changeStatus()
    if status[2] == 0:
        await interaction.followup.send(embed=Embed(title="NIRA Net Status", description=f"NIRA Netは稼働中です。\nステータスコード: `{status[2]}`/`{status[3]}`/`{status[4]}`", color=0x00ff00),ephemeral=True)
    else:
        await interaction.followup.send(embed=Embed(title="NIRA Net Status", description=f"NIRA Netに接続できませんでした。\nステータスコード: `{status[2]}`/`{status[3]}`/`{status[4]}`", color=0xff0000),ephemeral=True)



bot.run(TOKEN)
