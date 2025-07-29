-- AI Chatbot Database Schema for Supabase (UUID version)
-- Run these commands in your Supabase SQL editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing tables if they exist (to start fresh)
DROP TABLE IF EXISTS summaries CASCADE;
DROP TABLE IF EXISTS analytics CASCADE;
DROP TABLE IF EXISTS memory_vectors CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table with UUID
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory vectors table for conversation storage
CREATE TABLE memory_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    embedding vector(384), -- Adjust dimension based on your embedding model
    conversation_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics table for tracking usage
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    estimated_cost DECIMAL(10, 6) DEFAULT 0.00,
    conversation_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Summaries table for conversation summaries
CREATE TABLE summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id VARCHAR(255),
    summary TEXT NOT NULL,
    messages_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_memory_vectors_user_id ON memory_vectors(user_id);
CREATE INDEX idx_memory_vectors_conversation_id ON memory_vectors(conversation_id);
CREATE INDEX idx_memory_vectors_created_at ON memory_vectors(created_at);
CREATE INDEX idx_analytics_user_id ON analytics(user_id);
CREATE INDEX idx_analytics_created_at ON analytics(created_at);
CREATE INDEX idx_analytics_provider ON analytics(provider);
CREATE INDEX idx_analytics_model ON analytics(model);
CREATE INDEX idx_summaries_user_id ON summaries(user_id);
CREATE INDEX idx_summaries_conversation_id ON summaries(conversation_id);

-- Create a function for vector similarity search (UUID version)
CREATE OR REPLACE FUNCTION match_memory_vectors(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 4,
    p_user_id uuid DEFAULT NULL,
    p_conversation_id varchar DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    user_id uuid,
    role varchar,
    content text,
    conversation_id varchar,
    similarity float,
    created_at timestamp with time zone
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        memory_vectors.id,
        memory_vectors.user_id,
        memory_vectors.role,
        memory_vectors.content,
        memory_vectors.conversation_id,
        (memory_vectors.embedding <#> query_embedding) * -1 AS similarity,
        memory_vectors.created_at
    FROM memory_vectors
    WHERE 
        (p_user_id IS NULL OR memory_vectors.user_id = p_user_id)
        AND (p_conversation_id IS NULL OR memory_vectors.conversation_id = p_conversation_id)
        AND (memory_vectors.embedding <#> query_embedding) * -1 > match_threshold
    ORDER BY memory_vectors.embedding <#> query_embedding
    LIMIT match_count;
END;
$$;

-- Enable RLS (Row Level Security)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_vectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Enable read access for users to their own data" ON users
    FOR SELECT USING (true); -- Allow public read for login functionality

CREATE POLICY "Enable insert for registration" ON users
    FOR INSERT WITH CHECK (true); -- Allow registration

CREATE POLICY "Enable update for users on their own data" ON users
    FOR UPDATE USING (id = auth.uid());

-- Create policies for memory_vectors table
CREATE POLICY "Enable read access for users to their own vectors" ON memory_vectors
    FOR SELECT USING (true); -- We'll handle user filtering in the application

CREATE POLICY "Enable insert for users on their own vectors" ON memory_vectors
    FOR INSERT WITH CHECK (true); -- We'll handle user validation in the application

CREATE POLICY "Enable delete for users on their own vectors" ON memory_vectors
    FOR DELETE USING (true); -- We'll handle user validation in the application

-- Create policies for analytics table
CREATE POLICY "Enable read access for users to their own analytics" ON analytics
    FOR SELECT USING (true); -- We'll handle user filtering in the application

CREATE POLICY "Enable insert for users on their own analytics" ON analytics
    FOR INSERT WITH CHECK (true); -- We'll handle user validation in the application

-- Create policies for summaries table
CREATE POLICY "Enable read access for users to their own summaries" ON summaries
    FOR SELECT USING (true); -- We'll handle user filtering in the application

CREATE POLICY "Enable insert for users on their own summaries" ON summaries
    FOR INSERT WITH CHECK (true); -- We'll handle user validation in the application

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert a default admin user (change password before deployment!)
INSERT INTO users (username, password_hash, is_admin, email)
VALUES (
    'admin',
    '$2b$12$aoDovi744rJ8xSgXkjD1eexYra1cuiPXnUaEIBheu7uQIZmuyYnNK', -- password: 'admin123'
    true,
    'admin@example.com'
) ON CONFLICT (username) DO NOTHING;

-- Verify the setup
DO $$
BEGIN
    RAISE NOTICE 'Database schema setup completed successfully!';
    RAISE NOTICE 'Tables created: users, memory_vectors, analytics, summaries';
    RAISE NOTICE 'Default admin user: username=admin, password=admin123';
    RAISE NOTICE 'Please change the admin password after first login!';
END
$$;