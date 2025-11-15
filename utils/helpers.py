import os
from datetime import datetime, date

def get_country_code(country_name):
    """
    Convert a country name to its ISO 3166-1 alpha-2 code.
    Returns the lowercase country code or 'zz' if not found.
    """
    country_codes = {
        'afghanistan': 'af', 'albania': 'al', 'algeria': 'dz', 'andorra': 'ad', 'angola': 'ao',
        'antigua and barbuda': 'ag', 'argentina': 'ar', 'armenia': 'am', 'australia': 'au',
        'austria': 'at', 'azerbaijan': 'az', 'bahamas': 'bs', 'bahrain': 'bh', 'bangladesh': 'bd',
        'barbados': 'bb', 'belarus': 'by', 'belgium': 'be', 'belize': 'bz', 'benin': 'bj',
        'bhutan': 'bt', 'bolivia': 'bo', 'bosnia and herzegovina': 'ba', 'botswana': 'bw',
        'brazil': 'br', 'brunei': 'bn', 'bulgaria': 'bg', 'burkina faso': 'bf', 'burundi': 'bi',
        'cabo verde': 'cv', 'cambodia': 'kh', 'cameroon': 'cm', 'canada': 'ca',
        'central african republic': 'cf', 'chad': 'td', 'chile': 'cl', 'china': 'cn',
        'colombia': 'co', 'comoros': 'km', 'congo': 'cg', 'costa rica': 'cr', 'croatia': 'hr',
        'cuba': 'cu', 'cyprus': 'cy', 'czech republic': 'cz', 'czechia': 'cz',
        "côte d'ivoire": 'ci', 'democratic republic of the congo': 'cd', 'denmark': 'dk',
        'djibouti': 'dj', 'dominica': 'dm', 'dominican republic': 'do', 'ecuador': 'ec',
        'egypt': 'eg', 'el salvador': 'sv', 'equatorial guinea': 'gq', 'eritrea': 'er',
        'estonia': 'ee', 'eswatini': 'sz', 'ethiopia': 'et', 'fiji': 'fj', 'finland': 'fi',
        'france': 'fr', 'gabon': 'ga', 'gambia': 'gm', 'georgia': 'ge', 'germany': 'de',
        'ghana': 'gh', 'greece': 'gr', 'grenada': 'gd', 'guatemala': 'gt', 'guinea': 'gn',
        'guinea-bissau': 'gw', 'guyana': 'gy', 'haiti': 'ht', 'honduras': 'hn', 'hungary': 'hu',
        'iceland': 'is', 'india': 'in', 'indonesia': 'id', 'iran': 'ir', 'iraq': 'iq',
        'ireland': 'ie', 'israel': 'il', 'italy': 'it', 'jamaica': 'jm', 'japan': 'jp',
        'jordan': 'jo', 'kazakhstan': 'kz', 'kenya': 'ke', 'kiribati': 'ki', 'kuwait': 'kw',
        'kyrgyzstan': 'kg', 'laos': 'la', 'latvia': 'lv', 'lebanon': 'lb', 'lesotho': 'ls',
        'liberia': 'lr', 'libya': 'ly', 'liechtenstein': 'li', 'lithuania': 'lt', 'luxembourg': 'lu',
        'madagascar': 'mg', 'malawi': 'mw', 'malaysia': 'my', 'maldives': 'mv', 'mali': 'ml',
        'malta': 'mt', 'marshall islands': 'mh', 'mauritania': 'mr', 'mauritius': 'mu',
        'mexico': 'mx', 'micronesia': 'fm', 'moldova': 'md', 'monaco': 'mc', 'mongolia': 'mn',
        'montenegro': 'me', 'morocco': 'ma', 'mozambique': 'mz', 'myanmar': 'mm', 'namibia': 'na',
        'nauru': 'nr', 'nepal': 'np', 'netherlands': 'nl', 'new zealand': 'nz', 'nicaragua': 'ni',
        'niger': 'ne', 'nigeria': 'ng', 'north korea': 'kp', 'north macedonia': 'mk', 'norway': 'no',
        'oman': 'om', 'pakistan': 'pk', 'palau': 'pw', 'palestine': 'ps', 'panama': 'pa',
        'papua new guinea': 'pg', 'paraguay': 'py', 'peru': 'pe', 'philippines': 'ph', 'poland': 'pl',
        'portugal': 'pt', 'qatar': 'qa', 'romania': 'ro', 'russia': 'ru', 'rwanda': 'rw',
        'saint kitts and nevis': 'kn', 'saint lucia': 'lc', 'saint vincent and the grenadines': 'vc',
        'samoa': 'ws', 'san marino': 'sm', 'sao tome and principe': 'st', 'saudi arabia': 'sa',
        'senegal': 'sn', 'serbia': 'rs', 'seychelles': 'sc', 'sierra leone': 'sl', 'singapore': 'sg',
        'slovakia': 'sk', 'slovenia': 'si', 'solomon islands': 'sb', 'somalia': 'so',
        'south africa': 'za', 'south korea': 'kr', 'south sudan': 'ss', 'spain': 'es',
        'sri lanka': 'lk', 'sudan': 'sd', 'suriname': 'sr', 'sweden': 'se', 'switzerland': 'ch',
        'syria': 'sy', 'taiwan': 'tw', 'tajikistan': 'tj', 'tanzania': 'tz', 'thailand': 'th',
        'timor-leste': 'tl', 'togo': 'tg', 'tonga': 'to', 'trinidad and tobago': 'tt', 'tunisia': 'tn',
        'turkey': 'tr', 'turkmenistan': 'tm', 'tuvalu': 'tv', 'uganda': 'ug', 'ukraine': 'ua',
        'united arab emirates': 'ae', 'united kingdom': 'gb', 'united states': 'us', 'uruguay': 'uy',
        'uzbekistan': 'uz', 'vanuatu': 'vu', 'vatican city': 'va', 'venezuela': 've', 'vietnam': 'vn',
        'yemen': 'ye', 'zambia': 'zm', 'zimbabwe': 'zw'
    }
    
    return country_codes.get(country_name.lower(), 'zz')

def calculate_age(born):
    """
    Calculate age from a date of birth.
    
    Args:
        born: A date object representing the date of birth
        
    Returns:
        int: The calculated age
    """
    if not born:
        return None
        
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def save_profile_picture(file, user_id):
    """
    Save uploaded profile picture and return the relative path.
    
    Args:
        file: The uploaded file object
        user_id: ID of the user (used in the filename)
        
    Returns:
        str: Relative path to the saved profile picture
    """
    if not file or not file.filename:
        return None
        
    # Create uploads directory if it doesn't exist
    upload_folder = os.path.join('static', 'uploads', 'profile_pictures')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Get file extension and create a secure filename
    _, ext = os.path.splitext(file.filename)
    filename = f"user_{user_id}{ext}"
    filepath = os.path.join(upload_folder, filename)
    
    try:
        # Save the file
        file.save(filepath)
    except Exception as e:
        print(f"Error saving profile picture: {e}")
        return None
        
    # Return relative path from static folder
    return os.path.join('uploads', 'profile_pictures', filename)

def delete_old_profile_picture(profile_picture):
    """
    Delete old profile picture if it exists and is not the default one.
    
    Args:
        profile_picture: Relative path to the profile picture
    """
    if not profile_picture or 'default' in profile_picture:
        return
        
    try:
        # Build full path to the file
        filepath = os.path.join('static', profile_picture)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting old profile picture: {e}")
