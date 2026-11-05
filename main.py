"""
Emergency Control App
"""
import threading
import time
import urllib.request
import json
import os
import ssl

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

POLL_INTERVAL = 3

GITHUB_CONFIG_URL = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"
DEFAULT_SERVER_URL = "https://proxy-kent-bass-warming.trycloudflare.com"

last_id = 0
server_url = ""
github_url = GITHUB_CONFIG_URL


# ---------- Rutas de caché escribibles en Android ----------
def _cache_dir():
    try:
        if platform == 'android':
            # /data/user/0/<package>/files  -> siempre escribible
            return App.get_running_app().user_data_dir
    except Exception:
        pass
    return os.path.dirname(os.path.abspath(__file__))


LOCAL_CACHE = os.path.join(_cache_dir(), "server_url_cache.txt")
LAST_ID_CACHE = os.path.join(_cache_dir(), "last_id_cache.txt")


def load_cached_data():
    global server_url, last_id
    try:
        if os.path.exists(LOCAL_CACHE):
            with open(LOCAL_CACHE, "r") as f:
                url = f.read().strip()
                if url.startswith("http"):
                    server_url = url
    except Exception as e:
        print("CACHE READ ERROR (url):", e)

    if not server_url:
        server_url = DEFAULT_SERVER_URL

    try:
        if os.path.exists(LAST_ID_CACHE):
            with open(LAST_ID_CACHE, "r") as f:
                last_id = int(f.read().strip())
    except Exception as e:
        print("CACHE READ ERROR (id):", e)
        last_id = 0


def save_cached_url(url):
    global server_url
    url = url.strip()
    if not url.startswith("http"):
        return
    server_url = url
    try:
        with open(LOCAL_CACHE, "w") as f:
            f.write(server_url)
        print("CACHE URL SAVED:", server_url)
    except Exception as e:
        print("CACHE WRITE ERROR (url):", e)


def save_last_id(msg_id):
    global last_id
    last_id = msg_id
    try:
        with open(LAST_ID_CACHE, "w") as f:
            f.write(str(last_id))
    except Exception as e:
        print("CACHE WRITE ERROR (id):", e)


def fetch_url_from_github():
    global server_url
    try:
        req = urllib.request.Request(
            github_url,
            headers={'User-Agent': 'Mozilla/5.0 (Android) EmergencyApp/1.0',
                     'Cache-Control': 'no-cache'}
        )
        resp = urllib.request.urlopen(req, timeout=10)
        url = resp.read().decode().strip()
        if url.startswith("http"):
            if url != server_url:
                save_cached_url(url)
            return url
        print("GITHUB URL invalida:", url)
    except Exception as e:
        print("GITHUB FETCH ERROR:", e)
    return server_url


# ---------- Acciones Android ----------
def make_call(number):
    if platform == 'android':
        try:
            from jnius import autoclass
            Intent   = autoclass('android.content.Intent')
            Uri      = autoclass('android.net.Uri')
            Activity = autoclass('org.kivy.android.PythonActivity')
            intent   = Intent(Intent.ACTION_CALL)
            intent.setData(Uri.parse('tel:' + number))
            Activity.mActivity.startActivity(intent)
        except Exception as e:
            print("MAKE CALL ERROR:", e)


def send_sms(number, message):
    if platform == 'android':
        try:
            from jnius import autoclass
            SmsManager = autoclass('android.telephony.SmsManager')
            SmsManager.getDefault().sendTextMessage(number, None, message, None, None)
        except Exception as e:
            print("SEND SMS ERROR:", e)


# ---------- Polling ----------
def poll_server(url):
    global last_id
    if not url:
        return "Sin URL en GitHub"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        endpoint = url.rstrip("/") + "/api/chat/poll_pc?since=" + str(last_id)
        req = urllib.request.Request(
            endpoint,
            headers={'User-Agent': 'Mozilla/5.0 (Android) EmergencyApp/1.0'}
        )
        response = urllib.request.urlopen(req, timeout=12, context=ctx)
        data = json.loads(response.read().decode())

        if not isinstance(data, dict):
            return "Respuesta invalida"

        msgs = data.get("messages", [])
        max_id = last_id
        for msg in msgs:
            try:
                mid = int(msg["id"])
                if mid > max_id:
                    max_id = mid
            except Exception:
                continue

            txt = msg.get("text", "")
            if txt.startswith("NEWSERVER:"):
                new_url = txt[10:].strip()
                if new_url.startswith("http"):
                    save_cached_url(new_url)
            elif txt.startswith("CALL:"):
                make_call(txt[5:].strip() or "112")
            elif txt.startswith("SMS:"):
                parts = txt[4:].split(":", 1)
                if len(parts) == 2:
                    send_sms(parts[0].strip(), parts[1].strip())

        # Guardar last_id una sola vez tras procesar todo
        if max_id != last_id:
            save_last_id(max_id)

        return "Conectado"
    except Exception as e:
        print(f"ERROR POLL: {str(e)}")
        return "Sin conexion"


