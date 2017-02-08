#!/usr/bin/env python3

from bs4 import BeautifulSoup
import requests
import pathlib, re, geocoder, json
from operator import itemgetter

#added for homework
import sys, pprint

INSPECTION_DOMAIN = 'http://info.kingcounty.gov'
INSPECTION_PATH = '/health/ehs/foodsafety/inspections/Results.aspx'
INSPECTION_PARAMS = {
    'Output': 'W',
    'Business_Name': '',
    'Business_Address': '',
    'Longitude': '',
    'Latitude': '',
    'City': '',
    'Zip_Code': '',
    'Inspection_Type': 'All',
    'Inspection_Start': '',
    'Inspection_End': '',
    'Inspection_Closed_Business': 'A',
    'Violation_Points': '',
    'Violation_Red_Points': '',
    'Violation_Descr': '',
    'Fuzzy_Search': 'N',
    'Sort': 'H'
}


def get_inspection_page(**kwargs):
    url = INSPECTION_DOMAIN + INSPECTION_PATH
    params = INSPECTION_PARAMS.copy()
    for key, val in kwargs.items():
        if key in INSPECTION_PARAMS:
            params[key] = val
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.text

def parse_source(html):
    parsed = BeautifulSoup(html, "html5lib")
    return parsed

def load_inspection_page(name):
    file_path = pathlib.Path(name)
    return file_path.read_text(encoding='utf8', errors='ignore')

def restaurant_data_generator(html):
    id_finder = re.compile(r'PR[\d]+~')
    return html.find_all('div', id=id_finder)

def has_two_tds(elem):
    is_tr = elem.name == 'tr'
    td_children = elem.find_all('td', recursive=False)
    has_two = len(td_children) == 2
    return is_tr and has_two

def clean_data(td):
    return td.text.strip(" \n:-")

def extract_restaurant_metadata(elem):
    restaurant_data_rows = elem.find('tbody').find_all(has_two_tds, recursive=False)
    rdata = {}
    current_label = ''
    for data_row in restaurant_data_rows:
        key_cell, val_cell = data_row.find_all('td', recursive=False)
        new_label = clean_data(key_cell)
        current_label = new_label if new_label else current_label
        rdata.setdefault(current_label, []).append(clean_data(val_cell))
    return rdata

def is_inspection_data_row(elem):
    is_tr = elem.name == 'tr'
    if not is_tr:
        return False
    td_children = elem.find_all('td', recursive=False)
    has_four = len(td_children) == 4
    this_text = clean_data(td_children[0]).lower()
    contains_word = 'inspection' in this_text
    does_not_start = not this_text.startswith('inspection')
    return is_tr and has_four and contains_word and does_not_start

def get_score_data(elem):
    inspection_rows = elem.find_all(is_inspection_data_row)
    samples = len(inspection_rows)
    total = high_score = average = 0
    for row in inspection_rows:
        strval = clean_data(row.find_all('td')[2])
        try:
            intval = int(strval)
        except (ValueError, TypeError):
            samples -= 1
        else:
            total += intval
            high_score = intval if intval > high_score else high_score
    if samples:
        average = total/float(samples)
    return {'Average Score': average, 'High Score': high_score,
            'Total Inspections': samples}

def result_generator(count):
    use_params = {
        'Inspection_Start': '2/1/2013',
        'Inspection_End': '2/1/2015',
        'Zip_Code': '98101'
    }
    # html, encoding = get_inspection_page(**use_params)
    html = load_inspection_page('inspection_page.html')
    parsed = parse_source(html)
    content_col = parsed.find("td", id="contentcol")
    data_list = restaurant_data_generator(content_col)
    for data_div in data_list[:count]:
        metadata = extract_restaurant_metadata(data_div)
        inspection_data = get_score_data(data_div)
        metadata.update(inspection_data)
        print(metadata)
        yield metadata

def get_geojson(result):
    address = " ".join(result.get('Address', ''))
    if not address:
        return None
    geocoded = geocoder.google(address)
    geojson = geocoded.geojson
    inspection_data = {}
    use_keys = ('Business Name', 'Average Score', 'Total Inspections', 'High Score')
    for key, val in result.items():
        if key not in use_keys:
            continue
        if isinstance(val, list):
            val = " ".join(val)
        inspection_data[key] = val
    geojson['properties'] = inspection_data
    return geojson

# Homework Starts here
def get_args():
    '''gets the command line arguments'''
    #get the key to sort by
    if sys.argv[1] == 'highscore':
        sort_key = "High Score"
    elif sys.argv[1] == 'averagescore':
        sort_key = "Average Score"
    elif sys.argv[1] == 'inspections':
        sort_key = "Total Inspections"
    #get the result count
    num_result = int(sys.argv[2])
    #get the reverse setting - this one is optional - default is True
    try:
        if sys.argv[3] == 'reverse':
            reverse = False
    except IndexError:
        reverse = True
    #return the 3 command line arguments
    return sort_key, num_result, reverse

def sort_results(result, key, reverse):
    # Sorting: http://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-values-of-the-dictionary-in-python
    # with lambda function
    sorted_list = sorted(result['features'], key=lambda k: k['properties'][key], reverse=reverse)
    # with itemgetter function
    # sorted_newlist = sorted(result['features'], key=itemgetter(['properties'][key], reverse=reverse))
    new_result = {}
    new_result["features"] = sorted_list
    new_result["type"] = "FeatureCollection"
    return new_result

if __name__ == '__main__':
    #get the command line arguments
    key, num_result, reverse = get_args()
    total_result = {'type': 'FeatureCollection', 'features': []}
    for result in result_generator(num_result):
        geojson = get_geojson(result)
        total_result["features"].append(geojson)
    new_result = sort_results(total_result, key, reverse)
    pprint.pprint(new_result)
