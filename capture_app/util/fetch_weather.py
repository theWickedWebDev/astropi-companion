import requests

from capture_app.util.memoize import Memoize


WEATHER_API='http://wttr.in?format="%t+%w+%m+%M+%P+%z+%h+%C"'

@Memoize
async def fetchWeather():
    try:
        weather = {}
        r = requests.get(WEATHER_API)
        weather_data = r.json().split()
        for idx, k in enumerate(["temperature", "wind", "moonphase", "moonday", "precipitation", "zenith", "humidity", "condition"]):
            weather[k] = weather_data[idx]

        temp_f=weather["temperature"].replace('°F', '').replace('+', '')
        temp = (float(temp_f)-32)*(5/9)
        humidity_pc=weather["humidity"].replace('%', '')
        humidity=float(humidity_pc)/100
        
        return {
            **weather, 
            "temp_val": temp, 
            "humidity_val": humidity
        }
    except Exception as e:
        print(e)
        return {}