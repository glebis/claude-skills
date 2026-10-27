import unittest
from cloudflare_workflows import AdapterError, ApiError, canonical, instance_id, reconcile_or_create, receipt, poll

class Fake:
    def __init__(self, existing=None, error=None): self.existing=existing; self.error=error; self.creates=0
    def get(self, workflow, run_id):
        if self.error: raise self.error
        return self.existing
    def create(self, workflow, run_id, payload): self.creates+=1; return {'status':'queued'}

class CloudflareTests(unittest.TestCase):
    def profile(self): return {'profile':'example','backend':'cloudflare.workflows','projectRef':'example-account','environment':'production'}
    def test_ids_stable_for_canonical_payload_and_changed_for_new_work(self):
        p=self.profile(); a=instance_id(p,'example',{'a':1,'b':2},'request'); b=instance_id(p,'example',{'b':2,'a':1},'request')
        self.assertEqual(a,b); self.assertNotEqual(a,instance_id(p,'example',{'a':2},'request')); self.assertLessEqual(len(a),100)
    def test_missing_instance_created_once(self):
        f=Fake(error=ApiError(404)); result,reused=reconcile_or_create(f,'workflow','id',{'prompt':'test'}); self.assertFalse(reused); self.assertEqual(f.creates,1)
    def test_existing_instance_reconciled_without_creation(self):
        f=Fake(existing={'params':'{"prompt":"test"}','status':'complete'}); _,reused=reconcile_or_create(f,'workflow','id',{'prompt':'test'}); self.assertTrue(reused); self.assertEqual(f.creates,0)
    def test_auth_or_uncertain_network_error_never_creates(self):
        for error in (ApiError(403),AdapterError('network uncertain')):
            f=Fake(error=error)
            with self.assertRaises(AdapterError):reconcile_or_create(f,'workflow','id',{})
            self.assertEqual(f.creates,0)
    def test_mismatched_reuse_rejected(self):
        with self.assertRaises(AdapterError):reconcile_or_create(Fake(existing={'params':{'prompt':'old'}}),'workflow','id',{'prompt':'new'})
    def test_receipt_omits_private_input_and_account(self):
        out=receipt(self.profile(),'workflow','id',{'status':'complete','params':{'private':'data'},'output':'{"ok":true}'})
        self.assertNotIn('projectRef',out); self.assertNotIn('params',out); self.assertTrue(out['isSuccess']); self.assertEqual(out['output'],{'ok':True})
    def test_timeout_returns_existing_run_without_new_submission(self):
        f=Fake(existing={'status':'running'}); result,timed_out=poll(f,'workflow','id',0); self.assertTrue(timed_out); self.assertEqual(result['status'],'running'); self.assertEqual(f.creates,0)
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):canonical({'value':float('nan')})

if __name__=='__main__': unittest.main()
