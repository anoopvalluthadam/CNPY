import pandas as pd
import pprint
from lxml import etree
import collections
import json
import os
import argparse
from pandas import ExcelWriter

# JBS
start_point = 'Account Statement'
#stop_point = 'Carried forward'
stop_point = 'Report Details'

# Bos
#start_point = 'Securities Movements'
#stop_point = 'Current Account Movements'

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
    parser.add_argument('--output', action="store", dest="output",
                        required=True)

    return {'config_path': parser.parse_args().config,
            'xml_path': parser.parse_args().xml_path,
            'out_path': parser.parse_args().output}


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
    data = {key: [] for key in config_keys}
    keys = config_keys
    key_index = temp_next = 0

    # maintain temp_keys for verifying the order of keys
    temp_keys = []

    text = ''
    current_heading = keys[key_index]

    for p in tree.iter():
        if p.text not in ['  ', None, '']:
            temp_keys.append(p.text)
        # reset the temp_key for second table iteratin
        if p.text == config_keys[0]:
            temp_keys= []
            processing = False
            temp_keys.append(p.text)

        if len(temp_keys) == len(config_keys):
            if temp_keys == keys:
                if p.text == config_keys[-1]:
                    print('Gonna start processing...')
                    processing = True
                    key_index = temp_next = 0
                    current_heading = keys[key_index]
                    temp_keys = []
                    continue
            else:
                # reseting...
                temp_keys = []
        if processing:
            temp_keys = []
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

                elif int(p.attrib.get('left', 0)) in config[keys[temp_next]]:
                    if text:
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
                    if text:
                        data[current_heading].append(text)
                    text = ''
                    # need to verify where is our key index belongs to
                    temp_index = 0
                    for  i in range(key_index+1, len(keys)):
                        if int(p.attrib.get('left', 0)) in config[keys[i]]:
                            # reached end and in between gaps are there
                            if len(keys) == i+1:
                                current_heading = keys[i]
                                if p.text:
                                    data[current_heading].append(p.text)
                                print(current_heading)
                                print('Resetting')
                                key_index = 0
                                text = ''
                                current_heading = keys[key_index]
                            # between gaps are there, not reached end
                            else:
                                if text:
                                    data[current_heading].append(text)
                                key_index = i
                                if p.text:
                                    data[keys[key_index]].append(p.text)
                                text = ''
                    continue

    print(json.dumps(data))

    return data


def format_data(data, out_path):
    """
    Format the data into Excel
    Args:
        data (dict): parsed data from XML
    Returns:
        None
    """
    #df = pd.DataFrame.from_dict(data, orient='index')
    #df = pd.DataFrame.from_dict(data)

    highest = 0
    # verify the dataframe length
    for val in data.values():
        if len(val) > highest:
            highest = len(val)
    for d in data:
        if highest-len(data[d]) > 0:
            data[d].extend([0] * int(highest-len(data[d])))

    df = pd.DataFrame.from_dict(data)
    # write to a csv
    df.to_csv(out_path + '.csv', sep=',')

    # write to an Excel File
    writer = ExcelWriter(out_path + '.xlsx')
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

        return config, data['order']
    else:
        print('Error in config path')
        exit(1)


if __name__ == '__main__':
    # NOTE: Can read from the Directory asynchronously  and process in parellel
    args = parse_argument()
    xml_path = ROOT_DIR + '/' + args['xml_path']
    out_path = ROOT_DIR + '/' + args['out_path']
    config, config_keys = load_config(args.get('config_path', ''))

    data = parse_data(xml_path, config, config_keys)
    format_data(data, out_path)
