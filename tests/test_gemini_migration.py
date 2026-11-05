"""Offline contracts only: no claims about live model compatibility."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'llm-cli'))
from executor import LLMExecutor
from llm_skill import LLMSkill
from models import get_model


class MigrationTests(unittest.TestCase):
    def test_alias_and_explicit_legacy(self):
        skill = LLMSkill.__new__(LLMSkill)
        self.assertEqual(skill.select_model('gemini-flash'), ('gemini-3.5-flash-lite', 'google'))
        self.assertEqual(skill.select_model('gemini-2.5-flash'), ('gemini-2.5-flash', 'google'))
        self.assertIsNotNone(get_model('gemini-3.5-flash-lite'))

    def test_saved_choice_is_preserved(self):
        skill = LLMSkill.__new__(LLMSkill)
        skill.config = Mock()
        skill.config.get_last_model.return_value = 'gemini-2.5-flash'
        skill.config.config = {'last_provider': 'google'}
        self.assertEqual(skill.select_model(), ('gemini-2.5-flash', 'google'))

    @patch('executor.subprocess.run')
    def test_one_shot_selects_model(self, run):
        run.return_value = Mock(returncode=0, stdout='OK')
        self.assertEqual(LLMExecutor('gemini-3.5-flash-lite').execute_non_interactive('Hello'), 'OK')
        self.assertEqual(run.call_args.args[0], ['llm', '-m', 'gemini-3.5-flash-lite'])
        self.assertEqual(run.call_args.kwargs['input'], 'Hello')

    @patch('executor.subprocess.run')
    def test_chat_delegates_history_and_terminal(self, run):
        run.return_value = Mock(returncode=0)
        LLMExecutor('gemini-3.5-flash-lite').execute_interactive()
        run.assert_called_once_with(['llm', 'chat', '-m', 'gemini-3.5-flash-lite'])

    @patch('executor.subprocess.run')
    def test_chat_failure_surfaces(self, run):
        run.return_value = Mock(returncode=1)
        with self.assertRaises(RuntimeError):
            LLMExecutor('gemini-3.5-flash-lite').execute_interactive()

    def test_image_json_request_contract(self):
        create = Mock(return_value=types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='{"scores": {}}'))]))
        client = Mock()
        client.chat.completions.create = create
        factory = Mock(return_value=client)
        with patch.dict(sys.modules, {'openai': types.SimpleNamespace(OpenAI=factory), 'vault': types.SimpleNamespace(require=lambda name: 'test-key')}):
            spec = importlib.util.spec_from_file_location('vision_judge', ROOT / 'vision-bench/judge.py')
            judge = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(judge)
            for model in ['gemini-3.5-flash-lite', 'gemini-2.5-flash']:
                self.assertEqual(judge.call_judge(model, 'aW1hZ2U=', 'image/png', 'Return JSON'), {'scores': {}})
                self.assertEqual(create.call_args.kwargs, {
                    'model': model, 'response_format': {'type': 'json_object'},
                    'messages': [{'role': 'user', 'content': [
                        {'type': 'text', 'text': 'Return JSON'},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,aW1hZ2U='}},
                    ]}],
                })
            factory.assert_called_with(api_key='test-key', base_url='https://generativelanguage.googleapis.com/v1beta/openai/')


if __name__ == '__main__':
    unittest.main()
