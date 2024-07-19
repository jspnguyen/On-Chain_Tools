import asyncio
import websockets
import json
import aiohttp

with open('data/config.json', 'r') as f:
    config = json.load(f)

WEBHOOK_URL = config["WEBHOOK_URL"]
KEYWORD_ROLE_ID = config["KEYWORD_ROLE_ID"]

async def fetch_token_data(session, token_address, retries=4, delay=0.25):
    url = f"https://frontend-api.pump.fun/coins/{token_address}"
    for attempt in range(retries):
        async with session.get(url) as response:
            if response.status == 500:
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    continue
                else:
                    return {"error": "Max retries"}
            return await response.json()

async def post_to_webhook(session, url, data):
    async with session.post(url, json=data) as response:
        return response

async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        
        payload = {
            "method": "subscribeNewToken",
        }
        await websocket.send(json.dumps(payload))
        
        async with aiohttp.ClientSession() as session:
            async for message in websocket:
                message = json.loads(message)
                if "mint" in message:
                    token_address = message["mint"]
                    token = await fetch_token_data(session, token_address)
                    
                    with open('data/keywords.json', 'r') as f2:
                        keyword_list = json.load(f2)
                    
                    if "error" not in token:
                        token_name = token.get("name", "N/A") or "N/A"
                        token_symbol = token["symbol"]

                        if any(keyword.lower() in token_name.lower() or keyword.lower() in token_symbol.lower() for keyword in keyword_list.keys()):
                            token_description = token["description"]
                            token_image = token["image_uri"]
                            token_twitter = token.get("twitter", "No Twitter") or "No Twitter"
                            token_telegram = token.get("telegram", "No Telegram") or "No Telegram"
                            
                            if "https://" not in token_twitter and "No Twitter" not in token_twitter:
                                token_twitter = f"https://{token_twitter}"
                            if "https://" not in token_telegram and "No Telegram" not in token_telegram:
                                token_telegram = f"https://{token_telegram}"
                            
                            webhook_data = {
                                "embeds": [{
                                    "title": f"{token_name} ({token_symbol})",
                                    "description": f"**[Buy Now](https://pump.fun/{token_address}/)**\n\n**Description: **{token_description}\n\n{token_twitter} | {token_telegram}",
                                    "color": 47360,  
                                    "thumbnail": {
                                        "url": token_image  
                                    }
                                }],
                            }
                            
                            await post_to_webhook(session, WEBHOOK_URL, webhook_data)

if __name__ == "__main__":
    asyncio.run(subscribe())
