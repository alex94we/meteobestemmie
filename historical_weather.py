import urllib.request
import urllib.error
import json
import os
import datetime
import time

# Ordered list of the 20 regional capitals in Italy with their GPS coordinates.
# Order is preserved for matching multi-coordinate API requests.
CAPITALS = [
    {"slug": "ancona", "name": "Ancona", "lat": 43.6167, "lon": 13.5167},
    {"slug": "aosta", "name": "Aosta", "lat": 45.7333, "lon": 7.3333},
    {"slug": "bari", "name": "Bari", "lat": 41.1172, "lon": 16.8719},
    {"slug": "bologna", "name": "Bologna", "lat": 44.4949, "lon": 11.3426},
    {"slug": "cagliari", "name": "Cagliari", "lat": 39.2278, "lon": 9.1111},
    {"slug": "campobasso", "name": "Campobasso", "lat": 41.5610, "lon": 14.6684},
    {"slug": "catanzaro", "name": "Catanzaro", "lat": 38.9056, "lon": 16.5944},
    {"slug": "firenze", "name": "Firenze", "lat": 43.7696, "lon": 11.2558},
    {"slug": "genova", "name": "Genova", "lat": 44.4056, "lon": 8.9463},
    {"slug": "laquila", "name": "L'Aquila", "lat": 42.3540, "lon": 13.3972},
    {"slug": "milano", "name": "Milano", "lat": 45.4642, "lon": 9.1900},
    {"slug": "napoli", "name": "Napoli", "lat": 40.8518, "lon": 14.2681},
    {"slug": "palermo", "name": "Palermo", "lat": 38.1157, "lon": 13.3614},
    {"slug": "perugia", "name": "Perugia", "lat": 43.1107, "lon": 12.3908},
    {"slug": "potenza", "name": "Potenza", "lat": 40.6384, "lon": 15.8019},
    {"slug": "roma", "name": "Roma", "lat": 41.8919, "lon": 12.5113},
    {"slug": "torino", "name": "Torino", "lat": 45.0703, "lon": 7.6869},
    {"slug": "trento", "name": "Trento", "lat": 46.0678, "lon": 11.1211},
    {"slug": "trieste", "name": "Trieste", "lat": 45.6495, "lon": 13.7768},
    {"slug": "venezia", "name": "Venezia", "lat": 45.4408, "lon": 12.3155}
]

CACHE_FILE = "historical_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading cache file, starting fresh: {e}")
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving cache file: {e}")

def get_historical_date(target_date, year_offset):
    """
    Returns the target date shifted back by year_offset years.
    Handles leap year edge cases (Feb 29).
    """
    target_year = target_date.year - year_offset
    try:
        return target_date.replace(year=target_year)
    except ValueError:
        # Fallback for Feb 29 in non-leap years
        return target_date.replace(year=target_year, day=28)

def fetch_from_open_meteo(date_str):
    """
    Fetches temperature data for all 20 capitals for a single date_str (YYYY-MM-DD).
    Returns list of dicts with min and max temp.
    """
    lats = ",".join(str(c["lat"]) for c in CAPITALS)
    lons = ",".join(str(c["lon"]) for c in CAPITALS)
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lats}&longitude={lons}"
        f"&start_date={date_str}&end_date={date_str}"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&timezone=Europe/Rome"
    )
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        print(f"API Request to Open-Meteo for date: {date_str}...")
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        # Open-Meteo returns a list of dictionaries if multiple coordinates are requested.
        results = []
        for item in data:
            daily = item.get("daily", {})
            max_temps = daily.get("temperature_2m_max", [None])
            min_temps = daily.get("temperature_2m_min", [None])
            results.append({
                "min": min_temps[0] if min_temps else None,
                "max": max_temps[0] if max_temps else None
            })
        return results
    except Exception as e:
        print(f"Error fetching historical data from Open-Meteo for {date_str}: {e}")
        # Sleep briefly to avoid hammering on errors
        time.sleep(2)
        return None

