import requests
import json

def send_discord(webhook_url, username, message):
    data = {
        "content": message,
        "username": username
    }

    result = requests.post(webhook_url, json=data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))

# Example usage
if __name__ == '__main__':
    webhook_url = "https://discord.com/api/webhooks/1187665265299828806/EptC8PVDmt5zV9kxI-gENk0cqFKS2ooo_-1pk4TR70M0AFSnmmzoYVrkSSBTXLD1scDw"
    send_to_discord(webhook_url, "Hello, this is a test message from my script!")