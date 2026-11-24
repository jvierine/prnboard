import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'host'))
from program import compile_program,dds_frequency_bytes,dds_phase_bytes,save_program,DDS_CLOCK_HZ
import h5py
class ProgramTests(unittest.TestCase):
 def config(self,**kw):return dict(code='00101101',frequencies=[{'hz':500000},{'hz':30000000}],**kw)
 def test_default_and_frequency_error(self):
  p=compile_program(self.config());self.assertEqual(p['chip_ticks'],300)
  for hz,_,_,_,ftw in p['rows']:self.assertLessEqual(abs(ftw*DDS_CLOCK_HZ/2**32-hz),DDS_CLOCK_HZ/2**33)
 def test_boundaries(self):
  for x in [10,1000,10.1]:compile_program(self.config(chip_us=x))
  for x in [1,9.9,1000.1,float('nan'),10.01]:
   with self.assertRaises(ValueError):compile_program(self.config(chip_us=x))
 def test_schedule_overlap(self):
  c=self.config();c['frequencies']=[{'hz':1000000}]*151
  with self.assertRaises(ValueError):compile_program(c)
  c['frequencies']=c['frequencies'][:150];compile_program(c)
 def test_1000_frequencies(self):
  c=self.config(period_s=2000);c['frequencies']=[{'hz':1000000}]*1000
  self.assertEqual(len(compile_program(c)['rows']),1000)
 def test_serial_phase_bit(self):
  self.assertEqual(dds_frequency_bytes(0x12345678),bytes.fromhex('0412345678'))
  self.assertEqual(dds_phase_bytes(0),bytes.fromhex('050000'))
  self.assertEqual(dds_phase_bytes(1),bytes.fromhex('052000'))
 def test_invalid_codes_and_frequency(self):
  for key,value in [('code','012'),('code',''),('frequencies',[{'hz':True}]),('frequencies',[{'hz':30000001}])]:
   c=self.config();c[key]=value
   with self.assertRaises(ValueError):compile_program(c)
 def test_single_mode_and_hdf5(self):
  c=dict(mode='single',code='01',frequencies=[{'hz':10000000,'guard_us':0}])
  with tempfile.TemporaryDirectory() as t:
   f=Path(t)/'p.h5';save_program(c,f)
   with h5py.File(f) as h:self.assertEqual(h['dds_phase_words'].shape,(1,2,3));self.assertEqual(h.attrs['chip_ticks'],300)
if __name__=='__main__':unittest.main()
