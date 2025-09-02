import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

preamBot = commands.Bot(command_prefix="!", intents=intents)

@preamBot.event
async def on_ready():
    print(f"{preamBot.user} is ready!")


@preamBot.event
async def on_member_join(member):
    print(f"{member} is join!")

@preamBot.event

async def on_member_left(member):
    print(f"{member} is left!") 





preamBot.run("MTQxMTA3Mjg1MzgwOTU2MTY1MA.Gs-VFg._zwjyC0tmCBx1Io1EyuBQyxhVr01e0YgPYYb0M")

