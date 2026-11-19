import os
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

class EmergencyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        self.status = Label(text="Iniciando...", font_size='14sp', halign='center')
        layout.add_widget(self.status)
        
        btn = Button(text="LLAMAR 112", size_hint_y=None, height=60, background_color=(0.85, 0.15, 0.25, 1))
        btn.bind(on_press=lambda x: self._call("112"))
        layout.add_widget(btn)
        
        self.request_permissions()
        return layout

    def request_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CALL_PHONE, Permission.SEND_SMS, 
                Permission.INTERNET, Permission.WAKE_LOCK, 
                Permission.POST_NOTIFICATIONS, Permission.FOREGROUND_SERVICE
            ])

    def on_start(self):
        if platform == 'android':
            Clock.schedule_once(lambda dt: self.start_service(), 2)
            # Revisar el Intent inmediatamente al abrir
            Clock.schedule_once(lambda dt: self.check_pending_call(), 0.5)
            # Iniciar poll (por si la app está abierta)
            Clock.schedule_once(lambda dt: self.poll_loop(), 3)

    def start_service(self):
        try:
            from android import AndroidService
            self.svc = AndroidService(title='Emergency Control', description='Monitoreando...')
            self.svc.start('ok')
            self.status.text = "✅ Servicio activo"
        except Exception as e:
            self.status.text = f"Error servicio:\n{e}"

    def check_pending_call(self):
        """Lee el Intent que trae el número desde la notificación."""
        try:
            from jnius import autoclass
            Activity = autoclass('org.kivy.android.PythonActivity')
            intent = Activity.mActivity.getIntent()
            
            if intent and intent.hasExtra("numero_llamada"):
                number = intent.getStringExtra("numero_llamada")
                print(f"APP: LLAMADA DESDE NOTIFICACIÓN -> {number}")
                self.status.text = f"📞 Llamando al {number}..."
                self._call(number)
                # Limpiar el Intent para que no se repita
                intent.removeExtra("numero_llamada")
            else:
                print("APP: No hay llamada pendiente en el Intent.")
        except Exception as e:
            print(f"ERROR check_pending_call: {e}")

    def poll_loop(self):
        global last_id
        """Hace el poll del servidor cuando la app está en primer plano."""
        try:
            url = self.get_url()
            endpoint = url.rstrip("/") + "/api/chat/poll_pc?since=" + str(last_id)
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(endpoint, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=5, context=ctx)
            data = json.loads(resp.read().decode())
            
            for msg in data.get("messages", []):
                last_id = max(last_id, msg["id"])
                txt = msg["text"]
                if txt.startswith("CALL:"):
                    number = txt[5:].strip() or "112"
                    self.status.text = f"📞 Llamando al {number}..."
                    self._call(number)
        except Exception:
            pass
        finally:
            Clock.schedule_once(lambda dt: self.poll_loop(), 5)

    def get_url(self):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(GITHUB_URL_TXT, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=5, context=ctx)
            url = resp.read().decode('utf-8-sig').strip()
            if url.startswith("http"):
                return url
        except Exception:
            pass
        return DEFAULT_SERVER_URL

    def _call(self, number):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                Activity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Intent.ACTION_CALL)
                intent.setData(Uri.parse('tel:' + number))
                Activity.mActivity.startActivity(intent)
            except Exception as e:
                print(f"ERROR _call: {e}")
                self.status.text = f"Error llamada:\n{e}"

if __name__ == '__main__':
    EmergencyApp().run()
