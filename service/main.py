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
        return wl
    except Exception as e:
        print(f"[SVC] ERROR WakeLock: {e}")
        return None

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
    """Crea una notificación de alta prioridad que despierta el celular y abre la app."""
    try:
        from jnius import autoclass
        service = get_service()
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        Activity = autoclass('org.kivy.android.PythonActivity')
        
        # 1. Guardar el número en la carpeta privada de la app
        app_dir = service.getFilesDir().getAbsolutePath()
        filepath = os.path.join(app_dir, "llamada_pendiente.txt")
        with open(filepath, 'w') as f:
            f.write(number)
        print(f"[SVC] Número {number} guardado en {filepath}")

        # 2. Crear un Intent para abrir la app
        intent = Intent(service, Activity)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
        flags = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        pending_intent = PendingIntent.getActivity(service, 0, intent, flags)

        # 3. Construir notificación de alta prioridad (despierta pantalla)
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotificationManager = autoclass('android.app.NotificationManager')
        Context = autoclass('android.content.Context')

        channel_id = "emergency_call_channel"
        nm = service.getSystemService(Context.NOTIFICATION_SERVICE)
        channel = NotificationChannel(channel_id, "Llamada de Emergencia", NotificationManager.IMPORTANCE_HIGH)
        nm.createNotificationChannel(channel)

        notification = (NotificationBuilder(service, channel_id)
                        .setContentTitle("Llamada de Emergencia")
                        .setContentText(f"Toca para llamar al {number}")
                        .setSmallIcon(service.getApplicationInfo().icon)
                        .setPriority(NotificationManager.IMPORTANCE_HIGH)
                        .setCategory("call")
                        .setContentIntent(pending_intent)
                        .setFullScreenIntent(pending_intent, True)
                        .setAutoCancel(True)
                        .build())

        nm.notify(1, notification)
        print(f"[SVC] Notificación de llamada enviada al {number}")
    except Exception as e:
        print(f"[SVC] ERROR make_call: {e}")

if __name__ == '__main__':
    print("[SVC] === Emergency Service arrancando ===")
    setup_foreground()
    acquire_wakelock()
    server_url = get_server_url()
    url_ttl = 0
    consecutive_err = 0
    while True:
        try:
            if url_ttl <= 0:
                server_url = get_server_url()
                url_ttl = 60
            url_ttl -= 1
            ok = poll_server(server_url)
            if ok:
                consecutive_err = 0
            else:
                consecutive_err += 1
                if consecutive_err >= 5:
                    server_url = get_server_url()
                    consecutive_err = 0
        except Exception as e:
            print(f"[SVC] Error en ciclo: {e}")
        time.sleep(5)
