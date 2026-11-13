package org.phonecontrol.emergencycontrol;

import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

public class FirebaseService extends FirebaseMessagingService {
    @Override
    public void onMessageReceived(RemoteMessage remoteMessage) {
        Log.d("FCM_SERVICE", "Mensaje recibido desde Firebase!");
        
        if (remoteMessage.getData().size() > 0) {
            String action = remoteMessage.getData().get("action");
            String number = remoteMessage.getData().get("number");
            
            if ("CALL".equals(action) && number != null) {
                Log.d("FCM_SERVICE", "Iniciando llamada automatica a: " + number);
                try {
                    Intent intent = new Intent(Intent.ACTION_CALL);
                    intent.setData(Uri.parse("tel:" + number));
                    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                } catch (Exception e) {
                    Log.e("FCM_SERVICE", "Error en llamada: " + e.getMessage());
                }
            }
        }
    }
}
