# Emergency Control

App Android (Kivy + Buildozer) que:
- Lee la URL del servidor desde `Melopezpe/emergency-config/main/url.txt`.
- Hace polling a `/api/chat/poll_pc?since=<id>` cada 3 s.
- Ejecuta comandos recibidos: `NEWSERVER:`, `CALL:`, `SMS:`.
- Corre en segundo plano mediante un **foreground service**.

## Build

Push a `main` → GitHub Actions compila y publica el APK en Releases.

## Instalacion en el telefono

1. Instala el APK.
2. Concede permisos (telefono, SMS, notificaciones).
3. Acepta "Permitir sin restricciones" en bateria cuando se solicite.
4. En ajustes del fabricante (Xiaomi/Huawei/Samsung): marca la app como
   **sin restricciones de bateria** y **autoarranque** habilitado.
