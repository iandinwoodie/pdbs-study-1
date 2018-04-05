"""
Fetch all records for the REDCap project corresponding to the given API token.
"""

from requests import post
import config


def main():
    token = config.token
    url = 'https://collaborate.tuftsctsi.org/redcap/api/'

    payload = {
        'token': token,
        'format': 'csv',
        'content': 'record'
        }

    response = post(url, data=payload)
    print (response.status_code)

    data = response.json()


if __name__ == "__main__":
    main()
