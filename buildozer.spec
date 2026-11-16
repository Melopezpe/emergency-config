[app]
title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json

version = 2.0
requirements = python3,kivy,pyjnius,android

# ── Servicio de fondo ──────────────────────────────────────────────────────
# Formato: NombreVisible:ruta/al/entry_point.py:foreground
# "foreground" le dice a p4a que lo arranque como ForegroundService
# y que Android lo reinicie si lo mata (START_STICKY).
services = EmergencyService:./service/main.py:foreground

# ── Permisos ───────────────────────────────────────────────────────────────
android.permissions = \
    CALL_PHONE,\
    SEND_SMS,\
    INTERNET,\
    WAKE_LOCK,\
    RECEIVE_BOOT_COMPLETED,\
    FOREGROUND_SERVICE,\
    FOREGROUND_SERVICE_PHONE_CALL,\
    POST_NOTIFICATIONS,\
    SCHEDULE_EXACT_ALARM

# ── Android SDK ────────────────────────────────────────────────────────────
android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.accept_sdk_license = True

# Incluye el directorio del servicio en el APK
android.add_src = service

[buildozer]
log_level = 2
warn_on_root = 0
