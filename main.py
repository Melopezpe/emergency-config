"""
main.py – Diagnóstico + permisos robustos + servicio.
"""
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform

LOG = []

def log(msg):
    print(msg)
    LOG.append(msg)


class EmergencyApp(App):

    def build(self):
        self.title = "Emergency Control"
        root = BoxLayout(orientation='vertical', padding=16, spacing=10)

        scroll = ScrollView(size_hint=(1, 0.75))
        self.lbl = Label(
            text="Iniciando…",
            font_size='13sp',
            halign='left',
            valign='top',
            size_hint_y=None
        )
        self.lbl.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
        self.lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        scroll.add_widget(self.lbl)
        root.add_widget(scroll)

        btn112 = Button(
            text="LLAMAR 112",
            size_hint_y=None, height=60,
            background_color=(0.85, 0.15, 0.25, 1)
        )
        btn112.bind(on_press=lambda _: self._call("112"))
        root.add_widget(btn112)

        btn_perm = Button(
            text="🔑 Conceder permisos manualmente",
            size_hint_y=None, height=50,
            background_color=(0.2, 0.5, 0.9, 1)
        )
        btn_perm.bind(on_press=lambda _: self._open_app_settings())
        root.add_widget(btn_perm)

        return root

    def _ui(self, msg):
        self.lbl.text = msg

    # ── Ciclo de vida ───────────────────────────────────────

    def on_start(self):
        log(f"[APP] platform={platform}")
        if platform == 'android':
            Clock.schedule_once(self._check_and_request, 1.5)
        else:
            self._ui("Escritorio: sin permisos Android")

    # ── Permisos ────────────────────────────────────────────

    def _check_and_request(self, dt):
        try:
            from android.permissions import (
                request_permissions, check_permission, Permission
            )

            # Solo pedir los PELIGROSOS que Android muestra en diálogo
            candidates = {
                'CALL_PHONE':        Permission.CALL_PHONE,
                'SEND_SMS':          Permission.SEND_SMS,
            }
            # POST_NOTIFICATIONS solo existe en Android 13+
            try:
                candidates['POST_NOTIFICATIONS'] = Permission.POST_NOTIFICATIONS
            except AttributeError:
                log("[PERM] POST_NOTIFICATIONS no disponible (Android < 13)")

            # Ver cuáles ya están concedidos
            status = {name: check_permission(p) for name, p in candidates.items()}
            log(f"[PERM] Estado actual: {status}")

            needed = [p for name, p in candidates.items() if not status[name]]
            granted_names = [n for n, g in status.items() if g]
            denied_names  = [n for n, g in status.items() if not g]

            if not needed:
                self._ui("✅ Todos los permisos ya concedidos.\nArrancando servicio…")
                log("[PERM] Todo concedido, arrancando servicio")
                self._start_service()
                return

            self._ui(
                f"✅ Concedidos: {', '.join(granted_names) or 'ninguno'}\n"
                f"⏳ Solicitando: {', '.join(denied_names)}\n\n"
                "Acepta el diálogo que aparecerá…"
            )
            log(f"[PERM] Pidiendo: {denied_names}")
            request_permissions(needed, self._on_result)

        except Exception as e:
            log(f"[PERM] Excepción: {e}")
            self._ui(f"Error en permisos:\n{e}\n\nArrancando servicio de todas formas…")
            self._start_service()

    def _on_result(self, permissions, grants):
        result = dict(zip(permissions, grants))
        log(f"[PERM] Resultado: {result}")

        denied = [p.split('.')[-1] for p, g in result.items() if not g]

        if denied:
            self._ui(
                f"⚠️ Denegados: {', '.join(denied)}\n\n"
                "Pulsa el botón azul para ir a Ajustes\n"
                "y concederlos manualmente.\n\n"
                "El servicio arrancará de todas formas\n"
                "(sin CALL_PHONE no podrá llamar)."
            )
        else:
            self._ui("✅ Permisos concedidos. Arrancando servicio…")

        self._start_service()

    def _open_app_settings(self):
        """Abre la pantalla de permisos de esta app en Ajustes del sistema."""
        try:
            from jnius import autoclass
            Intent   = autoclass('android.content.Intent')
            Uri      = autoclass('android.net.Uri')
            Settings = autoclass('android.provider.Settings')
            Activity = autoclass('org.kivy.android.PythonActivity')

            intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            intent.setData(Uri.parse(
                'package:' + Activity.mActivity.getPackageName()
            ))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            Activity.mActivity.startActivity(intent)
        except Exception as e:
            log(f"[SETTINGS] Error: {e}")
            self._ui(f"No se pudo abrir Ajustes:\n{e}")

    # ── Servicio ────────────────────────────────────────────

    def _start_service(self):
        try:
            from android import AndroidService
            self.svc = AndroidService(
                title       = 'Emergency Control',
                description = 'Monitoreando en segundo plano'
            )
            self.svc.start('ok')
            log("[APP] Servicio arrancado")
            # Añadir confirmación sin borrar el mensaje de permisos
            current = self.lbl.text
            self._ui(current + "\n\n✅ Servicio activo.\nPuedes cerrar esta pantalla.")
        except Exception as e:
            log(f"[APP] Error servicio: {e}")
            self._ui(self.lbl.text + f"\n\n⚠️ Error servicio:\n{e}")

    # ── Llamada manual ───────────────────────────────────────

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
                log(f"[CALL] Error: {e}")

    def on_stop(self):
        pass


if __name__ == '__main__':
    EmergencyApp().run()
