-- Create read-only user for agent queries.
CREATE USER IF NOT EXISTS 'readonly_user'@'%' IDENTIFIED BY 'readonly_pass';
CREATE USER IF NOT EXISTS 'readonly_user'@'localhost' IDENTIFIED BY 'readonly_pass';
GRANT SELECT ON revenue.* TO 'readonly_user'@'%';
GRANT SELECT ON revenue.* TO 'readonly_user'@'localhost';
FLUSH PRIVILEGES;
