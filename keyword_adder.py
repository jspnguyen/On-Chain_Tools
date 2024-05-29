import discord, json
from discord import app_commands

with open('data/config.json', 'r') as f:
    config = json.load(f)

DISCORD_BOT_TOKEN = config["DISCORD_BOT_TOKEN"]

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

@bot.tree.command(name="show_keyword", description="Show currently active keywords")
async def remove_keyword(interaction: discord.Interaction):
    pass

@bot.tree.command(name="help", description="Shows commands for the bot") 
async def self(interaction: discord.Interaction):
    embed = discord.Embed(title="Commands", description="All bot commands", color=discord.Colour.gold())
    embed.add_field(name=f"/add_keyword", value=f"Add a keyword to monitor for in pump.fun deploys")
    embed.add_field(name=f"/remove_keyword", value=f"Remove a keyword from pump.fun deploy monitoring")
    embed.add_field(name=f"/show_keywords", value=f"Shows keywords being actively monitored (TO BE IMPLEMENTED)")
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == '__main__':
    bot.run(DISCORD_BOT_TOKEN)