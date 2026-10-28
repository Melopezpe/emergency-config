"""
Emergency Control App
La app lee la URL del servidor desde un archivo en GitHub.
Cuando Cloudflare cambia la URL, solo se actualiza el archivo
en GitHub. La app funciona para siempre sin reinstalacion.
"""
import threading
import time
import urllib.request
import json
import os

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

POLL_INTERVAL = 3

# URL FIJA en GitHub que contiene la URL actual del servidor Flask
# Esta URL NUNCA cambia. Solo cambia el contenido del archivo.
# Pasos para configurar:
# 1. Crea un repo publico en GitHub llamado "emergency-config"
# 2. Crea un archivo llamado "url.txt" con la URL de Cloudflare
# 3. Reemplaza TU-USUARIO con tu usuario de GitHub
GITHUB_CONFIG_URL = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"

# Cache local de la URL del servidor
LOCAL_CACHE = "server_url_cache.txt"

last_id = 0
server_url = ""
github_url = GITHUB_CONFIG_URL


def load_cached_url():
    """Carga la ultima URL conocida desde cache local."""
    global server_url
    try:
        if os.path.exists(LOCAL_CACHE):
            with open(LOCAL_CACHE, "r") as f:
                url = f.read().strip()
                if url:
                    server_url = url
    except Exception:
        pass


def save_cached_url(url):
    """Guarda la URL en cache local para uso sin internet."""
    global server_url
    server_url = url.strip()
    try:
        with open(LOCAL_CACHE, "w") as f:
            f.write(server_url)
    except Exception:
        pass


def fetch_url_from_github():
    """
    Lee la URL actual del servidor desde el archivo en GitHub.
    Si GitHub no responde, usa la cache local.
    """
    global server_url
    try:
        req = urllib.request.urlopen(github_url, timeout=8)
        url = req.read().decode().strip()
        if url.startswith("http"):
            if url != server_url:
                save_cached_url(url)
            return url
    except Exception:
        pass
    return server_url


def make_call(number):
    if platform == 'android':
        from jnius import autoclass
        Intent   = autoclass('android.content.Intent')
        Uri      = autoclass('android.net.Uri')
        Activity = autoclass('org.kivy.android.PythonActivity')
        intent   = Intent(Intent.ACTION_CALL)
        intent.setData(Uri.parse('tel:' + number))
        Activity.mActivity.startActivity(intent)


def send_sms(number, message):
    if platform == 'android':
        from jnius import autoclass
        SmsManager = autoclass('android.telephony.SmsManager')
        SmsManager.getDefault().sendTextMessage(
            number, None, message, None, None
        )


def poll_server(url):
    global last_id
    if not url:
        return "Sin URL en GitHub"
    try:
        endpoint = url.rstrip("/") + "/api/chat/poll_pc?since=" + str(last_id)
        req  = urllib.request.urlopen(endpoint, timeout=5)
        data = json.loads(req.read().decode())
        for msg in data.get("messages", []):
            last_id = max(last_id, msg["id"])
            txt = msg["text"]
            if txt.startswith("CALL:"):
                make_call(txt[5:].strip() or "112")
            elif txt.startswith("SMS:"):
                parts = txt[4:].split(":", 1)
                if len(parts) == 2:
                    send_sms(parts[0].strip(), parts[1].strip())
        return "Conectado"
    except Exception:
        return "Sin conexion"


class EmergencyApp(App):

    def build(self):
        self.title = "Emergency Control"
        load_cached_url()

        layout = BoxLayout(
            orientation='vertical',
            padding=24, spacing=12
        )

        layout.add_widget(Label(
            text="EMERGENCY CONTROL",
            font_size='16sp',
            color=(0.91, 0.27, 0.38, 1),
            size_hint_y=None, height=44
        ))

        self.status = Label(
            text="Iniciando...",
            font_size='12sp',
            color=(0.6, 0.6, 0.6, 1),
            size_hint_y=None, height=60,
            halign='center'
        )
        layout.add_widget(self.status)

        btn_112 = Button(
            text="LLAMAR 112",
            size_hint_y=None, height=56,
            background_color=(0.91, 0.27, 0.38, 1)
        )
        btn_112.bind(on_press=lambda x: make_call("112"))
        layout.add_widget(btn_112)

        layout.add_widget(Label(
            text="La app se configura automaticamente.\nNo requiere ninguna accion del usuario.",
            font_size='10sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None, height=44,
            halign='center'
        ))

        self.request_permissions()
        threading.Thread(target=self.main_loop, daemon=True).start()
        return layout

    def request_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CALL_PHONE,
                Permission.SEND_SMS,
                Permission.RECEIVE_BOOT_COMPLETED,
                Permission.FOREGROUND_SERVICE,
                Permission.INTERNET,
                Permission.WAKE_LOCK,
            ])

    def main_loop(self):
        github_check = 0
        while True:
            # Refrescar URL desde GitHub cada 60 segundos
            if github_check <= 0:
                current_url = fetch_url_from_github()
                github_check = 60
            else:
                current_url = server_url
                github_check -= POLL_INTERVAL

            result = poll_server(current_url)
            short = (current_url[:28] + "...") if len(current_url) > 28 else current_url
            Clock.schedule_once(
                lambda dt, r=result, u=short:
                setattr(self.status, 'text', f"{r}\n{u}"), 0
            )
            time.sleep(POLL_INTERVAL)

    def on_start(self):
        if platform == 'android':
            from jnius import autoclass
            Activity     = autoclass('org.kivy.android.PythonActivity')
            PowerManager = autoclass('android.os.PowerManager')
            pm = Activity.mActivity.getSystemService('power')
            self.wake_lock = pm.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK,
                'EmergencyApp::WakeLock'
            )
            self.wake_lock.acquire()


if __name__ == '__main__':
    EmergencyApp().run()
