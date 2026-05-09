-- ==============================================================================
-- SITP (Smart Intelligent Transit Platform) - DDL SQL Production-Grade
-- Auteur: CTO / Architecte Senior
-- Base de données: PostgreSQL 15+
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ==============================================================================
-- 1. TYPES & ENUMS
-- ==============================================================================
CREATE TYPE user_role AS ENUM ('PASSENGER', 'DRIVER', 'CONTROLLER', 'ADMIN', 'SUPER_ADMIN');
CREATE TYPE transaction_type AS ENUM ('CREDIT_RECHARGE', 'DEBIT_TICKET', 'REFUND_DISPUTE', 'DEBIT_FINE');
CREATE TYPE ticket_status AS ENUM ('ACTIVE', 'EXPIRED', 'USED', 'FRAUDULENT');
CREATE TYPE validation_status AS ENUM ('PENDING_SYNC', 'SYNCED', 'FLAGGED_REPLAY');
CREATE TYPE fine_status AS ENUM ('UNPAID', 'PAID', 'DISPUTED', 'UNPAID_PENALTY', 'CANCELLED');
CREATE TYPE dispute_status AS ENUM ('OPEN', 'UNDER_REVIEW', 'RESOLVED_REJECTED', 'RESOLVED_ACCEPTED');

-- ==============================================================================
-- 2. TRIGGERS & FUNCTIONS (Zero Trust, Append-Only, Auto-Update)
-- ==============================================================================
CREATE OR REPLACE FUNCTION prevent_update_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'CRITICAL SECURITY: This table is strictly append-only. UPDATE and DELETE operations are forbidden.';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- 3. DOMAINE : AUTHENTIFICATION & RBAC
-- ==============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL, -- Correction: VARCHAR(20)
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    fcm_token VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- 4. DOMAINE : WALLET & PAIEMENT
-- ==============================================================================
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passenger_id UUID UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
    balance NUMERIC(12,3) NOT NULL DEFAULT 0.000,
    currency VARCHAR(3) DEFAULT 'TND',
    last_synced TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_positive_balance CHECK (balance >= 0.000)
);

CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_id UUID REFERENCES wallets(id) ON DELETE RESTRICT,
    amount NUMERIC(12,3) NOT NULL,
    type transaction_type NOT NULL,
    reference_id UUID, 
    payment_gateway_ref VARCHAR(100), 
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT check_non_zero_amount CHECK (amount != 0.000) -- Correction: Interdit les transactions nulles
);
CREATE TRIGGER enforce_append_only_wallet_transactions BEFORE UPDATE OR DELETE ON wallet_transactions FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();

-- ==============================================================================
-- 5. DOMAINE : TICKETING & VALIDATION
-- ==============================================================================
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passenger_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    price_paid NUMERIC(12,3) NOT NULL,
    zone_validity VARCHAR(50) NOT NULL,
    cryptographic_signature TEXT NOT NULL, 
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NOT NULL,
    status ticket_status DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE validation_logs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE RESTRICT,
    controller_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    scan_location GEOMETRY(Point, 4326) NOT NULL, 
    scanned_at TIMESTAMPTZ NOT NULL,
    is_cryptographically_valid BOOLEAN NOT NULL,
    sync_status validation_status DEFAULT 'PENDING_SYNC',
    device_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- ==============================================================================
-- 6. DOMAINE : AMENDES & LITIGES
-- ==============================================================================
CREATE TABLE fines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    controller_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    passenger_cin VARCHAR(20) NOT NULL, 
    passenger_name VARCHAR(100),
    amount NUMERIC(12,3) NOT NULL,
    reason TEXT NOT NULL,
    infraction_location GEOMETRY(Point, 4326),
    status fine_status DEFAULT 'UNPAID',
    proof_photo_url VARCHAR(255), 
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TRIGGER update_fines_updated_at BEFORE UPDATE ON fines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE disputes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fine_id UUID REFERENCES fines(id) ON DELETE RESTRICT,
    passenger_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    reason TEXT NOT NULL,
    proof_url VARCHAR(255),
    status dispute_status DEFAULT 'OPEN',
    admin_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TRIGGER update_disputes_updated_at BEFORE UPDATE ON disputes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- 7. DOMAINE : FRAUDE, NOTIFICATIONS & ADMIN ACTIONS (Nouveaux)
-- ==============================================================================
CREATE TABLE fraud_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    passenger_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    ticket_id UUID REFERENCES tickets(id) ON DELETE RESTRICT,
    reason TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'HIGH',
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TRIGGER update_fraud_alerts_updated_at BEFORE UPDATE ON fraud_alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE admin_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    action VARCHAR(255) NOT NULL,
    target_entity VARCHAR(100),
    target_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 8. DOMAINE : TRANSPORT & TRACKING
-- ==============================================================================
CREATE TABLE lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    color_code VARCHAR(7),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    line_id UUID REFERENCES lines(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    path_geom GEOMETRY(LineString, 4326) NOT NULL, 
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    has_kiosk BOOLEAN DEFAULT FALSE
);

CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plate_number VARCHAR(50) UNIQUE NOT NULL,
    fleet_id VARCHAR(50) UNIQUE NOT NULL,
    capacity INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID REFERENCES routes(id) ON DELETE RESTRICT,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE RESTRICT,
    driver_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    scheduled_start TIMESTAMPTZ NOT NULL,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'SCHEDULED'
);

CREATE TABLE gps_logs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE RESTRICT,
    vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    location GEOMETRY(Point, 4326) NOT NULL,
    speed_kmh NUMERIC(5,2) NOT NULL,
    heading NUMERIC(5,2), -- Correction: NUMERIC(5,2)
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- ==============================================================================
-- 9. DOMAINE : AUDIT
-- ==============================================================================
CREATE TABLE audit_logs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    action VARCHAR(100) NOT NULL,
    target_table VARCHAR(50) NOT NULL,
    target_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE TRIGGER enforce_append_only_audit_logs BEFORE UPDATE OR DELETE ON audit_logs FOR EACH ROW EXECUTE FUNCTION prevent_update_delete();
