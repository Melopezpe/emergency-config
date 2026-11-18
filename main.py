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
            # Iniciar el servicio
            Clock.schedule_once(lambda dt: self.start_service(), 2)
            # Revisar si venimos de una llamada entrante
            Clock.schedule_once(lambda dt: self.check_incoming_call(), 4)
        else:
            self.status.text = "Escritorio: sin permisos Android"

    def start_service(self):
        try:
            from android import AndroidService
            self.svc = AndroidService(title='Emergency Control', description='Monitoreando comandos...')
            self.svc.start('ok')
            self.status.text = "✅ Servicio activo"
        except Exception as e:
            self.status.text = f"Error servicio:\n{e}"

    def check_incoming_call(self):
        """Revisa si el servicio nos pasó un número para llamar."""
        try:
            from jnius import autoclass
            Activity = autoclass('org.kivy.android.PythonActivity')
            intent = Activity.mActivity.getIntent()
            
            if intent and intent.hasExtra("numero_llamada"):
                number = intent.getStringExtra("numero_llamada")
                self.status.text = f"📞 Llamando al {number}..."
                print(f"APP: LLAMADA DESDE SERVICIO -> {number}")
                self._call(number)
                # Limpiar el extra para que no se repita al volver a abrir
                intent.removeExtra("numero_llamada")
        except Exception as e:
            print(f"ERROR check_incoming_call: {e}")

    def _call(self, number):
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
                print(f"ERROR _call: {e}")
                self.status.text = f"Error llamada:\n{e}"

if __name__ == '__main__':
    EmergencyApp().run()
