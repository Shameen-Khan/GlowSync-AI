"""SQLite persistence. Existing users, lists and notifications are preserved."""
import json
import sqlite3
import time
from pathlib import Path
from .catalogue import ROOT, upsert_products

def connect(path):
 db=sqlite3.connect(path,timeout=30)
 db.row_factory=sqlite3.Row
 db.execute('PRAGMA foreign_keys=ON')
 db.execute('PRAGMA journal_mode=WAL')
 return db

def initialize(path):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 with connect(path) as db:
  db.executescript('''
   CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS wishlist(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),product_id TEXT NOT NULL,variant_id TEXT NOT NULL,watching INTEGER NOT NULL DEFAULT 0,baseline BIGINT,UNIQUE(user_id,product_id,variant_id));
   CREATE TABLE IF NOT EXISTS notifications(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),title TEXT NOT NULL,created BIGINT NOT NULL,seen INTEGER NOT NULL DEFAULT 0);
   CREATE TABLE IF NOT EXISTS attempts(bucket TEXT PRIMARY KEY,count INTEGER NOT NULL,expires BIGINT NOT NULL);
   CREATE TABLE IF NOT EXISTS catalog_products(id TEXT PRIMARY KEY,brand TEXT NOT NULL,name TEXT NOT NULL,category TEXT NOT NULL,finish TEXT NOT NULL,search TEXT NOT NULL,min_price INTEGER,active INTEGER NOT NULL DEFAULT 1,data TEXT NOT NULL);
   CREATE INDEX IF NOT EXISTS catalog_filter ON catalog_products(active,brand,category);
   CREATE TABLE IF NOT EXISTS catalog_sources(brand TEXT PRIMARY KEY,data TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS app_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS price_history(product_id TEXT NOT NULL,variant_id TEXT NOT NULL,price INTEGER NOT NULL,observed_at INTEGER NOT NULL,PRIMARY KEY(product_id,variant_id,observed_at));
  ''')
  cols={r['name'] for r in db.execute('PRAGMA table_info(users)')}
  if 'is_admin' not in cols:
   db.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0')
   db.execute('UPDATE users SET is_admin=1 WHERE rowid=(SELECT MIN(rowid) FROM users)')
  if 'preferences' not in cols: db.execute("ALTER TABLE users ADD COLUMN preferences TEXT NOT NULL DEFAULT '{}'")
  if not db.execute("SELECT 1 FROM app_meta WHERE key='catalogue_seed_v2'").fetchone():
   seed=ROOT/'data/catalogue.json'
   if seed.exists():
    data=json.loads(seed.read_text(encoding='utf-8'))
    upsert_products(db,data['products'])
    for brand,status in data.get('sources',{}).items():
     db.execute('INSERT OR REPLACE INTO catalog_sources VALUES(?,?)',(brand,json.dumps(status)))
   db.execute("INSERT INTO app_meta VALUES('catalogue_seed_v2',?)",(str(int(time.time())),))
