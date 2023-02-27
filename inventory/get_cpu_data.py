#!/usr/bin/env python
# coding: utf-8

from django.conf import settings
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep


def get_intel_html(url):
    """Connect to Intel's ark website and retrieve HTML."""
    USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36")
    headers = {
        'User-Agent': USER_AGENT,
    }
    r = requests.get(url, headers=headers)
    return r.text


def get_amd_html(url):
    #driver = webdriver.PhantomJS('/usr/local/lib/node_modules/phantomjs2/lib/phantom/bin/phantomjs')
    #driver = webdriver.PhantomJS('/app/node_modules/.bin/phantomjs') # heroku, must be in $PATH
    #driver = webdriver.PhantomJS('/app/vendor/phantomjs/bin/phantomjs') # heroku
    #driver = webdriver.PhantomJS('/usr/local/lib/node_modules/phantomjs2/lib/phantom/bin/phantomjs') # local path

    phantomjs_path = settings.PHANTOMJS
    #phantomjs_path = '/usr/local/lib/node_modules/phantomjs2/lib/phantom/bin/phantomjs'
    service_args = ['--load-images=no']
    driver = webdriver.PhantomJS(executable_path=phantomjs_path, service_args=service_args)

    driver.get(url)
    sleep(2)
    html = driver.page_source
    driver.quit()
    return html


#
# INTEL
#
def generate_intel_data(html_input):
    """Generate a dictionary based on the HTML provided."""
    soup = BeautifulSoup(html_input, 'html5lib')
    data = dict()

    # Выбираем из всего списка свойств только нужные
    id_list = ['ProcessorNumber', 'StatusCodeText', 'BornOnDate', 'Lithography', 'Price1KUnits', 'CoreCount',
               'ThreadCount', 'ClockSpeed', 'MaxTDP', 'GraphicsModel', 'SocketsSupported', 'InstructionSet'] #also need Codename!

    for table in soup.select('table.specs'):
        rows = table.find_all("tr")
        for row in rows[1:]:
            try:
                need_row = row['id'] in id_list
            except:
                need_row = False
            if need_row:
                cells = [cell.get_text("\n", strip=True)
                         for cell in row.find_all('td')]

                if cells[0] == 'T\nCASE':
                    cells[0] = 'T(CASE)'
                if "\n" in cells[0]:
                    cells[0] = cells[0][:cells[0].index("\n")]

                data[cells[0]] = cells[1]
    return data

#
# AMD
#
def generate_amd_data(html_input):
    """Generate a dictionary based on the HTML provided."""
    #soup = BeautifulSoup(html_input, 'html.parser')
    soup = BeautifulSoup(html_input, 'html5lib')

    # Выбираем из всего списка свойств только нужные
    need_list = ['Family', 'Model number', 'Frequency', 'Socket', 'Microarchitecture', 'Processor core',
                 'Manufacturing process', 'Data width', 'The number of CPU cores', 'The number of threads',
                 'Integrated graphics', 'Thermal Design Power']

    data = dict()

    table = soup.find('table', attrs={'class':'spec_table'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    for row in rows[1:-2]:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        cols = [ele.replace(u' \xa0?', u'') for ele in cols]

        if len(cols) == 2:                                         # we need only two-column information
            if cols[0] in need_list:
                data[cols[0]] = ', '.join(cols[1].splitlines())    # replace multiline with comma
    print(type(data))
    return data


def cpu_data(url):
    """
    Must return a dict with CPU data fetched from Intel Ark or Cpu-world
    :param url:
    :return:
    """
    if 'ark.intel.com' in url:
        html = get_intel_html(url)
        data = generate_intel_data(html)
    elif 'cpu-world.com' in url:
        html = get_amd_html(url)
        data = generate_amd_data(html)
    else:
        data = None

    print(type(data))
    return data


if __name__ == '__main__':
    #
    # DEBUG
    #
    intel_url = 'http://ark.intel.com/ru/products/40478/Intel-Pentium-Processor-E5400-2M-Cache-2_70-GHz-800-MHz-FSB'
    amd_url = 'http://www.cpu-world.com/CPUs/K8/AMD-Athlon%2064%203000%2B%20-%20ADA3000DIK4BI%20(ADA3000BIBOX).html'

    data = cpu_data(amd_url)

    for key, value in data.items():
        print('{}: {}'.format(key, value))