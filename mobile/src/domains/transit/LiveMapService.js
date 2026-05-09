/**
 * DÉCISION CTO : Ingestion & Diffusion GPS WebSockets.
 * 
 * - Si le User est DRIVER : Il émet sa coordonnée GPS toutes les 2 secondes vers Channels.
 * - Si le User est PASSENGER : Il écoute la route sur laquelle il clique pour voir le bus sur Leaflet/Mapbox.
 */
class LiveMapService {
    constructor(tripId, token) {
        // En local, on vise localhost:8000
        this.wsUrl = `ws://192.168.1.14:8000/ws/transit/trip/${tripId}/?token=${token}`;
        this.socket = null;
    }

    connect(onMessageCallback) {
        this.socket = new WebSocket(this.wsUrl);

        this.socket.onopen = () => {
            console.log('[WEBSOCKET] Connecté au serveur de Tracking SITP.');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'gps_update') {
                // Appel callback pour redessiner le marqueur du bus sur Mapbox/Leaflet
                onMessageCallback(data.payload.lat, data.payload.lng);
            }
        };

        this.socket.onclose = () => {
            console.log('[WEBSOCKET] Déconnecté. Reconnexion auto en cours...');
            // Implémenter logique de retry (Exponential backoff)
        };
    }

    sendGpsDriver(lat, lng, speed, heading) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'driver_gps_push',
                payload: { lat, lng, speed, heading }
            }));
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

export default LiveMapService;
