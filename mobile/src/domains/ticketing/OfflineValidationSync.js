import { database } from '../../core/database';
import { Q } from '@nozbe/watermelondb';
import axios from 'axios';

/**
 * DÉCISION CTO : Worker de Synchronisation asynchrone (Eventual Consistency).
 * Les contrôleurs valident les tickets dans des zones blanches (métro).
 * Dès que le réseau revient (4G), ce worker vide la queue SQLite locale (PENDING)
 * vers l'API Backend. Le Backend déclenche alors Celery pour chasser la Fraude.
 */
class OfflineValidationSync {
    
    static async syncPendingLogs(token) {
        try {
            const validationLogsCollection = database.get('validation_logs');
            const pendingLogs = await validationLogsCollection.query(
                Q.where('sync_status', 'PENDING')
            ).fetch();

            if (pendingLogs.length === 0) return;

            // Formater le batch pour l'API Django
            const payload = pendingLogs.map(log => ({
                ticket_id: log.ticket_id,
                scan_location_lat: log.scan_location_lat,
                scan_location_lng: log.scan_location_lng,
                scanned_at: new Date(log.scanned_at).toISOString(),
                is_cryptographically_valid: log.is_cryptographically_valid,
                device_id: 'terminal_001_mobile'
            }));

            // Envoi HTTP réseau
            const response = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/tickets/validate/sync/`, payload, {
                headers: { Authorization: `Bearer ${token}` }
            });

            if (response.status === 201) {
                // Succès : Marquer SYNCED en SQLite
                await database.write(async () => {
                    for (const log of pendingLogs) {
                        await log.update(l => {
                            l.sync_status = 'SYNCED';
                        });
                    }
                });
                console.log(`[SYNC] ${pendingLogs.length} validations envoyées et sécurisées.`);
            }

        } catch (error) {
            console.error("[SYNC_ERROR] Echec de la synchronisation.", error);
        }
    }
}

export default OfflineValidationSync;
