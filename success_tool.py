import discord, json, requests
from discord import app_commands

with open('data/config.json', 'r') as f:
    config = json.load(f)

DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN2"]
CIELO_API_KEY = config["CIELO_API_KEY"]

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

@bot.tree.command(name="success_post", description="Display success for a token for your wallet")
@app_commands.describe(contract_address="Contract address for a token", wallet="Sol or EVM wallet address")
async def success_post(interaction: discord.Interaction, contract_address: str, wallet: str):
    # TODO:
    # Make wallet input optional but catch error
    # Finish the command
    url = f"https://feed-api.cielo.finance/api/v1/{wallet}/pnl/tokens?chains=solana&timeframe=max&cex_transfers=false"

    headers = {
        "accept": "application/json",
        "X-API-KEY": CIELO_API_KEY
    }

    response = requests.get(url, headers=headers)

@bot.tree.command(name="help", description="Shows commands for the bot") 
async def self(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="All bot commands", color=discord.Colour.gold())
    embed.add_field(name=f"/add_wallet", value=f"Add a wallet for success bot")
    embed.add_field(name=f"/success_post", value=f"Shows profit stats on a token for your wallet")
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)