"""Executable reference-model E2E test, NOT firmware or hardware validation.
Runs saved HDF5 -> virtual schedule -> AD9850 serial decode -> clocked DAC ->
nominal schematic LC filter -> delayed noisy echo -> independent range/Doppler RX.
All waveform products use HDF5. Script provenance is stored in metadata only.
"""
from pathlib import Path
import sys,json,hashlib,math
from dataclasses import dataclass
import numpy as np
import h5py
from scipy import signal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'host'))
from program import save_program
FS=100_000_000
REF=10_000_000
RXFS=1_000_000

def load_program(path):
 """Consume the actual saved artifact, independently decode its DDS words."""
 with h5py.File(path) as h:
  if h.attrs['format']!='prnboard-program' or h.attrs['version']!=1:raise ValueError('unsupported saved program')
  if h.attrs['dds_clock_hz']!=FS or h.attrs['ticks_per_second']!=REF:raise ValueError('clock mismatch')
  p={k:h.attrs[k] for k in ['mode','start_utc_unix','chip_ticks','period_s']}
  p['code']=h['code'][:];p['rows']=h['frequencies'][:];p['words']=h['dds_phase_words'][:]
 if not 100<=p['chip_ticks']<=10000 or not len(p['code']) or not np.isin(p['code'],[0,1]).all():raise ValueError('invalid code or chip period')
 if p['words'].shape!=(len(p['rows']),2,5):raise ValueError('bad DDS table shape')
 end=0
 for i,row in enumerate(p['rows']):
  if int(row['offset_ticks'])!=end:raise ValueError('noncontiguous schedule')
  end+=int(row['dwell_ticks'])
  if int(row['guard_ticks'])>=int(row['dwell_ticks']):raise ValueError('invalid guard')
  if not 500000<=row['hz']<=30000000:raise ValueError('out-of-band carrier')
  for phase in (0,1):
   ftw,angle=decode_serial(serial_bits(p['words'][i,phase]))
   if angle!=phase*16:raise ValueError('DDS word does not encode required BPSK phase')
   if abs(ftw*FS/2**32-int(row['hz']))>FS/2**33+1e-8:raise ValueError('DDS frequency word does not match requested carrier')
 if p['mode']=='periodic' and end>int(p['period_s'])*REF:raise ValueError('overlapping schedule')
 return p

def serial_bits(word):
 # Actual wire ordering of a byte-oriented DMA serializer: byte 0 first, LSB first.
 return np.unpackbits(np.asarray(word,dtype=np.uint8),bitorder='little')

def decode_serial(bits):
 # Receiver-side shift register, intentionally not int.from_bytes/compiler helper.
 if len(bits)!=40 or not np.isin(bits,[0,1]).all():raise ValueError('serial frame must be 40 bits')
 register=0
 for position,bit in enumerate(bits):register|=int(bit)<<position
 control=(register>>32)&255
 if control&7:raise ValueError('reserved/power-down/parallel control bits set')
 return register&0xffffffff,control>>3

def serial_events(word,update_cycle):
 bits=serial_bits(word)
 # SPI 10 Mbit/s, rising edges 10 DDS cycles apart; 100 ns after last edge to UPDATE.
 edges=update_cycle-400+np.arange(40,dtype=np.int64)*10
 return edges,bits,update_cycle

