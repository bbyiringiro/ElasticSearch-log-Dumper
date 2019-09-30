#!/usr/bin/python

import re

from operator import xor

from config import DEFAULT_RANGE
from getters import get_date_args, get_date_format, get_timezone
from logger import logger


# Handles date arguments' logic. See https://bit.ly/2Ovs2Cl for more info.
def date_handler(date_arg):
    fmt = get_date_format()
    tz = get_timezone()
    logger.debug('Date format used: \'{}\''.format(fmt))
    date_from, date_to, date_range = get_date_args(date_arg)

    if ((date_to is not None) & (date_range is not None)):
        # Search from (date_to - date_range) to date_to
        date_from = '{}||-{}'.format(date_to, date_range)
        date_to = '{}||'.format(date_to)
    elif ((date_from is not None)) & ((date_to is not None)):
        # Search from date_from to date_to
        date_from = '{}||'.format(date_from)
        date_to = '{}||'.format(date_to)
    elif ((date_from is not None) & (date_range is not None)):
        # Search from date_from to (date_from + date_range)
        date_to = '{}||+{}'.format(date_from, date_range)
        date_from = '{}||'.format(date_from)
    elif date_from is not None:
        # Search from beginning of date_from (00:00:00)
        # to end of date_from (23:59:59.999999)
        date_from = '{}||'.format(date_from)
        date_to = date_from
    elif date_range is not None:
        # Search from (now - date_range) to now
        date_to = 'now/s'
        date_from = 'now-{}/s'.format(date_range)
    else:
        # Search from (now - DEFAULT_RANGE) to now
        date_to = 'now/s'
        date_from = 'now-{}/s'.format(DEFAULT_RANGE)

    # Check if date_to / date_from does not contain "now" or ":"
    # (time string). If it does not, then we round it by a day.
    if not any(x in date_to for x in [':', 'now']):
        date_to += '/d'

    if not any(x in date_from for x in [':', 'now']):
        date_from += '/d'

    logger.info('Searching e-mails from \'{}\' to \'{}\'.'
                .format(date_from, date_to))

    return date_from, date_to, fmt, tz


# Check if an input is a date math operator
def is_date_math(date_str):
    if re.findall(r'\d+(\.\d+)?[yMwdhHms]', date_str):
        return True
    return False


# Handles direction logic for get_email
def direction_handler(sender, recipient):
    if xor(bool(sender), bool(recipient)) is False:
        # -a flag is raised, or BOTH -f and -t are raised. No direction
        return None
    elif recipient is not None:
        # -t is raised. We want to know who the sender is
        return 'from'
    else:
        # -f is raised. We want to know who the recipient is
        return 'to'


# Handles e-mail arguments' logic. Returns the relevant query string
# Converts "*" into "\\*" for escaping purposes (see https://bit.ly/2vnwjim)
def email_handler(email_all, sender, recipient, subject):
    if subject is not None:
        subject = subject.replace("*", "\\*");
        words = subject.split(" ");
        sub_query="";
        for i,word in enumerate (words):
            sub_query += "\"" + word +"\""
            if (i<len(words)-1):
                sub_query +=" OR "
        return '\"subject=\" AND {}' \
                .format(sub_query)
    elif ((sender is None) & (recipient is None)):
        # -a flag is raised, so we query for just the e-mail
        return '\"{}\"'.format(email_all.replace("*", "\\*"))
    elif recipient is not None:
        # even if both -f and -t are raised, we filter by recipient (first)
        return '\"to\" AND \"{}\" AND \"xdelay\"' \
                .format(recipient.replace("*", "\\*"))
    else:
        # only -f flag is raised, so we filter by sender
        return '\"from\" AND \"{}\" AND \"msgid\"' \
                .format(sender.replace("*", "\\*"))
