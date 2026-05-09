import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import LoginScreen from '../domains/auth/LoginScreen';
import SignupScreen from '../domains/auth/SignupScreen';
import WalletScreen from '../domains/wallet/WalletScreen';
import TicketPurchaseScreen from '../domains/ticketing/TicketPurchaseScreen';
import QRDisplayScreen from '../domains/ticketing/QRDisplayScreen';
import LiveMapScreen from '../domains/transit/LiveMapScreen';

const Stack = createStackNavigator();

const AppNavigator = () => {
    return (
        <Stack.Navigator initialRouteName="Login">
            <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
            <Stack.Screen name="Signup" component={SignupScreen} options={{ headerShown: false }} />
            <Stack.Screen name="Wallet" component={WalletScreen} options={{ title: 'Mon Wallet' }} />
            <Stack.Screen name="TicketPurchase" component={TicketPurchaseScreen} options={{ title: 'Acheter un Billet' }} />
            <Stack.Screen name="QRDisplay" component={QRDisplayScreen} options={{ title: 'Mon Titre de Transport' }} />
            <Stack.Screen name="LiveMap" component={LiveMapScreen} options={{ title: 'Tracking en Direct' }} />
        </Stack.Navigator>
    );
};

export default AppNavigator;
