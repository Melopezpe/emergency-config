import os
import shutil

def before_apk_build(toolchain):
    print("=== INICIANDO HOOK PARA JAVA ===")
    manifest_path = os.path.join(toolchain.ctx.dist_dir, "src", "main", "AndroidManifest.xml")
    
    if os.path.exists(manifest_path):
        java_dir = os.path.join(toolchain.ctx.dist_dir, "src", "main", "java", "org", "phonecontrol", "emergencycontrol")
        os.makedirs(java_dir, exist_ok=True)
        shutil.copy("EmergencyService.java", os.path.join(java_dir, "EmergencyService.java"))
        
        with open(manifest_path, "r") as f:
            content = f.read()
            
        service_tag = '<service android:name="org.phonecontrol.emergencycontrol.EmergencyService" android:foregroundServiceType="dataSync" android:exported="false" />'
        
        if "EmergencyService" not in content:
            content = content.replace("</application>", service_tag + "\n    </application>")
            with open(manifest_path, "w") as f:
                f.write(content)
            print("=== JAVA INYECTADO CORRECTAMENTE ===")
    else:
        print("=== ERROR: NO SE ENCUENTRA EL MANIFEST ===")
