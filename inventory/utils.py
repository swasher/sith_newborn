import re
import math
import calendar
import datetime
import currencylayer
from django.conf import settings


def human_to_bytes(capacity):
    """
    Convert human-like size of information (disk or memory) into bytes
    :param capacity: string, such as `256 MBytes`, `2048 MBytes`
    :return: int, the number of bytes
    """

    base = 1024

    MB = math.pow(base, 2)
    GB = math.pow(base, 3)
    TB = math.pow(base, 4)

    # Any value comparies with lower
    megabytes = ['mbytes', 'mb', 'мб']
    gigabytes = ['gbytes', 'gb', 'гб']
    terabytes = ['tbytes', 'tb', 'тб']

    regex = r"(\d+)\s*([a-zA-ZА-Яа-я]+)"
    matches = re.findall(regex, capacity) # result as [('250', 'Mbytes')]

    if matches:
        if len(matches[0]) == 2:
            amount = int(matches[0][0])
            unit = matches[0][1].lower()
            if unit in megabytes:
                bytes = amount * MB
            elif unit in gigabytes:
                bytes = amount * GB
            elif unit in terabytes:
                bytes = amount * TB
            else:
                bytes = 0
        else:
            bytes = 0
    else:
        bytes = 0

    return bytes


def bytes_to_human(size, base=1000):
    """
    Convert  size of volume in human readable. Assuming, 1 kilo = 1000 bytes, as HDD size.
    :param size: int, bytes in storage volume
    :return: string
    """

    if (size == 0):
       return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    log = math.log(size, 1000) # в какую степень нужно возвести 1000, чтобы получить size
    i = int(math.floor(log))   # округляем вниз до целого. Это целое - соответствует номеру "основы" из size_name
    p = math.pow(base, i)      # возводим 1000 в степень i. Получаем число, которое содержит кол-во байт, как в
                               # выбранной "основе". Например, если "основа"=KB, то p будет равно 1000^2 = 1000000
    s = round(size / p, 1)     # Считаем, сколько целых p умещается в наш size
    h = '{0:g}'.format(s)      # Отбрасываем незначащие нули
    return '{} {}'.format(h,size_name[i])


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
