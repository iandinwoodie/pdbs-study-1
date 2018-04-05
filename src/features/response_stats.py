"""
Compute the pdbs phase 1 response stats.
"""

import argparse
import os
import yaml
from collections import OrderedDict


# Parse the input file from the command-line arguments.
parser = argparse.ArgumentParser(description='Compute the pdbs phase 1 response stats')
parser.add_argument('filename')
args = parser.parse_args()
infile = args.filename

# Verify the file to analyze.
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

with open(infile, 'r') as fin:
    data = yaml.load(fin)

ignores = ['dog_name', 'dog_age_toay_years', 'dog_weight',
           'dog_age_today_years', 'q02_score', 'q03_count', 'q04_count',
           'purebred_breed', 'q03_person_freq', 'dog_age_today_months',
           'q01_age_months', 'dog_sex_year', 'dog_age_acq_years',
           'dog_age_acq_months', 'dog_sex_month', 'q03_dog_freq',
           'q01_age_years']

tally = OrderedDict()
users = 0
for user in data.keys():
    for dog in data[user]['dogs'].keys():
        for key, value in data[user]['dogs'][dog].items():
            if key in ignores:
                continue
            try:
                value = int(value)
                if not key in tally:
                    tally[key] = {}
                if not value in tally[key]:
                    tally[key][value] = 1
                else:
                    tally[key][value] += 1
            except:
                value = str(value)
    users += 1
tally['total users'] = users


represent_dict_order = lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', tally.items())
yaml.add_representer(OrderedDict, represent_dict_order)
with open('output.yml', 'w') as outfile:
    yaml.dump(tally, outfile, default_flow_style=False)
