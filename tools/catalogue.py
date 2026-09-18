"""Owner-operated catalogue CLI. Run from the GlowSync folder."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.catalogue import BY_BRAND,fetch_brand,validate_import,upsert_products
from backend.db import connect,initialize

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 sub=parser.add_subparsers(dest='command',required=True)
 sync=sub.add_parser('sync',help='Refresh complete public feeds');sync.add_argument('--brand',action='append',choices=[b for b,v in BY_BRAND.items() if v.get('feed_base')])
 imp=sub.add_parser('import',help='Merge a validated supplier JSON file');imp.add_argument('file',type=Path)
 sub.add_parser('status',help='Show current catalogue counts')
 args=parser.parse_args();path=str(os.environ.get('GLOWSYNC_DATABASE',ROOT/'local.db'));initialize(path)
 if args.command=='status':
  with connect(path) as db:
   for row in db.execute('SELECT brand,count(*) n FROM catalog_products WHERE active=1 GROUP BY brand'):print(f'{BY_BRAND[row["brand"]]["name"]}: {row["n"]:,} listings')
 elif args.command=='import':
  products=validate_import(json.loads(args.file.read_text(encoding='utf-8')))
  with connect(path) as db:upsert_products(db,products)
  print(f'Imported {len(products):,} listings. Existing matching IDs were updated.')
 else:
  failed=False
  for brand in args.brand or [b for b,v in BY_BRAND.items() if v.get('feed_base')]:
   try:
    products,status=fetch_brand(brand,print)
    with connect(path) as db:upsert_products(db,products,brand,True,status)
    print(f'{BY_BRAND[brand]["name"]}: {len(products):,} listings saved.')
   except Exception as e:failed=True;print(f'{BY_BRAND[brand]["name"]}: {e}; previous data retained.',file=sys.stderr)
  if failed:sys.exit(1)

if __name__=='__main__':main()
