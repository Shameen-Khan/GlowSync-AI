"""Source-grounded product data, bounded public feeds and atomic catalogue updates."""
from __future__ import annotations
import hashlib
import json
import re
import time
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
BRANDS = json.loads((ROOT / 'data/brands.json').read_text(encoding='utf-8'))
BY_BRAND = {b['id']: b for b in BRANDS}
CATEGORIES = {
 'foundation': 'Foundation & skin tint', 'concealer': 'Concealer',
 'primer': 'Primer', 'powder': 'Compact & powder', 'blush': 'Blush',
 'highlighter': 'Highlighter', 'contour': 'Contour & bronzer',
 'setting-spray': 'Setting spray', 'lipstick': 'Lipstick', 'lip-gloss': 'Lip gloss',
 'lip-liner': 'Lip liner', 'lip-balm': 'Lip balm & care', 'mascara': 'Mascara',
 'eyeliner': 'Eyeliner & kajal', 'eyeshadow': 'Eyeshadow', 'eyebrow': 'Eyebrows',
 'nails': 'Nails', 'skincare': 'Skincare', 'haircare': 'Haircare',
 'fragrance': 'Fragrance', 'bodycare': 'Bath & body', 'tools': 'Tools & accessories',
 'sets': 'Kits & sets', 'other': 'More beauty',
}
REGIONS = {
 'face': ['foundation','concealer','primer','powder','blush','highlighter','contour','setting-spray'],
 'lips': ['lipstick','lip-gloss','lip-liner','lip-balm'],
 'eyes': ['eyeliner','mascara','eyeshadow'], 'brows': ['eyebrow'],
}

def norm(value):
 return ''.join(c for c in unicodedata.normalize('NFKD',str(value)).lower() if not unicodedata.combining(c))

def category_for(title, product_type=''):
 t = norm(title)
 # Title is authoritative for classification; broad brand tags often contain every category.
 rules = [
  ('tools',r'\b(brush|brushes|sponge|blender|pouch|bag|mirror|sharpener|organizer|organiser|applicator|curler|tweezer|headband|makeup remover pad)\b'),
  ('sets',r'\b(kit|combo|duo|trio|bundle|set of|gift set|makeup set|pack of|hamper)\b'),
  ('lip-liner',r'lip.?liner'), ('lip-gloss',r'lip.?gloss|lip oil|plumping gloss'),
  ('lip-balm',r'lip.?balm|lip butter|lip mask|lip scrub|lip care'),
  ('lipstick',r'lipstick|lip colour|lip color|lip tint|lip stain|lip crayon|lip mousse|lip creme|lip cream|vinyl ink|matte ink|teddy tint|laque resistance|rouge signature'),
  ('eyebrow',r'\bbrow|eyebrow'), ('mascara',r'mascara'),
  ('eyeliner',r'eye.?liner|kajal|kohl'), ('eyeshadow',r'eye.?shadow|eye palette'),
  ('concealer',r'concealer|color corrector|colour corrector'),
  ('foundation',r'foundation|skin tint|serum tint|bb cream|cc cream|fresh tint'),
  ('blush',r'blush|cheek tint'), ('highlighter',r'highlighter|illuminator|strobe'),
  ('contour',r'contour|bronzer'), ('setting-spray',r'setting spray|setting mist|fixer|makeup spray'),
  ('powder',r'compact|powder'), ('primer',r'primer'),
  ('nails',r'nail'), ('haircare',r'shampoo|conditioner|hair|scalp'),
  ('fragrance',r'parfum|perfume|fragrance|eau de|body mist|cologne'),
  ('bodycare',r'body|shower|deodorant|hand cream|soap|bath'),
  ('skincare',r'cleanser|face.?wash|moisturi|sunscreen|sun screen|spf|serum|toner|face cream|face gel|face mask|face oil|night cream|scrub|micellar|makeup remover|cleansing|peel|face polish'),
 ]
 for category, pattern in rules:
  if re.search(pattern,t): return category
 if product_type and norm(product_type) != t:
  return category_for(product_type)
 return 'other'

def finish_for(title):
 t=norm(title)
 if 'matte' in t: return 'matte'
 if any(x in t for x in ['gloss','glow','dewy','shimmer','radiant','shine']): return 'radiant'
 if 'satin' in t: return 'satin'
 return 'unspecified'

