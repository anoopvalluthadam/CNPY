import pytest
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from app.parsing import parse_data, load_config


def test_parsing():
    """
    Test parsing
    """

    xml_path = os.path.abspath(os.path.join(os.getcwd())) + '/tests/test.xml'
    config_path = ('/tests/test.json')
    config, config_keys = load_config(config_path)
    # import pdb; pdb.set_trace()

    data = parse_data(xml_path, config, config_keys)
    assert len(data['Description']) == 13
