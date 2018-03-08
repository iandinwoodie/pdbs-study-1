import csv
import urllib.request
import json
import re


def extract_postal_data():
    """Extracts relevant data points from the raw data."""
    with open('pdbs_phase_1_raw.csv', 'r') as fin, open('geostat_data.csv', 'w') as fout:
        writer = csv.writer(fout, delimiter=',', lineterminator='\n')
        first_row = True
        for row in csv.reader(fin, delimiter=','):
            if first_row == True:
                first_row = False
                continue
            # Filter out incomplete survey responses
            complete = '2'
            if row[10] == complete:
                # Filter out incomplete geographic responses
                if row[8] != '' and row[9] != '':
                    writer.writerow([row[8], row[9]])


def create_postal_dictionary():
    """Creates a user/postal code dictionary from the filtered data."""
    postal_dict = {}
    with open('geostat_data.csv', 'r') as fin:
        for row in csv.reader(fin, delimiter=','):
            user_hash = row[0]
            # Remove whitespace from postal code and homogenize type case
            postal_code = row[1].replace(' ', '').upper()
            # Add the key/value pair to the dictionary if it does not exist
            # Print an error if there are conflicting data points for a user
            if not user_hash in postal_dict:
                postal_dict[user_hash] = postal_code
            elif postal_dict[user_hash] != postal_code:
                print("Error: user %s provided %s and %s as postal codes"
                      %(user_hash, postal_dict[user_hash], postal_code))
    return postal_dict

def determine_postal_country(postal_code):
    if postal_code != 'N/A':
        # US, Germany, Mexico, Dominican Republic, Spain, Finland, France,
        # Italy
        if re.match(r'^[0-9]{5}(\-[0-9]{4}){,1}$', postal_code):
            codes = ['us', 'de', 'mx', 'do', 'es', 'fi', 'fr', 'it']
        # Canada
        elif re.match(r'^([A-Z][0-9]){3}$', postal_code):
            codes = ['ca']
        # UK
        elif re.match(r'^[A-Z]{1,2}[0-9]{1,3}[A-Z]{0,2}$', postal_code):
            codes = ['gb']
        # Australia, Belgium, Austria, Argentina, Bangladesh, Bulgaria,
        # Switzerland, Denmark
        elif re.match(r'^[0-9]{4}$', postal_code):
            codes = ['au', 'be', 'at', 'ar', 'bd', 'bg', 'ch', 'dk']
        # Russia, India
        elif re.match(r'^[0-9]{6}$', postal_code):
            codes = ['ru', 'in']
        # Poland
        elif re.match(r'^[0-9]{2}\-{1}[0-9]{3}$', postal_code):
            codes = ['pl']
        # Portugal
        elif re.match(r'^[0-9]{4}\-{1}[0-9]{3}$', postal_code):
            codes = ['pt']
        else:
            codes = []
    return codes


def reformat_postal_code(postal_code, codes):
    if 'ca' in codes: postal_code = postal_code[:3]
    elif 'gb' in codes: postal_code = postal_code[:3]
    elif 'us' in codes: postal_code = postal_code[:5]
    return postal_code


def fetch_postal_info(postal_dict):
    country_dict = {}
    api_url = 'http://api.zippopotam.us/'
    for email in postal_dict:
        postal_code = postal_dict[email]
        if postal_code == 'N/A':
            cur_country = 'Undisclosed'
        else:
            codes = determine_postal_country(postal_code)
            postal_code = reformat_postal_code(postal_code, codes)
            # Fetch geo info from the API
            info_found = False
            for code in codes:
                cur_url = api_url + code + '/' + postal_code
                try:
                    with urllib.request.urlopen(cur_url) as response:
                        data = json.loads(response.read())
                        if 'country' in data:
                            print(data['country'])
                            info_found = True
                            cur_country = data['country']
                except:
                    pass
            if not info_found:
                cur_country = 'Unmatched'
                print('Email: %s, Postal Code: %s' %(email, postal_code))
        # Record relevant postal info
        if cur_country in country_dict:
            country_dict[cur_country] += 1
        else:
            country_dict[cur_country] = 1
    return country_dict


def print_line():
    print('-'*80)


def main():
    print_line()
    extract_postal_data()
    postal_dict = create_postal_dictionary()
    print_line()
    print(fetch_postal_info(postal_dict))
    print_line()


if __name__ == "__main__":
    main()
