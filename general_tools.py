import discord, json, requests, re, aiohttp, asyncio
from discord import app_commands
from playwright.async_api import async_playwright
from PIL import Image
from moralis import sol_api
from dexscreener import DexscreenerClient

with open('data/config.json', 'r') as f:
    config = json.load(f)

DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN"]
CIELO_API_KEY = config["CIELO_API_KEY"]
MORALIS_API_KEY = config["MORALIS_API_KEY"]

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

def find_solscan_links(text: str) -> list:
    """
    Finds all solscan.io links and returns them as a list
    """
    pattern = r'href="(https://solscan\.io/account/[^\s"]*)"'
    matches = re.findall(pattern, text)
    return matches

def clean_solscan_links(links: list) -> list:
    """
    Removes the unneeded parts of scraped data and return only the top 35 results.
    """
    [link.replace('https://solscan.io/account/', '') for link in links]
    cleaned_links = cleaned_links[7:]
    cleaned_links = cleaned_links[:35] 
    
    return cleaned_links

@bot.tree.command(name="add_keyword", description="Add a keyword to the pump.fun monitor list")
@app_commands.describe(keyword="Coin name keyword you want to look for")
async def add_keyword(interaction: discord.Interaction, keyword: str):
    """
    Add a keyword to the database, the pump.fun monitor will now consider it whenever posting a new deployment.
    """
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
    """
    Remove a keyword from the database, the pump.fun monitor will no longer consider this word whenever posting a new deployment.
    """
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
    """
    Retrieves and posts important stats on the trade performance of a wallet.
    """
    # TODO:Remove chains=solana?
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
            embed.add_field(name=f"Profile", value=f"[Link](https://app.cielo.finance/profile/{wallet})")
            
            await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="check_token_wallets", description="Check token wallets from a txt file")
@app_commands.describe(token_address="Token address for a specified coin you want to check top traders for")
async def check_token_wallets(interaction: discord.Interaction, token_address: str):
    """
    Gets the top holders of a tokens and filter them, posting only wallets that have good performance.
    """
    await interaction.response.defer()  
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(f"https://dexscreener.com/solana/{token_address}?embed=1&theme=dark")

        await asyncio.sleep(4)
        await page.click('button.chakra-button.custom-1tgk3lm')
        await asyncio.sleep(4)
        
        content = await page.content()

        await browser.close()
    
    links = find_solscan_links(content)
    cleaned_links = clean_solscan_links(links)
    
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
                        
                        if tokens_traded >= 10 and winrate >= 40:
                            smart_wallets.append(f"{wallet} {tokens_traded} {round(winrate, 2)}")
    
    # TODO: Improve formatting
    embed = discord.Embed(title=f"Potential Smart Wallets", description="\n".join(smart_wallets), color=discord.Colour.gold())
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="show_keywords", description="Show currently active keywords")
async def show_keywords(interaction: discord.Interaction):
    """
    Display the keywords that are currently being used for the pump.fun monitor.
    """
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
    """
    Retrieves and displays the bubblemap for specified token.
    """
    # TODO: Make the command word for all bubblemaps and not just pump.fun
    await interaction.response.defer()  
    bubblemap_link = f"https://app.bubblemaps.io/sol/token/{token_address}?pumpfun=true&hide_context"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(bubblemap_link)

        await asyncio.sleep(6)
        await page.evaluate('''() => {
            const dialog = document.querySelector('.mdc-dialog.mdc-dialog--open');
            if (dialog) {
                dialog.style.display = 'none';
            }
        }''')
        
        await page.evaluate('''() => {
            const element = document.querySelector('.not-listed-warning');
            if (element) {
                element.style.display = 'none';
            }
        }''')
        
        screenshot_path = "data/bubblemap.png"
        
        await page.screenshot(path=screenshot_path, full_page=True)
        await browser.close()

    image = Image.open(screenshot_path)
    width, height = image.size
    cropped_image = image.crop((0, 65, width, height))
    cropped_image.save(screenshot_path)

    await interaction.followup.send(content=f"[Link](<{bubblemap_link}>)", file=discord.File(screenshot_path))

@bot.tree.command(name="chart", description="Get the 1 hour chart for a token")
@app_commands.describe(token_address="Address for the coin you want to check")
async def chart(interaction: discord.Interaction, token_address: str):
    """
    Display the 15 minute Dexscreener chart for a specified token.
    """
    await interaction.response.defer()  
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(f"https://dexscreener.com/solana/{token_address}?embed=1&theme=dark")

        await asyncio.sleep(4)
        
        screenshot_path = "data/dexchart.png"
        
        await page.screenshot(path=screenshot_path, full_page=False)
        await browser.close()

    image = Image.open(screenshot_path)
    width, height = image.size
    cropped_image = image.crop((55, 41, width - 334, height - 291))
    cropped_image.save(screenshot_path)

    await interaction.followup.send(file=discord.File(screenshot_path))

