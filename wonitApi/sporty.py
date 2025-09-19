import requests
from datetime import datetime

def get_booking(code: str):
    url = f"https://www.sportybet.com/api/gh/orders/share/{code}?_t=1757526666143"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json().get("data", {})

        # Format deadline from ms timestamp to ISO string
        deadline = datetime.utcfromtimestamp(data["deadline"] / 1000).strftime("%Y-%m-%dT%H:%M:%S")

        games = []
        for outcome in data.get("outcomes", []):
            markets = outcome.get("markets", [])
            prediction = None
            odd = None

            if markets and markets[0].get("outcomes"):
                market_outcome = markets[0]["outcomes"][0]
                prediction = market_outcome["desc"]
                odd = float(market_outcome["odds"])

            games.append({
                "home": outcome["homeTeamName"],
                "away": outcome["awayTeamName"],
                "prediction": prediction,
                "odd": odd,
                "sport": outcome["sport"]["name"],
                "tournament": outcome["sport"]["category"]["tournament"]["name"]
            })

        return {
            "deadline": deadline,
            "shareCode": data["shareCode"],
            "shareURL": data["shareURL"],
            "games": games
        }

    except requests.RequestException as e:
        return {"error": f"Request failed: {e}"}
