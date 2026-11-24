"""One command for the reference-model E2E suite; use conda base."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,check=True)
for script in ['end_to_end.py','upstream_receiver.py','lfm_end_to_end.py','report.py']:
 subprocess.run([sys.executable,str(ROOT/'simulation'/script)],cwd=ROOT,check=True)
print('PASS: reference simulation and pinned upstream decoder. Hardware remains untested.')