def schedule(p,cycles=2,ready_tick=0):
 """Relative reference ticks; reacquisition waits for a complete program boundary."""
 period=int(p['period_s'])*REF
 first=0 if p['mode']!='periodic' else max(0,(ready_tick+period-1)//period)
 if p['mode']=='single':return [(ready_tick,ready_tick+cycles*period,0)]
 windows=[]
 for c in range(first,first+(cycles if p['mode']=='periodic' else 1)):
  for i,row in enumerate(p['rows']):
   start=c*period+int(row['offset_ticks'])
   if start<ready_tick:continue
   windows.append((start,start+int(row['dwell_ticks'])-int(row['guard_ticks']),i))
 return windows

def lc_filter():
 """Actual nominal ladder values in circuit.py, matched 49.9-ohm ports.
States: four inductor currents, three shunt capacitor voltages. ZOH discretization
models held DAC samples. Parasitics, tolerance and amplifier response excluded.
"""
 parts={p['ref']:p for p in json.loads((ROOT/'hardware/circuit.json').read_text())['parts']}
 def value(ref):
  text=parts[ref]['value']
  if 'R' in text:return float(text.replace('R','.'))
  suffix={'n':1e-9,'p':1e-12}
  return float(text[:-1])*suffix[text[-1]]
 L=np.array([value('L'+str(i)) for i in range(2,6)])
 C=np.array([value('C'+str(i)) for i in range(42,45)])
 R=value('R23')
 if value('R24')!=R:raise ValueError('filter model currently requires matched source/load')
 A=np.zeros((7,7));B=np.zeros((7,1));Y=np.zeros((1,7))
 A[0,0]=-R/L[0];A[0,4]=-1/L[0];B[0]=1/L[0]
 A[1,4]=1/L[1];A[1,5]=-1/L[1]
 A[2,5]=1/L[2];A[2,6]=-1/L[2]
 A[3,6]=1/L[3];A[3,3]=-R/L[3]
 for k in range(3):A[4+k,k]=1/C[k];A[4+k,k+1]=-1/C[k]
 Y[0,3]=R
 az,bz,cz,dz,_=signal.cont2discrete((A,B,Y,np.zeros((1,1))),1/FS,method='zoh')
 b,a=signal.ss2tf(az,bz,cz,dz)
 if np.max(abs(np.linalg.eigvals(az)))>=1:raise AssertionError('unstable LC discretization')
 return b[0],a

def render_dds(p,row_index,duration_s,mutation=None):
 row=p['rows'][row_index];step=int(p['chip_ticks'])*10;n=round(duration_s*FS)
 if step<1000:raise ValueError('unsupported chip duration')
 phase=np.zeros(n,dtype=np.int64);carrier_ftw=None;serial_preview=[]
 for chip_index,update in enumerate(range(0,n,step)):
  symbol=int(p['code'][chip_index%len(p['code'])]);word=p['words'][row_index,symbol]
  edges,bits,update=serial_events(word,update)
  if edges[0] < (update-step+1):raise AssertionError('serial preload misses preceding chip budget')
  if mutation=='reverse_bits':bits=bits[::-1]
  ftw,angle=decode_serial(bits)
  if mutation=='stuck_phase':angle=0
  if carrier_ftw is None:carrier_ftw=ftw
  if ftw!=carrier_ftw:raise AssertionError('carrier changes within dwell')
  # Frequency was pre-tuned while muted before this dwell. Phase update latency 13 clocks.
  a=update+13;b=min(n,update+step+13)
  if a<n:phase[a:b]=angle
  if len(serial_preview)<3:serial_preview.append((update,edges.copy(),bits.copy()))
 phase[:13]=0
 clock=np.arange(n,dtype=np.uint64)
 acc=(clock*np.uint64(carrier_ftw))&np.uint64(0xffffffff)
 acc=(acc+(phase.astype(np.uint64)<<27))&np.uint64(0xffffffff)
 ideal=np.cos(acc.astype(np.float64)*(2*np.pi/2**32))
 # Ten-bit DAC, normalized bipolar AC; DC and absolute RF power are not modeled.
 dac=2*np.rint((ideal+1)*511.5)/1023-1
 b,a=lc_filter();rf=2*signal.lfilter(b,a,dac)
 return rf,serial_preview,carrier_ftw

def reference_code(code,chip_ticks,n):
 # Independent receiver reference from input configuration, no transmitter waveform reuse.
 index=(np.arange(n,dtype=np.int64)*REF//RXFS)//chip_ticks
 bits=np.fromiter((int(c) for c in code),dtype=np.int8)
 return 1-2*bits[index%len(bits)]

def acquire(iq,code,chip_ticks,max_delay_us=500,doppler_grid=None):
 if doppler_grid is None:doppler_grid=np.arange(-250,251,5)
 maxlag=round(max_delay_us*RXFS/1e6)
 # Fixed integration window excludes startup/tail. No true channel delay is given to RX.
 skip=1000;count=len(iq)-skip-maxlag-1000
 if count<1000:raise ValueError('record too short for acquisition')
 r=reference_code(code,chip_ticks,len(iq));template=r[skip:skip+count]
 segment=iq[skip:skip+count+maxlag]
 t=np.arange(len(segment))/RXFS
 search=np.empty((len(doppler_grid),maxlag+1))
 for k,hz in enumerate(doppler_grid):
  shifted=segment*np.exp(-2j*np.pi*hz*t)
  search[k]=abs(signal.correlate(shifted,template,mode='valid',method='fft'))
 k,j=np.unravel_index(np.argmax(search),search.shape)
 denominator=np.linalg.norm(template)*np.linalg.norm(segment[j:j+count])
 return dict(delay_us=j*1e6/RXFS,doppler_hz=float(doppler_grid[k]),coherence=float(search[k,j]/denominator),map=search,doppler_grid=doppler_grid,delay_grid=np.arange(maxlag+1)*1e6/RXFS)

def rf_case(cfg,row_index,path,mutation=None):
 p=load_program(path);chip_ticks=int(p['chip_ticks']);code_period=len(cfg['code'])*chip_ticks/REF
 duration=max(.016,code_period*4)
 # Keep boundary runs bounded; one 31-chip code is used for long-chip scenarios.
 rf,serial,ftw=render_dds(p,row_index,duration,mutation)
 truth_delay_us=247.0;truth_doppler=125.;delay=round(truth_delay_us*FS/1e6)
 analytic=signal.hilbert(rf)
 echo=np.zeros(len(rf),dtype=np.complex128)
 echo[delay:]=analytic[:-delay]*np.exp(2j*np.pi*truth_doppler*np.arange(len(rf)-delay)/FS)
 rng=np.random.default_rng(1024+row_index+chip_ticks)
 rx_real=echo.real+rng.normal(0,np.sqrt(np.mean(echo.real**2)*10),len(rf))
 nominal=int(cfg['frequencies'][row_index]['hz'])
 mixed=2*rx_real*np.exp(-2j*np.pi*nominal*np.arange(len(rf))/FS)
 iq=signal.resample_poly(mixed,1,FS//RXFS)
 found=acquire(iq,cfg['code'],chip_ticks)
 found.update(carrier_hz=nominal,actual_carrier_hz=ftw*FS/2**32,chip_us=chip_ticks/10,truth_delay_us=truth_delay_us,truth_doppler_hz=truth_doppler,snr_rf_db=-10.,duration_s=duration)
 found['pass']=bool(abs(found['delay_us']-truth_delay_us)<=2 and abs(found['doppler_hz']-truth_doppler)<=5 and found['coherence']>.65)
 return found,dict(iq=iq,rf_preview=rf[:20000],serial=serial)

@dataclass
class Interlock:
 """Reference behavior only: timing constants are assumptions, not measured HC123 data."""
 last_pps:float=-math.inf
 last_status:float=-math.inf
 last_heartbeat:float=-math.inf
 qualified:bool=False
 def step(self,t,pps=False,status=False,lock=True,pa_ok=True,cpu_running=True):
  if pps:self.last_pps=t
  if status:self.last_status=t
  if cpu_running:
   self.qualified=bool(lock and pa_ok and t-self.last_pps<=1.2 and t-self.last_status<=1.5)
   if self.qualified:self.last_heartbeat=t
  # qualified can remain stuck high after CPU death; external heartbeat timeout still mutes.
  return self.qualified and t-self.last_pps<=2.2 and t-self.last_heartbeat<=.05

def fault_run(kind):
 gate=Interlock();t=np.arange(0,6,.01);on=[]
 for value in t:
  integer_second=abs(value-round(value))<1e-7
  pps=integer_second and not(kind=='pps_loss' and value>=2)
  status=integer_second and not(kind=='status_loss' and value>=2)
  on.append(gate.step(value,pps=pps,status=status,lock=not(kind=='lock_loss' and value>=2),pa_ok=not(kind=='pa_fault' and value>=2),cpu_running=not(kind=='cpu_crash' and value>=2)))
 on=np.array(on);after=np.where((t>=2)&~on)[0]
 return {'kind':kind,'mute_time_s':float(t[after[0]]),'pass':bool(len(after) and not on[t>=t[after[0]]].any())},t,on

def discipline_run():
 """Illustrative closed-loop plant, not implemented firmware or measured oscillator.
 2 ppm initial error, +0.1 ppb/s drift, 10 ppm/V tuning, 12-bit DAC, 30 ns PPS noise.
 """
 rng=np.random.default_rng(31);t=np.arange(600,dtype=float)
 phase=0.;control=0.;previous=0.;freq=[];phases=[];volts=[]
 for seconds in t:
  voltage=float(np.clip(np.rint((1.5+control/1e-5)*4095/3.3)*3.3/4095,.5,2.5))
  error=2e-6+seconds*1e-10+(voltage-1.5)*1e-5
  phase+=error
  measured=phase+rng.normal(0,30e-9)
  control-=.15*(measured-previous)+.005*measured;previous=measured
  control=float(np.clip(control,-1e-5,1e-5))
  freq.append(error);phases.append(phase);volts.append(voltage)
 freq=np.array(freq);phases=np.array(phases)
 result={'frequency_rms_ppb':float(np.sqrt(np.mean(freq[-120:]**2))*1e9),'phase_rms_ns':float(np.sqrt(np.mean(phases[-120:]**2))*1e9)}
 result['pass']=result['frequency_rms_ppb']<30 and result['phase_rms_ns']<100
 return result,dict(t_s=t,frequency_error=freq,phase_error_s=phases,control_voltage_v=volts)

def run(output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 rng=np.random.default_rng(25);code=''.join(map(str,rng.integers(0,2,127)))
 cfg=dict(mode='periodic',period_s=300,start_utc_unix=1800000000,chip_us=30,code=code,frequencies=[dict(hz=f,dwell_us=2000000,guard_us=100) for f in [30000000,500000,10000000]])
 path=output/'program.h5';save_program(cfg,path);p=load_program(path)
 windows=schedule(p,cycles=2)
 assert [i for _,_,i in windows]==[0,1,2,0,1,2]
 assert windows[3][0]==300*REF
 assert schedule(p,ready_tick=2*REF)[0][0]==300*REF
 cases=[]
 with h5py.File(output/'results.h5','w') as h:
  h.attrs.update(scope='REFERENCE_MODEL_SIMULATION_NOT_HARDWARE',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),program_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),circuit_sha256=hashlib.sha256((ROOT/'hardware/circuit.json').read_bytes()).hexdigest(),seed=25,rf_sample_rate_hz=FS,rx_sample_rate_hz=RXFS)
  h.create_dataset('schedule_ticks',data=np.array(windows,dtype=np.int64))
  servo,servo_data=discipline_run();g=h.create_group('discipline')
  for key,value in servo_data.items():g.create_dataset(key,data=value)
  g.attrs.update(servo)
  for index in range(3):
   result,data=rf_case(cfg,index,path);name=f'rf_{index}';g=h.create_group(name)
   for k in ['map','doppler_grid','delay_grid']:g.create_dataset(k,data=result.pop(k),compression='gzip')
   g.create_dataset('rx_iq',data=data['iq'],compression='gzip');g.create_dataset('rf_preview',data=data['rf_preview'],compression='gzip')
   g.create_dataset('serial_update_cycles',data=[v[0] for v in data['serial']]);g.create_dataset('serial_rising_cycles',data=[v[1] for v in data['serial']]);g.create_dataset('serial_bits',data=[v[2] for v in data['serial']])
   g.attrs.update(result);cases.append(result)
  for chip in [10,1000]:
   boundary=dict(cfg,chip_us=chip,code=code[:31])
   bp=output/f'program-{chip}us.h5';save_program(boundary,bp)
   for index in range(3):
    result,data=rf_case(boundary,index,bp);g=h.create_group(f'boundary_{chip}_{index}')
    for k in ['map','doppler_grid','delay_grid']:g.create_dataset(k,data=result.pop(k),compression='gzip')
    g.create_dataset('rx_iq',data=data['iq'],compression='gzip');g.create_dataset('rf_preview',data=data['rf_preview'],compression='gzip')
    g.attrs.update(result);cases.append(result)
  faults=[]
  for kind in ['lock_loss','pps_loss','status_loss','pa_fault','cpu_crash']:
   result,t,on=fault_run(kind);g=h.create_group(kind);g.create_dataset('t_s',data=t);g.create_dataset('tx_enable',data=on);g.attrs.update(result);faults.append(result)
  bad,data=rf_case(cfg,0,path,mutation='stuck_phase')
  negative=dict(kind='phase_modulator_stuck',detected=not bad['pass'],coherence=bad['coherence'])
 summary=dict(scope='REFERENCE_MODEL_SIMULATION_NOT_HARDWARE',rf_cases=cases,fault_cases=faults,negative_control=negative,schedule_checks=dict(user_order=True,repeat_300s=True,reacquisition_next_cycle=True),discipline_case=servo,pass_all=all(c['pass'] for c in cases+faults) and negative['detected'] and servo['pass'])
 (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))
 if not summary['pass_all']:raise AssertionError('E2E acceptance failure')
 return summary

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',type=Path,default=ROOT/'validation/end-to-end');args=a.parse_args();run(args.output)
