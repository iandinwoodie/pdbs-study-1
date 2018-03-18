"""
Attempting to restructure the data in a more readable format.
"""

import argparse
import csv
import os
import shutil


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
                data[user]['welcome'] = {}
                for i in range(0, 11):
                    data[user]['welcome'][header['welcome'][i]] = row[i]
                data[user]['feedback'] = {}
                for i in range(0, 4):
                    data[user]['feedback'][header['feedback'][i]] = row[i]
            #if user_hash in record_dict:
            #    dog_cnt = len(record_dict[user_hash]['dogs'])
            #else:
            #    dog_cnt = 0
            #    record_dict[user_hash] = {}
            #    record_dict[user_hash]['demo'] = row[0:11]
            #    record_dict[user_hash]['feed'] = row[685:689]
            #    record_dict[user_hash]['status'] = []
            #    record_dict[user_hash]['dogs'] = []
            #status = [row[145], row[280], row[415], row[550], row[684]]
            #record_dict[user_hash]['status'] += status
            #dogs = []
            #if status[0] == '2':
            #    dogs.append(row[11:145])
            #record_dict[user_hash]['dogs'] += dogs
print(data[user]['welcome'])
