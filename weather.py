import json
import keys
import logging
import os
import time
import urllib2

logger = logging.getLogger(__name__)
CACHE_PATH = '/tmp/forecast_cache.json'

def _extract_weather(obj):
    return {
        'weather': obj['weather'][0]['main'],
        'temp': int(obj['main']['temp']),
        'time': obj['dt'],
    }

def _extract_accuweather(obj):
    precip = obj.get('PrecipitationProbability', 0) > 50
    precip_type = 'Rain' if precip else ''
    if precip:
        if obj.get('WeatherIcon', 0) in [22, 23, 24, 29, 44]:
            precip_type = 'Snow'

    return {
        'weather': precip_type,
        'temp': int(obj['Temperature']['Value']),
        'time': obj['EpochDateTime'],
    }

def make_url(url):
    return url.format(key=keys.WEATHER)

def make_url_accuweather(url):
    return url.format(key=keys.ACCUWEATHER, loc=keys.ACCUWEATHER_LOCATION)

def current():
    url = make_url('http://api.openweathermap.org/data/2.5/weather?id=5125771&APPID={key}&units=imperial')
    response = urllib2.urlopen(url, None, timeout=4)
    contents = response.read()
    obj = json.loads(contents)
    logger.debug('current weather\n %s', json.dumps(obj, indent=2))
    return _extract_weather(obj)

def forecast():
    url = make_url('http://api.openweathermap.org/data/2.5/forecast?id=5125771&APPID={key}&units=imperial')
    response = urllib2.urlopen(url, None, timeout=4)
    contents = response.read()
    obj = json.loads(contents)
    logger.debug('forecast obj\n %s', json.dumps(obj, indent=2))
    forecasts = []
    now = time.time()
    for forecast in obj['list']:
        if forecast['dt'] > now:
            forecasts.append(_extract_weather(forecast))
        else:
            logger.debug('%d (%s) is rejected', forecast['dt'], time.ctime(forecast['dt']))
    forecasts = sorted(forecasts, key=lambda f: f['time'])
    logger.debug('forecast weather\n %s', json.dumps(forecasts, indent=2))
    return forecasts


def forecast_accuweather():
    cache_obj = None
    obj = None
    forecasts = []
    now = time.time()
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as fh:
            cache_obj = json.loads(fh.read())
            obj = cache_obj['data']
        
    if not cache_obj or cache_obj['expires'] < now:
        url = make_url_accuweather('https://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{loc}?apikey={key}')
        logger.debug('accuweather cache miss')
        response = urllib2.urlopen(url, None, timeout=4)
        contents = response.read()
        obj = json.loads(contents)
        with open(CACHE_PATH, 'w') as fh:
            fh.write(json.dumps({'expires': int(now) + 60 * 60, 'data': obj}, indent=2))

    for forecast in obj:
        if forecast['EpochDateTime'] > now:
            forecasts.append(_extract_accuweather(forecast))
    
    forecasts = sorted(forecasts, key=lambda f: f['time'])
    logger.debug('forecast accuweather\n %s', json.dumps(forecasts, indent=2))
    return forecasts



