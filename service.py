"""
Foreground service: mantiene el polling vivo aunque la UI se cierre.
"""
import time
import threading

from jnius import autoclass, cast

PythonService = autoclass('org.kivy.android.PythonService')
service = PythonService.mService


def start_foreground():
    Context            = autoclass('android.content.Context')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    PendingIntent       = autoclass('android.app.PendingIntent')
    Intent              = autoclass('android.content.Intent')
    Build               = autoclass('android.os.Build$VERSION')

    channel_id = "emergency_channel"
    nm = cast('android.app.NotificationManager',
              service.getSystemService(Context.NOTIFICATION_SERVICE))

    if Build.SDK_INT >= 26:
        ch = NotificationChannel(
            channel_id, "Emergency", NotificationManager.IMPORTANCE_LOW)
        nm.createNotificationChannel(ch)

    # PendingIntent para abrir la app al tocar la notificacion
    launch_intent = service.getPackageManager().getLaunchIntentForPackage(
        service.getPackageName())
    flags = PendingIntent.FLAG_UPDATE_CURRENT
    if Build.SDK_INT >= 23:
        flags |= PendingIntent.FLAG_IMMUTABLE
    pi = PendingIntent.getActivity(service, 0, launch_intent, flags)

    notif = NotificationBuilder(service, channel_id) \
        .setContentTitle("Emergency Control") \
        .setContentText("Servicio activo") \
        .setSmallIcon(service.getApplicationInfo().icon) \
        .setContentIntent(pi) \
        .setOngoing(True) \
        .build()

    service.startForeground(1, notif)


def loop():
    # Importa la logica de main.py (mismo directorio, empaquetado junto)
    from main import poll_server, fetch_url_from_github, server_url
    github_check = 0
    while True:
        if github_check <= 0:
            current_url = fetch_url_from_github()
            github_check = 60
        else:
            current_url = server_url
            github_check -= 3
        try:
            poll_server(current_url)
        except Exception as e:
            print("SERVICE POLL ERROR:", e)
        time.sleep(3)


if __name__ == '__main__':
    start_foreground()
    threading.Thread(target=loop, daemon=True).start()
    # Mantener el proceso del servicio vivo
    while True:
        time.sleep(60)