"""Integration and negative tests of the saved artifact and reference simulation."""
import unittest,tempfile,sys
from pathlib import Path
import numpy as np
import h5py
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'));sys.path.insert(0,str(ROOT/'host'))
from end_to_end import load_program,schedule,serial_events,decode_serial,render_dds,Interlock,fault_run,discipline_run
from program import save_program
class E2ETests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'program.h5'
  self.cfg=dict(mode='periodic',period_s=300,chip_us=10,code='01011001',frequencies=[{'hz':30000000},{'hz':500000},{'hz':10000000}])
  save_program(self.cfg,self.path)
 def tearDown(self):self.temp.cleanup()
 def test_saved_program_order_and_guard(self):
  p=load_program(self.path);w=schedule(p)
  self.assertEqual([int(p['rows'][i]['hz']) for _,_,i in w],[30000000,500000,10000000]*2)
  self.assertEqual(w[0][1],19999000);self.assertEqual(w[3][0],3000000000)
 def test_reacquisition_waits_for_boundary(self):
  p=load_program(self.path);self.assertEqual(schedule(p,ready_tick=20000000)[0][0],3000000000)
 def test_thousand_rows_and_single_once_modes(self):
  cfg=dict(self.cfg,period_s=2000,frequencies=[{'hz':10000000}]*1000)
  save_program(cfg,self.path);self.assertEqual(len(schedule(load_program(self.path))),2000)
  cfg=dict(self.cfg,mode='once');save_program(cfg,self.path);self.assertEqual(len(schedule(load_program(self.path))),3)
  cfg=dict(self.cfg,mode='single',frequencies=[{'hz':10000000,'guard_us':0}]);save_program(cfg,self.path)
  self.assertEqual(len(schedule(load_program(self.path))),1)
 def test_corrupted_phase_table_rejected(self):
  with h5py.File(self.path,'r+') as h:h['dds_phase_words'][0,1,4]=64
  with self.assertRaises(ValueError):load_program(self.path)
 def test_corrupted_carrier_rejected(self):
  with h5py.File(self.path,'r+') as h:h['dds_phase_words'][0,0,0]=0
  with self.assertRaises(ValueError):load_program(self.path)
 def test_wire_decode_and_transfer_budget(self):
  p=load_program(self.path)
  for phase in (0,1):
   edges,bits,update=serial_events(p['words'][0,phase],1000)
   self.assertEqual(int(edges[0]),600);self.assertEqual(int(edges[-1]),990)
   ftw,decoded=decode_serial(bits);self.assertEqual(decoded,phase*16)
   self.assertEqual(ftw,int(p['rows'][0]['ftw']))
  render_dds(p,0,.0001) # Ten minimum-length chips through actual frame decoder/DAC/filter.
 def test_reversed_wire_order_detected(self):
  with self.assertRaises((ValueError,AssertionError)):render_dds(load_program(self.path),0,.0001,'reverse_bits')
 def test_no_transmit_without_initial_timing(self):
  g=Interlock()
  for t in np.arange(0,2,.01):self.assertFalse(g.step(t))
 def test_faults_mute_within_reference_limits(self):
  limits={'lock_loss':2.01,'pa_fault':2.01,'pps_loss':2.22,'status_loss':2.52,'cpu_crash':2.06}
  for kind,limit in limits.items():
   result,_,_=fault_run(kind);self.assertTrue(result['pass']);self.assertLessEqual(result['mute_time_s'],limit)
 def test_quantized_servo_reference(self):self.assertTrue(discipline_run()[0]['pass'])
if __name__=='__main__':unittest.main()
