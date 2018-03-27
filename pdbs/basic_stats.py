"""
Compute basic stats for the raw data.
"""

import argparse
import csv
import os
import shutil


# Parse the input file from the command-line arguments.
parser = argparse.ArgumentParser(description='Scrub duplicates from raw data.')
parser.add_argument('filename')
args = parser.parse_args()
infile = args.filename

# Verify the file to analyze.
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

# Create a structure from the raw data.
record_dict = {}
with open(infile, 'r') as fin:
    first_row = True
    for row in csv.reader(fin, delimiter=','):
        if not first_row:
            user_hash = row[8]
            if user_hash in record_dict:
                dog_cnt = len(record_dict[user_hash]['dogs'])
            else:
                dog_cnt = 0
                record_dict[user_hash] = {}
                record_dict[user_hash]['demo'] = row[0:11]
                record_dict[user_hash]['feed'] = row[685:689]
                record_dict[user_hash]['status'] = []
                record_dict[user_hash]['dogs'] = []
            status = [row[145], row[280], row[415], row[550], row[684]]
            record_dict[user_hash]['status'] += status
            dogs = []
            if status[0] == '2':
                dogs.append(row[11:145])
            if status[1] == '2':
                dogs.append(row[146:280])
            if status[2] == '2':
                dogs.append(row[281:415])
            if status[3] == '2':
                dogs.append(row[416:550])
            if status[4] == '2':
                dogs.append(row[551:684])
            record_dict[user_hash]['dogs'] += dogs
        else:
            first_row = False

# Calculate and output basic stats.
tot_dog_cnt = 0
max_dog_cnt = 0
tot_dog_invite_cnt = 0
tot_usr_invite_cnt = 0
dog_name_dict = {}
for user in record_dict:
    cur_dog_list = record_dict[user]['dogs']
    cur_dog_cnt = len(cur_dog_list)
    tot_dog_cnt += cur_dog_cnt
    if cur_dog_cnt > max_dog_cnt:
        max_dog_cnt = cur_dog_cnt
    cur_dog_invite_cnt = 0
    for dog in cur_dog_list:
        if int(dog[39]) > 0:
            cur_dog_invite_cnt += 1
        cur_dog_name = dog[0].upper()
        if cur_dog_name in dog_name_dict:
            dog_name_dict[cur_dog_name] += 1
        else:
            dog_name_dict[cur_dog_name] = 1
    if (record_dict[user]['feed'][2] == '1' and
            record_dict[user]['feed'][3] == '2'):
        tot_usr_invite_cnt += 1
        tot_dog_invite_cnt += cur_dog_invite_cnt

print('Total phase I participants: %d' %len(record_dict))
print('Total phase I dogs: %d' %tot_dog_cnt)
print('Maximum number of dogs entered by a single user: %d' %max_dog_cnt)
print('Total invited phase II participants: %d' %tot_usr_invite_cnt)
print('Total invited phase II dogs: %d' %tot_dog_invite_cnt)
print('Number of unique dog names: %d' %len(dog_name_dict))
print('The most popular name was %s used %d times'
      %(max(dog_name_dict, key=dog_name_dict.get),
        dog_name_dict[max(dog_name_dict, key=dog_name_dict.get)]))
# Indicate that the script is complete.
print('Basic stats complete.')
