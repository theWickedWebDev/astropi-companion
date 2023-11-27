from quart import current_app
import requests

def getWeather():
    try:
        weather = {}
        WEATHER_API_URL = current_app.config['WEATHER_API_URL']

        r = requests.get(WEATHER_API_URL)
        weather_data = r.json()
        lines = weather_data.split()
        weather["temperature"] = lines[0]
        weather["wind"] = lines[1]
        weather["moonphase"] = lines[2]
        weather["moonday"] = lines[3]
        weather["precipitation"] = lines[4]
        weather["zenith"] = lines[5]
        weather["humidity"] = lines[6]
        weather["condition"] = lines[7]
        
        return weather
    except Exception as e:
        print(e)
        return {}
