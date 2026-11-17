"""
service/main.py  –  Proceso Android Service separado.
Corre aunque la app esté cerrada. No importa Kivy (sin UI).
"""
import time
import ssl
import json
import urllib.request

GITHUB_URL_TXT  = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"
DEFAULT_SERVER_URL = "https://bases-european-groups-room.trycloudflare.com"

last_id = 0


# ──────────────────────────────────────────────
# Android helpers
# ──────────────────────────────────────────────

def get_service():
    """Devuelve el contexto del Service de Android."""
    from jnius import autoclass
    return autoclass('org.kivy.android.PythonService').mService


def setup_foreground():
    """
    Promueve este proceso a Foreground Service.
    Con esto Android NO puede matarlo por memoria ni batería.
    Aparece una notificación persistente (obligatoria en Android 8+).
    """
    try:
        from jnius import autoclass
        service = get_service()

        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotifManager       = autoclass('android.app.NotificationManager')
        Builder            = autoclass('android.app.Notification$Builder')
        Context            = autoclass('android.content.Context')

        CHANNEL_ID = "emergency_fg"

        # Crear canal de notificación (Android 8+)
        nm = service.getSystemService(Context.NOTIFICATION_SERVICE)
        ch = NotificationChannel(
            CHANNEL_ID,
            "Servicio de Emergencia",
            NotifManager.IMPORTANCE_LOW          # Sin sonido
        )
        ch.setDescription("Monitorea comandos de emergencia")
        nm.createNotificationChannel(ch)

        # Notificación persistente mínima
        notif = (Builder(service, CHANNEL_ID)
                 .setContentTitle("Emergency Control")
                 .setContentText("Escuchando comandos…")
                 .setSmallIcon(service.getApplicationInfo().icon)
                 .setOngoing(True)               # No se puede descartar
                 .build())

        service.startForeground(1, notif)        # ← clave: protege el servicio
        print("[SVC] Foreground service activo")
    except Exception as e:
        print(f"[SVC] ERROR setup_foreground: {e}")


def acquire_wakelock():
    """
    WakeLock parcial: mantiene la CPU activa aunque la pantalla esté apagada.
    Sin esto Samsung / Xiaomi / Huawei pueden congelar el hilo en 10-30 s.
    """
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


# ──────────────────────────────────────────────
# Lógica de red
# ──────────────────────────────────────────────

def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    return ctx


def get_server_url():
    try:
        req  = urllib.request.Request(GITHUB_URL_TXT,
                                      headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10, context=_ssl_ctx())
        url  = resp.read().decode('utf-8-sig').strip()
        if url.startswith("http"):
            return url
    except Exception:
        pass
    return DEFAULT_SERVER_URL


def poll_server(url):
    global last_id
    try:
        endpoint = url.rstrip("/") + "/api/chat/poll_pc?since=" + str(last_id)
        req      = urllib.request.Request(endpoint,
                                          headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10, context=_ssl_ctx())
        data     = json.loads(response.read().decode())

        for msg in data.get("messages", []):
            last_id = max(last_id, msg["id"])
            handle_command(msg["text"])

        return True
    except Exception:
        return False


# ──────────────────────────────────────────────
# Ejecución de comandos
# ──────────────────────────────────────────────

def handle_command(txt: str):
    if txt.startswith("CALL:"):
        number = txt[5:].strip() or "112"
        make_call(number)


def make_call(number: str):
    """
    Realiza la llamada desde el contexto del Service.
    FLAG_ACTIVITY_NEW_TASK es obligatorio fuera de una Activity.
    """
    try:
        from jnius import autoclass
        service  = get_service()
        Intent   = autoclass('android.content.Intent')
        Uri      = autoclass('android.net.Uri')

        intent = Intent(Intent.ACTION_CALL)
        intent.setData(Uri.parse('tel:' + number))
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        service.startActivity(intent)
        print(f"[SVC] LLAMADA → {number}")
    except Exception as e:
        print(f"[SVC] ERROR make_call: {e}")


# ──────────────────────────────────────────────
# Entry point del servicio
# ──────────────────────────────────────────────

if __name__ == '__main__':
    print("[SVC] === Emergency Service arrancando ===")

    setup_foreground()
    acquire_wakelock()

    server_url      = get_server_url()
    url_ttl         = 0          # refresca URL cada 60 ciclos (~5 min)
    consecutive_err = 0

    while True:
        try:
            # Refrescar URL periódicamente por si cambia el túnel
            if url_ttl <= 0:
                server_url = get_server_url()
                url_ttl    = 60
            url_ttl -= 1

            ok = poll_server(server_url)
            if ok:
                consecutive_err = 0
            else:
                consecutive_err += 1
                # Tras 5 fallos seguidos forzar recarga de URL
                if consecutive_err >= 5:
                    server_url      = get_server_url()
                    consecutive_err = 0

        except Exception as e:
            print(f"[SVC] Error en ciclo: {e}")

        time.sleep(5)
