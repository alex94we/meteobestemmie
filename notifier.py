import subprocess
import os
import tempfile
import urllib.request
import urllib.parse

def send_notification(title, line1, line2, html_path):
    """
    Triggers a native Windows Toast Notification using a temporary PowerShell script.
    When the user clicks the notification, it launches the HTML dashboard.
    """
    html_abs_path = os.path.abspath(html_path)
    
    # Escape single quotes and double quotes for PowerShell
    title_escaped = title.replace('"', '`"').replace("'", "''")
    line1_escaped = line1.replace('"', '`"').replace("'", "''")
    line2_escaped = line2.replace('"', '`"').replace("'", "''")
    html_escaped = html_abs_path.replace('"', '`"').replace("'", "''")
    
    # Construct PowerShell script using ToastGeneric template
    ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
$xml = @"
<toast launch="{html_escaped}">
    <visual>
        <binding template="ToastGeneric">
            <text>{title_escaped}</text>
            <text>{line1_escaped}</text>
            <text>{line2_escaped}</text>
        </binding>
    </visual>
</toast>
"@

$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("MeteoApp")
$toast = New-Object Windows.UI.Notifications.ToastNotification ($doc)
$notifier.Show($toast)
"""
    
    # Write to a temporary file and execute it
    temp_dir = tempfile.gettempdir()
    temp_script_path = os.path.join(temp_dir, "send_meteo_toast.ps1")
    
    try:
        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(ps_script)
            
        # Run the PowerShell script
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        print("Toast notification triggered.")
        return True
    except Exception as e:
        print(f"Error triggering toast notification: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_script_path):
            try:
                os.remove(temp_script_path)
            except Exception:
                pass

def send_push_notification(title, line1, line2, click_url=None):
    """
    Sends a push notification via the free ntfy.sh service.
    This works on mobile (Android/iOS) and desktop browsers.
    No registration or API key required.
    """
    topic = "meteo-bestemmie-alex94we"
    
    # Build query parameters to support UTF-8, emojis, and click URLs safely
    params = {
        "title": title,
        "tags": "partly_sunny,chart_with_upwards_trend"
    }
    if click_url:
        params["click"] = click_url
        
    query_string = urllib.parse.urlencode(params)
    url = f"https://ntfy.sh/{topic}?{query_string}"
    
    # Message body is sent as plain text bytes
    message_body = f"{line1}\n{line2}".encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=message_body,
        headers={"Content-Type": "text/plain; charset=utf-8"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode('utf-8')
            print(f"Push notification successfully sent to ntfy topic: '{topic}'")
            return True
    except Exception as e:
        print(f"Error sending ntfy push notification: {e}")
        return False

if __name__ == '__main__':
    # Test notification
    print("Testing Notification System...")
    
    # Test local notification
    test_file = "index.html"
    if not os.path.exists(test_file):
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("<h1>Test OK! La notifica ti ha portato qui.</h1>")
            
    send_notification(
        title="Meteo Italia: Test Locale 🌤️",
        line1="Le temperature sono aumentate del +1.8°C rispetto alla media storica.",
        line2="Clicca per visualizzare l'analisi completa.",
        html_path=test_file
    )
    
    # Test push notification
    send_push_notification(
        title="Meteo Italia: Test Push 🌤️",
        line1="Le temperature sono aumentate di +1.8°C rispetto alla media storica.",
        line2="Notifica push ricevuta correttamente da ntfy.sh!",
        click_url="https://alex94we.github.io/meteobestemmie/"
    )
    
    print("Test run finished. Check your desktop and ntfy.sh/meteo-bestemmie-alex94we")
