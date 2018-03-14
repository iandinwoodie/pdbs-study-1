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

import os
import shutil
import csv


# Verify the file to be scrubbed.
infile = str(input('Enter file to be scrubbed of duplicates: '))
if not os.path.isfile(infile):
    print('Error: entered file does not exist')
    quit()

# Verify the output file.
base = os.path.splitext(os.path.basename(infile))[0]
outfile = base + '.data'
tempfile = ''
if infile == outfile:
    tempfile = outfile
    outfile = outfile + '.temp'

# Parse the raw data with relevant filters.
status_sum_dict = {}
dupe_cnt = 0
status_dict = {}
data_dict = {}
dog_dict = {}
with open(infile, 'r') as fin:
    with open(outfile, 'w') as fout:
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        first_row = True
        for row in csv.reader(fin, delimiter=','):
            write_row = False
            if not first_row:
                user_hash = row[8]
                status = [int(row[10]), int(row[145]), int(row[280]),
                          int(row[415]), int(row[550]), int(row[688])
                ]
                status_sum = sum(status)
                dogs = [row[11], row[146], row[281], row[416], row[551]]
                dogs = [x for x in dogs if x != '']
                if user_hash in status_dict:
                    dupe_cnt += 1
                    if status[5] == 0:
                        print('Duplicate found: updated entry is incomplete, '
                              'discard updated')
                    elif status_dict[user_hash][5] == 0:
                        print('Duplicate found: existing entry is incomplete, '
                              'save updated')
                        write_row = True
                    else:
                        old_dogs = set(dog_dict[user_hash])
                        new_dogs = set(dogs)
                        if not bool(old_dogs.symmetric_difference(new_dogs)):
                            print('Duplicate found: same set of dogs, ', end='')
                            if status_sum_dict[user_hash] <= status_sum:
                                print('but more complete data, save updated')
                                write_row = True
                            else:
                                print('but less complete data, discard updated')
                        else:
                            # For mismatched dog entries, see if there are similarities.
                            print('Duplicate found: UNCLASSIFIED')
                        #print(bool(set(dogs).symmetric_difference(dog_dict[user_hash])))
                        #if dog_dict[user_hash] == dogs and status_dict[user_hash] == status:
                            #print('MATCH %s %s' %(data_dict[user_hash][0], row[0]))
                            #print(set(data_dict[user_hash][1:]).symmetric_difference(row[1:]))
                    print(dog_dict[user_hash], end=' - ')
                    print(status_dict[user_hash])
                    print(dogs, end=' - ')
                    print(status)
                else:
                    write_row = True
            else:
                first_row = False
            if write_row:
                data_dict[user_hash] = row
                status_dict[user_hash] = status
                dog_dict[user_hash] = dogs
                status_sum_dict[user_hash] = status_sum
                #writer.writerow(row)

# If a temp file was used, move the results back to the requested destination.
if not tempfile == '':
    shutil.move(outfile, tempfile)

# Let the user know the script has finished.
print('Duplicates scrubbing complete.')
