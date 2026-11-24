"""Run the pinned upstream ionosonde decoder on saved synthetic IQ.
Imports only three reviewed function definitions; upstream module dependencies and
module-level statements are not executed. Original decoder bodies are unchanged.
"""
from pathlib import Path
import ast,hashlib,json,os,tempfile,urllib.request
import numpy as np
import h5py
from scipy.signal.windows import tukey
ROOT=Path(__file__).resolve().parents[1]
COMMIT='bf39b2f70e53b39f1366e2a85367dbd673ce25d5'
URL=f'https://raw.githubusercontent.com/jvierine/ionosonde/{COMMIT}/prc_lib.py'

def run():
 out=ROOT/'validation/end-to-end';cache=out/'upstream-prc_lib.py'
 if not cache.exists():
  with urllib.request.urlopen(URL,timeout=30) as response:cache.write_bytes(response.read())
 source=cache.read_bytes()
 if hashlib.sha256(source).hexdigest()!='7e8d41ffdd9fb401e30bf07b0dc1b6f4757b0cee6e4d782a0c91e9ebfebcbf55':raise ValueError('upstream source hash mismatch')
 tree=ast.parse(source)
 names={'periodic_convolution_matrix','create_estimation_matrix','analyze_prc2'}
 definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 if len(definitions)!=3:raise ValueError('upstream decoder definitions changed')
 namespace=dict(np=np,os=os,h5py=h5py,tukey=tukey)
 exec(compile(ast.Module(body=definitions,type_ignores=[]),URL,'exec'),namespace)
 with h5py.File(out/'program.h5') as f:
  chip_us=int(f.attrs['chip_ticks'])//10
  code=np.repeat(1-2*f['code'][:].astype(np.int8),chip_us).astype(np.complex64)
 results=[];cwd=Path.cwd()
 try:
  with tempfile.TemporaryDirectory() as tmp:
   os.chdir(tmp);Path('waveforms').mkdir()
   with h5py.File(out/'results.h5') as h:
    for case in ['rf_0','rf_1','rf_2']:
     g=h[case];iq=g['rx_iq'][:];periods=len(iq)//len(code)
     z=np.array(iq[:periods*len(code)],dtype=np.complex64)
     decoded=namespace['analyze_prc2'](z,code,n_ranges=500,cache_idx=0)
     power=abs(decoded['spec'])**2;k,r=np.unravel_index(np.argmax(power),power.shape)
     frequency=np.fft.fftshift(np.fft.fftfreq(periods,d=len(code)/1e6))[k]
     span=1e6/len(code);truth=float(g.attrs['truth_doppler_hz'])
     # Code-period sampling aliases Doppler; compare on its circular Nyquist interval.
     error=(frequency-truth+span/2)%span-span/2
     row=dict(case=case,carrier_hz=int(g.attrs['carrier_hz']),range_bin_us=int(r),doppler_bin_hz=float(frequency),doppler_wrapped_error_hz=float(error),doppler_bin_width_hz=span/periods,code_periods=periods)
     row['pass']=bool(abs(r-float(g.attrs['truth_delay_us']))<=2 and abs(error)<=span/periods/2)
     results.append(row)
 finally:os.chdir(cwd)
 summary=dict(scope='PINNED_UPSTREAM_DECODER_ON_SIMULATED_IQ',upstream_commit=COMMIT,upstream_source_url=URL,upstream_source_sha256=hashlib.sha256(source).hexdigest(),cases=results,pass_all=all(r['pass'] for r in results))
 (out/'upstream-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
 if not summary['pass_all']:raise AssertionError('upstream receiver acceptance failed')
 return summary
if __name__=='__main__':run()
