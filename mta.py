import urllib2
import time
from collections import defaultdict
import re
import json
import xml.etree.ElementTree as ET
import keys



REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'Referer': 'http://subwaytime.mta.info/index.html',
    'Accept': '*/*',
}


def make_url(url):
    return url.format(key=keys.MTA)
#
# Based on info from http://subwaytime.mta.info/
#
def times_from_subwaytime(stops):
    base_url = 'http://TrainTimeLB-367443097.us-east-1.elb.amazonaws.com/'
    request = urllib2.Request("http://subwaytime.mta.info/js/app.js", headers=REQUEST_HEADERS)
    contents = urllib2.urlopen(request, None, timeout=4).read()
    now = int(time.time())
    for line in contents.split('\n'):
        m = re.search(r'http.*elb.amazonaws.com/', line)
        if m:
            base_url = m.group(0)

    times_by_line = defaultdict(list)
    for url_part, direction in stops:
        url = base_url + "getTime/" + url_part
        request = urllib2.Request(url, headers=REQUEST_HEADERS)
        contents = urllib2.urlopen(request).read()
        obj = json.loads(contents)
        for obj_dir_field in ['direction1', 'direction2']:
            obj_dir = obj.get(obj_dir_field, {})
            if obj_dir.get('name') == direction:
                for stop_time in obj_dir.get('times', []):
                    times_by_line[stop_time['route']].append(now + stop_time['minutes'] * 60)

    for line, times in times_by_line.items():
        times_by_line[line] = sorted(times)[:3]
    return times_by_line

def status():
    url = 'http://web.mta.info/status/serviceStatus.txt'
    response = urllib2.urlopen(url)
    status = {}
    for line_el in ET.fromstring(response.read()).find('subway').iter('line'):
        name = line_el.find('name').text
        for line_char in name:
            status[line_char] = line_el.find('status').text

    return status

