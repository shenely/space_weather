''''''

#built-in libraries
import urllib
import datetime
import logging

#external libraries
#...

#internal libraries
#...

#exports
__all__ = ('ALERT',
           'MaskedFilter', 'EmailHandler',
           'parse_file', 'process_data')

#constants
FIVE_MINUTES = datetime.timedelta(minutes=5)
NINTY_MINUTES = datetime.timedelta(minutes=90)
TWO_HOURS = datetime.timedelta(hours=2)
ALERT = logging.ERROR - 1

class MaskedFilter(logging.Filter):

    def __init__(self, name='', *args):
        super(MaskedFilter, self).__init__(self, name)
        self.levels = args

    def filter(self, record):
        return record.levelno in self.levels

class EmailHandler(logging.handlers.SMTPHandler):

    def getSubject(self, record):
        return ('[%(levelname)s] Space Weather Alert' %
                {'levelname': record.levelname})

def parse_file(filename):
    f = urllib.urlopen(filename)
    data = (line.split()
            for line in f.read().splitlines()
            if not line.startswith((':', '#')))
    data = [(datetime.datetime(int(yr), int(mo), int(da),
                               int(hhmm[:2]), int(hhmm[2:])),
             float(p_gt_10))
            for (yr, mo, da,
                 hhmm, mjd, sod,
                 p_gt_1, p_gt_5, p_gt_10,
                 p_gt_30, p_gt_50, p_gt_100,
                 e_gt_0p8, e_gt_2p0, e_gt_4p0) in data]
    return data

def process_data(data):
    now = datetime.datetime.utcnow()
    quiet = reduce(lambda x, y:
                   x if x > y else y,
                   (t
                    for (t, p) in data
                    if p > 1),
                   now - TWO_HOURS) + FIVE_MINUTES
    p_gt_10 = data[-1][1]
    level = (logging.CRITICAL
             if p_gt_10 > 100 else
             ALERT
             if p_gt_10 > 10 else
             logging.WARNING
             if p_gt_10 > 1 else
             logging.INFO
             if p_gt_10 < 1
             and now - quiet >= NINTY_MINUTES else
             logging.NOTSET)
    return level, p_gt_10
