''''''

#built-in libraries
import time
import urlparse
import json
import sched

#external libraries
#...

#internal libraries
import __init__ as space_weather

#exports
__all__ = ()

#constants
TRIVIAL = 10000
LOW = 1000
NORMAL = 100
HIGH = 10
CRITICAL = 1

URL_PROTON_FLUX = ('http',
                   'services.swpc.noaa.gov',
                   '/text/goes-particle-flux-primary.txt',
                   '', '', '')
    
def blah(s):
    now = time.time()
    url = urlparse.urlunparse(URL_PROTON_FLUX)
    data = space_weather.parse_file(url)
    level, value = space_weather.process_data(now, data)

    if level in [space_weather.INFO,
                 space_weather.ALERT,
                 space_weather.CRITICAL]:
        head, body = (space_weather.generate_alert
                      (level, value, url))
        #space_weather.call_api('httpbin.org', 443, '/post', head, body)
    if level >= space_weather.INFO:
        space_weather.generate_plot(now, data, 'plot.png')
        msg = (space_weather.generate_email
               (level, value, 'plot.png',
                'sean@test.com',
                'sean.henely@gmail.com'))
        #space_weather.send_email(msg)

    delay = space_weather.next_notify(now)
    print delay
    s.enter(delay, NORMAL, blah, (s,))

def main():
    s = sched.scheduler(time.time, time.sleep)
    s.enter(0, NORMAL, blah, (s,))
    s.run()

if __name__ == '__main__':
    main()
