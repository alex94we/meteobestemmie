import os
import json
import datetime

# Italian weekday names
WEEKDAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

def get_day_name(date_str):
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return WEEKDAYS[dt.weekday()], dt.strftime("%d/%m")
    except Exception:
        return "Giorno", ""

def generate_report(weekly_forecast, historical_averages, forecast_dates):
    """
    Combines scraped forecasts and historical averages, then generates a beautiful
    interactive HTML dashboard (dashboard.html) in the current directory.
    """
    # Structure combined data
    combined_data = []
    
    # Sort cities alphabetically
    sorted_slugs = sorted(weekly_forecast.keys())
    
    for slug in sorted_slugs:
        forecast_info = weekly_forecast[slug]
        hist_info = historical_averages.get(slug, [])
        
        city_entry = {
            "city": forecast_info["city"],
            "slug": slug,
            "days": []
        }
        
        for idx, date_obj in enumerate(forecast_dates):
            date_str = date_obj.strftime("%Y-%m-%d")
            
            # Forecast details
            f_day = forecast_info["forecasts"][idx]
            if f_day:
                f_min = f_day["min_temp"]
                f_max = f_day["max_temp"]
                icon = f_day["icon"]
                alt = f_day["alt"]
            else:
                f_min = f_max = None
                icon = alt = None
                
            # Historical details
            h_day = hist_info[idx] if idx < len(hist_info) else {}
            h_min = h_day.get("min_avg")
            h_max = h_day.get("max_avg")
            
            # Calculate deltas
            min_delta = round(f_min - h_min, 1) if f_min is not None and h_min is not None else None
            max_delta = round(f_max - h_max, 1) if f_max is not None and h_max is not None else None
            
            # Get weekday name
            day_name, day_label = get_day_name(date_str)
            
            city_entry["days"].append({
                "index": idx,
                "date": date_str,
                "day_name": day_name,
                "day_label": day_label,
                "forecast": {
                    "min": f_min,
                    "max": f_max,
                    "icon": icon,
                    "alt": alt
                },
                "historical": {
                    "min": h_min,
                    "max": h_max
                },
                "deltas": {
                    "min_diff": min_delta,
                    "max_diff": max_delta
                }
            })
            
        combined_data.append(city_entry)

    # Calculate global/weekly summary stats to bake into the script
    # We will build dates labels for tabs
    tab_labels = []
    for idx, date_obj in enumerate(forecast_dates):
        name, label = get_day_name(date_obj.strftime("%Y-%m-%d"))
        # Mark tomorrow
        if idx == 0:
            name = "Domani"
        tab_labels.append({"index": idx, "name": name, "label": label})

    # Read base HTML template and replace placeholders
    html_content = get_html_template(combined_data, tab_labels)
    
    output_path = "index.html"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Beautiful dashboard generated successfully at: {os.path.abspath(output_path)}")
        return os.path.abspath(output_path)
    except Exception as e:
        print(f"Error generating dashboard HTML: {e}")
        return None

