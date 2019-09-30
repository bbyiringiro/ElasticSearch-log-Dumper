#!/usr/bin/python

import re
import time

from config import DAYFIRST, YEARFIRST
from logger import logger


# Get the message body of a document
def get_body(message):
    logger.debug('Retrieving message body from {}'.format(message))
    try:
        # Filter qid out and stitch the remaining parts back together
        body = ':'.join(message.split(':')[1:])
        logger.debug('Found message body: {}'.format(body))
    except KeyError as e:
        logger.error('No message body found: {}'.format(e))

    return body


# Get the date arguments from the string passed in -d
def get_date_args(date_arg):
    logger.debug('Parsing date arguments from {}'.format(date_arg))

    date_from = None
    date_to = None
    date_range = None

    try:
        date_arg = ' '.join(date_arg)
        date_args = date_arg.split(', ')
        # Assign date_arg to one of date_from, date_to, or date_range
        for idx, date_arg in enumerate(date_args):
            logger.debug('Parsing argument #{}: \'{}\''.format(idx+1, date_arg))
            if is_date_math(date_arg):   
                date_range = date_arg
                logger.debug('date_range: \'{}\''.format(date_arg))
            elif not idx:
                date_from = date_arg
                logger.debug('date_from: \'{}\''.format(date_arg))
            else:
                date_to = date_arg
                logger.debug('date_to: \'{}\''.format(date_arg))
    except (TypeError, AttributeError):
        # date_arg is None, so -d flag is not active
        logger.info('-d flag is not active.')

    return date_from, date_to, date_range


# Decide which date format to use, based on user's configuration
def get_date_format():
    if DAYFIRST & (not YEARFIRST):
        date = 'dd/MM/yyyy'
    elif DAYFIRST & YEARFIRST:
        date = 'yyyy/dd/MM'
    elif (not DAYFIRST) & YEARFIRST:
        date = 'yyyy/MM/dd'
    else:
        date = 'MM/dd/yyyy'

    return '{} HH:mm:ss||{} HH:mm:ss||{}||{}' \
           .format(date[:-2], date, date[:-2], date)


# Get the current UTC offset
def get_timezone():
    tz = time.strftime('%z')
    return tz[:3] + ':' + tz[3:]


# Get the list of e-mail from the message body of a document
def get_email(message, direction):
    logger.debug('Retrieving e-mails from {}'.format(message))
    if direction == 'from':
        emails = re.findall('(?:from=)<(.*?)>,', message)
    elif direction == 'to':
        emails = re.findall('(?:to=|,)<(.*?)>,', message)
    else:
        emails = []
    logger.debug('Found e-mails: {}'.format(emails))

    return emails


# Get the message body of a document
def get_qid(message):
    logger.debug('Retrieving query ID from {}'.format(message))
    try:
        qid = message.split(':')[0]
        logger.debug('Found query ID: {}'.format(qid))
    except KeyError as e:
        logger.error('No message body found: {}'.format(e))

    return qid


# Get sorted unique query IDs from the search response
def get_qids(response):
    qids = []
    dup_check = set()
    for hit in response:
        syslog = hit.system.syslog
        qid = get_qid(syslog.message)
        if qid not in dup_check:
            qid_dict = {'qid': qid,
                        # Ignore 'is.ed.ac.uk'
                        'host': syslog.hostname.split('.')[0]
                        }
            dup_check.add(qid)
            qids.append(qid_dict)

    logger.info('Got qid(s): {}'.format(qids))
    return qids


# Check if an input is a date math operator
def is_date_math(date_str):
    if re.findall(r'\d+(\.\d+)?[yMwdhHms]', date_str):
        return True
    return False
