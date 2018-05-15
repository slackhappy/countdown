import sys
import argparse
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from rgbmatrix.graphics import Color, DrawText, Font
import mta
import weather

COLORS = {
    'green': Color(0, 255, 0),
    'red': Color(255, 0, 0),
    'yellow': Color(255, 255, 0),
    'orange': Color(255, 140, 0),
}

GLYPH_COLORS = {
    'Q': COLORS['yellow'],
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
LINES = ['4', '5', '6', 'Q']

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
                err = None
            except Exception, ex:
                err = str(ex)


        if now - last_weather_fetch > 300:
            try:
                current = weather.current()
                forecast = weather.forecast()
                last_weather_fetch = now
            except Exception, ex:
                err = str(ex)


        status_lines = []
        # always display the lines in order
        for line in LINES:
            mins = []
            for stop_time in times_by_line.get(line, []):
                if stop_time - now < 60:
                    continue
                mins.append(str(int((stop_time - now) / 60)))
                if len(mins) == 2:
                    break
            if mins:
                line_status = status.get(line, 'GOOD SERVICE')
                status_lines.append(StatusLine(
                    [
                        StatusText(glyphs, '|', STATUS_COLORS.get(line_status, COLORS['green'])),
                        StatusText(glyphs, line, GLYPH_COLORS.get(line, COLORS['green'])),
                    ],
                    StatusText(font, ','.join(mins) + 'm')
                ))

        if current:
            status_lines.append(StatusLine([
                StatusText(font, str(current['temp'])),
                StatusText(glyphs, 'o')
            ]))

        if err:
            status_lines.append(StatusLine([StatusText(font, err)]))


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
    args = parser.parse_args()
    glyphs = Font()
    glyphs.LoadFont(args.glyphs)
    font = Font()
    font.LoadFont(args.font)
    render_loop(glyphs, font)
    #mta.status()
    #print weather.current()
    #for f in weather.forecast():
    #    print f
