#!/usr/bin/env python3

import requests
from os import environ
from time import sleep
import logging
import json
from datetime import datetime, timezone
import gzip
import shutil
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import xml.etree.ElementTree as ET

# Static Vars
API_KEY = environ.get('API_KEY')
DOMAIN = environ.get('DOMAIN')
SUBDOMAINS = environ.get('SUBDOMAINS')
NAMECHEAP_URL = 'https://dynamicdns.park-your-domain.com/update?host='
IP_URL ='http://checkip.amazonaws.com'
REQUEST_TIMEOUT = (5, 15)  # Connection and read timeouts, in seconds.


def compress_log(source, destination):
    with open(source, 'rb') as original, gzip.open(destination, 'wb') as archive:
        shutil.copyfileobj(original, archive)
    Path(source).unlink()


def archive_name(default_name):
    return default_name + '.gz'


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            'timestamp': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
        }
        for field in ('action', 'status', 'domain', 'subdomain', 'ip',
                      'http_status', 'error', 'error_type', 'service_url'):
            if hasattr(record, field):
                entry[field] = getattr(record, field)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging():
    retention_days = int(environ.get('LOG_RETENTION_DAYS', '14'))
    if retention_days < 1:
        raise ValueError('LOG_RETENTION_DAYS must be a positive integer')
    log_dir = Path(environ.get('LOG_DIR', '/logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        log_dir / 'current.log', when='midnight', interval=1,
        backupCount=retention_days, encoding='utf-8', utc=True)
    file_handler.namer = archive_name
    file_handler.rotator = compress_log
    handlers = [logging.StreamHandler(), file_handler]
    for handler in handlers:
        handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=handlers)


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
            response = requests.get(IP_URL, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.content.decode('UTF-8').strip()
            else:
                sleep(1)
        except:
            sleep(1)
            pass

    if count >= 5:
        return None

def update_namecheap(subdomain,domain,api_key,ip):
    context = {'action': 'update_ip', 'domain': domain,
               'subdomain': subdomain, 'ip': ip.strip()}

    def safe_error(error):
        text = str(error)
        return text.replace(api_key, '[REDACTED]') if api_key else text

    try:
        r = requests.get(
            f"{NAMECHEAP_URL}{subdomain}&domain={domain}&password={api_key}&ip={ip}",
            timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            content = r.content.decode('UTF-8')
            error_count = ET.fromstring(content).find("ErrCount").text
            if int(error_count) > 0:
                errors = ET.fromstring(content).find('errors')
                logging.error('DNS update rejected', extra={
                    **context, 'status': 'failure',
                    'error': safe_error(errors.find('Err1').text.replace(';', ''))})
            elif int(error_count) == 0:
                logging.info('DNS IP address updated', extra={
                    **context, 'status': 'success'})
        else:
            logging.error('DNS update request failed', extra={
                **context, 'status': 'failure', 'http_status': r.status_code})
    except Exception as e:
        logging.error('DNS update failed', extra={
            **context, 'status': 'failure', 'error': safe_error(e),
            'error_type': type(e).__name__})


if __name__ == '__main__':
    configure_logging()
    logging.info('DDNS service started', extra={
        'action': 'startup', 'status': 'success', 'domain': DOMAIN})
    while True:
        ip = get_global_ip()
        if ip == None:
            logging.error('Could not determine public IP address', extra={
                'action': 'get_public_ip', 'status': 'failure',
                'service_url': IP_URL})
        elif ip != None:
            subdomains = SUBDOMAINS.split(',')
            for subdomain in subdomains:
                update_namecheap(subdomain.strip(),DOMAIN,API_KEY,ip)

        start_sleep()
