''''''

#built-in libraries
import urlparse
import json
import logging
import logging.config
import logging.handlers

#external libraries
#...

#internal libraries
import __init__ as planet

#exports
__all__ = ()

#constants
URL_PROTON_FLUX = ('http',
                   'services.swpc.noaa.gov',
                   '/text/goes-particle-flux-primary.txt',
                   '', '', '')
LOG_FORMAT = ('Space weather %(levelname)s: '
                    '> 10 MeV proton flux '
                    'currently at %(value)s')
JSON_SCHEMA = {'alert_text': '%(msg)s',
               'level': '%(levelname)s',
               'link': '%(link)s'}
    
def main():
    logging.addLevelName(planet.ALERT, 'ALERT')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    #smtp_handle = planet.EmailHandler
    #smtp_handle.setLevel(planet.ALERT)
    alert_format = logging.Formatter(fmt=json.dumps(JSON_SCHEMA))
    #smtp_handle.setFormatter(alert_format)
    #logger.addHandler(smtp_handle)

    #http_handle = logging.handlers.HTTPHandler
    alert_filter = planet.MaskedFilter('API Calls',
                                       logging.INFO,
                                       planet.ALERT
                                       logging.CRITICAl)
    #http_handle.addFilter(alert_filter)
    #logger.addHandler(http_handle)

    filename = urlparse.urlunparse(URL_PROTON_FLUX)
    data = planet.parse_file(filename)
    level, p_gt_10 = planet.process_data(data)

    print level, p_gt_10
    extra = {'value': p_gt_10,
             'link': URL_PROTON_FLUX}
    logger.log(level, LOG_FORMAT, extra=extra)
    

if __name__ == '__main__':
    main()
