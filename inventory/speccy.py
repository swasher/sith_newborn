from lxml import etree
import re
from .utils import capacity_to_human
from .utils import bytes_to_human

def parse_speccy(speccy_xml):

    devices = []

    #tree = etree.parse('DAD.xml')
    #tree = etree.parse('sanya.xml')
    tree = etree.XML(speccy_xml)

    #
    # Summary
    #
    summary = dict()
    summary['user'] = tree.xpath('/speccydata/mainsection[@title="Network"]/section[@title="Computer Name"]/entry[@title="NetBIOS Name"]')[0].get('value')
    summary['os'] = tree.xpath('/speccydata/mainsection[@title="Summary"]/section[@title="Operating System"]/entry')[0].get('title')
    summary['cpu'] = tree.xpath('/speccydata/mainsection[@title="CPU"]/section/entry[@title="Name"]')[0].get('value')
    mem_size = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory"]/entry[@title="Size"]')[0].get('value')
    mem_total_physical = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Physical Memory"]/entry[@title="Total Physical"]')[0].get('value')
    ram = mem_total_physical if 'GB' in mem_total_physical else mem_size
    summary['ram'] = ram
    summary['installation_date'] = tree.xpath('/speccydata/mainsection[@title="Operating System"]/entry[contains(@value, "Installation Date")]')[0].get('value')
    # summary['ram_used_slots'] = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory slots"]/entry[@title="Used memory slots"]')[0].get('value')

    #
    # CPU
    #
    processors_branch = tree.iterfind('.//mainsection[@title="CPU"]/section')
    for leaf in processors_branch:
        feature = dict()
        feature['Процессор'] = leaf.xpath('entry[@title="Name"]')[0].get('value')
        feature['Количество ядер'] = leaf.xpath('entry[@title="Cores"]')[0].get('value')
        feature['Количество потоков'] = leaf.xpath('entry[@title="Threads"]')[0].get('value')
        feature['Архитектура'] = leaf.xpath('entry[@title="Code Name"]')[0].get('value')
        feature['Сокет'] = leaf.xpath('entry[@title="Package"]')[0].get('value')
        feature['Литография'] = leaf.xpath('entry[@title="Technology"]')[0].get('value')
        feature['Ревизия'] = leaf.xpath('entry[@title="Revision"]')[0].get('value')
        feature['Базовая тактовая частота процессора'] = leaf.xpath('entry[@title="Stock Core Speed"]')[0].get('value')
        #feature['socket'] = ''  # TODO Must return socket; must eligible with Motherboard socket; must searchable; look reference `CPU socket`

        device = dict()
        device['type'] = 'cpu'
        device['verbose'] = feature['Процессор']
        device['feature'] = feature
        devices.append(device)

    #
    # Motherboard
    #
    feature = dict()
    feature['Бренд'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Manufacturer"]')[0].get('value')
    feature['Модель'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Model"]')[0].get('value')
    feature['Чипсет, вендор'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Chipset Vendor"]')[0].get('value')
    feature['Чипсет, модель'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Chipset Model"]')[0].get('value')
    feature['Память, тип'] = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory"]/entry[@title="Type"]')[0].get('value')
    feature['Память, кол-во слотов'] = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory slots"]/entry[@title="Total memory slots"]')[0].get('value')
    feature['Биос, вендор'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/section[@title="BIOS"]/entry[@title="Brand"]')[0].get('value')
    feature['Биос, дата'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/section[@title="BIOS"]/entry[@title="Date"]')[0].get('value')

    device = dict()
    device['type'] = 'motherboard'
    device['verbose'] = ' '.join([feature['Бренд'], feature['Модель']])
    device['feature'] = feature
    devices.append(device)

    #
    # Memory
    #
    memory_slots_branch = tree.iterfind('.//section[@title="SPD"]/section')
    for leaf in memory_slots_branch:  # поиск элементов
        feature = dict()
        feature['Слот'] = leaf.get('title')
        feature['Тип модуля'] = leaf.xpath('entry[@title="Type"]')[0].get('value')
        feature['Объем'] = leaf.xpath('entry[@title="Size"]')[0].get('value')
        feature['Вендор'] = leaf.xpath('entry[@title="Manufacturer"]')[0].get('value')
        feature['Частота'] = leaf.xpath('entry[@title="Max Bandwidth"]')[0].get('value')
        feature['Серия (Part Number)'] = leaf.xpath('entry[@title="Part Number"]')[0].get('value')
        try:
            feature['Серийный номер'] = leaf.xpath('entry[@title="Serial Number"]')[0].get('value')
        except IndexError:
            pass
        try:
            feature['Изготовлено (Week-year)'] = leaf.xpath('entry[@title="Week/year"]')[0].get('value')
        except:
            pass

        device = dict()
        device['type'] = 'memory'
        device['verbose'] = ' '.join([feature['Вендор'], feature['Объем']])
        device['feature'] = feature
        devices.append(device)


    #
    # Monitor
    #
    monitor_branch = tree.iterfind('.//mainsection[@title="Graphics"]/section')
    for leaf in monitor_branch:  # поиск элементов

        monitor = leaf.get('title')

        if 'Monitor' in monitor:

            feature = dict()
            model_on_videocard = leaf.xpath('entry[@title="Name"]')[0].get('value')
            model_match = re.match(r'(.*)\son\s', model_on_videocard)
            try:
                feature['Модель'] = model_match.group(1)
            except AttributeError: pass
            feature['Нативное разрешение'] = leaf.xpath('entry[@title="Work Resolution"]')[0].get('value')
            device = dict()
            device['type'] = 'monitor'
            try:
                device['verbose'] = feature['model']
            except KeyError:
                device['verbose'] = leaf.get('title')
            device['feature'] = feature
            devices.append(device)


    #
    # Videocard
    #
    feature = dict()
    # Тут небольшой быдло-код. Эта секция называется в Speccy по имени видеокарты, например, <section title="ATI Radeon HD 4600 Series">
    # И я не знаю, как сделать на нее селект.
    # Пока работает таким образом, что я обращаюсь к полям по имени, и эти поля присутствуют только во сторой секции с видухой, и
    # отсутствуют в секции с монитором.
    # TODO еще больше проблем будет, когда надо будет делтаь массив видео карт для много-видеокартных систем
    #                                                                                ↓↓↓↓↓↓↓
    feature['Чипсет, вендор'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Manufacturer"]')[0].get('value')
    # Далее, нет способа определить, интегрированное видео или дискретное. Предположу, что Intel не делает дискретных
    # видух (пруф https://linustechtips.com/main/topic/380568-has-intel-ever-made-a-dedicated-graphics-card/),
    # а интегрированные бывают только 'Intel' или 'ATI'. Если так, то считаем, что видео интегрированное:
    # ==================== ШО ЗА БРЕД?! ATI МОЖЕТ БЫТЬ И ДИСКРЕТНАЯ

    if feature['Чипсет, вендор'] in ['Intel', 'ATI']:
        pass
    else:
        feature['Модель'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Model"]')[0].get('value')
        feature['Бренд'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Subvendor"]')[0].get('value')

        try:
            feature['Дата выпуска'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Release Date"]')[0].get('value')
        except IndexError: pass

        try:
            feature['Объем памяти'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Memory"]')[0].get('value')
        except:
            feature['Объем памяти'] = ''
        try:
            feature['Объем памяти'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Physical Memory"]')[0].get('value')
        except:
            feature['Объем памяти'] = ''

        try:
            feature['GPU'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="GPU"]')[0].get('value')
        except IndexError: pass

        try:
            feature['Литография'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Technology"]')[0].get('value')
        except IndexError: pass

        device = dict()
        device['type'] = 'videocard'
        device['verbose'] = ' '.join([feature['Чипсет, вендор'], feature['Модель']])
        device['feature'] = feature
        devices.append(device)

    #
    # HDD
    #
    disks_branch = tree.iterfind('.//section[@title="Hard drives"]/section')
    for leaf in disks_branch:
        feature = dict()

        feature['Модель'] = leaf.get('title')
        try:
            feature['Бренд'] = leaf.xpath('entry[@title="Manufacturer"]')[0].get('value')
        except (KeyError, IndexError):
            feature['Бренд'] = ''

        try:
            speed = leaf.xpath('entry[@title="Speed"]')[0].get('value')
        except:
            feature['Тип носителя'] = 'HDD'
        else:
            if 'SSD' in speed:
                feature['Тип носителя'] = 'SSD'
            else:
                feature['Тип носителя'] = 'HDD'
                feature['Скорость'] = speed

        capacity = leaf.xpath('entry[@title="Capacity"]')[0].get('value')
        feature['Емкость'] = capacity

        feature['Серийный номер'] = leaf.xpath('entry[@title="Serial Number"]')[0].get('value')
        feature['Интерфейс'] = leaf.xpath('entry[@title="Interface"]')[0].get('value')
        feature['Тип SATA'] = leaf.xpath('entry[@title="SATA type"]')[0].get('value')
        real_size = leaf.xpath('entry[@title="Real size"]')[0].get('value') #.replace(" ", "")

        # convert real_size to list, then filter only digets, then join and int them
        capacity_in_bytes = int(''.join(filter(lambda x: x.isdigit(), list(real_size))))
        feature['Емкость SI'] = bytes_to_human(capacity_in_bytes)
        # OR you can use feature['Емкость human readable'] = capacity_to_human(capacity)

        device = dict()
        device['type'] = 'storage'
        device['verbose'] = ' '.join([feature['Бренд'], feature['Емкость SI'], feature['Тип носителя']])
        device['feature'] = feature
        devices.append(device)

    #
    # CDROM
    #
    # Непонятно, как отличать виртуальные cdrom от реальных
    cdroms_branch = tree.iterfind('.//mainsection[@title="Optical Drives"]/section')
    for leaf in cdroms_branch:  # поиск элементов
        feature = dict()
        feature['Модель'] =leaf.get('title')
        if 'virtual' or 'clonedrive' in feature['Модель'].lower():
            continue
        #feature['name'] = leaf.xpath('entry[@title="Name"]')[0].get('value')
        feature['Тип првода'] = leaf.xpath('entry[@title="Media Type"]')[0].get('value')
        feature['Возможности чтения'] = leaf.xpath('entry[@title="Read capabilities"]')[0].get('value')
        feature['Возможности записи'] = leaf.xpath('entry[@title="Write capabilities"]')[0].get('value')
        device = dict()
        device['type'] = 'cdrom'
        device['verbose'] = feature['Модель']# + feature['name']
        device['feature'] = feature
        devices.append(device)


    # Как отделить встроенный звук от звуковой платы? Пока саунд грабить не буду, так как ни у кого отдельного звука нет
    # soundcard = tree.xpath('/speccydata/mainsection[@title="Audio"]/section[starts-with(@title, "Sound Card")]/entry')[0].get('title')

    # перефирия
    # - может, и вовсе не надо

    # сеть - то же самое, как отделить встроенную от внешней?..
    # network_card_name = tree.xpath('/speccydata/mainsection[@title="Network"]/section[@title="Adapters List"]/section/section')[0].get('title')

    return summary, devices