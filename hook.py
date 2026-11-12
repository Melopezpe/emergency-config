import os
import shutil

def before_apk_build(toolchain):
    print("=== INICIANDO HOOK PARA JAVA ===")
    # Buscar donde está el Manifest generado
    manifest_path = os.path.join(toolchain.ctx.dist_dir, "src", "main", "AndroidManifest.xml")
    
    if os.path.exists(manifest_path):
        # 1. Copiar el Java a la carpeta correcta de Gradle
        java_dir = os.path.join(toolchain.ctx.dist_dir, "src", "main", "java", "org", "phonecontrol", "emergencycontrol")
        os.makedirs(java_dir, exist_ok=True)
        shutil.copy("EmergencyService.java", os.path.join(java_dir, "EmergencyService.java"))
        
        # 2. Modificar el Manifest
        with open(manifest_path, "r") as f:
            content = f.read()
            
        service_tag = '<service android:name="org.phonecontrol.emergencycontrol.EmergencyService" android:foregroundServiceType="dataSync" android:exported="false" />'
        
        if "EmergencyService" not in content:
            content = content.replace("</application>", service_tag + "\n    </application>")
            with open(manifest_path, "w") as f:
                f.write(content)
            print("=== JAVA INYECTADO CORRECTAMENTE ===")
        else:
            print("=== EL JAVA YA ESTABA EN EL MANIFEST ===")
    else:
        print("=== ERROR: NO SE ENCUENTRA EL MANIFEST ===")
