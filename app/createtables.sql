CREATE TABLE IF NOT EXISTS users (
  membership_id INTEGER PRIMARY KEY,
  bungie_name TEXT,
  psn_name TEXT,
  psn_membership_id INTEGER,
  xbox_name TEXT,
  xbox_membership_id INTEGER,
  bliz_name TEXT,
  bliz_membership_id INTEGER
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS auths (
  token_type TEXT NOT NULL,
  token TEXT NOT NULL,
  expiry INTEGER NOT NULL,
  u_id INTEGER NOT NULL,
    FOREIGN KEY (u_id) REFERENCES users(membership_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
