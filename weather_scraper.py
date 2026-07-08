import urllib.request
import urllib.error
import re
import json
from html.parser import HTMLParser

TARGET_SLUGS = {
    'ancona', 'aosta', 'bari', 'bologna', 'cagliari', 'campobasso',
    'catanzaro', 'firenze', 'genova', 'laquila', 'milano', 'napoli',
    'palermo', 'perugia', 'potenza', 'roma', 'torino', 'trento',
    'trieste', 'venezia'
}

class MeteoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = None
        self.capture_city = False
        self.capture_temp = False

    def _save_current_row(self):
        if self.current_row is not None and self.current_row['city']:
            temp_str = self.current_row['temp_text'].strip()
            temp_str = temp_str.replace('\xa0', ' ').replace('&nbsp;', ' ')
            
            # Robustly extract any numbers (integers or floats)
            nums = re.findall(r'[-+]?\d*\.\d+|\d+', temp_str)
            if len(nums) >= 2:
                try:
                    self.current_row['min_temp'] = float(nums[0])
                    self.current_row['max_temp'] = float(nums[1])
                except ValueError:
                    self.current_row['min_temp'] = None
                    self.current_row['max_temp'] = None
            else:
                self.current_row['min_temp'] = None
                self.current_row['max_temp'] = None
                
            self.current_row['city'] = self.current_row['city'].strip()
            self.rows.append(self.current_row)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Check if we started a data row
        if tag == 'div' and 'table-row--data' in attrs_dict.get('class', ''):
            self.current_row = {
                'city': None,
                'slug': None,
                'icon': None,
                'alt': None,
                'temp_text': ''
            }
            
        if self.current_row is not None:
            # Look for city link
            if tag == 'a':
                href = attrs_dict.get('href', '')
                if href.startswith('/meteo/'):
                    slug = href.split('/')[-1]
                    if slug in TARGET_SLUGS:
                        self.current_row['slug'] = slug
                        self.capture_city = True
            # Look for weather icon image
            elif tag == 'img':
                src = attrs_dict.get('src', '')
                if 'icone' in src or 'set_icone' in src:
                    self.current_row['icon'] = src
                    self.current_row['alt'] = attrs_dict.get('alt', '')
            # Look for temperature text inside ds-body-medium
            elif tag == 'div' and 'ds-body-medium' in attrs_dict.get('class', ''):
                if self.current_row['city'] is not None:
                    self.capture_temp = True

    def handle_endtag(self, tag):
        if self.current_row is not None:
            if tag == 'a' and self.capture_city:
                self.capture_city = False
            elif tag == 'div' and self.capture_temp:
                self.capture_temp = False
                # Once we exit the temperature div, we have all data for this row!
                self._save_current_row()
                self.current_row = None

    def handle_data(self, data):
        if self.current_row is not None:
            if self.capture_city:
                if self.current_row['city'] is None:
                    self.current_row['city'] = data
                else:
                    self.current_row['city'] += data
            elif self.capture_temp:
                self.current_row['temp_text'] += data

def scrape_day(day_num):
    """
    Scrapes the 3bmeteo temperature table for a given day (1 to 7).
    Returns a list of dicts with city, slug, icon, alt, min_temp, max_temp.
    """
    url = f"https://www.3bmeteo.com/meteo/italia/temperature/{day_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8')
            
        parser = MeteoHTMLParser()
        parser.feed(html_content)
        parser.close()
        return parser.rows
    except urllib.error.URLError as e:
        print(f"Error fetching day {day_num} from 3bmeteo: {e}")
        return []
    except Exception as e:
        print(f"Error parsing day {day_num}: {e}")
        return []

def scrape_full_week():
    """
    Scrapes days 1 to 7 and structures the data by city and day.
    Returns:
        dict: A dictionary mapping city slugs to their forecast list (7 days)
    """
    weekly_forecast = {}
    
    for day in range(1, 8):
        print(f"Scraping day {day}/7 from 3bmeteo...")
        day_data = scrape_day(day)
        
        for row in day_data:
            slug = row['slug']
            if not slug or slug not in TARGET_SLUGS:
                continue
                
            if slug not in weekly_forecast:
                weekly_forecast[slug] = {
                    'city': row['city'],
                    'slug': slug,
                    'forecasts': [None] * 7  # 7 days, 0-indexed
                }
            
            # Save forecast info for this specific day
            weekly_forecast[slug]['forecasts'][day - 1] = {
                'day': day,
                'min_temp': row['min_temp'],
                'max_temp': row['max_temp'],
                'icon': row['icon'],
                'alt': row['alt']
            }
            
    return weekly_forecast

if __name__ == '__main__':
    print("Testing 3bmeteo Scraping...")
    results = scrape_day(1)
    print(f"Found {len(results)} cities.")
    if results:
        print("First city:", results[0])
        print("Last city:", results[-1])
    
    print("\nTesting full week structure...")
    full_week = scrape_full_week()
    print(f"Scraped {len(full_week)} unique cities.")
    sample_key = 'roma' if 'roma' in full_week else (list(full_week.keys())[0] if full_week else None)
    if sample_key:
        print(f"Sample city forecast details ({sample_key}):", full_week[sample_key])
