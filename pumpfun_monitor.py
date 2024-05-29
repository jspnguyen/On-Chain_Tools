import requests, time, json

with open('data/config.json', 'r') as f:
    config = json.load(f)

with open('data/keywords.json', 'r') as f2:
    keyword_list = json.load(f)

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
        latest_tokens_50 = requests.get(LATEST_TOKEN_REQUESTS_ENDPOINT).text
        
        for token in latest_tokens_50:
            token_signature = token["signature"]
            
            if token_signature not in posted_list:
                posted_list.append(token_signature)
                
                token_name = token["name"]
                token_symbol = token["symbol"]
                token_description = token["description"]
                token_image = token["image_uri"]
                token_twitter = token["twitter"]
                token_telegram = token["telegram"]
                
                if not token_twitter:
                    token_twitter = "No Twiter"
                if not token_telegram:
                    token_twitter = "No Telegram"
                
                webhook_data = {
                    "embeds": [{
                        "title": f"{token_name} ({token_symbol})",
                        "description": f"**Description: **{token_description}\n\n{token_twitter} | {token_telegram}",
                        "color": 47360,  
                        "thumbnail" : token_image
                    }],
                }
                
                if token_name in keyword_list:
                    mention_data = {'content': f"<@&{KEYWORD_ROLE_ID}>"}
                    requests.post(WEBHOOK_URL, json=mention_data)
                
                requests.post(WEBHOOK_URL, json=webhook_data)
            
            if len(posted_list) > POSTED_LIST_CAPACITY:
                posted_list = posted_list[200:]
        
        time.sleep(LATEST_TOKEN_REQUESTS_ENDPOINT)

if __name__ == "__main__":
    launch_monitor()