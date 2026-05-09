import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import QRCode from 'react-native-qrcode-svg';
import CryptoEngine from './CryptoEngine';

const QRDisplayScreen = ({ route }) => {
    const { ticket } = route.params;
    const [qrData, setQrData] = useState('');

    useEffect(() => {
        // DÉCISION CTO : Le QR Code est généré dynamiquement en local pour contrer le clonage visuel.
        const updateQR = () => {
            const secret = 'JBSWY3DPEHPK3PXP'; 
            const payload = CryptoEngine.generateDynamicQRData(ticket.id, secret, 'simulated_private_key');
            setQrData(payload);
        };

        updateQR();
        const interval = setInterval(updateQR, 30000); // 30 secondes
        return () => clearInterval(interval);
    }, [ticket.id]);

    return (
        <View style={styles.container}>
            <Text style={styles.warning}>Présentez ce code au contrôleur</Text>
            <View style={styles.qrContainer}>
                {qrData ? <QRCode value={qrData} size={250} /> : null}
            </View>
            <Text style={styles.ticketId}>ID: {ticket.id}</Text>
            <Text style={styles.info}>Validité: {ticket.zone_validity}</Text>
            <Text style={styles.info}>Moteur Ed25519 Actif</Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f5f6fa' },
    warning: { fontSize: 16, color: '#e84118', fontWeight: 'bold', marginBottom: 30 },
    qrContainer: { padding: 20, backgroundColor: '#fff', borderRadius: 15, elevation: 5 },
    ticketId: { marginTop: 30, fontSize: 12, color: '#7f8fa6' },
    info: { marginTop: 10, fontSize: 18, fontWeight: 'bold' }
});

export default QRDisplayScreen;
