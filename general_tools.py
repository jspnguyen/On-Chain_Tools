import discord, json, requests, os, re, aiohttp, asyncio
from discord import app_commands
from playwright.async_api import async_playwright
from PIL import Image

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

def find_solscan_links(text):
    pattern = r'href="(https?://[^\s"]*solscan\.io[^\s"]*)"'
    matches = re.findall(pattern, text)
    return matches

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
@app_commands.describe(wallet="Sol or EVM wallet address", timeframe="Time frame to check the wallet stats")
@app_commands.choices(timeframe=[
    app_commands.Choice(name="1 day", value="1d"),
    app_commands.Choice(name="7 days", value="7d"),
    app_commands.Choice(name="30 days", value="30d")
])
async def check_wallet(interaction: discord.Interaction, wallet: str, timeframe: str = "30d"):
    url = f"https://feed-api.cielo.finance/api/v1/{wallet}/pnl/total-stats?chains=solana&timeframe={timeframe}&cex_transfers=false"

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

@bot.tree.command(name="check_token_wallets", description="Check token wallets from a txt file")
@app_commands.describe(file="Upload the txt file containing token addresses")
async def check_token_wallets(interaction: discord.Interaction, file: discord.Attachment):
    if not file.filename.endswith('.txt'):
        await interaction.response.send_message("Please upload a valid .txt file.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    file_path = f"/tmp/{file.filename}"
    await file.save(file_path)
    
    try:
        with open(file_path, 'r') as f:
            html_element = f.read()
            links = find_solscan_links(html_element)
            cleaned_links = [link.replace('https://solscan.io/account/', '') for link in links]
            
            cleaned_links = cleaned_links[:25] # ! TEMP
            
            smart_wallets = []
            
            async with aiohttp.ClientSession() as session:
                for wallet in cleaned_links:
                    url = f"https://feed-api.cielo.finance/api/v1/{wallet}/pnl/total-stats?chains=solana&timeframe=30d&cex_transfers=false"
                    headers = {
                        "accept": "application/json",
                        "X-API-KEY": CIELO_API_KEY
                    }

                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            if response_data["status"] == "ok":
                                wallet_data = response_data["data"]
                                
                                tokens_traded = wallet_data["tokens_traded"]
                                winrate = wallet_data["winrate"]
                                
                                if tokens_traded >= 20 and winrate >= 60:
                                    smart_wallets.append(f"{wallet} {tokens_traded} {winrate}")
            
            # TODO: Improve formatting
            embed = discord.Embed(title=f"Potential Smart Wallets for TICKER", description="\n".join(smart_wallets), color=discord.Colour.gold())
            await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.response.send_message(f"An error occurred while processing the file: {e}", ephemeral=True)
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@bot.tree.command(name="show_keywords", description="Show currently active keywords")
async def show_keywords(interaction: discord.Interaction):
    with open('data/keywords.json', 'r') as f:
        keyword_list = json.load(f)
    
    if keyword_list:
        keywords = "\n".join(keyword_list.keys())
        await interaction.response.send_message(f"Active keywords:\n{keywords}")
    else:
        await interaction.response.send_message("No active keywords.")

@bot.tree.command(name="bubblemap", description="Get the bubblemap for a token")
@app_commands.describe(token_address="Address for the coin you want to check")
async def bubblemap(interaction: discord.Interaction, token_address: str):
    await interaction.response.defer()  
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"https://app.bubblemaps.io/sol/token/{token_address}?pumpfun=true&hide_context")

        await asyncio.sleep(4)
        await page.evaluate('''() => {
            const dialog = document.querySelector('.mdc-dialog.mdc-dialog--open');
            if (dialog) {
                dialog.style.display = 'none';
            }
        }''')
        
        screenshot_path = "bubblemap.png"
        
        await page.screenshot(path=screenshot_path, full_page=True)
        await browser.close()

    image = Image.open(screenshot_path)
    width, height = image.size
    cropped_image = image.crop((0, 65, width, height - 49))
    cropped_image.save(screenshot_path)

    await interaction.followup.send(file=discord.File(screenshot_path))

@bot.tree.command(name="help", description="Shows commands for the bot") 
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="All bot commands", color=discord.Colour.gold())
    embed.add_field(name=f"/add_keyword", value=f"Add a keyword to monitor for in pump.fun deploys")
    embed.add_field(name=f"/remove_keyword", value=f"Remove a keyword from pump.fun deploy monitoring")
    embed.add_field(name=f"/show_keywords", value=f"Shows keywords being actively monitored")
    embed.add_field(name=f"/check_wallet", value=f"Shows important stats on a wallet")
    embed.add_field(name=f"/add_success_wallet", value=f"Add a wallet for success bot")
    embed.add_field(name=f"/success_post", value=f"Shows profit stats on a token for your wallet")
    embed.add_field(name=f"/bubblemap", value=f"Generate a bubblemap for a token")
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)