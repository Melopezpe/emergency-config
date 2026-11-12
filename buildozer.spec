[app]

title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,java

version = 1.0
requirements = python3,kivy,pyjnius

# Conecta el hook de Python para inyectar el Java
p4a.hook = hook.py

android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS

android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
