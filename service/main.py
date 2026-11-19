import time
import ssl
import json
import urllib.request
import os

GITHUB_URL_TXT = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"
DEFAULT_SERVER_URL = "https://bases-european-groups-room.trycloudflare.com"
last_id = 0

def get_service():
    from jnius import autoclass
    return autoclass('org.kivy.android.PythonService').mService

def setup_foreground():
    try:
        from jnius import autoclass
        service = get_service()
        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotifManager = autoclass('android.app.NotificationManager')
        Builder = autoclass('android.app.Notification$Builder')
        Context = autoclass('android.content.Context')
        CHANNEL_ID = "emergency_fg"
        nm = service.getSystemService(Context.NOTIFICATION_SERVICE)
        ch = NotificationChannel(CHANNEL_ID, "Servicio de Emergencia", NotifManager.IMPORTANCE_LOW)
        nm.createNotificationChannel(ch)
        notif = (Builder(service, CHANNEL_ID)
                 .setContentTitle("Emergency Control")
                 .setContentText("Escuchando comandos…")
                 .setSmallIcon(service.getApplicationInfo().icon)
                 .setOngoing(True)
                 .build())
        service.startForeground(1, notif)
        print("[SVC] Foreground service activo")
    except Exception as e:
        print(f"[SVC] ERROR setup_foreground: {e}")

def acquire_wakelock():
    try:
        from jnius import autoclass
        service = get_service()
        PM = autoclass('android.os.PowerManager')
        pm = service.getSystemService('power')
        wl = pm.newWakeLock(PM.PARTIAL_WAKE_LOCK, 'EmergencyApp::WakeLock')
        wl.acquire()
        print("[SVC] WakeLock adquirido")
    except Exception as e:
        print(f"[SVC] ERROR WakeLock: {e}")

def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def get_server_url():
    try:
        req = urllib.request.Request(GITHUB_URL_TXT, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10, context=_ssl_ctx())
        url = resp.read().decode('utf-8-sig').strip()
        if url.startswith("http"):
            return url
    except Exception:
        pass
    return DEFAULT_SERVER_URL

def poll_server(url):
    global last_id
    try:
        endpoint = url.rstrip("/") + "/api/chat/poll_pc?since=" + str(last_id)
        req = urllib.request.Request(endpoint, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10, context=_ssl_ctx())
        data = json.loads(response.read().decode())
        for msg in data.get("messages", []):
            last_id = max(last_id, msg["id"])
            handle_command(msg["text"])
        return True
    except Exception:
        return False

def handle_command(txt: str):
    if txt.startswith("CALL:"):
        number = txt[5:].strip() or "112"
        make_call(number)

def make_call(number: str):
    try:
        from jnius import autoclass
        service = get_service()
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        Activity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')

        intent = Intent(service, Activity)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
        intent.putExtra("numero_llamada", number)

        flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        pending_intent = PendingIntent.getActivity(service, 0, intent, flags)

        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotificationManager = autoclass('android.app.NotificationManager')
        
        channel_id = "emergency_call_channel"
        nm = service.getSystemService(Context.NOTIFICATION_SERVICE)
        channel = NotificationChannel(channel_id, "Llamada de Emergencia", NotificationManager.IMPORTANCE_HIGH)
        nm.createNotificationChannel(channel)

        notification = (NotificationBuilder(service, channel_id)
                        .setContentTitle("Llamada de Emergencia")
                        .setContentText(f"Toca para llamar al {number}")
                        .setSmallIcon(service.getApplicationInfo().icon)
                        .setPriority(NotificationManager.IMPORTANCE_HIGH)
                        .setContentIntent(pending_intent)
                        .setFullScreenIntent(pending_intent, True)
                        .setAutoCancel(True)
                        .build())

        nm.notify(1, notification)
        print(f"[SVC] Notificación enviada para {number}")
    except Exception as e:
        print(f"[SVC] ERROR make_call: {e}")

if __name__ == '__main__':
    print("[SVC] Servicio iniciado")
    setup_foreground()
    acquire_wakelock()
    server_url = get_server_url()
    while True:
        poll_server(server_url)
        time.sleep(5)
