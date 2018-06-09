#!/usr/bin/env python2.7

'''Space Weather Tests'''

#built-in libraries
import unittest
import time
import datetime

#external libraries
#...

#internal libraries
import space_weather

#constants
MINUTE = datetime.timedelta(minutes=1)
HOUR = datetime.timedelta(hours=1)

class SpaceWeatherTestCase(unittest.TestCase):

    def setUp(self):
        space_weather.get_logger()

    def test_level_none(self):
        '''[BAD] Info ... if level < 1 for at least 90 minutes'''
        now = time.time()
        dt = datetime.datetime.utcfromtimestamp(now)
        data = [(dt - 90 * MINUTE, 1.1),
                (dt - 85 * MINUTE, 0.9)]
        level, value, _ = space_weather.process_data(now, data)
        self.assertEqual(level, space_weather.NOTSET)

    def test_level_info(self):
        '''[GOOD] Info ... if level < 1 for at least 90 minutes'''
        now = time.time()
        dt = datetime.datetime.utcfromtimestamp(now)
        data = [(dt - 2 * HOUR, 0.9)]
        level, value, _ = space_weather.process_data(now, data)
        self.assertEqual(level, space_weather.INFO)

    def test_level_warning(self):
        '''Warning ... if level > 1'''
        now = time.time()
        dt = datetime.datetime.utcfromtimestamp(now)
        data = [(dt - MINUTE, 1.1)]
        level, value, _ = space_weather.process_data(now, data)
        self.assertEqual(level, space_weather.WARNING)

    def test_level_alert(self):
        '''Alert ... if level > 10'''
        now = time.time()
        dt = datetime.datetime.utcfromtimestamp(now)
        data = [(dt - MINUTE, 10.1)]
        level, value, _ = space_weather.process_data(now, data)
        self.assertEqual(level, space_weather.ALERT)

    def test_level_critical(self):
        '''Alert ... if level > 100'''
        now = time.time()
        dt = datetime.datetime.utcfromtimestamp(now)
        data = [(dt - MINUTE, 100.1)]
        level, value, _ = space_weather.process_data(now, data)
        self.assertEqual(level, space_weather.CRITICAL)

    def test_email(self):
        '''Email address should be configurable'''
        now = time.time()
        level, value = space_weather.ALERT, 11
        data = [(now, value)]
        imgfile = 'test.png'
        fromaddr = 'space.weather@planet.com'
        toaddr = 'test@example.com'

        space_weather.generate_plot(now, data, imgfile)
        msg = space_weather.generate_email(level, value, imgfile,
                                           fromaddr, toaddr)
        self.assertEqual(msg['From'], fromaddr)
        self.assertEqual(msg['To'], toaddr)

    def test_schema(self):
        '''The alert API schema'''
        level, value = space_weather.WARNING, 9.9
        link = 'http://www.example.com/test.txt'
        headers, body = (space_weather.generate_alert
                         (level, value, link))
        self.assertEqual(headers['Content-Type'],
                         'application/json')
        self.assertIn('alert_text', body)
        self.assertIn('level', body)
        self.assertIn('link', body)
        self.assertIn('Space weather', body['alert_text'])
        self.assertIn(space_weather.LEVEL_MAP[level].lower(),
                      body['alert_text'])
        self.assertIn('> 10 MeV proton flux', body['alert_text'])
        self.assertIn('currently at', body['alert_text'])
        self.assertEqual(body['level'], space_weather.LEVEL_MAP[level])
        self.assertEqual(body['link'], link)

if __name__ == '__main__':
    unittest.main()
