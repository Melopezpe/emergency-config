import os
import time
import ssl
import json
import urllib.request
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

GITHUB_URL_TXT = "https://raw.githubusercontent.com/Melopezpe/emergency-config/main/url.txt"
DEFAULT_SERVER_URL = "https://bases-european-groups-room.trycloudflare.com"

last_id = 0

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
            print(f"LLAMADA INICIADA: {number}")
        except Exception as e:
            print(f"ERROR make_call: {e}")

def get_url_from_github():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(GITHUB_URL_TXT, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        url = resp.read().decode('utf-8-sig').strip()
        if url.startswith("http"):
            return url
    except Exception:
        pass
    return DEFAULT_SERVER_URL

def poll_server(url):
    global last_id
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        endpoint = url.rstrip("/") + "/api/chat/poll_pc?since=" + str(last_id)
        req = urllib.request.Request(endpoint, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10, context=ctx)
        data = json.loads(response.read().decode())
        
        for msg in data.get("messages", []):
            last_id = max(last_id, msg["id"])
            txt = msg["text"]
            if txt.startswith("CALL:"):
                make_call(txt[5:].strip() or "112")
        return True
    except Exception:
        return False

class EmergencyApp(App):
    def build(self):
        self.title = "Emergency Control"
        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        self.status = Label(text="Iniciando...", font_size='14sp', halign='center')
        layout.add_widget(self.status)
        
        btn = Button(text="LLAMAR 112", size_hint_y=None, height=60, background_color=(0.91, 0.27, 0.38, 1))
        btn.bind(on_press=lambda x: make_call("112"))
        layout.add_widget(btn)

        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CALL_PHONE, Permission.SEND_SMS, 
                Permission.INTERNET, Permission.WAKE_LOCK,
                Permission.POST_NOTIFICATIONS, Permission.FOREGROUND_SERVICE
            ])
        return layout

    def on_start(self):
        Clock.schedule_once(self.start_background, 1)

    def start_background(self, dt):
        self.status.text = "Servicio Activo\nRevisando comandos..."
        
        # 1. Pedir que no maten la app (WakeLock)
        if platform == 'android':
            try:
                from jnius import autoclass
                Activity = autoclass('org.kivy.android.PythonActivity')
                PowerManager = autoclass('android.os.PowerManager')
                pm = Activity.mActivity.getSystemService('power')
                self.wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'EmergencyApp::WakeLock')
                self.wake_lock.acquire()
            except Exception as e:
                print(f"Error WakeLock: {e}")

        # 2. Iniciar el bucle que despierta a Android con AlarmManager
        self.loop_running = True
        Clock.schedule_interval(self.run_poll, 5) # Cada 5 segundos

    def run_poll(self, dt):
        if not self.loop_running:
            return False
        
        url = get_url_from_github()
        exito = poll_server(url)
        
        if not exito:
            self.status.text = "Reconectando..."
        else:
            self.status.text = "Servicio Activo\nEscuchando..."
            
        # TRUCO ANTI-SAMSUNG: Forzar a Android a mantener el hilo despierto
        if platform == 'android':
            try:
                from jnius import autoclass
                SystemClock = autoclass('android.os.SystemClock')
                SystemClock.sleep(100) 
            except Exception:
                pass
        return True

if __name__ == '__main__':
    EmergencyApp().run()
