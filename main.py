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

def get_fcm_token():
    if platform == 'android':
        try:
            from jnius import autoclass
            FirebaseApp = autoclass('com.google.firebase.FirebaseApp')
            FirebaseMessaging = autoclass('com.google.firebase.messaging.FirebaseMessaging')
            Activity = autoclass('org.kivy.android.PythonActivity')
            
            FirebaseApp.initializeApp(Activity.mActivity)
            token = FirebaseMessaging.getInstance().getToken().getResult()
            print(f"FCM_TOKEN_GENERADO: {token}")
            
            # 1. Obtener la URL actual desde GitHub (la que puso el servidor)
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(GITHUB_URL_TXT, headers={'User-Agent': 'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=10, context=ctx)
                server_base_url = resp.read().decode('utf-8-sig').strip()
                print(f"URL obtenida de GitHub: {server_base_url}")
                
                # 2. Enviar el token al servidor
                if server_base_url.startswith("http"):
                    endpoint = server_base_url.rstrip("/") + "/api/set_fcm_token"
                    data = json.dumps({"token": token}).encode('utf-8')
                    req2 = urllib.request.Request(
                        endpoint,
                        data=data,
                        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
                    )
                    urllib.request.urlopen(req2, timeout=10, context=ctx)
                    print("✅ Token enviado al servidor correctamente.")
            except Exception as e:
                print(f"ERROR enviando token: {e}")
                
            return token
        except Exception as e:
            print(f"ERROR_FCM: {e}")
            return None

class EmergencyApp(App):
    def build(self):
        self.title = "Emergency Control"
        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        self.status = Label(text="Iniciando...", font_size='12sp', halign='center')
        layout.add_widget(self.status)
        
        btn = Button(text="LLAMAR 112", size_hint_y=None, height=56, background_color=(0.91, 0.27, 0.38, 1))
        btn.bind(on_press=lambda x: make_call("112"))
        layout.add_widget(btn)

        self.request_permissions()
        return layout

    def request_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            perms = [Permission.CALL_PHONE, Permission.SEND_SMS, Permission.INTERNET, Permission.POST_NOTIFICATIONS]
            request_permissions(perms)

    def on_start(self):
        # Sin retraso. Pedimos el token apenas arranque.
        self.init_fcm()

    def init_fcm(self):
        print("INICIANDO FCM EN LA APP...") # <-- AÑADIR ESTO
        token = get_fcm_token()
        if token:
            self.status.text = f"✅ Servicio conectado\nToken: {token[:12]}..."
            print(f"TOKEN MOSTRADO EN PANTALLA: {token}")
        else:
            self.status.text = "⚠️ Error al conectar con Firebase\nRevisa los logs."
            print("FALLO AL OBTENER EL TOKEN")

if __name__ == '__main__':
    EmergencyApp().run()
