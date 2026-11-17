"""
main.py  –  Interfaz mínima.
Su único trabajo: pedir permisos y luego iniciar el Foreground Service.
El polling ocurre en service/main.py, no aquí.
"""
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
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
            # Esperar 1 s a que la ventana esté completamente visible
            # antes de lanzar el diálogo de permisos.
            Clock.schedule_once(self._ask_permissions, 1)
        else:
            self.lbl_status.text = "Escritorio – sin servicio Android"

    def on_stop(self):
        pass  # El servicio sigue vivo al cerrar la app

    # ── Permisos ────────────────────────────────────

    def _ask_permissions(self, dt):
        """
        Pide los permisos peligrosos en tiempo de ejecución.
        Solo CALL_PHONE y POST_NOTIFICATIONS requieren diálogo;
        el resto (INTERNET, WAKE_LOCK, FOREGROUND_SERVICE) son normales
        y se otorgan automáticamente al instalar.
        Una vez que el usuario responde, _on_permissions_result arranca el servicio.
        """
        try:
            from android.permissions import request_permissions, Permission

            DANGEROUS = [
                Permission.CALL_PHONE,        # Marcar números
                Permission.SEND_SMS,          # SMS
                Permission.POST_NOTIFICATIONS, # Notificación persistente (Android 13+)
            ]

            self.lbl_status.text = "Solicitando permisos…\n(acepta todos para que funcione)"
            request_permissions(DANGEROUS, self._on_permissions_result)

        except Exception as e:
            print(f"[APP] Error pidiendo permisos: {e}")
            # Si falla el mecanismo de permisos, intentar arrancar igual
            self._start_service()

    def _on_permissions_result(self, permissions, grants):
        """
        Callback que Android llama cuando el usuario responde al diálogo.
        Aquí ya es seguro arrancar el servicio.
        """
        granted = dict(zip(permissions, grants))
        print(f"[APP] Permisos: {granted}")

        denied = [p for p, g in granted.items() if not g]
        if denied:
            names = [p.split('.')[-1] for p in denied]
            self.lbl_status.text = (
                f"⚠️  Permisos denegados:\n{', '.join(names)}\n\n"
                "El servicio puede no funcionar correctamente.\n"
                "Ve a Ajustes → Aplicaciones → Emergency Control → Permisos."
            )
        else:
            self.lbl_status.text = "✅ Permisos concedidos. Iniciando servicio…"

        # Arrancar el servicio independientemente (funciona para internet/polling
        # aunque CALL_PHONE sea denegado)
        self._start_service()

    # ── Servicio ────────────────────────────────────

    def _start_service(self):
        try:
            from android import AndroidService
            self.svc = AndroidService(
                title       = 'Emergency Control',
                description = 'Monitoreando en segundo plano'
            )
            self.svc.start('ok')

            if "✅" not in self.lbl_status.text and "⚠️" not in self.lbl_status.text:
                # Solo sobreescribir si no hay mensaje de permisos ya
                pass
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
