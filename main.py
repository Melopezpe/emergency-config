import os
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

def make_call(number):
    if platform == 'android':
        from jnius import autoclass
        Intent   = autoclass('android.content.Intent')
        Uri      = autoclass('android.net.Uri')
        Activity = autoclass('org.kivy.android.PythonActivity')
        intent   = Intent(Intent.ACTION_CALL)
        intent.setData(Uri.parse('tel:' + number))
        Activity.mActivity.startActivity(intent)

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
            return token
        except Exception as e:
            print(f"ERROR_FCM: {e}")
            return None

class EmergencyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        self.status = Label(text="Iniciando...", font_size='12sp')
        layout.add_widget(self.status)
        
        btn = Button(text="LLAMAR 112", size_hint_y=None, height=56)
        btn.bind(on_press=lambda x: make_call("112"))
        layout.add_widget(btn)

        self.request_permissions()
        return layout

    def request_permissions(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.CALL_PHONE, Permission.SEND_SMS, Permission.INTERNET, Permission.POST_NOTIFICATIONS])

    def on_start(self):
        Clock.schedule_once(lambda dt: self.init_fcm(), 3)

    def init_fcm(self):
        token = get_fcm_token()
        if token:
            self.status.text = f"Token:\n{token}"
        else:
            self.status.text = "Error con Firebase"

if __name__ == '__main__':
    EmergencyApp().run()
