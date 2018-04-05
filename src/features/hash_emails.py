"""
Replace emails with MD5 hashes.
The file input will contained the hashed emails.
A backup is created to preserve the original data.
"""

import argparse
import csv
import hashlib
import os
import re
import shutil


# Parse the input file from the command-line arguments.
parser = argparse.ArgumentParser(description='Replace emails with MD5 hashes.')
parser.add_argument('filename')
args = parser.parse_args()
infile = args.filename

# Verify the file to be scrubbed of emails.
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

# Create a backup of the original file if does not exist.
backup = infile + '.bak'
if not os.path.isfile(backup):
    print('Creating a backup of the the original file ...')
    shutil.copy(infile, backup)

# Scrub out the email address and replace with MD5 hashes.
hash_dict = {}
dupe_cnt = 0
m = hashlib.md5()
with open(backup, 'r') as fin:
    with open(infile, 'w') as fout:
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        first_row = True
        for row in csv.reader(fin, delimiter=','):
            if not first_row:
                if row[8] != '':
                    if not row[8] in hash_dict:
                        m.update(row[8].encode('utf-8'))
                        hash_dict[row[8]] = m.hexdigest()
                    else:
                        dupe_cnt += 1
                    row[8] = hash_dict[row[8]]
                else:
                    row[8] = 'N/A'
            else:
                first_row = False
            writer.writerow(row)

# Let the user know the script has finished.
print('Email hashing complete.')
