[app]
title = Emergency Control
package.name = emergency
package.domain = org.melopezpe

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.include_patterns = service.py

version = 1.0

requirements = python3,kivy,pyjnius,android

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

android.permissions = INTERNET,CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,WAKE_LOCK,POST_NOTIFICATIONS,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS

# Nombre del servicio: se genera como <package>.Service<Name>
# -> org.melopezpe.emergency.ServiceEmergency
services = emergency:service.py

# No usar presplash por ahora
presplash.filename =
icon.filename =

[buildozer]
log_level = 2
warn_on_root = 0