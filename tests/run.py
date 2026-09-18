"""Real Java + Python integration tests. Uses disposable databases, never local.db."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.app import create_app,apply_price_alerts
from backend.db import connect,initialize
from backend.catalogue import validate_import,upsert_products,from_shopify,BY_BRAND,fetch_brand,category_for

class GlowSyncTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.baseline=Path(cls.temp.name)/'baseline.db'
  initialize(str(cls.baseline))
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  os.environ['GLOWSYNC_JAVA_PORT']=str(port)
  cls.java=subprocess.Popen(['java','-cp',str(ROOT/'java'),'ShadeService'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  for _ in range(80):
   try:
    with urlopen(f'http://127.0.0.1:{port}/health',timeout=.5) as r:
     if r.status==200:break
   except OSError:time.sleep(.1)
  else:raise RuntimeError('Test Java service failed to start')

 @classmethod
 def tearDownClass(cls):
  cls.java.terminate();cls.java.wait(timeout=5);cls.java.stdout.close();cls.temp.cleanup()

 def setUp(self):
  self.path=Path(self.temp.name)/(self._testMethodName+'.db');shutil.copy2(self.baseline,self.path)
  self.app=create_app(str(self.path),testing=True);self.client=self.app.test_client()
  self.csrf=self.client.get('/api/session').json['csrf']

 def send(self,path,data=None,method='POST',client=None,csrf=None):
  return (client or self.client).open(path,method=method,json=data or {},headers={'X-CSRF-Token':csrf or self.csrf})

 def register(self,email='one@example.test',client=None):
  client=client or self.client;token=client.get('/api/session').json['csrf']
  response=self.send('/api/auth/register',{'email':email,'password':'Testing-12345!','name':'Test User'},client=client,csrf=token)
  self.assertEqual(response.status_code,200,response.json)
  if client is self.client:self.csrf=response.json['csrf']
  return response.json

 def a_product(self,brand='lakme'):
  return self.client.get('/api/products?brand='+brand+'&category=foundation').json['products'][0]

 def save(self,p):
  response=self.send('/api/wishlist',{'product_id':p['id'],'variant_id':p['variants'][0]['id']});self.assertEqual(response.status_code,200)
  return self.client.get('/api/wishlist').json['items'][0]

 def test_01_full_catalogue_and_pagination(self):
  meta=self.client.get('/api/meta').json
  self.assertGreater(meta['total'],3800);self.assertGreater(meta['variants'],10000)
  all_ids=set()
  data=self.client.get('/api/products?brand=swiss-beauty&limit=60').json
  for page in range(1,data['pages']+1):
   data=self.client.get('/api/products?brand=swiss-beauty&limit=60&page='+str(page)).json
   for p in data['products']:
    self.assertNotIn(p['id'],all_ids);all_ids.add(p['id'])
  self.assertEqual(len(all_ids),425)

 def test_02_filters_regions_prices_and_search(self):
  for region,categories in [('lips',{'lipstick','lip-gloss','lip-liner','lip-balm'}),('eyes',{'mascara','eyeliner','eyeshadow'}),('brows',{'eyebrow'})]:
   result=self.client.get('/api/products?region='+region).json
   self.assertTrue(result['products']);self.assertTrue(all(p['category'] in categories for p in result['products']))
  r=self.client.get('/api/products?region=eyes&category=lipstick').json;self.assertEqual(r['total'],0)
  r=self.client.get('/api/products?brand=maybelline&max_price=1000').json;self.assertEqual(r['total'],0);self.assertGreater(r['unknown_price_excluded'],0)
  r=self.client.get('/api/products?max_price=500&sort=price-asc&limit=60').json
  prices=[]
  for p in r['products']:
   vs=[v for v in p['variants'] if v['id'] in p['matching_variant_ids']]
   self.assertTrue(all(v['price'] is not None and v['price']<=50000 for v in vs));prices.append(min(v['price'] for v in vs))
  self.assertEqual(prices,sorted(prices))
  r=self.client.get('/api/products?q=Lakm%C3%A9').json;self.assertTrue(r['products']);self.assertTrue(all(p['brand']=='lakme' for p in r['products']))
  self.assertEqual(self.client.get('/api/products?max_price=NaN').status_code,400)
  self.assertEqual(self.client.get('/api/products?brand=missing').status_code,400)

 def test_03_auth_csrf_password_and_persistence(self):
  self.assertEqual(self.client.post('/api/auth/register',json={}).status_code,403)
  reg=self.register();self.assertTrue(reg['user']['is_admin'])
  with connect(str(self.path)) as db:
   password=db.execute('SELECT password FROM users').fetchone()[0]
   self.assertNotEqual(password,'Testing-12345!');self.assertTrue(password.startswith('scrypt:'))
  logout=self.send('/api/auth/logout');self.csrf=logout.json['csrf'];self.assertIsNone(self.client.get('/api/session').json['user'])
  wrong=self.send('/api/auth/login',{'email':'one@example.test','password':'wrong'});self.assertEqual(wrong.status_code,401)
  login=self.send('/api/auth/login',{'email':'one@example.test','password':'Testing-12345!'});self.assertEqual(login.status_code,200);self.csrf=login.json['csrf']
  self.assertIn('HttpOnly',login.headers['Set-Cookie']);self.assertIn('SameSite=Lax',login.headers['Set-Cookie'])
  second_app=create_app(str(self.path),testing=True);c=second_app.test_client();token=c.get('/api/session').json['csrf']
  self.assertEqual(self.send('/api/auth/login',{'email':'one@example.test','password':'Testing-12345!'},client=c,csrf=token).status_code,200)

 def test_04_user_isolation_and_wishlist(self):
  self.register();p=self.a_product();wish=self.save(p)
  self.save(p);self.assertEqual(len(self.client.get('/api/wishlist').json['items']),1)
  self.assertEqual(self.send('/api/wishlist',{'product_id':'invented','variant_id':'fake'}).status_code,400)
  c=self.app.test_client();second=self.register('two@example.test',c);self.assertFalse(second['user']['is_admin'])
  self.assertEqual(c.get('/api/wishlist').json['items'],[])
  self.assertEqual(self.send('/api/wishlist/'+wish['id'],method='DELETE',client=c,csrf=second['csrf']).status_code,404)
  self.assertEqual(self.send('/api/catalogue/sync',client=c,csrf=second['csrf']).status_code,403)
  self.assertEqual(self.send('/api/wishlist/'+wish['id'],method='DELETE').status_code,200)

 def test_05_quote_alert_rules(self):
  self.register();p=self.a_product();wish=self.save(p)
  self.assertEqual(self.send('/api/wishlist/'+wish['id']+'/watch',{'enabled':True},'PUT').status_code,200)
  now=int(time.time());p['observed_at']=now;p['currency']='INR';p['source_kind']='feed'
  v=p['variants'][0];v['price']=10000;v['available']=True
  with connect(str(self.path)) as db:
   apply_price_alerts(db,p,now)
   self.assertEqual(db.execute('SELECT baseline FROM wishlist').fetchone()[0],10000)
   self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0],0)
   for bad in ['snapshot','import','reference']:
    p['source_kind']=bad;v['price']=7000;apply_price_alerts(db,p,now)
   p['source_kind']='feed';p['observed_at']=now-900;apply_price_alerts(db,p,now)
   p['observed_at']=now;v['available']=False;apply_price_alerts(db,p,now)
   self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0],0)
   v['available']=True;v['price']=8000;apply_price_alerts(db,p,now);apply_price_alerts(db,p,now)
   v['price']=9000;apply_price_alerts(db,p,now);v['price']=8500;apply_price_alerts(db,p,now)
   self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0],1)
   v['price']=6000;apply_price_alerts(db,p,now)
   self.assertEqual(db.execute('SELECT count(*) FROM notifications').fetchone()[0],2)
  self.assertEqual(len(self.client.get('/api/notifications').json['items']),2)
  self.send('/api/notifications/read');self.assertTrue(all(n['seen'] for n in self.client.get('/api/notifications').json['items']))

 def test_06_import_validation_atomicity_and_export(self):
  self.register();example=json.loads((ROOT/'data/import-example.json').read_text(encoding='utf-8'))
  original=self.client.get('/api/meta').json['total']
  valid=self.send('/api/catalogue/import',example);self.assertEqual(valid.status_code,200,valid.json)
  self.assertEqual(self.client.get('/api/meta').json['total'],original)
  bad=copy.deepcopy(example);bad['products'].append(copy.deepcopy(bad['products'][0]));bad['products'][1]['url']='http://127.0.0.1/private'
  self.assertEqual(self.send('/api/catalogue/import',bad).status_code,400)
  self.assertEqual(self.client.get('/api/meta').json['total'],original)
  bad=copy.deepcopy(example);bad['products'][0]['variants'][0]['price_inr']='NaN';self.assertEqual(self.send('/api/catalogue/import',bad).status_code,400)
  exported=self.client.get('/api/catalogue/export');self.assertEqual(exported.status_code,200);self.assertEqual(exported.json['schema_version'],1)

 def test_07_java_integration_and_manual_preferences(self):
  data={'tone':'medium','undertone':'warm','occasion':'festive','clothing':'red','finish':'matte'}
  r=self.send('/api/recommend',data);self.assertEqual(r.status_code,200,r.json);self.assertIn('terracotta',r.json['palette']['direction'])
  self.assertEqual(len(r.json['palette']['colours']),4)
  self.assertTrue(r.json['shade_suggestions'])
  for p in r.json['shade_suggestions']:
   self.assertEqual(p['category'],'foundation')
   self.assertTrue(p['matching_variant_ids'])
   self.assertTrue(all(vid in {v['id'] for v in p['variants']} for vid in p['matching_variant_ids']))
  data['undertone']='cool';r2=self.send('/api/recommend',data);self.assertIn('berry',r2.json['palette']['direction']);self.assertNotEqual(r.json['palette']['colours'],r2.json['palette']['colours'])
  data['tone']='invalid';self.assertEqual(self.send('/api/recommend',data).status_code,400)
  self.register();self.assertEqual(self.send('/api/profile',{'name':'New Name','preferences':{'tone':'deep'}},'PUT').status_code,200)
  self.assertEqual(self.client.get('/api/session').json['user']['preferences']['tone'],'deep')

 def test_08_feed_pagination_complete_or_fail(self):
  raw={'id':1,'title':'Test Lipstick','handle':'test','variants':[{'id':11,'title':'Rose','price':'199.50','available':True}],'images':[]}
  with patch('backend.catalogue.get_json',side_effect=[{'currency':'INR'},{'products':[raw]},{'products':[]}]),patch('backend.catalogue.time.sleep'):
   ps,status=fetch_brand('lakme');self.assertTrue(status['complete']);self.assertEqual(ps[0]['variants'][0]['price'],19950)
  with patch('backend.catalogue.get_json',side_effect=[{'currency':'INR'},{'products':[raw]},{'products':[raw]}]),patch('backend.catalogue.time.sleep'):
   with self.assertRaises(ValueError):fetch_brand('lakme')
  with patch('backend.catalogue.get_json',return_value={'currency':'USD'}):
   with self.assertRaises(ValueError):fetch_brand('lakme')

 def test_09_source_validation_and_local_assets(self):
  data=json.loads((ROOT/'data/catalogue.json').read_text(encoding='utf-8'))
  ids=set()
  for p in data['products']:
   self.assertNotIn(p['id'],ids);ids.add(p['id']);self.assertTrue(p['url'].startswith('https://'));self.assertTrue(p['variants'])
   self.assertEqual(len(set(v['id'] for v in p['variants'])),len(p['variants']))
   for v in p['variants']:
    self.assertTrue(v['price'] is None or isinstance(v['price'],int) and v['price']>=0)
  for path in ['/','/studio','/catalogue','/static/app.js','/static/style.css','/static/studio.js','/static/vendor/mediapipe/face_landmarker.task','/static/vendor/mediapipe/wasm/vision_wasm_internal.wasm']:
   r=self.client.get(path);self.assertEqual(r.status_code,200,path);r.close()

 def test_10_host_origin_throttle_and_unauthenticated(self):
  self.assertEqual(self.client.get('/api/meta',headers={'Host':'evil.example'}).status_code,403)
  self.assertEqual(self.client.post('/api/auth/login',json={},headers={'X-CSRF-Token':self.csrf,'Origin':'https://evil.example'}).status_code,403)
  self.assertEqual(self.client.get('/api/wishlist').status_code,401)
  self.assertEqual(self.client.get('/api/catalogue/export').status_code,401)
  for _ in range(15):self.send('/api/auth/login',{'email':'nobody@example.test','password':'incorrect'})
  self.assertEqual(self.send('/api/auth/login',{'email':'nobody@example.test','password':'incorrect'}).status_code,429)

 def test_11_existing_database_migration(self):
  legacy=Path(self.temp.name)/'legacy.db'
  with sqlite3.connect(legacy) as c:
   c.executescript('CREATE TABLE users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL); INSERT INTO users VALUES("legacy","legacy@example.test","Existing User","preserved-hash");')
  initialize(str(legacy))
  with connect(str(legacy)) as c:
   user=c.execute('SELECT * FROM users WHERE id="legacy"').fetchone();self.assertEqual(user['password'],'preserved-hash');self.assertEqual(user['is_admin'],1)

if __name__=='__main__':unittest.main(verbosity=2)
