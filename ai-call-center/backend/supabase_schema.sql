-- ============================================================================
-- AI Call Center - Supabase Database Schema
-- ============================================================================
-- Run this in your Supabase SQL Editor (Dashboard → SQL Editor → New Query)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- INTERACTIONS TABLE
-- Stores all customer interaction sessions
-- ============================================================================
CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id TEXT,
    channel TEXT NOT NULL DEFAULT 'chat',
    status TEXT NOT NULL DEFAULT 'active',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_channel CHECK (channel IN ('chat', 'voice', 'web')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'in_progress', 'completed', 'escalated', 'abandoned'))
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_interactions_status ON interactions(status);
CREATE INDEX IF NOT EXISTS idx_interactions_started_at ON interactions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_customer_id ON interactions(customer_id);

-- ============================================================================
-- MESSAGES TABLE
-- Stores all messages within interactions
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id UUID NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('customer', 'agent', 'system'))
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_messages_interaction_id ON messages(interaction_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);

-- ============================================================================
-- AGENT DECISIONS TABLE
-- Stores decisions made by AI agents
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id UUID NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    decision_summary TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,
    confidence_level TEXT NOT NULL,
    processing_time_ms INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reasoning TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Constraints
    CONSTRAINT valid_agent_type CHECK (agent_type IN ('primary', 'supervisor', 'escalation')),
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT valid_confidence_level CHECK (confidence_level IN ('high', 'medium', 'low'))
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_decisions_interaction_id ON agent_decisions(interaction_id);
CREATE INDEX IF NOT EXISTS idx_decisions_agent_type ON agent_decisions(agent_type);
CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON agent_decisions(timestamp);

-- ============================================================================
-- AGENT CONFIGS TABLE
-- Stores configurable agent prompts and settings
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_configs (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    description TEXT,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    output_schema JSONB DEFAULT '{}',
    model TEXT DEFAULT 'gpt-4o-mini',
    temperature DECIMAL(2,1) DEFAULT 0.3,
    max_tokens INTEGER DEFAULT 1024,
    top_p DECIMAL(2,1) DEFAULT 1.0,
    confidence_threshold DECIMAL(2,1) DEFAULT 0.7,
    fallback_enabled BOOLEAN DEFAULT true,
    is_custom BOOLEAN DEFAULT false,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by TEXT,
    
    -- Constraints
    CONSTRAINT valid_agent_type_config CHECK (agent_type IN ('primary', 'supervisor', 'escalation'))
);

-- ============================================================================
-- AUDIT LOGS TABLE
-- Stores audit trail for compliance
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id UUID REFERENCES interactions(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    agent_type TEXT,
    decision_outcome TEXT,
    confidence_score DECIMAL(3,2),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_audit_interaction_id ON audit_logs(interaction_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);

-- ============================================================================
-- ROW LEVEL SECURITY (Optional - Enable for multi-tenancy)
-- ============================================================================

-- Uncomment these if you want to enable RLS for multi-tenancy:

-- ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_decisions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for interactions table
DROP TRIGGER IF EXISTS update_interactions_updated_at ON interactions;
CREATE TRIGGER update_interactions_updated_at
    BEFORE UPDATE ON interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for agent_configs table
DROP TRIGGER IF EXISTS update_agent_configs_updated_at ON agent_configs;
CREATE TRIGGER update_agent_configs_updated_at
    BEFORE UPDATE ON agent_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS (Optional - for easier querying)
-- ============================================================================

-- View for interaction summaries
CREATE OR REPLACE VIEW interaction_summaries AS
SELECT 
    i.id,
    i.customer_id,
    i.channel,
    i.status,
    i.started_at,
    i.ended_at,
    EXTRACT(EPOCH FROM (COALESCE(i.ended_at, NOW()) - i.started_at)) as duration_seconds,
    COUNT(DISTINCT m.id) as message_count,
    COUNT(DISTINCT d.id) as decision_count,
    BOOL_OR(i.status = 'escalated') as was_escalated
FROM interactions i
LEFT JOIN messages m ON m.interaction_id = i.id
LEFT JOIN agent_decisions d ON d.interaction_id = i.id
GROUP BY i.id, i.customer_id, i.channel, i.status, i.started_at, i.ended_at;

-- ============================================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================================

-- Uncomment to insert sample agent configs:

-- INSERT INTO agent_configs (id, agent_name, agent_type, description, system_prompt, user_prompt_template)
-- VALUES 
-- ('primary', 'Primary Interaction Agent', 'primary', 'First point of contact', 'You are a helpful AI assistant...', '## Customer Message\n{customer_message}'),
-- ('supervisor', 'Supervisor Review Agent', 'supervisor', 'Reviews decisions', 'You are a supervisor agent...', '## Review\n{decision}'),
-- ('escalation', 'Escalation Decision Agent', 'escalation', 'Handles escalations', 'You decide when to escalate...', '## Situation\n{context}')
-- ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- DONE! Your database is ready.
-- ============================================================================
