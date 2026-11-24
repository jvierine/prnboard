"""Generate editable KiCad review schematic. Uses conda base; no fabrication export."""
from pathlib import Path
import json, uuid, math
from circuit import parts, ROOT
out=ROOT/'hardware';out.mkdir(exist_ok=True)
uid=lambda x:str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/jvierine/prnboard/'+x))
q=lambda x:json.dumps(str(x))
eff='(effects (font (size 1 1)))'
rid=uid('schematic')
def geometry(p):
 n=len(p['pins']);rows=math.ceil(n/2);h=max(3.81,math.ceil((rows+1)/2)*1.27)
 return [(-15.24 if i<rows else 15.24,h-1.27-(i%rows)*1.27,0 if i<rows else 180) for i in range(n)],h

def libsym(p):
 ps,h=geometry(p);name=p['ref']
 s=f'(symbol "PRNboard:{name}" (pin_names (offset 0.7)) (in_bom yes) (on_board yes)\n'
 s+=f'(property "Reference" "{name[0]}" (at 0 {h+2.54} 0) {eff}) (property "Value" {q(p["value"])} (at 0 {h+5.08} 0) {eff})\n'
 s+=f'(symbol "{name}_0_1" (rectangle (start -10.16 {-h}) (end 10.16 {h}) (stroke (width .2) (type default)) (fill (type background))))\n(symbol "{name}_1_1"\n'
 for pin,(x,y,a) in zip(p['pins'],ps):
  typ=pin['type']
  s+=f'(pin {typ} line (at {x} {y} {a}) (length 5.08) (name {q(pin["label"])} (effects (font (size .7 .7)))) (number {q(pin["n"])} (effects (font (size .7 .7)))))\n'
 return s+'))\n'
def head(id,title,libs):
 return f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{id}") (paper "A3") (title_block (title {q(title)}) (date "2026-11-23") (rev "B DRAFT")) (lib_symbols {libs})\n'
sections=[]
for sec in dict.fromkeys(p['section'] for p in parts):
 pp=[p for p in parts if p['section']==sec]
 # Avoid tiny symbols / overcrowding; maximum 12 components per review sheet.
 for k in range(0,len(pp),12):sections.append((sec+(' '+str(k//12+1) if len(pp)>12 else ''),pp[k:k+12]))
parent=head(rid,'PRNboard — circuit review draft','')
parent+=f'(text "REVIEW DRAFT — not for fabrication. Wi-Fi + USB; 200 MHz AD9954 clock; single-frequency GNSS fallback." (at 20 20 0) (effects (font (size 1.3 1.3)) (justify left)) (uuid "{uid("overview")}"))\n'
for si,(name,pp) in enumerate(sections):
 sid=uid('sheet/'+name);file=name.lower().replace(' ','_')+'.kicad_sch';s=head(sid,'PRNboard / '+name,''.join(libsym(p) for p in pp))
 for i,p in enumerate(pp):
  x=50.8+96.52*(i%4);y=60.96+76.2*(i//4);ps,h=geometry(p);inst=uid('inst/'+p['ref'])
  s+=f'(symbol (lib_id "PRNboard:{p["ref"]}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{inst}")\n'
  props={'Reference':p['ref'],'Value':p['value'],'Footprint':'PRNboard:'+p['ref'],'MPN':p['mpn'],'LCSC':p['lcsc'] or ''}
  for pi,(pn,pv) in enumerate(props.items()):s+=f'(property {q(pn)} {q(pv)} (at {x} {y-h-5+pi*2} 0) (effects (font (size .9 .9))'+(' (hide yes)' if pi>1 else '')+'))\n'
  for pin in p['pins']:s+=f'(pin {q(pin["n"])} (uuid "{uid(inst+pin["n"])}"))\n'
  s+=f'(instances (project "prnboard" (path "/{rid}/{sid}" (reference "{p["ref"]}") (unit 1)))))\n'
  for pin,(px,py,a) in zip(p['pins'],ps):
   xx=x+px;yy=y-py
   if pin['net']:
    end=xx+(-2.54 if a==0 else 2.54);la=0 if a==0 else 180
    s+=f'(wire (pts (xy {xx} {yy}) (xy {end} {yy})) (stroke (width 0) (type default)) (uuid "{uid(inst+pin["n"]+"w")}"))\n'
    s+=f'(global_label {q(pin["net"])} (shape passive) (at {end} {yy} {la}) (effects (font (size .7 .7)) (justify '+('right' if la==0 else 'left')+f')) (uuid "{uid(inst+pin["n"]+"l")}"))\n'
   else:s+=f'(no_connect (at {xx} {yy}) (uuid "{uid(inst+pin["n"]+"nc")}"))\n'
 s+=')\n';(out/file).write_text(s)
 x=20+(si%4)*98;y=40+(si//4)*57
 parent+=f'(sheet (at {x} {y}) (size 86 38) (stroke (width .2) (type default)) (fill (color 0 0 0 0)) (uuid "{sid}") (property "Sheetname" {q(name)} (at {x} {y-2} 0) (effects (font (size 1.2 1.2)) (justify left))) (property "Sheetfile" {q(file)} (at {x} {y+40} 0) (effects (font (size .8 .8)) (justify left))) (instances (project "prnboard" (path "/{rid}" (page "{si+2}")))))\n'
(out/'prnboard.kicad_sch').write_text(parent+')\n')
(out/'prnboard.kicad_pro').write_text(json.dumps({'meta':{'filename':'prnboard.kicad_pro','version':1}},indent=2))
# Embedded schematic symbols suffice for editing; retain source manifest for reproducibility.
print('Generated',len(sections)+1,'schematic sheets')

(out/'fp-lib-table').write_text('(fp_lib_table (lib (name \"PRNboard\") (type \"KiCad\") (uri \"${KIPRJMOD}/PRNboard.pretty\") (options \"\") (descr \"Local draft footprints\")))\n')

(out/'PRNboard.kicad_sym').write_text('(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+''.join(libsym(p).replace('"PRNboard:'+p['ref']+'"','"'+p['ref']+'"',1) for p in parts)+')\n')
(out/'sym-lib-table').write_text('(sym_lib_table (lib (name "PRNboard") (type "KiCad") (uri "${KIPRJMOD}/PRNboard.kicad_sym") (options "") (descr "PRNboard draft circuit")))\n')
