-- Football Club Management System Database Schema
-- Created: November 2025
-- Version: 2.0.0

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS player_statistics;
DROP TABLE IF EXISTS match_events;
DROP TABLE IF EXISTS match_players;
DROP TABLE IF EXISTS player_contracts;
DROP TABLE IF EXISTS player_photos;
DROP TABLE IF EXISTS training_attendance;
DROP TABLE IF EXISTS training_sessions;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS positions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS settings;

-- Roles table
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table (for authentication)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    last_login TIMESTAMP,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- Positions table
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    short_name VARCHAR(5) NOT NULL,
    position_type VARCHAR(20) NOT NULL, -- 'Goalkeeper', 'Defender', 'Midfielder', 'Forward'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staff table
CREATE TABLE staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    phone VARCHAR(20),
    address TEXT,
    position VARCHAR(100) NOT NULL, -- Job title/position
    department VARCHAR(50),
    hire_date DATE NOT NULL,
    salary DECIMAL(10, 2),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Teams table
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10),
    founded_year INTEGER,
    stadium_name VARCHAR(100),
    stadium_capacity INTEGER,
    manager_id INTEGER,
    coach_id INTEGER,
    logo_path VARCHAR(255),
    primary_color VARCHAR(7) DEFAULT '#000000',
    secondary_color VARCHAR(7) DEFAULT '#FFFFFF',
    website VARCHAR(255),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES staff(id) ON DELETE SET NULL,
    FOREIGN KEY (coach_id) REFERENCES staff(id) ON DELETE SET NULL
);

-- Players table
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    team_id INTEGER,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    nationality VARCHAR(50),
    height_cm INTEGER,
    weight_kg DECIMAL(5, 2),
    position_id INTEGER,
    preferred_foot VARCHAR(10), -- 'left', 'right', 'both'
    jersey_number INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL
);

-- Player photos table
CREATE TABLE player_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    photo_path VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- Player contracts table
CREATE TABLE player_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    signing_bonus DECIMAL(10, 2) DEFAULT 0,
    release_clause DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CHECK (end_date > start_date)
);

-- Matches table
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    competition VARCHAR(100) NOT NULL, -- League, Cup, Friendly, etc.
    match_date DATETIME NOT NULL,
    venue VARCHAR(100),
    home_team_score INTEGER DEFAULT 0,
    away_team_score INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'in_progress', 'completed', 'postponed', 'cancelled'
    match_week INTEGER,
    season VARCHAR(20),
    referee_name VARCHAR(100),
    attendance INTEGER,
    weather_conditions VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CHECK (home_team_id != away_team_id)
);

-- Match players (squad for each match)
CREATE TABLE match_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    is_starting BOOLEAN DEFAULT 0,
    position_id INTEGER,
    jersey_number INTEGER,
    captain BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL,
    UNIQUE(match_id, player_id)
);

-- Match events (goals, cards, substitutions, etc.)
CREATE TABLE match_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    event_type VARCHAR(20) NOT NULL, -- 'goal', 'yellow_card', 'red_card', 'substitution', 'injury', 'penalty', 'own_goal', 'penalty_save', 'penalty_miss'
    minute INTEGER NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    assist_player_id INTEGER,
    related_player_id INTEGER, -- For substitutions, the player coming off
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE SET NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    FOREIGN KEY (assist_player_id) REFERENCES players(id) ON DELETE SET NULL,
    FOREIGN KEY (related_player_id) REFERENCES players(id) ON DELETE SET NULL
);

-- Player statistics (seasonal)
CREATE TABLE player_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    season VARCHAR(20) NOT NULL,
    matches_played INTEGER DEFAULT 0,
    matches_started INTEGER DEFAULT 0,
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    clean_sheets INTEGER DEFAULT 0, -- For goalkeepers and defenders
    saves INTEGER DEFAULT 0, -- For goalkeepers
    goals_conceded INTEGER DEFAULT 0, -- For goalkeepers
    penalties_saved INTEGER DEFAULT 0, -- For goalkeepers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    UNIQUE(player_id, team_id, season)
);

