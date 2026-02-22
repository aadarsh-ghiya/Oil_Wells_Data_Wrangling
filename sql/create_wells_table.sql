CREATE DATABASE IF NOT EXISTS oil_wells;
USE oil_wells;

CREATE TABLE IF NOT EXISTS wells (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_file VARCHAR(255),
  well_file_no VARCHAR(64),
  well_name VARCHAR(255),
  api_number VARCHAR(32),
  county VARCHAR(128),
  section VARCHAR(32),
  township VARCHAR(32),
  `range` VARCHAR(32),
  quarter_quarter VARCHAR(64),
  footages VARCHAR(128),
  latitude DECIMAL(10,7) NULL,
  longitude DECIMAL(10,7) NULL,
  operator VARCHAR(255),
  spud_date DATE NULL,
  completion_date DATE NULL,
  stimulation_type VARCHAR(255),
  field_name VARCHAR(255),
  pool VARCHAR(255),
  raw_text_sample TEXT,
  api_clean VARCHAR(32),
  well_name_clean VARCHAR(255),
  detail_url VARCHAR(255),
  well_status VARCHAR(128),
  well_type VARCHAR(128),
  closest_city VARCHAR(128),
  oil_produced DOUBLE NULL,
  gas_produced DOUBLE NULL
);
