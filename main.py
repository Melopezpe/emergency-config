from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform

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

    def start_service(self):
        try:
            from jnius import autoclass
            Activity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            ServiceClass = autoclass('org.phonecontrol.emergencycontrol.ServiceEmergencyService')
            
            # Arrancar el servicio de Android de forma nativa
            intent = Intent(Activity.mActivity, ServiceClass)
            Activity.mActivity.startService(intent)
            
            self.status.text = "✅ Servicio iniciado\nPuedes cerrar la app."
            print("SERVICIO ARRANCADO OK")
        except Exception as e:
            self.status.text = f"Error: {e}"
            print(f"ERROR start_service: {e}")

    def _call(self, number):
        if platform == 'android':
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            Activity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Intent.ACTION_CALL)
            intent.setData(Uri.parse('tel:' + number))
            Activity.mActivity.startActivity(intent)

if __name__ == '__main__':
    EmergencyApp().run()