-- Training sessions
CREATE TABLE training_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(100),
    coach_id INTEGER,
    team_id INTEGER,
    focus_area VARCHAR(50), -- 'fitness', 'tactics', 'set_pieces', 'recovery', 'match_preparation'
    intensity VARCHAR(20), -- 'low', 'medium', 'high'
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'cancelled'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES staff(id) ON DELETE SET NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
    CHECK (end_time > start_time)
);

-- Training attendance
CREATE TABLE training_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    training_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'present', 'absent', 'late', 'excused'
    performance_rating INTEGER, -- 1-5 scale
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (training_id) REFERENCES training_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE(training_id, player_id),
    CHECK (performance_rating BETWEEN 1 AND 5 OR performance_rating IS NULL)
);

-- Financial transactions
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- 'income', 'expense', 'transfer_fee', 'salary', 'bonus', 'other'
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    reference_number VARCHAR(50),
    related_entity_type VARCHAR(20), -- 'player', 'staff', 'supplier', 'other'
    related_entity_id INTEGER,
    payment_method VARCHAR(30), -- 'cash', 'bank_transfer', 'check', 'card', 'other'
    status VARCHAR(20) DEFAULT 'completed', -- 'pending', 'completed', 'cancelled', 'refunded'
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Application settings
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(50) NOT NULL UNIQUE,
    setting_value TEXT,
    setting_group VARCHAR(50),
    data_type VARCHAR(20) DEFAULT 'string', -- 'string', 'integer', 'float', 'boolean', 'json'
    is_public BOOLEAN DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INSERT INITIAL DATA
-- =============================================

-- Insert default roles
INSERT INTO roles (name, description) VALUES 
('admin', 'System administrator with full access'),
('manager', 'Team manager with administrative privileges'),
('coach', 'Team coach with training and match management'),
('player', 'Player with access to personal dashboard'),
('staff', 'Non-coaching staff with limited access');

-- Insert default positions
INSERT INTO positions (name, short_name, position_type) VALUES
-- Goalkeepers
('Goalkeeper', 'GK', 'Goalkeeper'),
-- Defenders
('Center Back', 'CB', 'Defender'),
('Right Back', 'RB', 'Defender'),
('Left Back', 'LB', 'Defender'),
('Wing Back', 'WB', 'Defender'),
('Sweeper', 'SW', 'Defender'),
-- Midfielders
('Defensive Midfielder', 'DM', 'Midfielder'),
('Central Midfielder', 'CM', 'Midfielder'),
('Attacking Midfielder', 'AM', 'Midfielder'),
('Right Midfielder', 'RM', 'Midfielder'),
('Left Midfielder', 'LM', 'Midfielder'),
('Right Winger', 'RW', 'Midfielder'),
('Left Winger', 'LW', 'Midfielder'),
-- Forwards
('Striker', 'ST', 'Forward'),
('Center Forward', 'CF', 'Forward'),
('Second Striker', 'SS', 'Forward');

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES 
('admin', 'admin@example.com', 'pbkdf2:sha256:260000$2X5O6v8x0Y9z1A3B$4f8c3e2d1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5', 1, 1);

-- Insert default team
INSERT INTO teams (name, short_name, founded_year, stadium_name, stadium_capacity, primary_color, secondary_color) 
VALUES ('Football Club', 'FC', 2023, 'FC Stadium', 5000, '#1a237e', '#ffffff');

-- Insert default settings
INSERT INTO settings (setting_key, setting_value, setting_group, data_type, is_public, description) VALUES
('site_name', 'Football Club Management System', 'general', 'string', 1, 'Name of the website'),
('site_description', 'Comprehensive football club management solution', 'general', 'string', 1, 'Website description'),
('contact_email', 'info@example.com', 'contact', 'string', 1, 'Primary contact email'),
('items_per_page', '10', 'pagination', 'integer', 0, 'Number of items per page in lists'),
('maintenance_mode', '0', 'system', 'boolean', 0, 'Whether the site is in maintenance mode'),
('registration_enabled', '1', 'authentication', 'boolean', 0, 'Whether new user registration is enabled'),
('password_reset_enabled', '1', 'authentication', 'boolean', 0, 'Whether password reset is enabled'),
('default_user_role', '5', 'authentication', 'integer', 0, 'Default role ID for new users (5 = staff)');

