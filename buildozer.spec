[app]

# (str) Title of your application
title = Emergency Control

# (str) Package name
package.name = emergencycontrol

# (str) Package domain (needed for android packaging)
package.domain = org.phonecontrol

# (str) Source files where the let's go
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,txt

# (list) Application version
version = 1.0

# (list) Application requirements
requirements = python3,kivy,pyjnius

# (list) Permissions (AÑADIDO POST_NOTIFICATIONS)
android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (int) Android NDK version to use
android.ndk = 25c

# (str) Android archs to build for
android.archs = arm64-v8a

# (str) Android build tools version
android.build_tools_version = 34.0.0

# (Bool) Accept SDK license
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (default))
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 0
