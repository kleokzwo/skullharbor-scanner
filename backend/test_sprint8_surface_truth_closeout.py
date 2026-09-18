from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scanner import normalize_surface_xml
from services.plans.advanced import POLICY
assert 80 not in POLICY.surface_ports and 443 not in POLICY.surface_ports
required=(21,22,23,25,110,111,143,389,445,465,587,636,993,995,2049,2375,2376,3306,3389,5432,5900,6379,9200,11211,27017)
assert all(p in POLICY.surface_ports for p in required)
xml='''<?xml version="1.0"?><nmaprun><host><ports><port protocol="tcp" portid="22"><state state="open"/><service name="ssh"/></port><port protocol="tcp" portid="445"><state state="filtered"/></port><port protocol="tcp" portid="3306"><state state="closed"/></port><port protocol="tcp" portid="80"><state state="open"/></port></ports></host><runstats><finished/></runstats></nmaprun>'''
items=normalize_surface_xml(xml,'https://example.test')
assert len(items)==1, items
assert items[0]['rule_id']=='surface.external-service.22'
assert items[0]['severity']=='info'
assert 'does not by itself prove a vulnerability' in items[0]['description']
print('surface truth closeout tests: OK')
