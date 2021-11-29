#!/usr/bin/env python3

import requests
from os import environ
from time import sleep
import logging
import xml.etree.ElementTree as ET

# Static Vars
API_KEY = environ.get('API_KEY')
DOMAIN = environ.get('DOMAIN')
SUBDOMAINS = environ.get('SUBDOMAINS')
NAMECHEAP_URL = 'https://dynamicdns.park-your-domain.com/update?host='
IP_URL = 'http://api.myip.com'


logging.basicConfig(
    format='%(asctime)s - [ %(levelname)s ]: %(message)s',
    level=logging.INFO)


def start_sleep():
	if environ.get('INTERVAL') != None:
		try:
			sleep_time = int(environ.get('INTERVAL'))
			sleep(sleep_time)
		except ValueError:
			sleep(600)
	if environ.get('INTERVAL') == None:
		sleep(600)	

def get_global_ip():
    count = 0
    while count < 5:
        try:
            count += 1
            response = requests.get(IP_URL)
            if response.status_code == 200:
                return response.json()['ip']
            else:
                sleep(1)
        except:
            sleep(1)
            pass

    if count >= 5:
        return None

def update_namecheap(subdomain,domain,api_key,ip):
    try:
        r = requests.get(f"{NAMECHEAP_URL}{subdomain}&domain={domain}&password={api_key}&ip={ip}")
        if r.status_code == 200:
            content = r.content.decode('UTF-8')
            error_count = ET.fromstring(content).find("ErrCount").text
            if int(error_count) > 0:
                errors = ET.fromstring(content).find('errors')
                logging.error(f"{subdomain}.{DOMAIN} {errors.find('Err1').text.replace(';','')}")
            elif int(error_count) == 0:
                logging.info(f'{subdomain}.{DOMAIN} updated to {ip}')
    except Exception as e:
        logging.error(e)


if __name__ == '__main__':
    while True:
        ip = get_global_ip()
        if ip == None:
            logging.error(f'Could not contact {IP_URL.strip("http://")}')
        elif ip != None:
            subdomains = SUBDOMAINS.split(',')
            for subdomain in subdomains:
                update_namecheap(subdomain.strip(),DOMAIN,API_KEY,ip)

        start_sleep()
    