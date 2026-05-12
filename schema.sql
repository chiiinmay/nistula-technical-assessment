-- ==============================================================================
-- NISTULA UNIFIED MESSAGING PLATFORM SCHEMA
-- Version: 1.1
-- Author: Nagachinmay K N
-- ==============================================================================

-- Enable UUID for secure, non-sequential identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. PROPERTIES
-- Core entity representing managed villas.
-- ------------------------------------------------------------------------------
CREATE TABLE properties (
    property_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    base_rate_per_night DECIMAL(10, 2) NOT NULL CHECK (base_rate_per_night >= 0),
    max_guests INTEGER NOT NULL DEFAULT 1 CHECK (max_guests > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. GUESTS (UNIFIED IDENTITY)
-- Designed to consolidate guest data across multiple acquisition channels.
-- ------------------------------------------------------------------------------
CREATE TABLE guests (
    guest_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure at least one contact method exists
    CONSTRAINT guest_contact_info CHECK (email IS NOT NULL OR phone_number IS NOT NULL)
);

-- ------------------------------------------------------------------------------
-- 3. RESERVATIONS
-- Bridges the guest to the property with specific temporal constraints.
-- ------------------------------------------------------------------------------
CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_ref VARCHAR(100) UNIQUE NOT NULL, 
    guest_id UUID REFERENCES guests(guest_id) ON DELETE CASCADE,
    property_id VARCHAR(50) REFERENCES properties(property_id) ON DELETE RESTRICT,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('confirmed', 'cancelled', 'completed', 'in_house')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT date_validity CHECK (check_out_date > check_in_date)
);

-- ------------------------------------------------------------------------------
-- 4. CONVERSATIONS
-- A logical session grouping messages between a guest and the platform.
-- ------------------------------------------------------------------------------
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    guest_id UUID REFERENCES guests(guest_id) ON DELETE CASCADE,
    property_id VARCHAR(50) REFERENCES properties(property_id),
    reservation_id UUID REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 5. MESSAGES
-- The transaction log of all inbound and outbound communication.
-- ------------------------------------------------------------------------------
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    source_channel VARCHAR(50) NOT NULL CHECK (source_channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')),
    message_text TEXT NOT NULL,
    
    -- AI metadata for auditing and logic execution
    query_type VARCHAR(50),
    ai_confidence_score DECIMAL(3, 2) CHECK (ai_confidence_score BETWEEN 0 AND 1),
    ai_drafted_reply TEXT,
    
    -- Workflow state
    handling_status VARCHAR(50) NOT NULL CHECK (handling_status IN ('ai_drafted', 'agent_edited', 'auto_sent', 'escalated')),
    agent_id UUID, -- Links to an internal staff table
    
    external_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- INDEXES & OPTIMIZATIONS
-- ------------------------------------------------------------------------------
CREATE INDEX idx_msg_conv ON messages(conversation_id);
CREATE INDEX idx_conv_guest ON conversations(guest_id);
CREATE INDEX idx_res_ref ON reservations(booking_ref);
CREATE INDEX idx_msg_type ON messages(query_type) WHERE query_type IS NOT NULL;

-- ------------------------------------------------------------------------------
-- DESIGN DECISIONS & RATIONALE
-- ------------------------------------------------------------------------------
/*
1. Identity Normalization: The `guests` table enforces a check that at least one contact method (email/phone) 
   exists, while using UUIDs for internal references. This decouples guest identity from channel-specific IDs.

2. Referential Integrity: Used `ON DELETE CASCADE` for conversations when a guest is removed, but `ON DELETE RESTRICT` 
   for properties to prevent orphaned data if a villa is active in reservations.

3. Workflow Auditing: The `handling_status` and `ai_confidence_score` columns allow Nistula to run analytics 
   on AI performance (e.g., "Average confidence per channel" or "AI-to-Agent edit ratio").

4. Hardest Design Decision: 
   The most difficult trade-off was between a 'Flat' message table and a 'Scoped' one. 
   I chose to introduce `conversations` as a middleware layer. While it adds a join, it allows us 
   to link a guest's query specifically to a *Reservation* or a *Property Enquiry* without 
   duplicating that context in every single message row. This is critical for RAG (Retrieval Augmented Generation) 
   later on—the AI needs to know if it's talking to a "Checked-in Guest" vs a "Prospective Lead".
*/
