CREATE TABLE IF NOT EXISTS categories (id INTEGER, name TEXT);

CREATE TABLE IF NOT EXISTS channels 
(id TEXT, id_cat INTEGER, name TEXT, language TEXT, status INTEGER, 
  address TEXT, protocol TEXT, 
  unverified INTEGER, my integer, deleted integer);

PRAGMA user_version=0001;
