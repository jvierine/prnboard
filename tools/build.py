"""Base-conda entry point. Invokes KiCad's bundled interpreter only for pcbnew."""
from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1]
K=Path(os.environ.get('KICAD_APP','/Volumes/KiCad/KiCad/KiCad.app'))
for name in ['circuit.py','cad.py']:
 subprocess.run([sys.executable,str(ROOT/'tools'/name)],cwd=ROOT,check=True)
kp=K/'Contents/Frameworks/Python.framework/Versions/3.9/bin/python3'
subprocess.run([str(kp),str(ROOT/'tools/board.py')],cwd=ROOT,check=True)
