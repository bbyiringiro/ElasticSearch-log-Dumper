#!/usr/bin/python

import argparse
import os
import sys
from functools import reduce

from datetime import date, datetime, time, timedelta
from elasticsearch import Elasticsearch, ElasticsearchException
from elasticsearch_dsl import Q, Search

from config import ES_SERVER, help
from formatters import fmt_title, fmt_response
from getters import get_email, get_qids
from handlers import date_handler, direction_handler, email_handler
from logger import logger


# Instantiate an Elasticsearch client with the required settings
def init_elastic(user, password):
    auth_values = (user, password)
    es = Elasticsearch([ES_SERVER['base_url']],
                       use_ssl=True,
                       verify_certs=True,
                       ca_certs=ES_SERVER['crt_path'],
                       http_auth=auth_values)
    return es


# Query Elasticsearch with the relevant parameters
def search_mail(client, query_str, date_arg, asc=True, qid=False):
    logger.info('Searching for {}'.format(query_str))

    # Determine the sort order
    order = '' if asc else '-'

    # Instantiate a Search object
    s = Search(using=client, index='mail_relay_and_directory*') \
        .source(['system.syslog.message',
                 'system.syslog.timestamp',
                 'system.syslog.hostname']) \
        .query('query_string', query=query_str,
               default_field='system.syslog.message') \
        .sort(order + 'system.syslog.timestamp') \
        .extra(size=10000)

    # Filter by the specified date range
    if qid is False:
        date_from, date_to, fmt, tz = date_handler(date_arg)
        date_filter = {'gte': date_from,
                       'lte': date_to,
                       'format': fmt,
                       'time_zone': tz}
        s = s.filter('range', system__syslog__timestamp=date_filter)

    response = s.execute()
    logger.debug('Got response: {}'.format(response))

    return response


# Driver programme
def main(args):
    # Read the password from the config file
    try:
        pwd_file = open(ES_SERVER['pwd_path'])
        password = pwd_file.read().strip()
        pwd_file.close()
    except IOError, e:
        logger.error(e)
        sys.exit(1)

    # Create an Elasticsearch instance
    es = init_elastic(ES_SERVER['username'], password)

    # Decide what string to search, based on user arguments
    query_str = email_handler(args.email_all,
                              args.sender,
                              args.recipient, args.subject)

    response = search_mail(es, query_str, args.date, asc=False)

    # Get all sorted unique query IDs
    qids = get_qids(response)

    # Additional processing if both -f and -t are raised
    if ((args.sender is not None) & (args.recipient is not None)):
        logger.info('Both -f and -t flags are raised')

        # Search for all e-mails sent by -f
        query_str = email_handler(args.email_all,
                                  args.sender, None)
        response = search_mail(es, query_str, args.date, asc=False)

        # Get all sorted unique query IDs for e-mails sent by -f
        qids_from = get_qids(response)

        # Return only common e-mail from `qids` and `qids_from`
        qids_filtered = [qid for qid in qids_from if qid in qids]
        logger.info('Found common qid(s): {}'.format(qids_filtered))
        qids = qids_filtered

    # Print messages to std.out
    for idx, qid_dict in enumerate(qids):
        # Search the contents of each message
        response = list(search_mail(es, qid_dict['qid'], args.date, qid=True))

        # Decide whether to print the sender / recipient of each e-mail
        direction = direction_handler(args.sender, args.recipient)
        emails = []

        # Grab the e-mails from message body and store them in emails
        if direction is not None:
            for hit in response:
                emails.extend(get_email(hit.system.syslog.message, direction))

        if idx == 0:
            print('')

        # Print the title of each message
        title = fmt_title(idx+1, qid_dict['qid'],
                          qid_dict['host'], emails,
                          direction=direction)
        print('{}'.format(title))
        print('-' * len(title))

        # Print the contents of each message
        for hit in response:
            print('{}'.format(fmt_response(hit)))

        print('')

    if len(qids) == 0:
        logger.warning('No e-mails found; try relaxing your filters.')

if __name__ == '__main__':
    # Define command line arguments' structure
    parser = argparse.ArgumentParser(description=help['desc'])
    parser.add_argument('-a', dest='email_all', nargs='?', const={None},
                        metavar='<EMAIL>', help=help['a'])
    parser.add_argument('-f', dest='sender', nargs='?', const={None},
                        metavar='<SENDER>', help=help['f'])
    parser.add_argument('-t', dest='recipient', nargs='?', const={None},
                        metavar='<RECIPIENT>', help=help['t'])
    parser.add_argument('-d', dest='date', nargs='+', default=None,
                        metavar='<DATE_ARG>', help=help['d'])
    parser.add_argument('-s', dest='subject', nargs='?', const={None},
                        metavar='<SUBJECT>', help=help['s'])
    parser.add_argument('--debug', dest='enable_log',
                        action='store_true', help=help['debug'])

    # Parse arguments
    args = parser.parse_args()

    if not args.enable_log:
        logger.disabled = True

    if not args.email_all and not args.sender and not args.recipient and not args.subject:
        logger.error('At least one of -a, -t,-f, or -s must be specified.')
        sys.exit(1)

    

    main(args)
