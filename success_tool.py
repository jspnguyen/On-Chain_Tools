import discord, json
from discord import app_commands

with open('data/config.json', 'r') as f:
    config = json.load(f)

DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN2"]

class PreBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(intents=discord.Intents.all(), *args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.synced = False

    async def on_ready(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True
            print("Bot Online")

bot = PreBot()

# TODO: 

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)