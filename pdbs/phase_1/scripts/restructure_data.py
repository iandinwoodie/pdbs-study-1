"""
Attempting to restructure the data in a more readable format.
"""

import argparse
import csv
import os
import shutil
import yaml
from collections import OrderedDict


# Parse the input file from the command-line arguments and verify.
parser = argparse.ArgumentParser(description='Scrub duplicates from raw data.')
parser.add_argument('filename')
args = parser.parse_args()
infile = args.filename
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

# Create a structure from the raw data.
header = {}
data = {}
kcount = 0
with open(infile, 'r') as fin:
    is_header = True
    for row in csv.reader(fin, delimiter=','):
        if is_header:
            header['welcome'] = row[0:11]
            # Exclude 'more dogs' question (col 144)
            header['survey'] = row[11:144]
            header['feedback'] = row[685:689]
            for k in header.keys():
                length = len(header[k])
                for i in range(0, length):
                    header[k][i] = header[k][i].replace('\ufeff', '')
                    header[k][i] = header[k][i].replace('_1a', '')
            # Indicate that the header has been recorded.
            is_header = False
        else:
            user = row[8]
            if not user in data:
                data[user] = {}
                data[user]['welcome'] = OrderedDict()
                for i in range(0, 11):
                    data[user]['welcome'][header['welcome'][i]] = row[i]
                data[user]['feedback'] = OrderedDict()
                for i in range(0, 4):
                    data[user]['feedback'][header['feedback'][i]] = row[i+685]
                data[user]['dogs'] = {}
            status_cols = [145, 280, 415, 550, 684]
            for index, col in enumerate(status_cols):
                offset = index * 135
                if row[col] == '2':
                    name = row[11+offset]
                    data[user]['dogs'][name] = OrderedDict()
                    for i in range(0, 133):
                        data[user]['dogs'][name][header['survey'][i]] = row[11+offset]
                    kcount += 1
            if kcount > 2500:
                break




            #status = [row[145], row[280], row[415], row[550], row[684]]
            #record_dict[user_hash]['status'] += status
            #dogs = []
            #if status[0] == '2':
            #    dogs.append(row[11:145])
            #record_dict[user_hash]['dogs'] += dogs
represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items())
yaml.add_representer(OrderedDict, represent_dict_order)
with open('output.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)
