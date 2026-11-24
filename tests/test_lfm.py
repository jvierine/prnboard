import sys,tempfile,unittest
from pathlib import Path
import h5py
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'host'),str(ROOT/'simulation')]
from lfm import save_lfm,compile_lfm,FS
from lfm_end_to_end import Ramp,phase_error
class LFMTests(unittest.TestCase):
 def cfg(self,rate=100000):return dict(start_hz=500000,stop_hz=30000000,rate_hz_s=rate,endpoint='hold')
 def test_rate_bounds_and_fine_steps(self):
  for rate in [100000,500000]:
   p=compile_lfm(self.cfg(rate));self.assertLess(abs(p['rate_error_ppm']),200);self.assertLess(p['frequency_step_hz'],2)
 def test_exact_register_format_and_no_phase_clear(self):
  p=compile_lfm(self.cfg());self.assertEqual(p['frames'][0],bytes.fromhex('0000200240'))
  self.assertEqual(p['frames'][1],bytes.fromhex('010000a0'))
 def test_invalid_modes_and_band(self):
  for key,value in [('endpoint','wrap'),('rate_hz_s',0),('stop_hz',30000001),('start_hz',True)]:
   c=self.cfg();c[key]=value
   with self.assertRaises(ValueError):compile_lfm(c)
 def test_full_sweep_and_endpoint_continuity(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'p.h5';save_lfm(self.cfg(),f);m=Ramp(f)
   self.assertAlmostEqual(m.hold_cycle/FS,295,delta=.05)
   for n in [m.L-1,m.L,m.hold_cycle-1,m.hold_cycle,m.hold_cycle+1]:self.assertEqual(m.phase_word_sum(n+1)-m.phase_word_sum(n),m.frequency_word(n))
   self.assertEqual(m.frequency_word(m.hold_cycle+FS),m.w1)
 def test_phase_residual_is_bounded_without_per_step_fit(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'p.h5';save_lfm(self.cfg(500000),f);m=Ramp(f)
   for q in [0,1,100000,10000000]:
    for r in [0,m.L//2,m.L-1]:self.assertLess(abs(phase_error(m,q*m.L+r)),1e-5)
 def test_corrupted_ramp_word_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'p.h5';save_lfm(self.cfg(),f)
   with h5py.File(f,'r+') as h:h['register_writes/6'][-1]=8
   with self.assertRaises(ValueError):Ramp(f)
 def test_phase_clear_is_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'p.h5';save_lfm(self.cfg(),f)
   with h5py.File(f,'r+') as h:h['register_writes/0'][3]=h['register_writes/0'][3]|0x20
   with self.assertRaises(ValueError):Ramp(f)
if __name__=='__main__':unittest.main()
