'''Space weather alerts'''

#built-in libraries
import urllib
import httplib
import smtplib
import datetime
import json
import email.mime.multipart
import email.mime.text
import email.mime.image
import logging

#external libraries
from matplotlib import pyplot
import matplotlib.dates

#internal libraries
#...

#exports
__all__ = ('NOTSET', 'INFO', 'WARNING', 'ALERT', 'CRITICAL',
           'get_logger',
           'retrieve_data', 'process_data',
           'format_filename',
           'generate_email', 'generate_alert', 'generate_plot',
           'send_email', 'call_api',
           'next_notify')

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

#NOTE: makes it easier to do time math
SECOND = datetime.timedelta(seconds=1)
MINUTE = datetime.timedelta(minutes=1)
HOUR = datetime.timedelta(hours=1)

FILENAME_FORMAT = '{0:%Y%m%d_%H%M}_{1}.{2}'
TIME_FORMAT = '%H:%M'

def get_logger():
    global logger
    logger = logging.getLogger('space_weather')
    handler = logging.StreamHandler()
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def retrieve_data(filename):
    'Scrape data from provided website'
    f = urllib.urlopen(filename)
    lines = f.read().splitlines()
    data = (line.split()
            for line in lines
            if not line.startswith((':', '#')))
    try:
        data = [(datetime.datetime(int(yr), int(mo), int(da),
                                   int(hhmm[:2]), int(hhmm[2:])),
                 float(p_gt_10))
                for (yr, mo, da,
                     hhmm, mjd, sod,
                     p_gt_1, p_gt_5, p_gt_10,
                     p_gt_30, p_gt_50, p_gt_100,
                     e_gt_0p8, e_gt_2p0, e_gt_4p0) in data]
        filename = lines[0].split()[1]
        return data, filename
    except ValueError:
        logger.error('invalid file format in %s '
                    '(may not exist)', filename)
        raise SystemExit

def process_data(now, data):
    'Determine alert level and last known value'
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

    if level > NOTSET:
        logger.info('%s space weather with proton flux of %.3e',
                    LEVEL_MAP[level], p_gt_10)
    else:
        logger.info('current proton flux of %.3e', p_gt_10)
    return level, p_gt_10

def format_filename(now, filename, ext):
    'Generate filename from data provided'
    now = datetime.datetime.utcfromtimestamp(now)
    stem = filename.split('.')[0]
    return FILENAME_FORMAT.format(now, stem, ext)

def generate_email(level, value, imgfile, fromaddr, *toaddrs):
    'Create email with plot attached'
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

    for toaddr in toaddrs:
        logger.info('generated %s email for %s',
                    LEVEL_MAP[level], toaddr)

    return msg

def generate_plot(now, data, imgfile):
    'Create plot of data over specified timeframe'
    now = datetime.datetime.utcfromtimestamp(now)
    x = [t for (t, p) in data]#date/time
    y = [p for (t, p) in data]#proton flux

    fig, ax = pyplot.subplots()
    ax.set_title('Particle Flux (>10 MeV)')
    ax.set_xlim(x[0], now)
    ax.set_ylim(0.01, 1000)

    #bands representing alert levels
    ax.axhspan(0.01, 1, alpha=0.2, color='green')
    ax.axhspan(1, 10, alpha=0.2, color='yellow')
    ax.axhspan(10, 100, alpha=0.2, color='orange')
    ax.axhspan(100, 1000, alpha=0.2, color='red')
    ax.semilogy(x, y)

    #axis labels
    xaxis = ax.get_xaxis()
    yaxis = ax.get_yaxis()
    xaxis.set_label_text('UTC Time')
    yaxis.set_label_text('Protons/cm2-s-sr')

    #makes times on x-axis look better
    time_min = matplotlib.dates.MinuteLocator(range(0, 60, 5))
    time_maj = matplotlib.dates.MinuteLocator(range(0, 60, 10))
    time_fmt = matplotlib.dates.DateFormatter(TIME_FORMAT)
    xaxis.set_minor_locator(time_min)
    xaxis.set_major_locator(time_maj)
    xaxis.set_major_formatter(time_fmt)
    fig.autofmt_xdate()
    
    pyplot.savefig(imgfile, fmt='png')
    logger.info('plot saved to %s', imgfile)

def generate_alert(level, value, link):
    'Create JSON document describing alert'
    #NOTE: mostly from requirements
    headers = {'Content-Type': 'application/json'}
    body = {'alert_text': ('Space weather %(level)s: '
                           '> 10 MeV proton flux currently at %(value).3e' %
                           {'level': LEVEL_MAP[level].lower(),
                            'value': value}),
            'level': LEVEL_MAP[level],
            'link': link}
    logger.info('generated %s alert', LEVEL_MAP[level])
    return headers, body

def send_email(host, port, tls, username, password,
               msg, fromaddr, *toaddrs):
    'Send email to listed addresses'
    try:
        server = smtplib.SMTP(host, port)
        if tls:server.starttls()
        server.login(username, password)
        senderrs = server.sendmail(fromaddr, toaddrs, msg.as_string())
        server.quit()
    except (smtplib.SMTPException, smtplib.socket.error) as err:
        logger.error('could not send email becaues %s', err)
        raise SystemExit
    else:
        #NOTE: there's more info here, but addresses are enough
        for toaddr in senderrs.keys():
            logging.warning('could not send to %s', toaddr)

def call_api(host, port, url, headers, data):
    'Make call to configured API'
    body = json.dumps(data)

    try:
        conn = httplib.HTTPSConnection(host, port)
        conn.request('POST', url, body, headers)
        response = conn.getresponse()
        conn.close()
    except (httplib.HTTPException, httplib.socket.error) as err:
        logger.error('could not call API because %s', err)
        raise SystemExit
    else:
        logger.log(logging.INFO
                   if response.status == httplib.OK
                   else logging.WARNING,
                   'received %s status from API', response.reason)

def next_notify(now):
    'Determine next time to notify of alerts'
    #XXX: this fixes call times to :01 and :06, plus 30sec buffer
    last_call = (datetime.datetime.utcfromtimestamp
                 ((int(now) - 60) / (5 * 60) * (5 * 60))
                 + MINUTE + 30 * SECOND)
    
    #XXX: calls happen every 5min
    next_call = last_call + 5 * MINUTE
    
    now = datetime.datetime.utcfromtimestamp(now)
    delay = (next_call - now).total_seconds()
    logger.info('next alerts at %s (in %.0f seconds)',
                next_call.strftime('%Y-%m-%dT%H:%M:%S'), delay)
    return delay
