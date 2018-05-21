import pandas as pd
import pprint
from lxml import etree
import collections
import json
import os
import argparse
from pandas import ExcelWriter

config = collections.OrderedDict()

xml_data = 'jbs.xml'

start_point = 'Account Statement'
stop_point = 'Report Details'

config = {
    'Booking Date': list(range(170,176)),
    'Txn Date': list(range(288,297)),
    'Booking Text': list(range(387,390)),
    'Value Date': list(range(801,810)),
    'Debit': list(range(927,967)),
    'Credit': list(range(1021,1084)),
    'Balance': list(range(1140,1209))
}

config_keys = ['Booking Date', 'Txn Date', 'Booking Text', 'Value Date', 'Debit', 'Credit', 'Balance']

data = {key: [] for key in config}
ROOT_DIR= os.path.abspath(os.path.join(os.getcwd()))

def parse_argument():
    """
    Parse CLI arguments
    """

    parser = argparse.ArgumentParser(description='Data parsing')

    parser.add_argument('--config', action="store", dest="config",
                        required=True)
    parser.add_argument('--xml', action="store", dest="xml_path",
                        required=True)

    return {'config_path': parser.parse_args().config,
            'xml_path': parser.parse_args().xml_path}


def parse_data(xml_path, config, config_keys):
    """
    parse XML
    Args:
        xml_path (str): XML path
        config (dict): Configuration for the PDF
        config_keys (list): order of config keys
    Returns:
        data (dict): parsed data from XML
    """
    tree = etree.parse(xml_path)

    processing = False
    current_heading = None

    keys = config_keys
    key_index = temp_next = 0

    # maintain temp_keys for verifying the order of keys
    temp_keys = []

    text = ''
    current_heading = keys[key_index]
    for p in tree.iter():
        temp_keys.append(p.text)

        if len(temp_keys) == len(config_keys):
            if temp_keys == keys:
                if p.text == config_keys[-1]:
                    print('Gonna start processing...')
                    processing = True
                    key_index = temp_next = 0
                    current_heading = keys[key_index]
                    continue
            else:
                # reseting...
                temp_keys = []
        if processing:
            if p.attrib:
                if p.text == stop_point:
                    print('-' * 100)
                    #exit(1)
                    break

                # Get the key
                # print(p.attrib.get('left', 0), current_heading, )
                current_left = int(p.attrib.get('left', 0))
                temp_next = 0 if len(keys) == key_index + 1 else key_index + 1  # noqa
                if current_left in config[current_heading]:
                    # import pdb; pdb.set_trace()
                    if p.text:
                        text += p.text + ' '
                    # print(p.attrib.get('left', 0), p.text)

                elif int(p.attrib.get('left', 0)) in config[keys[temp_next]]:
                    data[current_heading].append(text)
                    text = ''
                    if p.text:
                        text += p.text + ' '

                    # Time to change the key(heading)
                    key_index += 1
                    if len(keys) == key_index:
                        print('Resetting')
                        key_index = 0
                    current_heading = keys[key_index]
                else:
                    continue

    print(json.dumps(data))

    return data


def format_data(data):
    """
    Format the data into Excel
    Args:
        data (dict): parsed data from XML
    Returns:
        None
    """
    df = pd.DataFrame.from_dict(data,orient='index')

    # write to a csv
    df.to_csv('out.csv', sep=',')

    # write to an Excel File
    writer = ExcelWriter('out.xlsx')
    df.to_excel(writer,'Sheet5')
    writer.save()


def load_config(path):
    """
    Read config data from the config file as json
    Args:
        path (str): File path
    Returns:
        config (dict): configuration
    """

    if path:
        path = ROOT_DIR + '/' + path
        data = {}
        with open(path, 'r') as f:
            data = json.load(f)

        config = {}
        for key in data['order']:
            start = int(data['config'][key].split(',')[0])
            end = int(data['config'][key].split(',')[1])
            config[key] = list(range(start, end))

        return config, config_keys
    else:
        print('Error in config path')
        exit(1)


if __name__ == '__main__':
    # NOTE: Can read from the Directory asynchronously  and process in parellel
    args = parse_argument()
    xml_path = ROOT_DIR + '/' + args['xml_path']
    config, config_keys = load_config(args.get('config_path', ''))
    print(config)

    data = parse_data(xml_path, config, config_keys)
    format_data(data)
