#!/usr/bin/env python2.7

'''Top-level script'''

#built-in libraries
import argparse
import ConfigParser
import time
import sched

#external libraries
#...

#internal libraries
try:
    import space_weather
except ImportError:
    import __init__ as space_weather

#constants
TRIVIAL = 10000
LOW = 1000
NORMAL = 100
HIGH = 10
CRITICAL = 1
    
def main():
    '''Main function'''
    global last_level
    now = time.time()

    url = config.get('data', 'url')
    data, filename = space_weather.retrieve_data(url)
    filename = space_weather.format_filename(now, filename, 'png')
    level, value = space_weather.process_data(now, data)

    if level > last_level:
        if level in [space_weather.INFO,
                     space_weather.ALERT,
                     space_weather.CRITICAL]:
            headers, body = (space_weather.generate_alert
                             (level, value, url))
            space_weather.call_api(config.get('alert', 'host'),
                                   config.getint('alert', 'port'),
                                   config.get('alert', 'url'),
                                   headers, body)
        if level >= space_weather.INFO:
            space_weather.generate_plot(now, data, filename)
            fromaddr = config.get('email', 'fromaddr')
            toaddrs = config.get('email', 'toaddrs').split(',')
            msg = (space_weather.generate_email
                   (level, value, filename,
                    fromaddr, *toaddrs))
            space_weather.send_email(config.get('email', 'host'),
                                     config.getint('email', 'port'),
                                     config.getboolean('email', 'tls'),
                                     config.get('email', 'username'),
                                     config.get('email', 'password'),
                                     msg, fromaddr, *toaddrs)
    last_level = level

    delay = space_weather.next_notify(now)
    schedule.enter(delay, NORMAL, main, ())

if __name__ == '__main__':
    logger = space_weather.get_logger()
    
    parser = argparse.ArgumentParser(description='Space weather alerts')
    parser.add_argument('-c', '--config', type=str, default='./planet.conf',
                        help='configuration file')
    args = vars(parser.parse_args())
    
    config = ConfigParser.SafeConfigParser()
    config.read(args['config'])
    
    last_level = space_weather.NOTSET#email/alert only sent at first breach
    schedule = sched.scheduler(time.time, time.sleep)
    schedule.enter(0, NORMAL, main, ())

    try:
        schedule.run()
    except KeyboardInterrupt:
        raise SystemExit
