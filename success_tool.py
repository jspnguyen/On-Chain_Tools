import discord, json, aiohttp
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
    page_number = "1"
    url_template = f"https://feed-api.cielo.finance/api/v1/{wallet}/pnl/tokens?chains=solana&timeframe=max&next_object={{}}&cex_transfers=false"

    headers = {
        "accept": "application/json",
        "X-API-KEY": CIELO_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        while True:
            url = url_template.format(page_number)
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    
                    if response_data["status"] == "ok":
                        profit_data = response_data["data"]["items"]
                        
                        for token in profit_data:
                            if token["token_address"] == contract_address:
                                initial_buy = token["total_buy_usd"]
                                realized_pnl = token["total_pnl_usd"]
                                unrealized_pnl = token["unrealized_pnl_usd"]
                                
                                total_pnl = realized_pnl + unrealized_pnl
                                total_roi = (total_pnl) / initial_buy
                                current_value = initial_buy + total_pnl
                                
                                await interaction.response.send_message(f"Initial: ${round(initial_buy, 2)}\nCurrent Value: ${round(current_value, 2)}\nROI: {round(total_roi, 2)}%")
                                return
                        
                        page_data = response_data["data"]["paging"]
                        
                        if page_data["has_next_page"]:
                            page_number = page_data["next_object"]
                        else:
                            break
                    else:
                        break
                else:
                    break
        await interaction.response.send_message("Token not found or an error occurred.")

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)