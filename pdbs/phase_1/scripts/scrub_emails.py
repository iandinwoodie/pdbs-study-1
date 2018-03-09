"""Scrubs emails from raw data by replacement with MD5 hashes."""

import re
import os
import shutil
import csv
import hashlib


# Verify the file to be scrubbed of emails.
print(os.listdir(os.getcwd()))
filename = str(input('Enter file to be scrubbed of emails: '))
if not os.path.isfile(filename):
    print('Error: entered filename does not exist')
    quit()

# Create a backup of the original file if does not exist.
backup = filename + '.bak'
if not os.path.isfile(backup):
    print('Creating a backup of the the original file ...')
    shutil.copy(filename, backup)

# Scrub out the email address and replace with MD5 hashes.
hash_dict = {}
dupe_cnt = 0
m = hashlib.md5()
with open(backup, 'r') as fin:
    with open(filename, 'w') as fout:
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
print('dupes: %d' %dupe_cnt)
print('Email scrubbing of %s is complete.' %filename)
