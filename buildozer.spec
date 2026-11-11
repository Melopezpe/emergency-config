[app]

title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt

version = 1.0
requirements = python3,kivy,pyjnius

android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS

# ¡ESTA ES LA LÍNEA MÁGICA!
android.add_src = src

android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.accept_sdk_license = True
