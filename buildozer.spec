[app]

title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,java

version = 1.0
# OBLIGAMOS a Buildozer a instalar el paquete local
requirements = python3,kivy,pyjnius,.

android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS

# Aquí le decimos a p4a que compile el servicio
android.add_src = src/main/java/org/phonecontrol/emergencycontrol/EmergencyService.java
android.services = org.phonecontrol.emergencycontrol.EmergencyService:foregroundServiceType=dataSync

android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