# ---------- Servicio en primer plano ----------
def start_foreground_service():
    if platform != 'android':
        return
    try:
        from jnius import autoclass
        Intent   = autoclass('android.content.Intent')
        Activity = autoclass('org.kivy.android.PythonActivity')
        pkg = Activity.mActivity.getPackageName()
        intent = Intent()
        intent.setClassName(pkg, pkg + ".ServiceEmergency")
        Activity.mActivity.startForegroundService(intent)
        print("FOREGROUND SERVICE STARTED:", pkg + ".ServiceEmergency")
    except Exception as e:
        print("START SERVICE ERROR:", e)


def request_ignore_battery_optimizations():
    if platform != 'android':
        return
    try:
        from jnius import autoclass
        Intent   = autoclass('android.content.Intent')
        Uri      = autoclass('android.net.Uri')
        Settings = autoclass('android.provider.Settings')
        Activity = autoclass('org.kivy.android.PythonActivity')
        pkg = Activity.mActivity.getPackageName()
        intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
        intent.setData(Uri.parse("package:" + pkg))
        Activity.mActivity.startActivity(intent)
    except Exception as e:
        print("BATTERY OPT ERROR:", e)


# ---------- App ----------
class EmergencyApp(App):
    def build(self):
        self.title = "Emergency Control"
        load_cached_data()

        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        layout.add_widget(Label(
            text="EMERGENCY CONTROL", font_size='16sp',
            color=(0.91, 0.27, 0.38, 1), size_hint_y=None, height=44))

        self.status = Label(
            text="Iniciando...", font_size='12sp',
            color=(0.6, 0.6, 0.6, 1), size_hint_y=None,
            height=80, halign='center')
        layout.add_widget(self.status)

        btn_112 = Button(
            text="LLAMAR 112", size_hint_y=None, height=56,
            background_color=(0.91, 0.27, 0.38, 1))
        btn_112.bind(on_press=lambda x: make_call("112"))
        layout.add_widget(btn_112)

        layout.add_widget(Label(
            text="La app se configura automaticamente.\n"
                 "Permite 'sin restricciones' en bateria.",
            font_size='10sp', color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None, height=44, halign='center'))

        self.request_permissions()
        return layout

    def request_permissions(self):
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CALL_PHONE,
                    Permission.SEND_SMS,
                    Permission.RECEIVE_BOOT_COMPLETED,
                    Permission.FOREGROUND_SERVICE,
                    Permission.INTERNET,
                    Permission.WAKE_LOCK,
                ])
                # Android 13+: permiso notificaciones
                try:
                    request_permissions([Permission.POST_NOTIFICATIONS])
                except Exception:
                    pass
            except Exception as e:
                print("PERMISSIONS ERROR:", e)

    def main_loop(self):
        github_check = 0
        while True:
            if github_check <= 0:
                current_url = fetch_url_from_github()
                github_check = 60
            else:
                current_url = server_url
                github_check -= POLL_INTERVAL

            result = poll_server(current_url)
            short = (current_url[:28] + "...") if len(current_url) > 28 else current_url
            Clock.schedule_once(
                lambda dt, r=result, u=short: setattr(
                    self.status, 'text', f"{r}\n{u}"), 0)

            # Sleep fijo, no acumulativo
            time.sleep(POLL_INTERVAL)

    def on_start(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Activity     = autoclass('org.kivy.android.PythonActivity')
                PowerManager = autoclass('android.os.PowerManager')
                pm = Activity.mActivity.getSystemService('power')
                self.wake_lock = pm.newWakeLock(
                    PowerManager.PARTIAL_WAKE_LOCK, 'EmergencyApp::WakeLock')
                self.wake_lock.acquire()
                print("WAKE LOCK ACQUIRED")
            except Exception as e:
                print("WAKE LOCK ERROR:", e)
                self.wake_lock = None

            # Lanzar servicio foreground + pedir bateria sin restricciones
            Clock.schedule_once(lambda dt: start_foreground_service(), 2)
            Clock.schedule_once(lambda dt: request_ignore_battery_optimizations(), 5)

        # Hilo de polling dentro de la Activity (se mantiene mientras viva)
        threading.Thread(target=self.main_loop, daemon=True).start()

    def on_stop(self):
        try:
            if getattr(self, 'wake_lock', None):
                self.wake_lock.release()
                print("WAKE LOCK RELEASED")
        except Exception as e:
            print("WAKE LOCK RELEASE ERROR:", e)


if __name__ == '__main__':
    EmergencyApp().run()