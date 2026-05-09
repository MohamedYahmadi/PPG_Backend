import React, { useEffect, useState } from 'react';
import { View, StyleSheet } from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import LiveMapService from './LiveMapService';

const LiveMapScreen = () => {
    const [busLocation, setBusLocation] = useState(null);

    useEffect(() => {
        const liveService = new LiveMapService("123", global.userToken);
        
        liveService.connect((lat, lng) => {
            setBusLocation({ latitude: lat, longitude: lng });
        });

        return () => liveService.disconnect();
    }, []);

    return (
        <View style={styles.container}>
            <MapView 
                style={styles.map}
                initialRegion={{
                    latitude: 36.8065,
                    longitude: 10.1815,
                    latitudeDelta: 0.0922,
                    longitudeDelta: 0.0421,
                }}
            >
                {busLocation && (
                    <Marker coordinate={busLocation} title="Bus TGM" description="En approche" pinColor="blue" />
                )}
            </MapView>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1 },
    map: { width: '100%', height: '100%' }
});

export default LiveMapScreen;
