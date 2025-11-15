import os
import requests
from pathlib import Path

# Create flags directory if it doesn't exist
flags_dir = Path('static/img/flags')
flags_dir.mkdir(parents=True, exist_ok=True)

# List of country codes we need (from the CSS file)
country_codes = [
    'zm', 'gb', 'br', 'fr', 'de', 'es', 'it', 'pt', 'ng', 'gh',
    'za', 'ke', 'eg', 'ma', 'sn', 'ci', 'cm', 'zw', 'mw', 'mz',
    'na', 'bw', 'tz', 'ug', 'rw', 'bi', 'cd', 'ao', 'sz', 'ls',
    'mu', 'sc', 'mg'
]

def download_flag(country_code):
    url = f'https://flagcdn.com/16x12/{country_code}.png'
    response = requests.get(url)
    if response.status_code == 200:
        with open(flags_dir / f'{country_code}.png', 'wb') as f:
            f.write(response.content)
        print(f'Downloaded flag for {country_code.upper()}')
    else:
        print(f'Failed to download flag for {country_code.upper()}')

if __name__ == '__main__':
    print('Downloading country flags...')
    for code in country_codes:
        download_flag(code)
    print('All flags downloaded!')
