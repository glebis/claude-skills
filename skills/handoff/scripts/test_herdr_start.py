import importlib.machinery,importlib.util,unittest,tempfile
from pathlib import Path
from unittest.mock import patch,Mock
loader=importlib.machinery.SourceFileLoader('handoff_tested',str(Path(__file__).with_name('handoff')));spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
class HerdrStartup(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.state={'id':'test','pane':'stale','workspace':'stale'};self.p=patch.object(m,'state_root',return_value=self.root);self.p.start()
 def tearDown(self):self.p.stop();self.tmp.cleanup()
 def test_opt_out_never_probes_or_starts(self):
  with patch.object(m,'herdr_running') as probe,patch.object(m.subprocess,'Popen') as start:
   self.assertFalse(m.ensure_herdr(self.root,self.state,disabled=True));probe.assert_not_called();start.assert_not_called()
 def test_no_binary_falls_back(self):
  with patch.object(m.shutil,'which',return_value=None),patch.object(m.subprocess,'Popen') as start:
   self.assertFalse(m.ensure_herdr(self.root,self.state));start.assert_not_called()
 def test_running_does_not_restart(self):
  with patch.object(m.shutil,'which',return_value='/bin/herdr'),patch.object(m,'herdr_running',return_value=True),patch.object(m.subprocess,'Popen') as start:
   self.assertTrue(m.ensure_herdr(self.root,self.state));start.assert_not_called()
 def test_stopped_server_is_started(self):
  with patch.object(m.shutil,'which',return_value='/bin/herdr'),patch.object(m,'herdr_running',side_effect=[False,True]),patch.object(m.subprocess,'Popen') as start:
   self.assertTrue(m.ensure_herdr(self.root,self.state));self.assertEqual(start.call_args.args[0],['herdr','server'])
 def test_failed_start_falls_back_with_log(self):
  with patch.object(m.shutil,'which',return_value='/bin/herdr'),patch.object(m,'herdr_running',return_value=False),patch.object(m.subprocess,'Popen',return_value=Mock(poll=Mock(return_value=1))):
   self.assertFalse(m.ensure_herdr(self.root,self.state));self.assertIn('herdr-start.log',self.state['herdr_fallback'])
 def test_timeout_does_not_kill_existing_work(self):
  proc=Mock(poll=Mock(return_value=None))
  with patch.object(m.shutil,'which',return_value='/bin/herdr'),patch.object(m,'herdr_running',return_value=False),patch.object(m.subprocess,'Popen',return_value=proc):
   self.assertFalse(m.ensure_herdr(self.root,self.state,timeout=0));proc.terminate.assert_not_called()
 def test_new_pane_replaces_persisted_id(self):
  def attach(root,state):
   self.assertIsNone(state['pane']);state['pane']='new';state['workspace']='new-w';return 'new'
  with patch.object(m,'ensure_herdr',return_value=True),patch.object(m,'watch_in_herdr',side_effect=attach):
   m.prepare_herdr(self.root,self.state);self.assertEqual(self.state['ui_mode'],'herdr')
 def test_pane_failure_is_reported_detached(self):
  with patch.object(m,'ensure_herdr',return_value=True),patch.object(m,'watch_in_herdr',return_value=None):
   m.prepare_herdr(self.root,self.state);self.assertEqual(self.state['ui_mode'],'detached');self.assertIn('pane',self.state['herdr_fallback'])
if __name__=='__main__':unittest.main()
