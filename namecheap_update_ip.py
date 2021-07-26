from os import environ
from requests import get
from json import loads
from ipaddress import ip_address
from time import strftime, sleep
from xml.etree import ElementTree 
import logging


# Static Vars
API_KEY = environ.get('API_KEY')
DOMAIN = environ.get('DOMAIN')
SUBDOMAINS = environ.get('SUBDOMAINS')
NAMECHEAP_URL = 'https://dynamicdns.park-your-domain.com/update?host='
IP_URL = 'http://ipconfig.io/json'


# Get global ip address from api
def get_ip(logger):
	try:
		r = get(IP_URL)
		if r.status_code == 200:
			r_dic = loads(r.content.decode('UTF-8'))
			return r_dic['ip']
		if r.status_code != 200:
			logger.info(f'Connection Error to {IP_URL} {r.status_code}')
	except Exception as e:
		logger.info(f'Unable to connect to {IP_URL}')
		
		
# update ip to NameCheap
def update_ip(subdomain, ip, logger):
	try:
		if subdomain != '':
			r = get(f"{NAMECHEAP_URL}{subdomain}&domain={DOMAIN}&password={API_KEY}&ip={ip}")
			if r.status_code == 200:
				errCount = ElementTree.fromstring(r.content).find("ErrCount").text
				if int(errCount) > 0:
					errors = ElementTree.fromstring(r.content).find('errors')
					logger.warning(f"{subdomain}.{DOMAIN} {errors.find('Err1').text.replace(';','')}")
				else:
					logger.info(f'{subdomain}.{DOMAIN} updated to {ip}')
	except Exception as e:
		get_module_logger(__name__).info(e)

										
def start_sleep():
	if environ.get('INTERVAL') != None:
		try:
			sleep_time = int(environ.get('INTERVAL'))
			sleep(sleep_time)
		except ValueError:
			sleep(600)
	if environ.get('INTERVAL') == None:
		sleep(600)	


def get_module_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    """
    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

if __name__ == '__main__':
	logg = get_module_logger(__name__)
    
	while True:
		ip = get_ip(logg)
		try:
			ip_address(ip)
			subdomains = SUBDOMAINS.split(',')
			for subdomain in subdomains:
				r = update_ip(subdomain, ip, logg)
				#print(r)
		except ValueError:
			pass
		except AttributeError:
			logg.info('Invalid Subdomains')
		start_sleep()