@bot.tree.command(name="check_holders", description="Check top 20 holder stats")
@app_commands.describe(token_address="Address for the coin you want to check")
async def check_holders(interaction: discord.Interaction, token_address: str):
    url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
    await interaction.response.defer()  
    
    response = requests.get(url)
    
    if response.status_code == 200:
        response_data = response.json()
        ticker = response_data['fileMeta']['symbol']
        top_holder_list = response_data["topHolders"]
        
        fresh_wallets = 0
        less_than_30 = 0
        less_than_50 = 0
        less_than_70 = 0
        greater_than_70 = 0
        
        for holder in top_holder_list:
            holder_address = holder['owner']
            
            url = f"https://feed-api.cielo.finance/api/v1/{holder_address}/pnl/total-stats?chains=solana&timeframe=30d&cex_transfers=false"

            headers = {
                "accept": "application/json",
                "X-API-KEY": CIELO_API_KEY
            }

            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data["status"] == "ok":
                    wallet_data = response_data["data"]
                    
                    tokens_traded = wallet_data["tokens_traded"]
                    winrate = round(wallet_data["winrate"], 2)
                    
                    if tokens_traded > 0:
                        if winrate < 30:
                            less_than_30 += 1
                        elif winrate < 50:
                            less_than_50 += 1
                        elif winrate < 70:
                            less_than_70 += 1
                        else:
                            greater_than_70 += 1
                    else:
                        fresh_wallets += 1
        embed = discord.Embed(title=f"Top Wallet Report for ${ticker}", description=f"Fresh Wallets: {fresh_wallets}\n0-30% winrate: {less_than_30}\n30-50% winrate: {less_than_50}\n50-70% winrate: {less_than_70}\n>70% winrate: {greater_than_70}", color=discord.Colour.gold())
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="notable_holders", description="Check top 20 notable holders")
@app_commands.describe(token_address="Address for the coin you want to check")
async def notable_holders(interaction: discord.Interaction, token_address: str):
    WHITELIST = ["michi", "usdc", "mew", "aura", "soy", "mongy", "$wif", "selfie", "mumu", "brainlet", "mini", "lockin"]
    THRESHOLD_LIMIT = 20000
    top_holders = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
    return_string = ""
    
    await interaction.response.defer()  
    client = DexscreenerClient()

    response = requests.get(top_holders)
    top_holders = response.json()["topHolders"][1:]

    wallet_rank = 1
    for holder in top_holders:
        holder_address = holder["owner"]
        
        params = {
        "network": "mainnet",
        "address": holder_address
        }   

        holdings = sol_api.account.get_spl(
            api_key=MORALIS_API_KEY,
            params=params,
        )
        
        print_string = f"Top Wallet #{wallet_rank}: "
        print_status = False

        for holding in holdings:
            holding_ticker = holding['symbol'].lower()
            
            if holding_ticker in WHITELIST:
                holding_amount = float(holding['amount'])
                holding_token_address = holding['mint']

                if holding_ticker != "usdc":
                    try:
                        pairs = client.get_token_pairs(holding_token_address)
                        price = pairs[0].price_usd
                        
                        holding_value = holding_amount * price
                        if holding_value >= THRESHOLD_LIMIT:
                            print_string += f"${holding_value:,.2f} of {holding_ticker} "
                            print_status = True
                    except:
                        pass
                else:
                    if holding_amount >= THRESHOLD_LIMIT:
                        print_string += f"${holding_amount:,.2f} of {holding_ticker} "
                        print_status = True

        if print_status:
            return_string += f"{print_string}\n"
        
        wallet_rank += 1
    embed = discord.Embed(title=f"Notable Holders", description=return_string, color=discord.Colour.gold())
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Shows commands for the bot") 
async def help(interaction: discord.Interaction, command: str = "all"):
    """
    Display all available commands for the bot.
    """
    commands = ["add_keyword", "remove_keyword", "show_keywords", "check_wallet", "check_token_wallets", "bubblemap", "chart"]
    
    if command == "all":
        embed = discord.Embed(title="Commands", description="Guide to all bot commands", color=discord.Colour.gold())
        embed.add_field(name=f"/add_keyword", value=f"Add a keyword to monitor for in pump.fun deploys")
        embed.add_field(name=f"/remove_keyword", value=f"Remove a keyword from pump.fun deploy monitoring")
        embed.add_field(name=f"/show_keywords", value=f"Shows keywords being actively monitored")
        embed.add_field(name=f"/check_wallet", value=f"Shows important stats on a wallet")
        embed.add_field(name=f"/check_token_wallets", value=f"Check top wallets on a certain token for smart wallets")
        # embed.add_field(name=f"/success_post", value=f"Shows profit stats on a token for your wallet")
        embed.add_field(name=f"/bubblemap", value=f"Generate a bubblemap for a token")
        embed.add_field(name=f"/chart", value=f"Generate a chart for a token")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif command.lower() in commands:
        # TODO: Finish this up
        await interaction.response.send_message(f"WIP")
    else:
        await interaction.response.send_message(f"Invalid command option.")

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)