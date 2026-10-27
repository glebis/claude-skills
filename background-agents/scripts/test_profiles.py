import copy
import unittest
from profiles import ProfileError, list_profiles, resolve, validate

class ProfileTests(unittest.TestCase):
    def config(self):
        return {'schemaVersion': 1, 'defaultProfile': 'base', 'defaults': {'projectRef': 'env:TRIGGER_PROJECT_REF', 'environment': 'env:TRIGGER_ENVIRONMENT', 'limits': {'concurrency': 2, 'maxAttempts': 1}}, 'profiles': {'base': {'agent': {'engine': 'pi', 'provider': 'openrouter', 'model': 'env:PI_MODEL'}, 'tasks': {'run': 'env:PI_RUN_TASK_ID'}, 'capabilities': ['prompt'], 'credentialsEnv': ['OPENROUTER_API_KEY']}, 'review': {'extends': 'base', 'tasks': {'run': 'env:PI_REVIEW_TASK_ID'}, 'capabilities': ['source-review']}}}
    def env(self):
        return {'TRIGGER_PROJECT_REF': 'example-project', 'TRIGGER_ENVIRONMENT': 'prod', 'PI_MODEL': 'example/model', 'PI_RUN_TASK_ID': 'example-prompt-task', 'PI_REVIEW_TASK_ID': 'example-review-task', 'OPENROUTER_API_KEY': 'credential-value-must-not-be-resolved'}
    def test_trigger_default_and_explicit_selection(self):
        config = self.config()
        base = resolve(config, env=self.env()); review = resolve(config, 'review', self.env())
        self.assertEqual(base['backend'], 'trigger.dev'); self.assertEqual(base['profile'], 'base')
        self.assertEqual(review['tasks']['run'], 'example-review-task'); self.assertEqual(review['capabilities'], ['source-review'])
        self.assertEqual(review['limits']['concurrency'], 2)
    def test_future_engine_and_backend_preserved(self):
        c = self.config(); c['profiles']['review'].update({'backend': 'future-backend', 'environment': 'custom-environment', 'agent': {'engine': 'future-engine'}, 'credentialsEnv': []})
        r = resolve(c, 'review', self.env()); self.assertEqual(r['backend'], 'future-backend'); self.assertEqual(r['agent']['engine'], 'future-engine')
    def test_credentials_never_expanded(self):
        r = resolve(self.config(), env=self.env())
        self.assertEqual(r['credentialsEnv'], ['OPENROUTER_API_KEY']); self.assertNotIn(self.env()['OPENROUTER_API_KEY'], str(r))
    def test_refuses_credential_reference_in_normal_fields(self):
        c = self.config(); c['profiles']['base']['projectRef'] = 'env:OPENROUTER_API_KEY'
        with self.assertRaises(ProfileError) as raised: resolve(c, env=self.env())
        self.assertNotIn(self.env()['OPENROUTER_API_KEY'], str(raised.exception))
    def test_disabled_and_missing_env_stop(self):
        c = self.config(); c['profiles']['review']['enabled'] = False
        with self.assertRaises(ProfileError): resolve(c, 'review', self.env())
        with self.assertRaises(ProfileError): resolve(self.config(), env={})
    def test_missing_parent_and_cycle_stop(self):
        c = self.config(); c['profiles']['base']['extends'] = 'missing'
        with self.assertRaises(ProfileError): validate(c)
        c = self.config(); c['profiles']['base']['extends'] = 'review'
        with self.assertRaises(ProfileError): validate(c)
    def test_lists_without_credentials_or_identifier_resolution(self):
        rows = list_profiles(self.config()); self.assertEqual(len(rows), 2); self.assertNotIn('projectRef', rows[0])
    def test_rejects_secrets_and_bad_limits(self):
        for change in [{'secretKey': 'do-not-store-this'}, {'limits': {'concurrency': True}}, {'limits': {'maxAttempts': 0}}]:
            c = self.config(); c['profiles']['base'].update(change)
            with self.assertRaises(ProfileError): validate(c)
    def test_trigger_environment_explicit_and_valid(self):
        env = self.env(); env['TRIGGER_ENVIRONMENT'] = 'production'
        with self.assertRaises(ProfileError): resolve(self.config(), env=env)
    def test_input_not_mutated(self):
        c = self.config(); original = copy.deepcopy(c); resolve(c, env=self.env()); self.assertEqual(c, original)

if __name__ == '__main__':
    unittest.main()