def get_html_template(data, tabs):
    # Serialize data to JSON for embedding in the HTML script
    data_json = json.dumps(data, ensure_ascii=False)
    tabs_json = json.dumps(tabs, ensure_ascii=False)
    generation_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi Temperature Italia - 3BMeteo vs Storico</title>
    <!-- Google Fonts Outfit -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0c0a1c;
            --card-bg: rgba(22, 20, 38, 0.45);
            --card-border: rgba(255, 255, 255, 0.08);
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent-gradient: linear-gradient(135deg, #6366f1, #a855f7);
            --accent-solid: #8b5cf6;
            --color-hot: #f43f5e;
            --color-cold: #3b82f6;
            --color-normal: #10b981;
            --glow-color: rgba(139, 92, 246, 0.15);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Outfit', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}

        body {{
            background: linear-gradient(135deg, #090714 0%, #0e0b20 50%, #04030a 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2.5rem 1.5rem;
            overflow-x: hidden;
        }}

        /* Background animated blobs */
        .bg-blob {{
            position: fixed;
            border-radius: 50%;
            filter: blur(100px);
            z-index: -1;
            opacity: 0.3;
            animation: float 20s infinite alternate;
        }}
        .bg-blob-1 {{
            width: 400px;
            height: 400px;
            background: #6366f1;
            top: -100px;
            right: -50px;
        }}
        .bg-blob-2 {{
            width: 500px;
            height: 500px;
            background: #a855f7;
            bottom: -150px;
            left: -100px;
        }}
        @keyframes float {{
            0% {{ transform: translate(0, 0) scale(1); }}
            100% {{ transform: translate(80px, 50px) scale(1.15); }}
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Header section */
        header {{
            margin-bottom: 2.5rem;
            animation: fadeInDown 0.6s ease forwards;
        }}
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .header-title-group {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 1.5rem;
        }}
        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 30%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1rem;
            margin-top: 0.25rem;
        }}
        .meta-info {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.5rem 0.8rem;
            border-radius: 30px;
            backdrop-filter: blur(10px);
        }}

        /* Summary Stats Cards */
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
            animation: fadeInUp 0.6s ease 0.1s forwards;
            opacity: 0;
        }}
        .stat-card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            transition: all 0.3s ease;
        }}
        .stat-card:hover {{
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }}
        .stat-title {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .stat-value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}
        .stat-value.delta-hot {{ color: var(--color-hot); }}
        .stat-value.delta-cold {{ color: var(--color-cold); }}
        .stat-value.delta-normal {{ color: var(--color-normal); }}
        .stat-desc {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        /* Navigation & Search toolbar */
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 2rem;
            animation: fadeInUp 0.6s ease 0.2s forwards;
            opacity: 0;
        }}
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Tabs Container */
        .tabs-container {{
            display: flex;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0.35rem;
            border-radius: 30px;
            backdrop-filter: blur(10px);
            overflow-x: auto;
            max-width: 100%;
        }}
        .tab-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 0.6rem 1.2rem;
            border-radius: 20px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.25s ease;
            white-space: nowrap;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.1rem;
        }}
        .tab-btn span.tab-date {{
            font-size: 0.7rem;
            opacity: 0.7;
        }}
        .tab-btn:hover {{
            color: var(--text-primary);
        }}
        .tab-btn.active {{
            background: var(--accent-gradient);
            color: white;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        }}

        /* Search input wrapper */
        .search-wrapper {{
            position: relative;
            min-width: 250px;
        }}
        .search-input {{
            width: 100%;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 30px;
            padding: 0.75rem 1.25rem;
            padding-left: 2.75rem;
            color: var(--text-primary);
            font-size: 0.95rem;
            outline: none;
            transition: all 0.3s ease;
        }}
        .search-input:focus {{
            border-color: var(--accent-solid);
            background: rgba(255, 255, 255, 0.07);
            box-shadow: 0 0 15px rgba(139, 92, 246, 0.1);
        }}
        .search-icon {{
            position: absolute;
            left: 1.1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            pointer-events: none;
            width: 16px;
            height: 16px;
        }}

        /* Grid */
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
            animation: fadeInUp 0.6s ease 0.3s forwards;
            opacity: 0;
        }}

        /* City Card */
        .city-card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        .city-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: transparent;
            transition: background 0.3s ease;
        }}
        .city-card.card-hot::before {{
            background: linear-gradient(90deg, var(--color-hot), transparent);
        }}
        .city-card.card-cold::before {{
            background: linear-gradient(90deg, var(--color-cold), transparent);
        }}
        .city-card:hover {{
            transform: translateY(-6px);
            border-color: rgba(255, 255, 255, 0.15);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3), 0 0 15px var(--glow-color);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.25rem;
        }}
        .card-title-group {{
            display: flex;
            flex-direction: column;
        }}
        .city-name {{
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.3px;
        }}
        .weather-desc {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 0.15rem;
            text-transform: capitalize;
        }}

        .weather-icon-container {{
            width: 44px;
            height: 44px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .weather-icon-container img {{
            width: 36px;
            height: 36px;
            object-fit: contain;
        }}

        /* Temps layout */
        .temp-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin-bottom: 1.25rem;
        }}
        .temp-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.25rem;
        }}
        .temp-val {{
            font-size: 1.25rem;
            font-weight: 600;
            display: flex;
            align-items: baseline;
            gap: 0.15rem;
        }}
        .temp-val span.unit {{
            font-size: 0.85rem;
            font-weight: 400;
            opacity: 0.8;
        }}
        .temp-subval {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.15rem;
        }}

        /* Delta tags */
        .delta-badge-container {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.25rem;
        }}
        .delta-badge {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.25rem;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.4rem 0.6rem;
            border-radius: 8px;
            border: 1px solid transparent;
        }}
        .delta-badge.badge-hot {{
            background: rgba(244, 63, 94, 0.1);
            color: var(--color-hot);
            border-color: rgba(244, 63, 94, 0.15);
        }}
        .delta-badge.badge-cold {{
            background: rgba(59, 130, 246, 0.1);
            color: var(--color-cold);
            border-color: rgba(59, 130, 246, 0.15);
        }}
        .delta-badge.badge-normal {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--color-normal);
            border-color: rgba(16, 185, 129, 0.15);
        }}

        /* Visual Slider Bar comparison */
        .visual-bar-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 0.35rem;
        }}
        .visual-bar-container {{
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
            position: relative;
            overflow: visible;
        }}
        .historical-bar {{
            position: absolute;
            height: 10px;
            background: rgba(255, 255, 255, 0.12);
            border-radius: 5px;
            z-index: 1;
        }}
        .forecast-bar {{
            position: absolute;
            height: 6px;
            top: 2px;
            border-radius: 3px;
            z-index: 2;
        }}
        .forecast-bar.bar-hot {{
            background: linear-gradient(90deg, #f59e0b, var(--color-hot));
        }}
        .forecast-bar.bar-cold {{
            background: linear-gradient(90deg, var(--color-cold), #06b6d4);
        }}
        .forecast-bar.bar-normal {{
            background: linear-gradient(90deg, #10b981, #84cc16);
        }}
        /* Tooltip style */
        .bar-tooltip {{
            position: absolute;
            background: #1e1b4b;
            border: 1px solid rgba(255, 255, 255, 0.15);
            font-size: 0.7rem;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            bottom: 14px;
            left: 50%;
            transform: translateX(-50%);
            white-space: nowrap;
            display: none;
            z-index: 10;
        }}
        .visual-bar-container:hover .bar-tooltip {{
            display: block;
        }}

        /* Card overlay for creative weather complaints */
        .card-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 8, 22, 0.96);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            z-index: 10;
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 20px;
            transform: scale(0.95);
        }}
        .card-overlay.active {{
            opacity: 1;
            pointer-events: auto;
            transform: scale(1);
        }}
        .overlay-text {{
            font-size: 1.15rem;
            font-weight: 700;
            text-align: center;
            color: #f3f4f6;
            line-height: 1.5;
            background: linear-gradient(135deg, #f43f5e 30%, #fb7185 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 4px 12px rgba(244, 63, 94, 0.15);
        }}
        .overlay-close {{
            position: absolute;
            top: 0.75rem;
            right: 0.75rem;
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-secondary);
            cursor: pointer;
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.2s ease;
        }}
        .overlay-close:hover {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
        }}

        /* Empty state */
        .empty-state {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-secondary);
            background: var(--card-bg);
            border: 1px dashed rgba(255, 255, 255, 0.1);
            border-radius: 20px;
        }}
        .empty-state h3 {{
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }}

        /* Footer */
        footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        /* Responsive adjustments */
        @media(max-width: 768px) {{
            body {{
                padding: 1.5rem 1rem;
            }}
            .header-title-group {{
                flex-direction: column;
                align-items: flex-start;
            }}
            h1 {{
                font-size: 1.8rem;
            }}
            .toolbar {{
                flex-direction: column;
                align-items: stretch;
            }}
            .search-wrapper {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="bg-blob bg-blob-1"></div>
    <div class="bg-blob bg-blob-2"></div>

    <div class="container">
        <header>
            <div class="header-title-group">
                <div>
                    <h1>Temperature Italia: Analisi e Deviazioni</h1>
                    <div class="subtitle">Scraping da 3BMeteo vs. Media Storica 5 anni (Open-Meteo Archive API)</div>
                </div>
                <div class="meta-info">Generato il: {generation_time}</div>
            </div>
        </header>

        <!-- Summary Statistics Header Panel -->
        <section class="summary-stats" id="summary-panel">
            <!-- Populated via Javascript -->
        </section>

        <!-- Search and Date Filter Toolbar -->
        <div class="toolbar">
            <div class="tabs-container" id="tabs-container">
                <!-- Day Tabs populated via Javascript -->
            </div>
            
            <div class="search-wrapper">
                <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input type="text" id="search-input" class="search-input" placeholder="Cerca città..." oninput="handleSearch(this.value)">
            </div>
        </div>

        <!-- Cards Grid -->
        <main class="grid-container" id="cards-grid">
            <!-- Populated via Javascript -->
        </main>

        <footer>
            Weather Scraper & Comparison Daemon &bull; Basato su dati storici ed elaborazioni 3BMeteo
        </footer>
    </div>

    <script>
        // Data injected from Python
        const weatherData = {data_json};
        const tabList = {tabs_json};

        let currentDayIdx = 0;
        let searchQuery = "";

        // Temperature absolute bounds for rendering visual horizontal bar (e.g. 10C to 45C)
        const scaleMin = 10;
        const scaleMax = 45;

        // Initialize Page
        window.addEventListener('DOMContentLoaded', () => {{
            renderTabs();
            renderDashboard();
        }});

        function renderTabs() {{
            const tabsContainer = document.getElementById('tabs-container');
            tabsContainer.innerHTML = '';
            
            tabList.forEach((tab, index) => {{
                const btn = document.createElement('button');
                btn.className = `tab-btn ${{index === currentDayIdx ? 'active' : ''}}`;
                btn.onclick = () => selectDay(index);
                
                btn.innerHTML = `
                    <span>${{tab.name}}</span>
                    <span class="tab-date">${{tab.label}}</span>
                `;
                tabsContainer.appendChild(btn);
            }});
        }}

        function selectDay(index) {{
            currentDayIdx = index;
            document.querySelectorAll('.tab-btn').forEach((btn, i) => {{
                if (i === index) btn.classList.add('active');
                else btn.classList.remove('active');
            }});
            renderDashboard();
        }}

        function handleSearch(val) {{
            searchQuery = val.toLowerCase().trim();
            renderDashboard();
        }}

        function renderDashboard() {{
            renderSummaryStats();
            renderCityGrid();
        }}

        function renderSummaryStats() {{
            const summaryPanel = document.getElementById('summary-panel');
            
            // Gather statistics across all cities for the current day
            let totalMaxForecast = 0;
            let totalMaxHist = 0;
            let maxDeltaVal = -999;
            let maxDeltaCity = "";
            let hottestCity = "";
            let hottestVal = -999;
            let coldestCity = "";
            let coldestVal = 999;
            let validCities = 0;
            
            weatherData.forEach(city => {{
                const dayData = city.days[currentDayIdx];
                if (dayData && dayData.forecast.max !== null && dayData.historical.max !== null) {{
                    const fMax = dayData.forecast.max;
                    const hMax = dayData.historical.max;
                    const delta = dayData.deltas.max_diff;
                    
                    totalMaxForecast += fMax;
                    totalMaxHist += hMax;
                    validCities++;
                    
                    if (delta > maxDeltaVal) {{
                        maxDeltaVal = delta;
                        maxDeltaCity = city.city;
                    }}
                    
                    if (fMax > hottestVal) {{
                        hottestVal = fMax;
                        hottestCity = city.city;
                    }}
                    
                    const fMin = dayData.forecast.min;
                    if (fMin !== null && fMin < coldestVal) {{
                        coldestVal = fMin;
                        coldestCity = city.city;
                    }}
                }}
            }});

            if (validCities === 0) {{
                summaryPanel.innerHTML = '<div class="stat-card" style="grid-column: 1/-1; text-align: center;">Nessun dato disponibile</div>';
                return;
            }}

            const avgMaxForecast = (totalMaxForecast / validCities).toFixed(1);
            const avgMaxHist = (totalMaxHist / validCities).toFixed(1);
            const avgDelta = (avgMaxForecast - avgMaxHist).toFixed(1);
            
            let deltaClass = "delta-normal";
            let deltaSymbol = "";
            let summaryMessage = "In linea con la media storica";
            
            if (avgDelta > 0.5) {{
                deltaClass = "delta-hot";
                deltaSymbol = "+";
                summaryMessage = "Più caldo rispetto al passato 🔥";
            }} else if (avgDelta < -0.5) {{
                deltaClass = "delta-cold";
                deltaSymbol = "";
                summaryMessage = "Più freddo rispetto al passato ❄️";
            }}

            summaryPanel.innerHTML = `
                <div class="stat-card">
                    <span class="stat-title">Deviazione Media Max</span>
                    <span class="stat-value ${{deltaClass}}">${{deltaSymbol}}${{avgDelta}} °C</span>
                    <span class="stat-desc">${{summaryMessage}}</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Temperatura Max Media</span>
                    <span class="stat-value">${{avgMaxForecast}} °C</span>
                    <span class="stat-desc">Storico: ${{avgMaxHist}} °C</span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Picco Anomalie Calde</span>
                    <span class="stat-value delta-hot">+${{maxDeltaVal.toFixed(1)}} °C</span>
                    <span class="stat-desc">Aumento maggiore a: <strong>${{maxDeltaCity}}</strong></span>
                </div>
                <div class="stat-card">
                    <span class="stat-title">Estremi Nazionali</span>
                    <span class="stat-value" style="font-size: 1.4rem; padding: 0.2rem 0;">
                        <span style="color: var(--color-hot);">${{hottestVal}}°</span> / 
                        <span style="color: var(--color-cold);">${{coldestVal}}°</span>
                    </span>
                    <span class="stat-desc">Caldo a <strong>${{hottestCity}}</strong> &bull; Freddo a <strong>${{coldestCity}}</strong></span>
                </div>
            `;
        }}

        function renderCityGrid() {{
            const grid = document.getElementById('cards-grid');
            grid.innerHTML = '';
            
            const filteredData = weatherData.filter(city => 
                city.city.toLowerCase().includes(searchQuery)
            );

            if (filteredData.length === 0) {{
                grid.innerHTML = `
                    <div class="empty-state">
                        <h3>Nessuna città trovata</h3>
                        <p>Nessun capoluogo corrisponde alla ricerca "${{searchQuery}}"</p>
                    </div>
                `;
                return;
            }}

            filteredData.forEach(city => {{
                const dayData = city.days[currentDayIdx];
                if (!dayData) return;
                
                const fMin = dayData.forecast.min;
                const fMax = dayData.forecast.max;
                const hMin = dayData.historical.min;
                const hMax = dayData.historical.max;
                const maxDelta = dayData.deltas.max_diff;
                const alt = dayData.forecast.alt || "Meteo";
                const icon = dayData.forecast.icon || "https://www.3bmeteo.com/images/set_icone/24/1.svg";

                // Determine classification for styles
                let themeClass = "card-normal";
                let badgeClass = "badge-normal";
                let badgeSymbol = "";
                let badgeIcon = "🌤️";
                let barClass = "bar-normal";
                
                if (maxDelta !== null) {{
                    if (maxDelta > 0.5) {{
                        themeClass = "card-hot";
                        badgeClass = "badge-hot";
                        badgeSymbol = "+";
                        badgeIcon = "🔥";
                        barClass = "bar-hot";
                    }} else if (maxDelta < -0.5) {{
                        themeClass = "card-cold";
                        badgeClass = "badge-cold";
                        badgeSymbol = "";
                        badgeIcon = "❄️";
                        barClass = "bar-cold";
                    }}
                }}

                // Calculate CSS percentages for slider bar positioning
                // Range: scaleMin to scaleMax
                const scaleRange = scaleMax - scaleMin;
                
                // Helper to clamp percentages between 0 and 100
                const getPct = (val) => {{
                    if (val === null) return 0;
                    const pct = ((val - scaleMin) / scaleRange) * 100;
                    return Math.max(0, Math.min(100, pct));
                }};

                const fMinPct = getPct(fMin);
                const fMaxPct = getPct(fMax);
                const hMinPct = getPct(hMin);
                const hMaxPct = getPct(hMax);

                const fWidth = Math.max(2, fMaxPct - fMinPct);
                const hWidth = Math.max(2, hMaxPct - hMinPct);

                grid.innerHTML += `
                    <div class="city-card ${{themeClass}}" onclick="triggerBestemmia(this, '${{city.slug}}')">
                        <!-- Card overlay for blasphemy -->
                        <div class="card-overlay" id="overlay-${{city.slug}}">
                            <span class="overlay-close" onclick="closeBestemmia(event, '${{city.slug}}')">&times;</span>
                            <div class="overlay-text" id="text-${{city.slug}}"></div>
                        </div>
                        <div class="card-header">
                            <div class="card-title-group">
                                <span class="city-name">${{city.city}}</span>
                                <span class="weather-desc">${{alt}}</span>
                            </div>
                            <div class="weather-icon-container">
                                <img src="${{icon}}" alt="${{alt}}" onerror="this.src='https://www.3bmeteo.com/images/set_icone/24/1.svg'">
                            </div>
                        </div>

                        <div class="temp-row">
                            <div>
                                <div class="temp-label">Previsione</div>
                                <div class="temp-val">
                                    ${{fMin !== null ? fMin + '<span class="unit">°</span>' : '--'}}
                                    <span style="font-size: 0.9rem; opacity: 0.5; font-weight:400; margin: 0 0.2rem;">/</span>
                                    ${{fMax !== null ? fMax + '<span class="unit">°</span>' : '--'}}
                                </div>
                            </div>
                            <div>
                                <div class="temp-label">Storico 5a</div>
                                <div class="temp-val" style="color: var(--text-secondary); font-weight: 500;">
                                    ${{hMin !== null ? hMin + '<span class="unit">°</span>' : '--'}}
                                    <span style="font-size: 0.8rem; opacity: 0.5; font-weight:400; margin: 0 0.15rem;">/</span>
                                    ${{hMax !== null ? hMax + '<span class="unit">°</span>' : '--'}}
                                </div>
                            </div>
                        </div>

                        <div class="delta-badge-container">
                            <div class="delta-badge ${{badgeClass}}">
                                <span>${{badgeIcon}}</span>
                                <span>Max: ${{maxDelta !== null ? badgeSymbol + maxDelta.toFixed(1) + '°C' : '--'}}</span>
                            </div>
                        </div>

                        <!-- Range slider overlay visualization -->
                        <div class="visual-bar-label">
                            <span>Storico (${{hMin}}°-${{hMax}}°)</span>
                            <span>Previsto (${{fMin}}°-${{fMax}}°)</span>
                        </div>
                        <div class="visual-bar-container">
                            <div class="bar-tooltip">Storico: ${{hMin}}°-${{hMax}}° | Previsto: ${{fMin}}°-${{fMax}}°</div>
                            <!-- Historical outline bar -->
                            <div class="historical-bar" style="left: ${{hMinPct}}%; width: ${{hWidth}}%;"></div>
                            <!-- Forecast colored range bar -->
                            <div class="forecast-bar ${{barClass}}" style="left: ${{fMinPct}}%; width: ${{fWidth}}%;"></div>
                        </div>
                    </div>
                `;
            }});
        }}

        // Blasphemies dataset for creative weather complaints
        const bestemmie = [
            "Maremma maiala, che afa d'inferno! 🥵",
            "Dio cagnaccio, si bolle vivi pure all'ombra! ☀️",
            "Cristo santo, c'è un'umidità che si taglia col coltello! 🌫️",
            "Mannaggia la pupazza, sembra di stare dentro una fornace! 🌋",
            "Dio ladro, che caldo bestiale! 🐕",
            "Ostia benedetta, si suda stando completamente immobili! 💦",
            "Maremma impestata, un caldo così non si vedeva dal 2003! 📉",
            "Dio canterino, accendete quel stramaledetto condizionatore! ❄️",
            "Porco cane, si gela da far battere i denti! 🥶",
            "Cristo d'un Dio, viene giù che Dio la manda! 🌧️",
            "Santo cielo, c'è una cappa d'afa che toglie il fiato! 😷",
            "Maremma strabica, tira un vento che porta via pure i peccati! 💨",
            "Dio s'impesti, che sbalzo termico della madonna! 📈",
            "Porca miseria, ma quando rinfresca un attimo?! 🧊",
            "Dio caro, c'è un sole assassino che spacca le pietre! 🪨",
            "Ostia, umidità al 99% e ascelle in lacrime! 😭",
            "Maremma impestata ladra, che tempesta di fulmini pazzesca! ⚡",
            "Cristo lupo, fa un freddo cane che si staccano le orecchie! 🐺",
            "Dio fulminato, neanche all'inferno fa un'afa del genere! 😈",
            "Maremma maiala, tempo instabile quanto la mia salute mentale! 🏛️"
        ];

        function triggerBestemmia(card, slug) {{
            // Select a random creative blasphemy
            const randomIdx = Math.floor(Math.random() * bestemmie.length);
            const selectedText = bestemmie[randomIdx];
            
            // Set text and show overlay
            const overlay = document.getElementById("overlay-" + slug);
            const textField = document.getElementById("text-" + slug);
            if (overlay && textField) {{
                textField.innerHTML = selectedText;
                overlay.classList.add('active');
            }}
        }}

        function closeBestemmia(event, slug) {{
            // Prevent triggering the card's onclick again
            event.stopPropagation();
            const overlay = document.getElementById("overlay-" + slug);
            if (overlay) {{
                overlay.classList.remove('active');
            }}
        }}
    </script>
</body>
</html>
"""
    return html
