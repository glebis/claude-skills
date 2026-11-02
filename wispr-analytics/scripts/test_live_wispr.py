import importlib.util, json, sqlite3, tempfile, unittest, time
from pathlib import Path
spec=importlib.util.spec_from_file_location('live',Path(__file__).with_name('live_wispr.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CaptureTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name);self.db=self.base/'flow.sqlite'
  with sqlite3.connect(self.db) as c:
   c.execute('CREATE TABLE History(transcriptEntityId TEXT PRIMARY KEY,timestamp TEXT,status TEXT,asrText TEXT,formattedText TEXT,duration REAL)')
   c.execute("INSERT INTO History VALUES('old','2026-01-01','formatted','private past',NULL,1)")
  self.root=m.create_session(self.base/'vault','Talk')
 def tearDown(self): self.temp.cleanup()
 def update(self,*values):
  with sqlite3.connect(self.db) as c: c.execute('INSERT OR REPLACE INTO History VALUES(?,?,?,?,?,?)',values)
 def test_single_note_curated_edits_revisions_timeout_restart_and_safe_fence(self):
  visible=list(self.root.glob('*.md'))
  self.assertEqual([p.name for p in visible],['Source.md'])
  w=m.Watcher(self.db,self.root,deadline=.01);self.assertEqual(sorted(p.name for p in (self.root/'.live').iterdir()),['state.json']);self.assertEqual(w.tick(),[])
  self.update('new','2026-10-07',None,None,None,None)
  self.assertEqual(w.tick(),[]);time.sleep(.02)
  self.assertEqual(w.tick()[0]['kind'],'transcription_timeout')
  note=self.root/'Source.md'; note.write_text(note.read_text().replace('## Capture notes','## Capture notes\n\nCurated term'),encoding='utf-8')
  speech='Hello\n```\n# fake heading\n<!-- WISPR TRANSCRIPT END -->\n```'
  self.update('new','2026-10-07','formatted',speech,None,1)
  self.assertEqual(w.tick()[0]['revision'],1)
  text=note.read_text();self.assertIn('Curated term',text);self.assertNotIn('private past',text)
  self.assertIn('````text',text);self.assertIn('\\<!-- WISPR TRANSCRIPT END -->',text)
  self.assertEqual(m.Watcher(self.db,self.root).tick(),[])
  self.update('new','2026-10-07','formatted','Revised',None,1)
  w.tick();text=note.read_text();self.assertIn('Revised',text);self.assertNotIn(speech,text);self.assertIn('Curated term',text)
  state=json.loads((self.root/'.live/state.json').read_text())
  self.assertEqual([(e['id'],e['revision']) for e in state['events'] if e['kind']=='transcript'],[('new',1),('new',2)])
  self.assertEqual(sorted(p.name for p in (self.root/'.live').iterdir()),['state.json'])
 def test_meeting_partial_append_correction_resume_and_legacy_state(self):
  f=self.base/'meetings/m1/live.ndjson';f.parent.mkdir(parents=True)
  f.write_text(json.dumps({'meta':{}})+'\n'+json.dumps({'id':'marker','marker':'pause'})+'\n')
  w=m.Watcher(self.db,self.root,meeting_id='m1');self.assertEqual(w.tick(),[])
  line=json.dumps({'id':'s1','timestamp':'2026-10-07','text':'First','startEpochMs':1000,'endEpochMs':2000})
  with f.open('a') as out:out.write(line)
  self.assertEqual(w.tick(),[])
  with f.open('a') as out:out.write('\n')
  self.assertEqual(w.tick()[0]['text'],'First')
  state=json.loads((self.root/'.live/state.json').read_text());state.pop('events');state.pop('status');(self.root/'.live/state.json').write_text(json.dumps(state))
  self.assertEqual(m.Watcher(self.db,self.root,meeting_id='m1').tick(),[])
  with f.open('a') as out:out.write(json.dumps({'id':'s1','timestamp':'2026-10-07','text':'Corrected'})+'\n')
  self.assertEqual(w.tick()[0]['revision'],2)
  self.assertEqual(list(self.root.glob('*.md')),[self.root/'Source.md'])
  with self.assertRaises(ValueError):m.Watcher(self.db,self.root,meeting_id='different')
 def test_talk_folders_are_independent(self):
  other=m.create_session(self.base/'vault','Talk');self.assertNotEqual(other,self.root)
  self.assertNotEqual(self.root/'Source.md',other/'Source.md')

if __name__=='__main__':unittest.main()
