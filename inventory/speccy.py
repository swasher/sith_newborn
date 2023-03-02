from lxml import etree
import re
from .utils import bytes_to_human, human_to_bytes

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

    # DEPRECATED; Now we calc total RAM as total sum of every ram module
    # mem_size = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory"]/entry[@title="Size"]')[0].get('value')
    # mem_total_physical = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Physical Memory"]/entry[@title="Total Physical"]')[0].get('value')
    # ram = mem_total_physical if 'GB' in mem_total_physical else mem_size
    # summary['ram'] = ram

    summary['installation_date'] = tree.xpath('/speccydata/mainsection[@title="Operating System"]/entry[contains(@value, "Installation Date")]')[0].get('value')

    #
    # CPU
    #
    processors_branch = tree.iterfind('.//mainsection[@title="CPU"]/section')
    for leaf in processors_branch:
        feature = dict()
        feature['Процессор'] = leaf.xpath('entry[@title="Name"]')[0].get('value')
        feature['Количество ядер'] = leaf.xpath('entry[@title="Cores"]')[0].get('value')
        feature['Количество потоков'] = leaf.xpath('entry[@title="Threads"]')[0].get('value')
        try:
            feature['Архитектура'] = leaf.xpath('entry[@title="Code Name"]')[0].get('value')
        except IndexError:
            feature['Архитектура'] = 'Speccy Unknown'

        try:
            feature['Сокет'] = leaf.xpath('entry[@title="Package"]')[0].get('value')
        except IndexError:
            feature['Сокет'] = 'Speccy Unknown'

        try:
            feature['Литография'] = leaf.xpath('entry[@title="Technology"]')[0].get('value')
        except IndexError:
            feature['Литография'] = 'Speccy Unknown'

        try:
            feature['Ревизия'] = leaf.xpath('entry[@title="Revision"]')[0].get('value')
        except IndexError:
            feature['Ревизия'] = 'Speccy Unknown'

        try:
            feature['Базовая тактовая частота процессора'] = leaf.xpath('entry[@title="Stock Core Speed"]')[0].get('value')
        except IndexError:
            feature['Базовая тактовая частота процессора'] = 'Speccy Unknown'

        device = dict()
        device['type'] = 'cpu'
        device['verbose'] = '{Процессор} ({Архитектура}, {Сокет})'.format(**feature)
        device['feature'] = feature
        devices.append(device)

    #
    # Motherboard
    #
    feature = dict()
    feature['Бренд'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Manufacturer"]')[0].get('value')
    feature['Модель'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Model"]')[0].get('value')

    try:
        feature['Чипсет, вендор'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Chipset Vendor"]')[0].get('value')
    except IndexError:
        feature['Чипсет, вендор'] = 'Speccy Unknown'

    try:
        feature['Чипсет, модель'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/entry[@title="Chipset Model"]')[0].get('value')
    except IndexError:
        feature['Чипсет, модель'] = 'Speccy Unknown'

    try:
        feature['Память, тип'] = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory"]/entry[@title="Type"]')[0].get('value')
    except IndexError:
        feature['Память, тип'] = 'Speccy Unknown'

    try:
        feature['Память, кол-во слотов'] = tree.xpath('/speccydata/mainsection[@title="RAM"]/section[@title="Memory slots"]/entry[@title="Total memory slots"]')[0].get('value')
    except IndexError:
        feature['Память, кол-во слотов'] = 'Speccy Unknown'

    feature['Биос, вендор'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/section[@title="BIOS"]/entry[@title="Brand"]')[0].get('value')
    feature['Биос, дата'] = tree.xpath('/speccydata/mainsection[@title="Motherboard"]/section[@title="BIOS"]/entry[@title="Date"]')[0].get('value')

    device = dict()
    device['type'] = 'motherboard'
    device['verbose'] = '{Бренд} {Модель}'.format(**feature)
    device['feature'] = feature
    devices.append(device)

    #
    # Memory
    #
    memory_slots_branch = tree.iterfind('.//section[@title="SPD"]/section')
    for leaf in memory_slots_branch:  # поиск элементов
        feature = dict()
        #feature['Слот'] = leaf.get('title')
        feature['Тип'] = leaf.xpath('entry[@title="Type"]')[0].get('value')

        # rename DDR to DDR1, so you can select only ddr1 (without ddr2, ddr3, etc)
        if feature['Тип'] == 'DDR':
            feature['Тип'] = 'DDR1'

        mem = leaf.xpath('entry[@title="Size"]')[0].get('value')
        mem = human_to_bytes(mem)
        mem = bytes_to_human(mem, base=1024)
        feature['Объем'] = mem
        feature['Вендор'] = leaf.xpath('entry[@title="Manufacturer"]')[0].get('value')
        feature['Частота'] = leaf.xpath('entry[@title="Max Bandwidth"]')[0].get('value')
        try:
            feature['Серия (Part Number)'] = leaf.xpath('entry[@title="Part Number"]')[0].get('value')
        except IndexError:
            feature['Серия (Part Number)'] = 'Speccy Unknown'

        try:
            feature['Серийный номер'] = leaf.xpath('entry[@title="Serial Number"]')[0].get('value')
        except IndexError:
            feature['Серийный номер'] = 'Speccy Unknown'

        try:
            feature['Изготовлено (Week-year)'] = leaf.xpath('entry[@title="Week/year"]')[0].get('value')
        except IndexError:
            feature['Изготовлено (Week-year)'] = 'Speccy Unknown'

        device = dict()
        device['type'] = 'memory'
        device['verbose'] = '{Вендор} {Объем} {Тип}'.format(**feature)
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
            except AttributeError:
                feature['Модель'] = 'Speccy Unknown'

            feature['Нативное разрешение'] = leaf.xpath('entry[@title="Current Resolution"]')[0].get('value')
            device = dict()
            device['type'] = 'monitor'
            try:
                device['verbose'] = feature['Модель']
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
    try:
        feature['Чипсет, вендор'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Manufacturer"]')[0].get('value')
    except IndexError:
        feature = None

    # Далее, нет способа определить, интегрированное видео или дискретное. Предположу, что Intel не делает дискретных
    # видух (пруф https://linustechtips.com/main/topic/380568-has-intel-ever-made-a-dedicated-graphics-card/),
    # а интегрированные бывают только 'Intel' или 'ATI'. Если так, то считаем, что видео интегрированное:
    # ==================== ШО ЗА БРЕД?! ATI МОЖЕТ БЫТЬ И ДИСКРЕТНАЯ

    if feature and feature['Чипсет, вендор'] not in ['Intel', 'ATI']:
        feature['Модель'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Model"]')[0].get('value')
        feature['Бренд'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Subvendor"]')[0].get('value')

        try:
            feature['Дата выпуска'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Release Date"]')[0].get('value')
        except IndexError:
            feature['Дата выпуска'] = 'Speccy Unknown'

        try:
            feature['Объем памяти'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Memory"]')[0].get('value')
        except:
            feature['Объем памяти'] = 'Speccy Unknown'
        try:
            feature['Объем памяти'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Physical Memory"]')[0].get('value')
        except:
            feature['Объем памяти'] = 'Speccy Unknown'

        try:
            feature['GPU'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="GPU"]')[0].get('value')
        except IndexError:
            feature['GPU'] = 'Speccy Unknown'

        try:
            feature['Литография'] = tree.xpath('/speccydata/mainsection[@title="Graphics"]/section/entry[@title="Technology"]')[0].get('value')
        except IndexError:
            feature['Литография'] = 'Speccy Unknown'

        device = dict()
        device['type'] = 'videocard'
        device['verbose'] = ' '.join([feature['Чипсет, вендор'], feature['Модель']])
        device['feature'] = feature
        devices.append(device)
    else:
        pass

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
            feature['Бренд'] = 'Speccy Unknown'

        try:
            features = leaf.xpath('entry[@title="Features"]')[0].get('value')
        except:
            feature['Тип носителя'] = 'Speccy Unknown'
        else:
            if 'SSD' in features:
                feature['Тип носителя'] = 'SSD'
            else:
                feature['Тип носителя'] = 'HDD'

        try:
            feature['Серийный номер'] = leaf.xpath('entry[@title="Serial Number"]')[0].get('value')
        except IndexError:
            feature['Серийный номер'] = 'Speccy Unknown'

        interface = leaf.xpath('entry[@title="Interface"]')[0].get('value')
        feature['Интерфейс'] = 'IDE' if interface=='ATA' else interface

        try:
            feature['Ревизия SATA'] = leaf.xpath('entry[@title="SATA type"]')[0].get('value')
        except IndexError:
            feature['Ревизия SATA'] = 'Speccy Unknown'

        try:
            feature['Стандарт ATA'] = leaf.xpath('entry[@title="ATA Standard"]')[0].get('value')
        except IndexError:
            feature['Стандарт ATA'] = 'Speccy Unknown'

        try:
            feature['Форм-фактор'] = leaf.xpath('entry[@title="Form Factor"]')[0].get('value')
        except IndexError:
            feature['Форм-фактор'] = 'Speccy Unknown'

        try:
            feature['Шпиндель (RPM-class)'] = leaf.xpath('entry[@title="Speed"]')[0].get('value')
        except IndexError:
            feature['Шпиндель (RPM-class)'] = 'Speccy Unknown'

        real_size = leaf.xpath('entry[@title="Real size"]')[0].get('value') #.replace(" ", "")

        # convert real_size to list, then filter only digets, then join and int them.
        # Example of real_size: 1 000 204 886 016 bytes
        capacity_in_bytes = int(''.join(filter(lambda x: x.isdigit(), list(real_size))))
        feature['Емкость'] = bytes_to_human(capacity_in_bytes, base=1000)

        device = dict()
        device['type'] = 'storage'
        device['verbose'] = '{Бренд} {Емкость} {Тип носителя}'.format(**feature)
        #device['verbose'] = ' '.join([feature['Бренд'], feature['Емкость'], feature['Тип носителя']])
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