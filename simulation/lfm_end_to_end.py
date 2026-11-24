"""Register-driven, full-duration AD9954 LFM model with independent analytic dechirp.
Phase accumulator arithmetic is integer-exact; this does not execute MCU firmware.
"""
from pathlib import Path
from fractions import Fraction
import sys,json,hashlib,math
import numpy as np
import h5py
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'host'),str(ROOT/'simulation')]
from lfm import save_lfm,FS
from end_to_end import serial_bits,decode_serial

class Ramp:
 def __init__(self,path):
  with h5py.File(path) as h:
   if h.attrs['format']!='prnboard-lfm-program' or h.attrs['dds_clock_hz']!=FS:raise ValueError('invalid LFM program/clock')
   self.metadata=dict(h.attrs);registers={}
   for key in sorted(h['register_writes'],key=int):
    a,v=decode_serial(serial_bits(h['register_writes'][key][:]));registers[a]=v
  cfr=registers[0]
  if not cfr&(1<<21) or cfr&((1<<13)|(1<<10)|(1<<2)|(1<<31)):raise ValueError('sweep missing, phase clear, RAM override or flyback enabled')
  if (registers[1]>>3)&31!=20:raise ValueError('incorrect PLL multiplier')
  self.w0=registers[4];self.w1=registers[6];self.d=registers[8]&0xffffffff;self.r=registers[8]>>32;self.L=4*self.r
  if not (self.d and 1<=self.r<=255 and self.w1>self.w0):raise ValueError('invalid ramp words')
  if registers[7]!=registers[8]:raise ValueError('this model requires matching up/down ramp parameters')
  actual=Fraction(self.d*FS**2,self.L*2**32)
  declared=Fraction(int(self.metadata['achieved_rate_numerator']),int(self.metadata['achieved_rate_denominator']))
  if actual!=declared:raise ValueError('register ramp differs from declared receiver rate')
  self.rate=actual;self.J=(self.w1-self.w0+self.d-1)//self.d
  # Post-PS0-latency origin: accumulator seeded by delta, as described in the datasheet.
  self.hold_cycle=(self.J-1)*self.L
 def phase_word_sum(self,n):
  if n<0:raise ValueError('time before effective sweep start')
  q,r=divmod(int(n),self.L);k=min(q,self.J-1)
  full=self.w0*k*self.L+self.d*self.L*k*(k+1)//2
  current=min(self.w0+(k+1)*self.d,self.w1)
  return full+(int(n)-k*self.L)*current
 def frequency_word(self,n):return min(self.w0+(int(n)//self.L+1)*self.d,self.w1)

def ideal_cycles(model,n):
 # Independent continuous quadratic phase: midpoint-equivalent intercept and achieved slope.
 return Fraction((2*model.w0+model.d)*n*model.L+model.d*n*n,2*model.L*2**32)

def phase_error(model,n):return float(Fraction(model.phase_word_sum(n),2**32)-ideal_cycles(model,n))*2*np.pi

def run(output):
 out=Path(output);out.mkdir(parents=True,exist_ok=True);cases=[]
 with h5py.File(out/'results.h5','w') as h:
  h.attrs.update(scope='AD9954_REGISTER_REFERENCE_MODEL_NOT_HARDWARE',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),pll_clock_hz=FS,ps0_pipeline_cycles=28,origin='after aligned PS0 pipeline latency; first delta already seeded')
  for requested in [100000,500000]:
   path=out/f'program-{requested}.h5';compiled=save_lfm(dict(start_hz=500000,stop_hz=30000000,rate_hz_s=requested,endpoint='hold'),path)
   m=Ramp(path)
   # Full-span state queries and explicit near-edge samples, without materializing billions of DAC samples.
   points={int(n) for n in np.linspace(0,m.hold_cycle-1,20001)}
   for q in np.linspace(1,m.J-2,1001,dtype=np.int64):
    points.update([int(q)*m.L-1,int(q)*m.L,int(q)*m.L+1,int(q)*m.L+m.L//2])
   ns=np.array(sorted(points),dtype=np.int64);errors=np.array([phase_error(m,int(n)) for n in ns])
   # Prove accumulator increments across selected update edges and the endpoint; no per-step phase fitting.
   edges=[m.L,m.L*100,m.hold_cycle,m.hold_cycle+FS]
   continuous=all(m.phase_word_sum(n+1)-m.phase_word_sum(n)==m.frequency_word(n) for n in edges)
   held=m.frequency_word(m.hold_cycle+FS)==m.w1
   # Received delayed chirp, dechirped with an independent continuous reference.
   fs_rx=20000;t=np.arange(1280)/fs_rx+1.;counts=np.rint(t*FS).astype(np.int64);delay=FS//1000;doppler=25
   values=[]
   for n in counts:
    n=int(n);cycles=Fraction(m.phase_word_sum(n-delay),2**32)-ideal_cycles(m,n)+Fraction(doppler*n,FS)
    values.append(float(cycles%1)*2*np.pi)
   rng=np.random.default_rng(requested)
   z=np.exp(1j*np.array(values))+(rng.normal(size=len(t))+1j*rng.normal(size=len(t)))*.005
   slope,intercept=np.polyfit(t,np.unwrap(np.angle(z)),1);beat=slope/(2*np.pi)
   expected=doppler-float(m.rate)*.001
   phase_rms=float(np.std(np.unwrap(np.angle(z))-(slope*t+intercept)))
   # Wrong rate on the receiver reference must fail the same beat acceptance.
   wrong_expected=doppler-float(m.rate)*1.01*.001
   result={k:v for k,v in compiled.items() if k!='frames'}
   result.update(duration_to_hold_s=m.hold_cycle/FS,max_phase_residual_rad=float(max(abs(errors))),phase_continuous=continuous,endpoint_holds=held,beat_hz=float(beat),expected_beat_hz=expected,dechirped_phase_rms_rad=phase_rms,wrong_rate_rejected=bool(abs(beat-wrong_expected)>.05))
   result['pass']=bool(continuous and held and max(abs(errors))<1e-5 and abs(beat-expected)<.05 and phase_rms<.02 and result['wrong_rate_rejected'])
   g=h.create_group(str(requested));g.create_dataset('sysclk_cycles',data=ns);g.create_dataset('phase_residual_rad',data=errors);g.create_dataset('rx_time_s',data=t);g.create_dataset('dechirped_iq',data=z);g.attrs.update(result)
   cases.append(result)
 summary=dict(scope='AD9954_REGISTER_REFERENCE_MODEL_NOT_HARDWARE',cases=cases,pass_all=all(c['pass'] for c in cases),limitations=['No firmware execution','PLL/noise/analog RF not modeled in LFM test','Phase origin assumes aligned PS0 and first-delta seed; bench verification required','Nominal-rate error is exported, not concealed by recalibrating the requested rate'])
 (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
 if not summary['pass_all']:raise AssertionError('LFM reference acceptance failed')
 return summary
if __name__=='__main__':run(ROOT/'validation/lfm')
