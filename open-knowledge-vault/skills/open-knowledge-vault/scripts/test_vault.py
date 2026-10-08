import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('vault',Path(__file__).with_name('vault.py'));v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class VaultTests(unittest.TestCase):
 def test_init_is_portable_and_preserves_edits(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);v.init(p,'Demo','meeting');self.assertFalse((p/'.obsidian').exists());self.assertFalse(v.audit(p)['errors']);(p/'index.md').write_text('My manual index');v.init(p,'Demo','meeting');self.assertEqual((p/'index.md').read_text(),'My manual index')
 def test_conformance_is_permissive(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'x.md').write_text(v.fm({'type':'Unknown type','custom':'retain','verified':{'by':'human:tester','at':'2026-10-08T10:00:00+02:00'}},'[future](missing.md)'));r=v.audit(p);self.assertFalse(r['errors']);self.assertTrue(r['warnings'])
 def test_invalid_core_and_reserved_files(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'note.md').write_text('# Untyped');(p/'sub').mkdir();(p/'sub/index.md').write_text(v.fm({'type':'Map'},'# Wrong'));self.assertEqual(len(v.audit(p)['errors']),2)
 def test_dataview_preserves_plugins_and_excludes_personal_state(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);root=p/'vault';src=p/'plugin';root.mkdir();src.mkdir();(src/'manifest.json').write_text(json.dumps({'id':'dataview','version':'fixture'}));(src/'main.js').write_text('// fixture');(src/'data.json').write_text('{"personal":"secret","enableDataviewJs":true}');(root/'.obsidian').mkdir();(root/'.obsidian/community-plugins.json').write_text('["existing"]');v.dataview(root,src);self.assertEqual(json.loads((root/'.obsidian/community-plugins.json').read_text()),['existing','dataview']);d=json.loads((root/'.obsidian/plugins/dataview/data.json').read_text());self.assertNotIn('personal',d);self.assertFalse(d['enableDataviewJs']);self.assertRaises(ValueError,v.dataview,root,src)
if __name__=='__main__':unittest.main()