def shade_tags(name):
 """Conservative editorial tags from published shade names, never numeric shade codes."""
 text=norm(name)
 tones=[('deep',r'espresso|cocoa|chocolate|mahogany|ebony|deep|mocha'),
        ('tan',r'caramel|toffee|chestnut|almond|\btan\b|bronze'),
        ('fair',r'porcelain|alabaster|\bfair\b|snow'),
        ('light',r'ivory|vanilla|\blight\b'),
        ('medium',r'\bmedium\b|\bbeige\b|\bsand\b|wheat|natural')]
 tone=next((tone for tone,pattern in tones if re.search(pattern,text)),None)
 undertone=next((u for u in ['warm','cool','neutral'] if re.search(r'\b'+u+r'\b',text)),None)
 return tone,undertone

def money(value):
 if value in (None,''): return None
 try:
  n=Decimal(str(value))
  if not n.is_finite() or n<0 or n>1000000: raise ValueError('Invalid price')
  return int((n*100).quantize(Decimal('1')))
 except (InvalidOperation,TypeError): raise ValueError('Invalid price') from None

def safe_url(url, allowed_hosts=None):
 u=urlparse(str(url))
 if u.scheme!='https' or not u.hostname or u.username or u.password or (u.port not in (None,443)):
  raise ValueError('Only public HTTPS product URLs are accepted')
 if allowed_hosts and u.hostname.lower() not in allowed_hosts:
  raise ValueError('URL is outside the configured brand domains')
 return str(url)

class BrandRedirect(HTTPRedirectHandler):
 def __init__(self, hosts): self.hosts=hosts
 def redirect_request(self, req, fp, code, msg, headers, newurl):
  safe_url(newurl,self.hosts)
  return super().redirect_request(req,fp,code,msg,headers,newurl)

def get_json(brand, path):
 """No arbitrary URL fetching. Credentials and private redirects are never followed."""
 base=brand.get('feed_base')
 if not base or not path.startswith('/') or path.startswith('//'): raise ValueError('No feed configured')
 hosts=set(brand['allowed_hosts'])
 url=safe_url(base+path,hosts)
 with build_opener(BrandRedirect(hosts)).open(Request(url,headers={'Accept':'application/json','User-Agent':'GlowSync/2.0 (public product catalogue)'}),timeout=18) as response:
  payload=response.read(24*1024*1024+1)
 if len(payload)>24*1024*1024: raise ValueError('Source response exceeds 24 MB')
 return json.loads(payload)

def from_shopify(brand, raw, observed_at, currency, source_kind='snapshot'):
 bid=brand['id']; pid=f'{bid}:{raw["id"]}'
 url=f'{brand["feed_base"]}/products/{quote(str(raw["handle"]),safe="-")}'
 images=raw.get('images',[])
 img=next((i.get('src') for i in images if str(i.get('src','')).startswith('https://')),None)
 variants=[]
 for v in raw.get('variants',[]):
  variant_image=next((i['src'] for i in images if v['id'] in i.get('variant_ids',[]) and str(i.get('src','')).startswith('https://')),None)
  price=money(v.get('price')) if currency=='INR' else None
  compare=money(v.get('compare_at_price')) if currency=='INR' else None
  variants.append({'id':str(v['id']),'name':str(v.get('title') or 'Standard').replace('Default Title','Standard'),
   'price':price,'mrp':compare if compare and price is not None and compare>price else None,
   'available':v.get('available') if isinstance(v.get('available'),bool) else None,
   'image':variant_image,'url':url+'?variant='+str(v['id'])})
 if not variants: variants=[{'id':'range','name':'See brand for options','price':None,'mrp':None,'available':None,'image':None,'url':url}]
 return {'id':pid,'brand':bid,'name':str(raw['title']).strip(),'category':category_for(raw['title'],raw.get('product_type','')),
  'finish':finish_for(raw['title']), 'url':url,'image':img,'handle':raw['handle'],
  'source_url':brand['feed_base']+'/products.json','source_kind':source_kind,
  'observed_at':observed_at,'currency':'INR' if currency=='INR' else None,'variants':variants}

def fetch_brand(brand_id, progress=None):
 brand=BY_BRAND[brand_id]
 if not brand.get('feed_base'): raise ValueError('This brand needs a supplier file; no public feed is configured')
 meta=get_json(brand,'/meta.json')
 if meta.get('currency')!='INR': raise ValueError('Source currency could not be verified as INR')
 seen=set(); products=[]; observed=int(time.time())
 for page in range(1,81):
  data=get_json(brand,f'/products.json?limit=250&page={page}')
  rows=data.get('products')
  if not isinstance(rows,list): raise ValueError('Source did not return a product list')
  if not rows:
   if not products: raise ValueError('Empty feed: keeping the previous catalogue')
   return products,{'complete':True,'pages':page-1,'observed_at':observed,'count':len(products)}
  ids={str(p['id']) for p in rows}
  if not ids-seen: raise ValueError('Repeated pagination: keeping the previous catalogue')
  products.extend(from_shopify(brand,p,observed,'INR','feed') for p in rows if str(p['id']) not in seen)
  seen.update(ids)
  if progress: progress(f'{brand["name"]}: page {page}, {len(products):,} products')
  time.sleep(.25)
 raise ValueError('Pagination safety limit reached; no partial catalogue was published')

