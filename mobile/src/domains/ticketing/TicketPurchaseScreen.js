import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import axios from 'axios';

const TicketPurchaseScreen = ({ navigation }) => {
    const [loading, setLoading] = useState(false);

    const handlePurchase = async () => {
        setLoading(true);
        try {
            const response = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/tickets/purchase/`, {
                zone_validity: 'ZONE_A',
                price: 1.500
            }, {
                headers: { Authorization: `Bearer ${global.userToken}` }
            });
            
            Alert.alert("Succès", "Billet acheté avec succès !");
            navigation.navigate('QRDisplay', { ticket: response.data });
        } catch (error) {
            Alert.alert("Erreur", "Fonds insuffisants ou erreur système.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Achat Rapide</Text>
            <View style={styles.card}>
                <Text style={styles.zone}>Ticket Zone A (Métro/Bus)</Text>
                <Text style={styles.price}>1.500 TND</Text>
                <TouchableOpacity style={styles.button} onPress={handlePurchase} disabled={loading}>
                    <Text style={styles.buttonText}>{loading ? "Traitement..." : "Payer avec Wallet"}</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: '#f5f6fa' },
    title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
    card: { backgroundColor: '#fff', padding: 20, borderRadius: 10, elevation: 3 },
    zone: { fontSize: 18, color: '#2f3640', marginBottom: 10 },
    price: { fontSize: 28, fontWeight: 'bold', color: '#4cd137', marginBottom: 20 },
    button: { backgroundColor: '#00a8ff', padding: 15, borderRadius: 10, alignItems: 'center' },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});

export default TicketPurchaseScreen;
