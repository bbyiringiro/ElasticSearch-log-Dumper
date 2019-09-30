#!/usr/bin/python

from datetime import datetime
from getters import get_body


# Formats the title of each response
def fmt_title(msg_no, qid, host, emails=None, direction=None):
    title = 'Message #{:03d} [{}] [{}]'.format(msg_no, qid, host)
    if len(emails) == 0:
        return title
    else:
        title_emails = '{} [{}: {}]'.format(title,
                                            direction.upper(),
                                            ', '.join(emails))
        return title_emails


# Formats the content of each response
def fmt_response(hit):
    msg = hit.system.syslog
    date = datetime.strptime(msg.timestamp[:-6], '%Y-%m-%dT%H:%M:%S.%f') \
                   .strftime('%a, %d %b %Y %H:%M:%S')
    return '{} - {}'.format(date, get_body(msg.message))
