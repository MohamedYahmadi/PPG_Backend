-- ==============================================================================
-- SITP - Stratégie de Partitionnement et d'Indexation (Corrections CTO appliquées)
-- ==============================================================================

-- GPS Logs
CREATE TABLE gps_logs_y2026m04 PARTITION OF gps_logs FOR VALUES FROM ('2026-04-01 00:00:00') TO ('2026-05-01 00:00:00');
CREATE TABLE gps_logs_y2026m05 PARTITION OF gps_logs FOR VALUES FROM ('2026-05-01 00:00:00') TO ('2026-06-01 00:00:00');

-- Validation Logs
CREATE TABLE validation_logs_y2026m04 PARTITION OF validation_logs FOR VALUES FROM ('2026-04-01 00:00:00') TO ('2026-05-01 00:00:00');
CREATE TABLE validation_logs_y2026m05 PARTITION OF validation_logs FOR VALUES FROM ('2026-05-01 00:00:00') TO ('2026-06-01 00:00:00');

-- Audit Logs
CREATE TABLE audit_logs_y2026m04 PARTITION OF audit_logs FOR VALUES FROM ('2026-04-01 00:00:00') TO ('2026-05-01 00:00:00');
CREATE TABLE audit_logs_y2026m05 PARTITION OF audit_logs FOR VALUES FROM ('2026-05-01 00:00:00') TO ('2026-06-01 00:00:00');

-- PostGIS Spatial Indexes
CREATE INDEX idx_stations_location_gist ON stations USING GIST (location);
CREATE INDEX idx_gps_logs_location_gist ON gps_logs USING GIST (location);
CREATE INDEX idx_routes_path_geom_gist ON routes USING GIST (path_geom);
CREATE INDEX idx_validation_logs_location_gist ON validation_logs USING GIST (scan_location);

-- BRIN Indexes
CREATE INDEX idx_gps_logs_recorded_at_brin ON gps_logs USING BRIN (recorded_at);
CREATE INDEX idx_validation_logs_scanned_at_brin ON validation_logs USING BRIN (scanned_at);
CREATE INDEX idx_audit_logs_created_at_brin ON audit_logs USING BRIN (created_at);

-- ==============================================================================
-- PARTIAL INDEXES & CORRECTIONS (CTO Review)
-- Les fonctions mutables comme NOW() sont interdites dans un prédicat d'index.
-- ==============================================================================
-- 1. Index composite sur statut et validité (correction CTO)
CREATE INDEX idx_tickets_status_validity ON tickets (status, valid_until) 
WHERE status = 'ACTIVE';

-- 2. Index sur passenger_cin pour recherche foudroyante d'amendes (Correction CTO)
CREATE INDEX idx_fines_passenger_cin ON fines (passenger_cin);

-- 3. Accélérer la recherche d'amendes non payées
CREATE INDEX idx_fines_unpaid_lookup ON fines (passenger_cin) 
WHERE status = 'UNPAID';

-- B-TREE INDEXES (Foreign Keys)
CREATE INDEX idx_wallets_passenger ON wallets (passenger_id);
CREATE INDEX idx_wallet_transactions_wallet ON wallet_transactions (wallet_id);
CREATE INDEX idx_tickets_passenger ON tickets (passenger_id);
CREATE INDEX idx_validation_logs_ticket ON validation_logs (ticket_id);
CREATE INDEX idx_trips_route ON trips (route_id);
CREATE INDEX idx_trips_vehicle ON trips (vehicle_id);
CREATE INDEX idx_trips_driver ON trips (driver_id);
CREATE INDEX idx_gps_logs_trip ON gps_logs (trip_id);
CREATE INDEX idx_fines_controller ON fines (controller_id);
CREATE INDEX idx_disputes_fine ON disputes (fine_id);
CREATE INDEX idx_fraud_alerts_passenger ON fraud_alerts (passenger_id);
CREATE INDEX idx_notifications_user ON notifications (user_id);
