"""Render the actual KiCad placement and annotate named components for review."""
from pathlib import Path
import subprocess, tempfile, json, io
import cairosvg
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
CLI='/Volumes/KiCad/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
with tempfile.TemporaryDirectory() as folder:
 svg=Path(folder)/'layout.svg'
 subprocess.run([CLI,'pcb','export','svg','--layers','F.Cu,F.Fab,F.Silkscreen,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','--mode-single','--output',str(svg),str(ROOT/'hardware/prnboard.kicad_pcb')],check=True)
 pic=Image.open(io.BytesIO(cairosvg.svg2png(url=str(svg),output_width=1500,background_color='#ecf3ed')))
 fig,ax=plt.subplots(figsize=(14,9),layout='constrained')
 ax.imshow(pic,extent=(0,95,85,0))
 parts={p['ref']:p for p in json.loads((ROOT/'hardware/circuit.json').read_text())['parts']}
 labels=[('J1','USB-C',-5,5),('U4','RP2040 timing / USB',-5,28),('U5','Program flash',-5,40),('U14','PPS / heartbeat interlock',-5,62),('J8','Digital I/O',-5,77),('U6','ESP32-S3 Wi-Fi',100,4),('U7','MAX-M10S GNSS',100,15),('J2','GNSS antenna SMA',100,25),('U9','10 MHz reference buffer',100,38),('U10','1.8 V analog supply',100,48),('U11','AD9954 DDS',100,57),('U13','RF output driver',100,68),('J3','Exciter output SMA',100,79)]
 for ref,name,tx,ty in labels:
  p=parts[ref]
  ax.annotate(f'{ref}  {name}',xy=(p['x'],p['y']),xytext=(tx,ty),ha='right' if tx<0 else 'left',va='center',fontsize=10,color='#16302b',arrowprops=dict(arrowstyle='-',color='#58736b',lw=.9),bbox=dict(facecolor='white',edgecolor='none',pad=2))
 ax.set_xlim(-53,155);ax.set_ylim(89,-5);ax.set_aspect('equal');ax.axis('off')
 fig.savefig(ROOT/'docs/board-layout.png',dpi=180,facecolor='white');plt.close(fig)
