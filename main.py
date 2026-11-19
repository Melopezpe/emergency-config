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
            Clock.schedule_once(lambda dt: self.setup_broadcast_receiver(), 3)

    def start_service(self):
        try:
            from android import AndroidService
            self.svc = AndroidService(title='Emergency Control', description='Monitoreando...')
            self.svc.start('ok')
            self.status.text = "✅ Servicio activo"
        except Exception as e:
            self.status.text = f"Error servicio:\n{e}"

    def setup_broadcast_receiver(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            from android import mActivity
            
            # Creamos una clase Java que escucha el Broadcast
            class BroadcastReceiver(PythonJavaClass):
                __javainterfaces__ = ['android/content/BroadcastReceiver']
                __javacontext__ = 'app'

                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback

                @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
                def onReceive(self, context, intent):
                    if intent.getAction() == "EMERGENCY_CALL_ACTION":
                        number = intent.getStringExtra("numero_llamada")
                        if number:
                            self.callback(number)

            # Instanciamos el receptor y lo registramos
            self.receiver = BroadcastReceiver(self._call)
            
            IntentFilter = autoclass('android.content.IntentFilter')
            filter = IntentFilter("EMERGENCY_CALL_ACTION")
            
            # Registramos el receptor en la actividad
            mActivity.registerReceiver(self.receiver, filter)
            print("APP: BroadcastReceiver registrado y escuchando.")
            
        except Exception as e:
            print(f"ERROR setup_broadcast_receiver: {e}")

    def _call(self, number):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                Activity = autoclass('org.kivy.android.PythonActivity')
                
                self.status.text = f"📞 Llamando al {number}..."
                intent = Intent(Intent.ACTION_CALL)
                intent.setData(Uri.parse('tel:' + number))
                Activity.mActivity.startActivity(intent)
            except Exception as e:
                print(f"ERROR _call: {e}")
                self.status.text = f"Error llamada:\n{e}"

if __name__ == '__main__':
    EmergencyApp().run()
