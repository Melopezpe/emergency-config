import os, json, ssl, time, threading, urllib.request
from jnius import autoclass, cast

GITHUB_URL_TXT = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"
DEFAULT_SERVER_URL = "https://bases-european-groups-room.trycloudflare.com"
POLL_INTERVAL = 5
URL_REFRESH = 300

PythonService = autoclass('org.kivy.android.PythonService')
Context = autoclass('android.content.Context')
Uri = autoclass('android.net.Uri')
Build = autoclass('android.os.Build')
PowerManager = autoclass('android.os.PowerManager')
TelecomManager = autoclass('android.telecom.TelecomManager')
Bundle = autoclass('android.os.Bundle')
NotificationManager = autoclass('android.app.NotificationManager')
NotificationChannel = autoclass('android.app.NotificationChannel')
NotificationBuilder = autoclass('android.app.Notification$Builder')
PendingIntent = autoclass('android.app.PendingIntent')
Intent = autoclass('android.content.Intent')

ctx = PythonService.mService
STATE = os.path.join(os.environ.get('ANDROID_PRIVATE', os.path.expanduser('~')), 'last_id')

last_id = 0
catch_up = True
cached_url = DEFAULT_SERVER_URL
url_ts = 0.0
lock = threading.Lock()

def load_state():
    global last_id, catch_up
    try:
        last_id = int(open(STATE).read().strip())
        catch_up = False
    except Exception:
        last_id = 0
        catch_up = True

def save_state():
    try:
        with open(STATE, 'w') as f:
            f.write(str(last_id))
    except Exception:
        pass

def ssl_ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c

def get_url():
    global cached_url, url_ts
    if time.time() - url_ts < URL_REFRESH:
        return cached_url
    url_ts = time.time()
    try:
        req = urllib.request.Request(GITHUB_URL_TXT, headers={'User-Agent': 'Mozilla/5.0'})
        u = urllib.request.urlopen(req, timeout=10, context=ssl_ctx()).read().decode('utf-8-sig').strip()
        if u.startswith('http'):
            cached_url = u
    except Exception:
        pass
    return cached_url

def notify(title, text):
    try:
        nm = cast('android.app.NotificationManager', ctx.getSystemService(Context.NOTIFICATION_SERVICE))
        ch = 'emergency_call'
        if Build.VERSION.SDK_INT >= 26:
            nm.createNotificationChannel(NotificationChannel(ch, 'Llamadas', NotificationManager.IMPORTANCE_HIGH))
        b = NotificationBuilder(ctx, ch) if Build.VERSION.SDK_INT >= 26 else NotificationBuilder(ctx)
        b.setSmallIcon(autoclass('android.R$drawable').ic_menu_call)
        b.setContentTitle(title)
        b.setContentText(text)
        b.setAutoCancel(True)
        b.setPriority(2)
        nm.notify(int(time.time()) % 100000, b.build())
    except Exception as e:
        print('notify:', e)

def place_call(number):
    number = (number or '112').strip()
    try:
        tm = cast('android.telecom.TelecomManager', ctx.getSystemService(Context.TELECOM_SERVICE))
        tm.placeCall(Uri.parse('tel:' + number), Bundle())
        notify('Llamando', number)
        return
    except Exception as e:
        print('placeCall fallo:', e)

    # Respaldo: startActivity desde el servicio (requiere "Aparecer encima")
    try:
        i = Intent(Intent.ACTION_CALL, Uri.parse('tel:' + number))
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        ctx.startActivity(i)
        notify('Llamando (respaldo)', number)
    except Exception as e:
        print('startActivity fallo:', e)

def poll():
    global last_id, catch_up
    with lock:
        url = get_url()
        endpoint = url.rstrip('/') + '/api/chat/poll_pc?since=' + str(last_id)
        try:
            req = urllib.request.Request(endpoint, headers={'User-Agent': 'Mozilla/5.0'})
            data = json.loads(urllib.request.urlopen(req, timeout=10, context=ssl_ctx()).read().decode())
        except Exception:
            return False

        msgs = data.get('messages', [])
        if catch_up:
            if msgs:
                last_id = max(last_id, max(m['id'] for m in msgs))
            catch_up = False
            save_state()
            return True

        for m in sorted(msgs, key=lambda x: x['id']):
            if m['id'] <= last_id:
                continue
            last_id = m['id']
            save_state()
            txt = (m.get('text') or '').strip()
            if txt.startswith('CALL:'):
                place_call(txt[5:].strip())
            elif txt.startswith('SMS:'):
                pass  # pendiente
        return True

def loop():
    while True:
        try:
            poll()
        except Exception as e:
            print('loop:', e)
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    load_state()
    try:
        pm = cast('android.os.PowerManager', ctx.getSystemService(Context.POWER_SERVICE))
        wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'Emergency::poll')
        wl.setReferenceCounted(False)
        wl.acquire()
    except Exception as e:
        print('wakelock:', e)
    threading.Thread(target=loop, daemon=True).start()
    while True:
        time.sleep(3600)
