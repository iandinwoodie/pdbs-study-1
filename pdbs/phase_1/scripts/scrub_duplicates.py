"""
Scrubs duplicates from raw data.

Criteria to update existing response:
    - The updated response must not replace a complete entry for a specific dog
      with an incomplete entry.
    - The updated response must not replace a complete entry for a specific dog
      with an entry for a different dog.
    - The updated response must not detract from the existing data of a complete
      entry for a specific dog.

Criteria to dispose subsequent response:
    - The updated response replaces a complete entry for a specific dog with an
      incomplete entry.
    - The updated response replaces a complete entry for a specific dog with an
      entry for a different dog.
    - The updated response detracts from the existing data of a complete entry
      for a specific dog.

Criteria to keep existing and subsequent responses:
    - Both the existing and updated responses contain complete dog-specific
      entries.
    - No complete entry for the same specific dog is shared in both responses.
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

# Verify the file to be scrubbed.
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

# Make a copy of the input file.
base = os.path.splitext(os.path.basename(infile))[0]
outfile = base + '.data'
bakfile = base + '.bak'
shutil.copy(infile, bakfile)

# Parse the raw data with relevant filters.
status_sum_dict = {}
status_dict = {}
data_dict = {}
dog_dict = {}
update_dict = {}
duplicate_cnt = 0
with open(bakfile, 'r') as fin:
    with open(outfile, 'w') as fout:
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        first_row = True
        for row in csv.reader(fin, delimiter=','):
            write_row = False
            remove_previous = False
            if not first_row:
                user_hash = row[8]
                status = [int(row[10]), int(row[145]), int(row[280]),
                          int(row[415]), int(row[550]), int(row[688])
                ]
                status_sum = sum(status)
                dogs = [row[11], row[146], row[281], row[416], row[551]]
                dogs = [x for x in dogs if x != '']
                if user_hash in status_dict:
                    duplicate_cnt += 1
                    if status[5] == 0:
                        # Current entry is incomplete, discard it.
                        pass
                    elif status_dict[user_hash][5] == 0:
                        # Existing entry is incomplete, replace it.
                        remove_previous = True
                        write_row = True
                    else:
                        old_dogs = set(dog_dict[user_hash])
                        new_dogs = set(dogs)
                        if not bool(old_dogs.symmetric_difference(new_dogs)):
                            if status_sum_dict[user_hash] <= status_sum:
                                # Old entry for same list of dogs is less
                                # complete, replace it.
                                remove_previous = True
                                write_row = True
                        elif bool(new_dogs.intersection(old_dogs)):
                            if status_sum_dict[user_hash] <= status_sum:
                                # Old entry shares at least one dog, but is
                                # less complete, replace it.
                                remove_previous = True
                                write_row = True
                        else:
                            # New entry is for different set of dogs, keep both.
                            duplicate_cnt -= 1
                            write_row = True
                else:
                    write_row = True
                if write_row:
                    data_dict[user_hash] = row
                    status_dict[user_hash] = status
                    dog_dict[user_hash] = dogs
                    status_sum_dict[user_hash] = status_sum
                    if remove_previous:
                        update_dict[user_hash] = row[0]
            else:
                write_row = True
                first_row = False
            if write_row:
                writer.writerow(row)

# Replace the input file with the first round of filter data.
shutil.copy(outfile, bakfile)

# Loop back through file and remove all entries marked for removal.
remaining_cnt = 0
with open(bakfile, 'r') as fin:
    with open(outfile, 'w') as fout:
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        first_row = True
        for row in csv.reader(fin, delimiter=','):
            write_row = True
            if not first_row:
                user_hash = row[8]
                if user_hash in update_dict:
                    if update_dict[user_hash] != row[0]:
                        write_row = False
                if write_row:
                    remaining_cnt += 1
            else:
                first_row = False
            if write_row:
                writer.writerow(row)

# Delete copy of input file.
os.remove(bakfile)

# Let the user know the script has finished.
print('Duplicates: %d, Remaining Entries: %d' %(duplicate_cnt, remaining_cnt))
print('Duplicates scrubbing complete.')
