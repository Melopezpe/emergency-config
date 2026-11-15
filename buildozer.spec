[app]
title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,java,xml

version = 2.0
requirements = python3,kivy,pyjnius

services = poller:pollservice.py:foreground

android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS,SYSTEM_ALERT_WINDOW,USE_FULL_SCREEN_INTENT,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,USE_EXACT_ALARM,SCHEDULE_EXACT_ALARM

android.api = 33
android.minapi = 23
android.ndk = 25c
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.accept_sdk_license = True
android.add_src = java
android.extra_manifest_xml = manifest_extras.xml

[buildozer]
log_level = 2
warn_on_root = 0
