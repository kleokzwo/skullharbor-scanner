from pathlib import Path
from scanner import normalize_surface_xml

xml = """<nmaprun><host><ports><port protocol='tcp' portid='80'><state state='open'/><service name='http'/></port><port protocol='tcp' portid='443'><state state='open'/><service name='https'/></port><port protocol='tcp' portid='22'><state state='open'/><service name='ssh'/></port><port protocol='tcp' portid='445'><state state='filtered'/></port></ports></host><runstats><finished time='1'/></runstats></nmaprun>"""
items = normalize_surface_xml(xml, "https://example.test")
assert {x['rule_id'] for x in items} == {'surface.external-service.22'}
assert all(x['severity'] == 'info' for x in items)
assert all('does not by itself prove a vulnerability' in x['description'] for x in items)
root=Path(__file__).resolve().parents[1]
ui=(root/'frontend/src/components/ui.jsx').read_text()
css=(root/'frontend/src/style.css').read_text()
dash=(root/'frontend/src/pages/DashboardPage.jsx').read_text()
assert 'readiness-flow' in ui and ui.count('readiness-connector') >= 2
assert '.readiness-connector' in css
assert 'Security results' in dash and 'normal website ports 80/443 are excluded' in dash
print('surface observations and readiness flow tests: OK')
