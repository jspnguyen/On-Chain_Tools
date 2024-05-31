import discord, json, requests
from discord import app_commands

with open('data/config.json', 'r') as f:
    config = json.load(f)

DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN"]
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

@bot.tree.command(name="add_keyword", description="Add a keyword to the pump.fun monitor list")
@app_commands.describe(keyword="Coin name keyword you want to look for")
async def add_keyword(interaction: discord.Interaction, keyword: str):
    with open('data/keywords.json', 'r') as f:
        keyword_list = json.load(f)
    
    if keyword not in keyword_list:
        keyword_list[keyword] = True
        
        with open('data/keywords.json', 'w') as f2:
            json.dump(keyword_list, f2)
        
        await interaction.response.send_message(f"Success! Keyword '{keyword}' has been added.")
    else:
        await interaction.response.send_message(f"The keyword '{keyword}' already exists in the list.")

@bot.tree.command(name="remove_keyword", description="Remove a keyword from the pump.fun monitor list")
@app_commands.describe(keyword="Coin name keyword you want to remove")
async def remove_keyword(interaction: discord.Interaction, keyword: str):
    with open('data/keywords.json', 'r') as f:
        keyword_list = json.load(f)
    
    if keyword in keyword_list:
        del keyword_list[keyword]
        
        with open('data/keywords.json', 'w') as f2:
            json.dump(keyword_list, f2)
        
        await interaction.response.send_message(f"Success! Keyword '{keyword}' has been removed.")
    else:
        await interaction.response.send_message(f"The keyword '{keyword}' does not exist in the list.")

@bot.tree.command(name="check_wallet", description="Display important stats for a wallet")
@app_commands.describe(wallet="Sol or EVM wallet address")
async def check_wallet(interaction: discord.Interaction, wallet: str):
    # TODO: 
    # Add optional time frame param with 3 choices: 1d, 7d, 30d
    # Defaults to 30 days
    url = f"https://feed-api.cielo.finance/api/v1/{wallet}/pnl/total-stats?chains=solana&cex_transfers=false"

    headers = {
        "accept": "application/json",
        "X-API-KEY": CIELO_API_KEY
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        
        if response_data["status"] == "ok":
            wallet_data = response_data["data"]
            
            realized_pnl_usd = round(wallet_data["realized_pnl_usd"], 2)
            realized_roi_percentage = round(wallet_data["realized_roi_percentage"], 2)
            tokens_traded = wallet_data["tokens_traded"]
            unrealized_pnl_usd = round(wallet_data["unrealized_pnl_usd"], 2)
            unrealized_roi_percentage = round(wallet_data["unrealized_roi_percentage"], 2)
            winrate = round(wallet_data["winrate"], 2)
            combined_pnl_usd = round(wallet_data["combined_pnl_usd"], 2)
            combined_roi_percentage = round(wallet_data["combined_roi_percentage"], 2)
            
            embed = discord.Embed(title=f"{wallet[:4]}...{wallet[-4:]}", color=discord.Colour.gold())
            embed.add_field(name=f"Realized PNL", value=f"${realized_pnl_usd}")
            embed.add_field(name=f"Unrealized PNL", value=f"${unrealized_pnl_usd}")
            embed.add_field(name=f"Combined PNL", value=f"${combined_pnl_usd}")
            
            embed.add_field(name=f"Realized ROI", value=f"{realized_roi_percentage}%")
            embed.add_field(name=f"Unrealized ROI", value=f"{unrealized_roi_percentage}%")
            embed.add_field(name=f"Combined ROI", value=f"{combined_roi_percentage}%")
            
            embed.add_field(name=f"Win Rate", value=f"{winrate}%")
            embed.add_field(name=f"Tokens Traded", value=f"{tokens_traded}")
            
            await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="show_keywords", description="Show currently active keywords")
async def show_keywords(interaction: discord.Interaction):
    pass

@bot.tree.command(name="help", description="Shows commands for the bot") 
async def self(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="All bot commands", color=discord.Colour.gold())
    embed.add_field(name=f"/add_keyword", value=f"Add a keyword to monitor for in pump.fun deploys")
    embed.add_field(name=f"/remove_keyword", value=f"Remove a keyword from pump.fun deploy monitoring")
    embed.add_field(name=f"/show_keywords", value=f"Shows keywords being actively monitored")
    embed.add_field(name=f"/check_wallet", value=f"Shows important stats on a wallet")
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)