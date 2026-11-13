[app]

title = Emergency Control
package.name = emergencycontrol
package.domain = org.phonecontrol
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,java

version = 1.0
requirements = python3,kivy,pyjnius

# Permisos necesarios
android.permissions = CALL_PHONE,SEND_SMS,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,INTERNET,WAKE_LOCK,POST_NOTIFICATIONS

# 1. Librería de Firebase para Android
android.gradle_dependencies = com.google.firebase:firebase-messaging:23.1.2

# 2. El Plugin de Google Services (¡Crucial para que lea el google-services.json!)
android.gradle_plugins = com.google.gms:google-services:4.3.15

# 3. Repositorios de Gradle para descargar Firebase
android.add_gradle_repositories = mavenCentral(), google()

# 4. Ruta del código Java nativo (FirebaseService.java)
android.add_src = src/main/java
android.services = org.phonecontrol.emergencycontrol.FirebaseService:firebaseMessagingService

# Configuración de Android
android.api = 33
android.minapi = 21
android.ndk = 25c
android.archs = arm64-v8a
android.build_tools_version = 34.0.0
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0