def resolve_historical_data(forecast_dates):
    """
    Ensures the cache contains all historical dates for the last 5 years
    corresponding to the 7 forecast dates.
    Returns:
        dict: A dictionary mapping city slug -> date_str -> {'min': float, 'max': float}
    """
    cache = load_cache()
    
    # Identify which historical dates (YYYY-MM-DD) are missing from the cache
    missing_dates = set()
    years = [1, 2, 3, 4, 5]  # last 5 years
    
    for f_date in forecast_dates:
        for y_offset in years:
            h_date = get_historical_date(f_date, y_offset)
            h_date_str = h_date.strftime("%Y-%m-%d")
            
            # Check if any capital is missing this historical date in cache
            is_missing = False
            for cap in CAPITALS:
                slug = cap["slug"]
                if slug not in cache or h_date_str not in cache[slug]:
                    is_missing = True
                    break
            
            if is_missing:
                missing_dates.add(h_date_str)
                
    if missing_dates:
        print(f"Found {len(missing_dates)} missing historical dates in cache. Fetching...")
        # Fetch each missing date
        # Open-Meteo archive API has a rate limit of 10k/day, so fetching days sequentially is perfectly fine
        for m_date_str in sorted(missing_dates):
            results = fetch_from_open_meteo(m_date_str)
            if results and len(results) == len(CAPITALS):
                # Update cache
                for idx, cap in enumerate(CAPITALS):
                    slug = cap["slug"]
                    if slug not in cache:
                        cache[slug] = {}
                    cache[slug][m_date_str] = results[idx]
                save_cache(cache)
                # Sleep to respect API rate limiting guidelines
                time.sleep(1.0)
            else:
                print(f"Skipping update for date {m_date_str} due to error.")
    else:
        print("All historical dates are already cached!")
        
    return cache

def get_weekly_historical_averages(forecast_dates):
    """
    Computes the 5-year historical average for each day of the forecast week.
    Returns:
        dict: mapping city slug -> list of 7 daily average dicts {'min_avg': float, 'max_avg': float}
    """
    # First, make sure all historical data is in the cache
    cache = resolve_historical_data(forecast_dates)
    
    weekly_averages = {}
    years = [1, 2, 3, 4, 5]
    
    for cap in CAPITALS:
        slug = cap["slug"]
        weekly_averages[slug] = []
        
        for f_date in forecast_dates:
            min_vals = []
            max_vals = []
            
            for y_offset in years:
                h_date = get_historical_date(f_date, y_offset)
                h_date_str = h_date.strftime("%Y-%m-%d")
                
                # Retrieve from cache
                val = cache.get(slug, {}).get(h_date_str, {})
                if val.get("min") is not None:
                    min_vals.append(val["min"])
                if val.get("max") is not None:
                    max_vals.append(val["max"])
            
            # Compute averages
            min_avg = sum(min_vals) / len(min_vals) if min_vals else None
            max_avg = sum(max_vals) / len(max_vals) if max_vals else None
            
            weekly_averages[slug].append({
                "date": f_date.strftime("%Y-%m-%d"),
                "min_avg": round(min_avg, 1) if min_avg is not None else None,
                "max_avg": round(max_avg, 1) if max_avg is not None else None,
                "data_points": len(min_vals)
            })
            
    return weekly_averages

if __name__ == '__main__':
    # Test execution
    print("Testing Historical Weather cache and API...")
    # Simulate a 7-day forecast week starting tomorrow
    today = datetime.date.today()
    test_dates = [today + datetime.timedelta(days=i) for i in range(1, 8)]
    
    print("Test dates:")
    for d in test_dates:
        print("  -", d)
        
    start_time = time.time()
    averages = get_weekly_historical_averages(test_dates)
    end_time = time.time()
    
    print(f"\nResolved averages in {end_time - start_time:.2f} seconds.")
    print("Sample city (roma) historical averages:")
    for day_idx, avg in enumerate(averages["roma"]):
        print(f"  Day {day_idx+1} ({avg['date']}): Min Avg: {avg['min_avg']}°C, Max Avg: {avg['max_avg']}°C (Based on {avg['data_points']} years)")
