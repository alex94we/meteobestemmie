import time
import sys
import datetime
import argparse
import os

# Import our custom modules
import weather_scraper
import historical_weather
import report_generator
import notifier

def run_update():
    """
    Orchestrates a single update run:
    1. Scrapes 3BMeteo for the 7-day forecast.
    2. Resolves historical averages from Open-Meteo.
    3. Generates the interactive HTML dashboard.
    4. Calculates dynamic statistics for the toast notification.
    5. Sends the toast notification.
    """
    print(f"\n--- Starting weather update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # 1. Scrape 3BMeteo for the 7-day forecast
    weekly_forecast = weather_scraper.scrape_full_week()
    if not weekly_forecast:
        print("Failed to scrape forecast from 3BMeteo. Aborting this run.")
        return False
        
    # 2. Get forecast dates (Days 1 to 7 correspond to tomorrow onwards)
    today = datetime.date.today()
    forecast_dates = [today + datetime.timedelta(days=i) for i in range(1, 8)]
    
    # 3. Get historical averages (automatically uses local cache first)
    historical_averages = historical_weather.get_weekly_historical_averages(forecast_dates)
    if not historical_averages:
        print("Failed to retrieve historical averages. Aborting this run.")
        return False
        
    # 4. Generate the HTML report dashboard.html
    html_path = report_generator.generate_report(weekly_forecast, historical_averages, forecast_dates)
    if not html_path:
        print("Failed to generate dashboard report. Aborting this run.")
        return False
        
    # 5. Compute statistics for Tomorrow (Day 1, index 0) to display in the notification
    tomorrow_forecast_max_sum = 0
    tomorrow_hist_max_sum = 0
    valid_cities = 0
    
    max_delta_val = -999.0
    max_delta_city = ""
    
    for slug, city_data in weekly_forecast.items():
        # Day 1 forecast (tomorrow)
        f_day = city_data["forecasts"][0]
        hist_days = historical_averages.get(slug, [])
        h_day = hist_days[0] if hist_days else None
        
        if f_day and h_day and f_day["max_temp"] is not None and h_day["max_avg"] is not None:
            f_max = f_day["max_temp"]
            h_max = h_day["max_avg"]
            delta = f_max - h_max
            
            tomorrow_forecast_max_sum += f_max
            tomorrow_hist_max_sum += h_max
            valid_cities += 1
            
            if delta > max_delta_val:
                max_delta_val = delta
                max_delta_city = city_data["city"]
                
    if valid_cities > 0:
        avg_f_max = tomorrow_forecast_max_sum / valid_cities
        avg_h_max = tomorrow_hist_max_sum / valid_cities
        avg_delta = avg_f_max - avg_h_max
        
        # Format the notification text
        delta_symbol = "+" if avg_delta > 0 else ""
        delta_trend_emoji = "📈" if avg_delta > 0.5 else ("❄️" if avg_delta < -0.5 else "🌤️")
        
        title = "Meteo Italia: Tendenze Settimana 🌤️"
        line1 = f"Domani: media max {avg_f_max:.1f}°C ({delta_symbol}{avg_delta:.1f}°C vs. media storica {delta_trend_emoji})"
        
        if avg_delta > 0.5:
            line2 = f"Più caldo del solito. Picco a {max_delta_city} (+{max_delta_val:.1f}°C). Clicca per il report."
        elif avg_delta < -0.5:
            line2 = f"Più fresco del solito. Picco freddo a {max_delta_city} ({max_delta_val:.1f}°C). Clicca per il report."
        else:
            line2 = "In linea con le medie storiche. Clicca per l'analisi dettagliata."
    else:
        # Fallback text
        title = "Meteo Italia: Report Aggiornato 🌤️"
        line1 = "L'analisi delle temperature della settimana è pronta."
        line2 = "Clicca per visualizzare il report dettagliato."
        
    # 6. Send Notifications based on execution environment
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"
    
    if is_github_actions:
        # Running in GitHub Actions: send ONLY push notification with GitHub Pages URL
        click_url = "https://alex94we.github.io/meteobestemmie/"
        notifier.send_push_notification(title, line1, line2, click_url)
    else:
        # Running locally: send Windows Toast Notification
        notifier.send_notification(title, line1, line2, html_path)
        # Also send a test push notification with the eventual GitHub Pages URL
        click_url = "https://alex94we.github.io/meteobestemmie/"
        notifier.send_push_notification(title, line1, line2, click_url)
        
    print("Update cycle completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Weather Monitor & Historical Comparison Daemon")
    parser.add_argument("--once", action="store_true", help="Run once and exit immediately (no background loop)")
    parser.add_argument("--interval", type=float, default=12.0, help="Check interval in hours (default: 12.0)")
    args = parser.parse_args()
    
    # Write a pid file so that we can easily stop the background process if needed
    pid = os.getpid()
    try:
        with open("weather_monitor.pid", "w") as f:
            f.write(str(pid))
        print(f"Weather Monitor running with PID: {pid}")
    except Exception as e:
        print(f"Warning: Could not write PID file: {e}")
        
    if args.once:
        run_update()
        # Clean up PID file on exit
        if os.path.exists("weather_monitor.pid"):
            try: os.remove("weather_monitor.pid")
            except Exception: pass
        sys.exit(0)
        
    # Daemon loop mode
    interval_seconds = int(args.interval * 3600)
    print(f"Starting in background daemon mode. Update interval: {args.interval} hours ({interval_seconds} seconds).")
    
    # Run once immediately upon startup
    run_update()
    
    try:
        while True:
            print(f"Sleeping for {args.interval} hours... (Press Ctrl+C to exit if running interactively)")
            time.sleep(interval_seconds)
            run_update()
    except KeyboardInterrupt:
        print("\nDaemon stopped by user.")
    finally:
        # Clean up PID file on exit
        if os.path.exists("weather_monitor.pid"):
            try: os.remove("weather_monitor.pid")
            except Exception: pass
        print("Exit.")

if __name__ == '__main__':
    main()
