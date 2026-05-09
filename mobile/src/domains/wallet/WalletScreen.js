import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import axios from 'axios';

const WalletScreen = ({ navigation }) => {
    const [balance, setBalance] = useState(null);

    useEffect(() => {
        const unsubscribe = navigation.addListener('focus', () => {
            fetchWallet();
        });
        return unsubscribe;
    }, [navigation]);

    const fetchWallet = async () => {
        try {
            const response = await axios.get(`${process.env.EXPO_PUBLIC_API_URL}/wallet/`, {
                headers: { Authorization: `Bearer ${global.userToken}` }
            });
            setBalance(response.data.balance);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.label}>Solde Actuel</Text>
            {balance !== null ? (
                <Text style={styles.balance}>{balance} TND</Text>
            ) : (
                <ActivityIndicator size="large" color="#00a8ff" />
            )}

            <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('TicketPurchase')}>
                <Text style={styles.buttonText}>Acheter un Billet</Text>
            </TouchableOpacity>

            <TouchableOpacity style={[styles.button, styles.secondaryButton]} onPress={() => navigation.navigate('LiveMap')}>
                <Text style={styles.buttonText}>Live Tracking (Bus)</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, alignItems: 'center', padding: 20, backgroundColor: '#f5f6fa' },
    label: { fontSize: 20, color: '#7f8fa6', marginTop: 40 },
    balance: { fontSize: 48, fontWeight: 'bold', color: '#2f3640', marginBottom: 60 },
    button: { backgroundColor: '#4cd137', padding: 15, borderRadius: 10, width: '100%', alignItems: 'center', marginBottom: 15 },
    secondaryButton: { backgroundColor: '#e1b12c' },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});

export default WalletScreen;
