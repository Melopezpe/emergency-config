[app]
title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a,armeabi-v7a

# Arrancar automaticamente al encender el telefono
android.add_activities = org.phonecontrol.BootReceiver

[buildozer]
log_level = 2
warn_on_root = 1
