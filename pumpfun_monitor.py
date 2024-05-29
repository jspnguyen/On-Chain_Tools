import requests, time, json

with open('data/config.json', 'r') as f:
    config = json.load(f)

with open('data/keywords.json', 'r') as f2:
    keyword_list = json.load(f2)

LATEST_TOKEN_REQUESTS_ENDPOINT = config["LATEST_TOKEN_REQUESTS_ENDPOINT"]
MONITOR_REFRESH_RATE = config["MONITOR_REFRESH_RATE"]
POSTED_LIST_CAPACITY = config["POSTED_LIST_CAPACITY"]
WEBHOOK_URL = config["WEBHOOK_URL"]
KEYWORD_ROLE_ID = config["KEYWORD_ROLE_ID"]

def launch_monitor():
    """
    Monitors pump.fun endpoint to monitor new deployments. Ping associated role if keyword is hit.
    """
    posted_list = []
    
    while True:
        latest_tokens_50_reponse = requests.get(LATEST_TOKEN_REQUESTS_ENDPOINT)
        
        if latest_tokens_50_reponse.status_code == 200:
            latest_tokens_50 = latest_tokens_50_reponse.json()
        
            for token in latest_tokens_50:
                
                token_mint = token["mint"]
                
                if token_mint not in posted_list:
                    posted_list.append(token_mint)
                    
                    token_name = token["name"]
                    token_symbol = token["symbol"]
                    token_description = token["description"]
                    token_image = token["image_uri"]
                    token_twitter = token["twitter"]
                    token_telegram = token["telegram"]
                    
                    if not token_twitter:
                        token_twitter = "No Twiter"
                    if not token_telegram:
                        token_telegram = "No Telegram"
                    
                    if "https://" not in token_twitter and "No Twitter" not in token_twitter:
                        token_twitter = f"https://{token_twitter}"
                    if "https://" not in token_telegram and "No Telegram" not in token_telegram:
                        token_telegram = f"https://{token_telegram}"
                    
                    webhook_data = {
                        "embeds": [{
                            "title": f"{token_name} ({token_symbol})",
                            "description": f"**[Buy Now](https://pump.fun/{token_mint}/)**\n\n**Description: **{token_description}\n\n{token_twitter} | {token_telegram}",
                            "color": 47360,  
                            "thumbnail": {
                                "url": token_image  
                            }
                        }],
                    }
                    
                    if token_name in keyword_list:
                        mention_data = {'content': f"<@&{KEYWORD_ROLE_ID}>"}
                        requests.post(WEBHOOK_URL, json=mention_data)
                    
                    requests.post(WEBHOOK_URL, json=webhook_data)
                
                if len(posted_list) > POSTED_LIST_CAPACITY:
                    posted_list = posted_list[500:]
        
        time.sleep(MONITOR_REFRESH_RATE)

if __name__ == "__main__":
    launch_monitor()