def upsert_products(db, products, brand_id=None, complete=False, status=None):
 """Caller owns transaction; a failed import never deactivates existing rows."""
 if complete and brand_id:
  db.execute('UPDATE catalog_products SET active=0 WHERE brand=?',(brand_id,))
 for p in products:
  prices=[v['price'] for v in p['variants'] if v.get('price') is not None]
  search=norm(' '.join([p['name'],BY_BRAND[p['brand']]['name'],p['category']]+[v['name'] for v in p['variants']]))
  db.execute('''INSERT INTO catalog_products(id,brand,name,category,finish,search,min_price,active,data)
   VALUES(?,?,?,?,?,?,?,1,?) ON CONFLICT(id) DO UPDATE SET brand=excluded.brand,name=excluded.name,
   category=excluded.category,finish=excluded.finish,search=excluded.search,min_price=excluded.min_price,active=1,data=excluded.data''',
   (p['id'],p['brand'],p['name'],p['category'],p.get('finish','unspecified'),search,min(prices) if prices else None,json.dumps(p,ensure_ascii=False)))
 if brand_id and status:
  db.execute('INSERT INTO catalog_sources(brand,data) VALUES(?,?) ON CONFLICT(brand) DO UPDATE SET data=excluded.data',(brand_id,json.dumps(status)))

def validate_import(payload):
 if not isinstance(payload,dict) or payload.get('schema_version')!=1 or not isinstance(payload.get('products'),list):
  raise ValueError('Expected schema_version: 1 and a products array. See data/import-example.json.')
 if not 1<=len(payload['products'])<=20000: raise ValueError('Import 1–20,000 products per file')
 output=[]; seen=set()
 for p in payload['products']:
  if not isinstance(p,dict): raise ValueError('Each product must be an object')
  brand=BY_BRAND.get(p.get('brand'))
  if not brand: raise ValueError('Unknown brand. Add it to data/brands.json and restart first.')
  product_id=str(p.get('id',''))
  if not re.fullmatch(re.escape(brand['id'])+r':[a-zA-Z0-9_.-]{1,100}',product_id) or product_id in seen: raise ValueError('Invalid or duplicate product ID')
  seen.add(product_id)
  name=str(p.get('name','')).strip()
  if not name or len(name)>400: raise ValueError('Product name must contain 1–400 characters')
  category=p.get('category')
  if category not in CATEGORIES: raise ValueError('Invalid category')
  url=safe_url(p.get('url',''),brand['allowed_hosts'])
  image=p.get('image')
  if image: safe_url(image,brand.get('image_hosts',brand['allowed_hosts']))
  variants=p.get('variants')
  if not isinstance(variants,list) or not 1<=len(variants)<=500: raise ValueError('Provide 1–500 variants')
  vs=[]; vids=set()
  for v in variants:
   vid=str(v.get('id','')); vn=str(v.get('name','')).strip()
   if not re.fullmatch(r'[\w.-]{1,100}',vid) or vid in vids or not vn or len(vn)>200: raise ValueError('Invalid variant ID or name')
   vids.add(vid)
   # Imported prices use decimal rupees and are dated snapshots, never live quotes.
   price=money(v.get('price_inr')); mrp=money(v.get('mrp_inr'))
   if v.get('available') is not None and not isinstance(v['available'],bool): raise ValueError('available must be true, false or null')
   vs.append({'id':vid,'name':vn,'price':price,'mrp':mrp if mrp and price is not None and mrp>price else None,
    'available':v.get('available'),'image':None,'url':safe_url(v.get('url',url),brand['allowed_hosts'])})
  observed=p.get('observed_at')
  if not isinstance(observed,int) or isinstance(observed,bool) or observed<0 or observed>time.time()+300: raise ValueError('observed_at must be a real Unix timestamp, not a future date')
  output.append({'id':product_id,'brand':brand['id'],'name':name,'category':category,'finish':finish_for(name),
   'url':url,'image':image,'source_url':safe_url(p.get('source_url',url),brand['allowed_hosts']),
   'source_kind':'import','observed_at':observed,'currency':'INR','variants':vs})
 return output
