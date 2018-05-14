import urllib2
import json
import time
import keys

def _extract_weather(obj):
    return {
        'weather': obj['weather'][0]['main'],
        'temp': int(obj['main']['temp']),
        'time': obj['dt'],
    }

def make_url(url):
    return url.format(key=keys.WEATHER)

def current():
    url = make_url('http://api.openweathermap.org/data/2.5/weather?id=5125771&APPID={key}&units=imperial')
    response = urllib2.urlopen(url, None, timeout=4)
    contents = response.read()
    obj = json.loads(contents)
    return _extract_weather(obj)

def forecast():
    url = make_url('http://api.openweathermap.org/data/2.5/forecast?id=5125771&APPID={key}&units=imperial')
    response = urllib2.urlopen(url, None, timeout=4)
    contents = response.read()
    obj = json.loads(contents)
    forecasts = []
    now = time.time()
    for forecast in obj['list']:
        if forecast['dt'] > now:
            forecasts.append(_extract_weather(forecast))
    return sorted(forecasts, key=lambda f: f['time'])
