"""Compile portable PRNboard programs to HDF5. No hardware transmission occurs.
Hardware time units are 100 ns ticks of the disciplined reference.
"""
from decimal import Decimal
from pathlib import Path
import argparse,json,math
import h5py
import numpy as np
TICKS_PER_SECOND=10_000_000
DDS_CLOCK_HZ=100_000_000

def integer(value,name):
 if isinstance(value,bool) or not isinstance(value,int):raise ValueError(name+' must be an integer')
 return value

def ticks_us(value,name):
 try:d=Decimal(str(value))*10
 except Exception:raise ValueError(name+' must be numeric')
 if not d.is_finite() or d!=d.to_integral_value():raise ValueError(name+' must be a multiple of 0.1 us')
 return int(d)

def compile_program(cfg):
 mode=cfg.get('mode','periodic')
 if mode not in ['periodic','once','single']:raise ValueError('unsupported mode')
 chip=ticks_us(cfg.get('chip_us',30),'chip_us')
 if not 100<=chip<=10000:raise ValueError('chip_us must be 10–1000')
 code=cfg.get('code')
 if not isinstance(code,str) or not code or set(code)-set('01'):raise ValueError('code must be a nonempty explicit binary string')
 if len(code)>65536:raise ValueError('draft code limit is 65536 chips')
 rows=cfg.get('frequencies',[])
 if not isinstance(rows,list) or not 1<=len(rows)<=1000:raise ValueError('require 1–1000 frequency entries')
 if mode=='single' and len(rows)!=1:raise ValueError('single mode requires one frequency')
 start=integer(cfg.get('start_utc_unix',0),'start_utc_unix')
 if not 0<=start<2**53:raise ValueError('invalid UTC epoch')
 result=[];offset=0
 for row in rows:
  if not isinstance(row,dict):raise ValueError('frequency entry must be an object')
  hz=integer(row['hz'],'hz')
  if not 500000<=hz<=30000000:raise ValueError('frequency outside 0.5–30 MHz')
  dwell=ticks_us(row.get('dwell_us',2000000),'dwell_us')
  guard=ticks_us(row.get('guard_us',100),'guard_us')
  if not 0<=guard<dwell or dwell<chip:raise ValueError('invalid dwell or guard')
  if mode!='single' and guard<100:raise ValueError('hops require at least 10 us mute guard in this draft')
  if dwell>86400*TICKS_PER_SECOND:raise ValueError('dwell exceeds draft 24-hour limit')
  ftw=(hz*2**32+DDS_CLOCK_HZ//2)//DDS_CLOCK_HZ
  result.append((hz,offset,dwell,guard,ftw));offset+=dwell
 period=integer(cfg.get('period_s',300),'period_s')
 if mode=='periodic' and (period<=0 or offset>period*TICKS_PER_SECOND):raise ValueError('sweep does not fit repeat interval')
 return dict(mode=mode,start=start,chip_ticks=chip,code=np.fromiter((int(c) for c in code),dtype=np.uint8),rows=result,period_s=period)

def dds_bytes(ftw,chip):
 """AD9850 serial order: FTW bits 0..31, control bits 0..7; bits within bytes LSB first."""
 if not 0<=ftw<2**32 or chip not in (0,1):raise ValueError('invalid DDS word')
 return ftw.to_bytes(4,'little')+bytes([0x80 if chip else 0])

def save_program(cfg,path):
 p=compile_program(cfg)
 dt=np.dtype([('hz','<u4'),('offset_ticks','<u8'),('dwell_ticks','<u8'),('guard_ticks','<u8'),('ftw','<u4')])
 with h5py.File(path,'w') as f:
  f.attrs.update(format='prnboard-program',version=1,mode=p['mode'],start_utc_unix=p['start'],chip_ticks=p['chip_ticks'],ticks_per_second=TICKS_PER_SECOND,dds_clock_hz=DDS_CLOCK_HZ,period_s=p['period_s'],status='HOST_REFERENCE_FORMAT_NOT_FIRMWARE_UPLOAD')
  f.create_dataset('code',data=p['code'])
  f.create_dataset('frequencies',data=np.array(p['rows'],dtype=dt))
  f.create_dataset('dds_phase_words',data=np.array([[list(dds_bytes(row[4],c)) for c in (0,1)] for row in p['rows']],dtype=np.uint8))
 return p

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('configuration',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
 p=save_program(json.loads(args.configuration.read_text()),args.output)
 print(f"Compiled {len(p['rows'])} frequencies and {len(p['code'])} chips to {args.output}")
