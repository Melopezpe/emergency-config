"""
main.py  –  Interfaz mínima.
Su único trabajo: iniciar el Foreground Service y dar retroalimentación visual.
El polling ya NO ocurre aquí; ocurre en service/main.py.
"""
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.utils import platform


class EmergencyApp(App):

    def build(self):
        self.title = "Emergency Control"

        root = BoxLayout(orientation='vertical', padding=32, spacing=16)

        self.lbl_status = Label(
            text="Iniciando…",
            font_size='15sp',
            halign='center',
            valign='middle'
        )
        self.lbl_status.bind(size=self.lbl_status.setter('text_size'))
        root.add_widget(self.lbl_status)

        btn = Button(
            text="LLAMAR 112",
            size_hint_y=None,
            height=64,
            background_color=(0.91, 0.27, 0.38, 1),
            font_size='16sp'
        )
        btn.bind(on_press=lambda _: self._call("112"))
        root.add_widget(btn)

        return root

    # ── Ciclo de vida ───────────────────────────────

    def on_start(self):
        if platform == 'android':
            self._request_permissions()
            self._start_service()
        else:
            # Modo escritorio / test
            self.lbl_status.text = "Ejecutándose en escritorio (sin servicio Android)"

    def on_stop(self):
        # El servicio sigue vivo aunque el usuario cierre la app.
        # NO llamamos a service.stop() aquí.
        pass

    # ── Permisos ────────────────────────────────────

    def _request_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CALL_PHONE,
                Permission.SEND_SMS,
                Permission.INTERNET,
                Permission.WAKE_LOCK,
                Permission.POST_NOTIFICATIONS,
                Permission.FOREGROUND_SERVICE,
            ])
        except Exception as e:
            print(f"[APP] Error permisos: {e}")

    # ── Servicio ────────────────────────────────────

    def _start_service(self):
        """
        Arranca service/main.py como Android Service independiente.
        AndroidService lo registra con una notificación persistente
        y lo mantiene vivo incluso si la app se cierra.
        """
        try:
            from android import AndroidService
            self.svc = AndroidService(
                title   = 'Emergency Control',          # Título notif
                message = 'Monitoreando en segundo plano'  # Subtítulo
            )
            self.svc.start('ok')                        # Arranca service/main.py

            self.lbl_status.text = (
                "✅  Servicio activo en segundo plano\n\n"
                "Puedes cerrar esta pantalla.\n"
                "El servicio seguirá escuchando\n"
                "y realizará la llamada automáticamente."
            )
            print("[APP] Servicio iniciado")
        except Exception as e:
            self.lbl_status.text = f"⚠️  Error iniciando servicio:\n{e}"
            print(f"[APP] Error _start_service: {e}")

    # ── Llamada manual ──────────────────────────────

    def _call(self, number: str):
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
                print(f"[APP] Error llamada: {e}")


if __name__ == '__main__':
    EmergencyApp().run()
