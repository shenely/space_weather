''''''

#built-in libraries
import urllib
import httplib
import smtplib
import datetime
import json
import email.mime.multipart
import email.mime.text
import email.mime.image

#external libraries
from matplotlib import pyplot
import matplotlib.dates

#internal libraries
#...

#exports
__all__ = ('INFO', 'WARNING', 'ALERT', 'CRITICAL',
           'parse_file', 'process_data',
           'generate_email', 'generate_alert',
           'send_email', 'call_api')

#constants
NOTSET = 0
INFO = 1
WARNING = 10
ALERT = 100
CRITICAL = 1000
LEVEL_MAP = {INFO: 'INFO',
             WARNING: 'WARNING',
             ALERT: 'ALERT',
             CRITICAL: 'CRITICAL'}

SECOND = datetime.timedelta(seconds=1)
MINUTE = datetime.timedelta(minutes=1)
HOUR = datetime.timedelta(hours=1)

TIME_FORMAT = '%H:%M'

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

def process_data(now, data):
    now = datetime.datetime.utcfromtimestamp(now)
    quiet = reduce(lambda x, y:
                   x if x > y else y,
                   (t
                    for (t, p) in data
                    if p > 1),
                   now - 2 * HOUR) + 5 * MINUTE
    p_gt_10 = data[-1][1]
    level = (CRITICAL if p_gt_10 > 100 else
             ALERT if p_gt_10 > 10 else
             WARNING if p_gt_10 > 1 else
             INFO if p_gt_10 < 1
             and now - quiet >= 90 * MINUTE
             else NOTSET)
    return level, p_gt_10

def generate_email(level, value, imgfile, fromaddr, *toaddrs):
    msg = email.mime.multipart.MIMEMultipart()
    
    msg['Subject'] = '[%s] Space Weather Alert' % LEVEL_MAP[level]
    msg['From'] = fromaddr
    msg['To'] = ', '.join(toaddrs)
    
    msg.preample = 'who wants this dog'

    txt = (email.mime.text.MIMEText
           ('> 10 MeV proton flux currently at %.3e' % value,
            'plain'))
    msg.attach(txt)

    with open(imgfile, 'rb') as fin:
        img = email.mime.image.MIMEImage(fin.read())
        msg.attach(img)

    return msg

def generate_plot(now, data, imgfile):
    now = datetime.datetime.utcfromtimestamp(now)
    x = [t for (t, p) in data]
    y = [p for (t, p) in data]

    fig, ax = pyplot.subplots()
    ax.set_title('Particle Flux (>10 MeV)')
    
    ax.set_xlim(x[0], now)
    ax.set_ylim(0.01, 1000)
    
    ax.axhspan(0.01, 1, alpha=0.2, color='green')
    ax.axhspan(1, 10, alpha=0.2, color='yellow')
    ax.axhspan(10, 100, alpha=0.2, color='orange')
    ax.axhspan(100, 1000, alpha=0.2, color='red')
    
    ax.semilogy(x, y)

    time_min = matplotlib.dates.MinuteLocator(range(0, 60, 5))
    time_maj = matplotlib.dates.MinuteLocator(range(0, 60, 10))
    time_fmt = matplotlib.dates.DateFormatter(TIME_FORMAT)
    
    xaxis = ax.get_xaxis()
    yaxis = ax.get_yaxis()
    
    xaxis.set_label_text('UTC Time')
    yaxis.set_label_text('Protons/cm2-s-sr')
    
    xaxis.set_minor_locator(time_min)
    xaxis.set_major_locator(time_maj)
    xaxis.set_major_formatter(time_fmt)
    fig.autofmt_xdate()
    
    pyplot.show()
    pyplot.savefig(imgfile, fmt='png')
    
    return True

def generate_alert(level, value, link):
    head = {'Content-Type': 'application/json'}
    body = {'alert_text': ('Space weather %(level)s: '
                           '> 10 MeV proton flux currently at %(value).3e' %
                           {'level': LEVEL_MAP[level].lower(),
                            'value': value}),
            'level': LEVEL_MAP[level],
            'link': link}
    return head, body

def send_email(host, port, msg):
    server = smtplib.SMTP(host, port)
    senderrs = server.sendemail(msg)
    server.quit()
    
    print senderrs

def call_api(host, port, url, headers, data):
    body = json.dumps(data)
    
    conn = httplib.HTTPSConnection(host, port)
    conn.request('POST', url, body, headers)
    response = conn.getresponse()
    conn.close()

    return response.status == httplib.OK

def next_notify(now):
    last_call = (datetime.datetime.utcfromtimestamp
                 ((int(now) - 60) / (5 * 60) * (5 * 60))
                 + MINUTE + 30 * SECOND)
    next_call = last_call + 5 * MINUTE
    now = datetime.datetime.utcfromtimestamp(now)
    return (next_call - now).total_seconds()
