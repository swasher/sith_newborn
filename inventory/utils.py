import re
import math
import calendar
import datetime
import currencylayer
from django.conf import settings

def capacity_to_human(capacity):

    regex = r"(\d+)\s*([a-zA-Z]+)"
    matches = re.findall(regex, capacity)[0]

    GB = 1024*1024*1024/1000/1000/1000

    if len(matches)==2:
        if matches[1] in ['GB', 'Gigabytes']:
            human_value = round(int(matches[0]) * GB)
            human_unit = 'GB'
            human = '{}{}'.format(human_value, human_unit)
        else:
            human = 'Unpredictable unit'
    else:
        human =  ''

    return human

def bytes_to_human(bytes):
   if (bytes == 0):
       return '0B'
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(bytes, 1024)))
   p = math.pow(1000, i)
   s = round(bytes / p)
   return '{} {}'.format(s,size_name[i])


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12 )
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)


def uah_to_usd(uah, date):
    CURRENCYLAYER_API_KEY = settings.CURRENCYLAYER_API_KEY
    exchange_rate = currencylayer.Client(access_key=CURRENCYLAYER_API_KEY)
    cur = exchange_rate.historical(date=date, base_currency='USD')

    if cur['success']:
        usd = round(uah / cur['quotes']['USDUAH'], 2)
    else:
        usd = None

    return usd
