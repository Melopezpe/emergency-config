from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.utils import platform

class EmergencyApp(App):
    def build(self):
        self.title = "Emergency Control"
        layout = BoxLayout(orientation='vertical', padding=24, spacing=12)
        self.status = Label(text="Servicio en segundo plano activo", font_size='14sp', halign='center')
        layout.add_widget(self.status)
        layout.add_widget(Button(text="LLAMAR 112", size_hint_y=None, height=60,
                                 background_color=(0.91, 0.27, 0.38, 1),
                                 on_press=lambda x: self.call("112")))
        layout.add_widget(Button(text="Permitir aparecer encima de otras apps",
                                 size_hint_y=None, height=48, on_press=lambda x: self.overlay()))
        layout.add_widget(Button(text="Ignorar optimizacion de bateria",
                                 size_hint_y=None, height=48, on_press=lambda x: self.battery()))
        return layout

    def call(self, n):
        from jnius import autoclass, cast
        from android.runnable import run_on_ui_thread
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        Uri = autoclass('android.net.Uri')
        TelecomManager = autoclass('android.telecom.TelecomManager')
        Context = autoclass('android.content.Context')
        Bundle = autoclass('android.os.Bundle')
        tm = cast('android.telecom.TelecomManager', ctx.getSystemService(Context.TELECOM_SERVICE))
        tm.placeCall(Uri.parse('tel:' + n), Bundle())

    def overlay(self):
        from jnius import autoclass
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        i = autoclass('android.content.Intent')('android.settings.action.MANAGE_OVERLAY_PERMISSION')
        i.setData(autoclass('android.net.Uri').parse('package:' + ctx.getPackageName()))
        ctx.startActivity(i)

    def battery(self):
        from jnius import autoclass
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        i = autoclass('android.content.Intent')('android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS')
        i.setData(autoclass('android.net.Uri').parse('package:' + ctx.getPackageName()))
        ctx.startActivity(i)

    def on_start(self):
        if platform != 'android':
            return
        from android.permissions import request_permissions, Permission
        request_permissions([Permission.CALL_PHONE, Permission.SEND_SMS, Permission.INTERNET,
                             Permission.WAKE_LOCK, Permission.POST_NOTIFICATIONS,
                             Permission.FOREGROUND_SERVICE], self._after_perms)

    def _after_perms(self, perms, grants):
        from jnius import autoclass
        act = autoclass('org.kivy.android.PythonActivity').mActivity
        autoclass('org.phonecontrol.emergencycontrol.ServicePoller').start(act, '')

    def on_pause(self):
        return True   # no destruir la Activity

    def on_resume(self):
        pass

if __name__ == '__main__':
    EmergencyApp().run()