-- Create indexes for better performance
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_position ON players(position_id);
CREATE INDEX idx_matches_dates ON matches(match_date);
CREATE INDEX idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX idx_match_events_match ON match_events(match_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_player_stats_season ON player_statistics(season, player_id);

-- Create triggers for timestamps
CREATE TRIGGER update_players_updated_at
AFTER UPDATE ON players
FOR EACH ROW
BEGIN
    UPDATE players SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_teams_updated_at
AFTER UPDATE ON teams
FOR EACH ROW
BEGIN
    UPDATE teams SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Create view for player stats
CREATE VIEW vw_player_season_stats AS
SELECT 
    p.id AS player_id,
    p.first_name || ' ' || p.last_name AS player_name,
    t.name AS team_name,
    ps.season,
    ps.matches_played,
    ps.matches_started,
    ps.minutes_played,
    ps.goals,
    ps.assists,
    ps.yellow_cards,
    ps.red_cards,
    ps.clean_sheets,
    ps.saves,
    ps.goals_conceded,
    ps.penalties_saved,
    ROUND(CAST(ps.goals AS FLOAT) / NULLIF(ps.matches_played, 0), 2) AS goals_per_match,
    ROUND(CAST(ps.assists AS FLOAT) / NULLIF(ps.matches_played, 0), 2) AS assists_per_match
FROM players p
JOIN player_statistics ps ON p.id = ps.player_id
JOIN teams t ON ps.team_id = t.id;

-- Create view for team standings
CREATE VIEW vw_team_standings AS
WITH match_results AS (
    SELECT 
        m.season,
        m.home_team_id AS team_id,
        t.name AS team_name,
        COUNT(*) AS matches_played,
        SUM(CASE 
            WHEN m.home_team_score > m.away_team_score THEN 1 
            ELSE 0 
        END) AS wins,
        SUM(CASE 
            WHEN m.home_team_score = m.away_team_score THEN 1 
            ELSE 0 
        END) AS draws,
        SUM(CASE 
            WHEN m.home_team_score < m.away_team_score THEN 1 
            ELSE 0 
        END) AS losses,
        SUM(m.home_team_score) AS goals_for,
        SUM(m.away_team_score) AS goals_against,
        SUM(m.home_team_score - m.away_team_score) AS goal_difference
    FROM matches m
    JOIN teams t ON m.home_team_id = t.id
    WHERE m.status = 'completed'
    GROUP BY m.season, m.home_team_id, t.name
    
    UNION ALL
    
    SELECT 
        m.season,
        m.away_team_id AS team_id,
        t.name AS team_name,
        COUNT(*) AS matches_played,
        SUM(CASE 
            WHEN m.away_team_score > m.home_team_score THEN 1 
            ELSE 0 
        END) AS wins,
        SUM(CASE 
            WHEN m.away_team_score = m.home_team_score THEN 1 
            ELSE 0 
        END) AS draws,
        SUM(CASE 
            WHEN m.away_team_score < m.home_team_score THEN 1 
            ELSE 0 
        END) AS losses,
        SUM(m.away_team_score) AS goals_for,
        SUM(m.home_team_score) AS goals_against,
        SUM(m.away_team_score - m.home_team_score) AS goal_difference
    FROM matches m
    JOIN teams t ON m.away_team_id = t.id
    WHERE m.status = 'completed'
    GROUP BY m.season, m.away_team_id, t.name
)
SELECT 
    season,
    team_id,
    team_name,
    SUM(matches_played) AS matches_played,
    SUM(wins) AS wins,
    SUM(draws) AS draws,
    SUM(losses) AS losses,
    SUM(goals_for) AS goals_for,
    SUM(goals_against) AS goals_against,
    SUM(goal_difference) AS goal_difference,
    SUM(wins * 3 + draws) AS points
FROM match_results
GROUP BY season, team_id, team_name
ORDER BY points DESC, goal_difference DESC, goals_for DESC;
