"""Check generated draft connectivity and report remaining release failures honestly."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'hardware/circuit.json').read_text())
xml=ET.parse(ROOT/'validation/netlist.xml')
actual={}
for net in xml.findall('./nets/net'):
 for node in net.findall('node'):actual[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name'].lstrip('/')
errors=[]
for p in d['parts']:
 for pin in p['pins']:
  if pin['net'] and actual.get((p['ref'],pin['n']))!=pin['net']:errors.append([p['ref'],pin['n'],pin['net'],actual.get((p['ref'],pin['n']))])
fp=json.loads((ROOT/'validation/footprints.json').read_text())
erc=json.loads((ROOT/'validation/erc.json').read_text())
drc=json.loads((ROOT/'validation/drc.json').read_text())
report=dict(status='ENGINEERING_DRAFT_NOT_FOR_FABRICATION',connectivity_mismatches=errors,footprint_missing_pins=fp['missing_pads'],footprint_unmapped_pads=fp['unmapped_pads'],erc_findings=sum(len(s['violations']) for s in erc['sheets']),pcb_findings=len(drc['violations']),pcb_unconnected_items=len(drc['unconnected_items']),component_estimate_usd=round(sum(p['cost_usd'] for p in d['parts']),2),hardware_tested=False,firmware_implemented=False,routing_complete=False)
(ROOT/'validation/status.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert not errors and not fp['missing_pads'] and not fp['unmapped_pads']
assert report['erc_findings']==0
# Deliberately do not present this check as a release gate: DRC and firmware remain unfinished.
