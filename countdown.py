import argparse
import logging
import mta
import sys
import time
import weather

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix.graphics import Color, DrawText, Font, DrawLine

logger = logging.getLogger(__name__)

COLORS = {
    'white': Color(255, 255, 255),
    'blue': Color(0, 0, 255),
    'black': Color(0, 0, 0),
    'green': Color(0, 255, 0),
    'red': Color(255, 0, 0),
    'yellow': Color(255, 255, 0),
    'orange': Color(255, 140, 0),
}

GLYPH_COLORS = {
    'Q': COLORS['yellow'],
    'M': COLORS['orange'],
    '4': COLORS['green'],
    '5': COLORS['green'],
    '6': COLORS['green'],
}

STATUS_COLORS = {
    'GOOD SERVICE': COLORS['green'],
    'SERVICE CHANGE': COLORS['orange'],
    'PLANNED WORK': COLORS['orange'],
    'DELAYS' : COLORS['red'],
}

SUBWAYTIME_STOPS = [('Q/Q04', 'Downtown'), ('5/626', 'Downtown')]
SLOTS = ['6', '4|5', 'Q|M']

class StatusBar:
    def __init__(self, height, color=None):
        self.height = height
        self.color = color
        if not color:
            self.color = COLORS['green']

    def draw(self, matrix, x, y):
        DrawLine(matrix, x, y, x, y - self.height, self.color)
        return 1

class StatusText:
    def __init__(self, font, text, color=None):
        self.font = font
        self.text = text
        self.color = color
        if not color:
            self.color = COLORS['green']

    def draw(self, matrix, x, y):
        return DrawText(matrix, self.font, x, y, self.color, self.text)
    
class StatusLine:
    def __init__(self, lefts, right=None):
        self.lefts = lefts
        self.right = right

    def height(self):
        if self.right:
            return max(self.lefts[0].font.height, self.right.font.height)
        return self.lefts[0].font.height

    def baseline(self):
        if self.right:
            return max(self.lefts[0].font.baseline, self.right.font.baseline)
        return self.lefts[0].font.baseline

    def draw(self, matrix, y):
        if self.lefts:
            x = 0
            for l in self.lefts:
                x += l.draw(matrix, x, y)
        if self.right:
            w = self.right.draw(matrix, 64, y)
            self.right.draw(matrix, 64 - w, y)
        return self.height() 

def init():
    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'regular' 
    options.brightness = 10
    return RGBMatrix(options = options)

def render_loop(glyphs, font):
    last_mta_fetch = 0
    last_weather_fetch = 0
    matrix = init()
    times_by_line = {}
    current = {}
    forecast = []
    status = {}
    while True:
        now = time.time()
        if now - last_mta_fetch > 60:
            try:
                status = mta.status()
                times_by_line.update(mta.times_from_subwaytime(SUBWAYTIME_STOPS))
                last_mta_fetch = now
            except Exception, ex:
                logger.exception('failed to get time')

        if now - last_weather_fetch > 300:
            try:
                current = weather.current()
                forecast = weather.forecast_accuweather()
                last_weather_fetch = now
            except Exception, ex:
                logger.exception('failed to get time')


        status_lines = []
        # always display the lines in order
        for slot in SLOTS:
            slot_entries = []
            slot_lines = slot.split('|')
            for line in slot_lines:
                for stop_time in times_by_line.get(line, []):
                    if stop_time - now < 60:
                        continue
                    slot_entries.append((int((stop_time - now) / 60.0), line))
            slot_entries = sorted(slot_entries)[0:2]
            mins = [str(e[0]) for e in slot_entries]
            seen = set()
            lines = [e[1] for e in slot_entries if not (e[1] in seen or seen.add(e[1]))]
            if not lines:
                lines = [slot_lines[0]]

            status_line = []
            for line in lines:
                line_status = status.get(line, 'GOOD SERVICE')
                status_line.append(StatusText(glyphs, '|', STATUS_COLORS.get(line_status, COLORS['green'])))
                status_line.append(StatusText(glyphs, line, GLYPH_COLORS.get(line, COLORS['green'])))
            status_lines.append(StatusLine(
                status_line,
                StatusText(font, ','.join(mins) + 'm' if mins else '?')
            ))


        if current:
            status_line = [
                StatusText(glyphs, '|', COLORS['black']),
                StatusText(font, str(current['temp'])),
                StatusText(glyphs, 'o')
            ]
            if forecast:
                forecast = forecast[0:24]
                high = max([hr['temp'] for hr in forecast])
                low = min([hr['temp'] for hr in forecast])
                status_line.extend([
                    StatusText(font, ' {}-{}'.format(low, high)),
                    StatusText(glyphs, 'o')
                ])
                status_lines.append(StatusLine(status_line))
                status_line = [StatusText(glyphs, '|||||||||||||', COLORS['black'])]
                temp_range = high - low
                div = 9 / (temp_range + 0.1)
                for hr in forecast:
                    height = round((hr['temp'] - low) * div)
                    color = COLORS['blue'] if hr['weather'] == 'Rain' else COLORS['green']
                    color = COLORS['white'] if hr['weather'] == 'Snow' else color
                    status_line.append(StatusBar(height, color))
            status_lines.append(StatusLine(status_line))

        render(matrix, status_lines)
        time.sleep(5) 


def render(matrix, status_lines):
    matrix.Clear()
    if not status_lines:
        return

    y = status_lines[0].baseline()
    for status_line in status_lines:
        y += status_line.draw(matrix, y)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='countdown. find and display subway info')
    parser.add_argument('--glyphs', type=str, help='glyph font', required=True)
    parser.add_argument('--font', type=str, help='normal font', required=True)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=fmt)
    if args.debug:
        logger.setLevel('DEBUG')
        mta.logger.setLevel('DEBUG')
        weather.logger.setLevel('DEBUG')

    glyphs = Font()
    glyphs.LoadFont(args.glyphs)
    font = Font()
    font.LoadFont(args.font)
    render_loop(glyphs, font)
