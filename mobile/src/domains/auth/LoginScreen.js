import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import axios from 'axios';

const LoginScreen = ({ navigation }) => {
    const [phone, setPhone] = useState('+21699000000');
    const [password, setPassword] = useState('Passenger123!');

    const handleLogin = async () => {
        try {
            const response = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/auth/login/`, {
                phone_number: phone,
                password: password,
                device_id: 'device-003-passenger'
            });

            const token = response.data.access;
            global.userToken = token;
            navigation.replace('Wallet');
        } catch (error) {
            Alert.alert("Erreur", "Identifiants invalides");
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>SITP Passenger</Text>
            <TextInput
                style={styles.input}
                value={phone}
                onChangeText={setPhone}
                placeholder="Numéro de Téléphone"
                keyboardType="phone-pad"
            />
            <TextInput
                style={styles.input}
                value={password}
                onChangeText={setPassword}
                placeholder="Mot de passe"
                secureTextEntry
            />
            <TouchableOpacity style={styles.button} onPress={handleLogin}>
                <Text style={styles.buttonText}>Se Connecter</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.link} onPress={() => navigation.navigate('Signup')}>
                <Text style={styles.linkText}>Pas de compte ? Créer un compte</Text>
            </TouchableOpacity>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', padding: 20, backgroundColor: '#f5f6fa' },
    title: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', marginBottom: 40, color: '#2f3640' },
    input: { backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 15, fontSize: 16 },
    button: { backgroundColor: '#00a8ff', padding: 15, borderRadius: 10, alignItems: 'center' },
    buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
    link: { marginTop: 20, alignItems: 'center' },
    linkText: { color: '#00a8ff', fontSize: 16 }
});

export default LoginScreen;
