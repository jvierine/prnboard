"""AD9954 autonomous LFM register compiler, reference format only; no hardware I/O."""
from fractions import Fraction
from pathlib import Path
import argparse,json,math
import h5py
import numpy as np
FS=200_000_000
CFR1_BASE=(1<<9)|(1<<6) # Separate SDO; comparator off; all phase-clear functions OFF.
CFR1_SWEEP=CFR1_BASE|(1<<21)
CFR2_PLL20=20<<3 # Low VCO range at 200MHz; no external Si5351.
WIDTH={0:4,1:3,4:4,5:2,6:4,7:5,8:5}

def write(address,value):
 if address not in WIDTH or not 0<=value<1<<(8*WIDTH[address]):raise ValueError('register/value outside range')
 return bytes([address])+value.to_bytes(WIDTH[address],'big')

def compile_lfm(cfg):
 start=cfg['start_hz'];stop=cfg['stop_hz'];rate=cfg['rate_hz_s']
 if any(isinstance(v,bool) or not isinstance(v,int) for v in [start,stop,rate]):raise ValueError('integer frequencies and rate required')
 if not 500000<=start<stop<=30000000:raise ValueError('ascending LFM must remain within 0.5–30MHz')
 if rate<=0:raise ValueError('positive rate required; descending mode is not implemented')
 if cfg.get('endpoint')!='hold':raise ValueError('explicit endpoint=hold required; no implicit flyback')
 # Favor rate accuracy subject to <=2Hz frequency increments for this revision.
 candidates=[]
 for r in range(1,256):
  d=max(1,round(rate*4*2**32*r/FS**2));step=d*FS/2**32
  if step>2:continue
  actual=Fraction(d*FS**2,4*r*2**32)
  candidates.append((abs(actual-rate),d,r,actual))
 if not candidates:raise ValueError('requested ramp is outside supported fine-ramp envelope')
 _,d,r,actual=min(candidates)
 if abs(float(actual)/rate-1)>200e-6:raise ValueError('rate approximation exceeds provisional 200ppm limit')
 w0=round(start*2**32/FS);w1=round(stop*2**32/FS)
 frames=[write(0,CFR1_SWEEP),write(1,CFR2_PLL20),write(4,w0),write(5,0),write(6,w1),write(7,(r<<32)|d),write(8,(r<<32)|d)]
 return dict(start_hz=start,stop_hz=stop,requested_rate_hz_s=rate,ftw0=w0,ftw1=w1,delta=d,timer=r,
   achieved_rate_numerator=actual.numerator,achieved_rate_denominator=actual.denominator,
   achieved_rate_hz_s=float(actual),rate_error_ppm=(float(actual)/rate-1)*1e6,
   frequency_step_hz=d*FS/2**32,update_interval_s=4*r/FS,endpoint='hold',frames=frames)

def save_lfm(cfg,path):
 p=compile_lfm(cfg)
 with h5py.File(path,'w') as h:
  h.attrs.update(format='prnboard-lfm-program',version=1,dds='AD9954',dds_clock_hz=FS,reference_clock_hz=10000000,pll_multiplier=20,status='REFERENCE_FORMAT_NOT_FLASHABLE_FIRMWARE')
  for key,value in p.items():
   if key!='frames':h.attrs[key]=value
  g=h.create_group('register_writes')
  for i,frame in enumerate(p['frames']):g.create_dataset(str(i),data=np.frombuffer(frame,dtype=np.uint8))
 return p

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('configuration',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
 p=save_lfm(json.loads(args.configuration.read_text()),args.output)
 print({k:v for k,v in p.items() if k!='frames'})
