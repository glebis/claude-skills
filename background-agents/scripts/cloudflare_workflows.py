#!/usr/bin/env python3
"""Submit/reconcile/status Cloudflare Workflows selected by an agent profile."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from profiles import ProfileError, resolve

API_ORIGIN = 'https://api.cloudflare.com/client/v4'
TERMINAL = {'complete', 'errored', 'terminated'}

class AdapterError(RuntimeError):
    pass

class ApiError(AdapterError):
    def __init__(self, status):
        self.status = status
        super().__init__('Cloudflare API request failed (HTTP ' + str(status) + '); check permissions, account and resource')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AdapterError('Refusing a redirect on a credential-bearing API request')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def instance_id(profile, workflow, payload, request_id):
    material = {'backend': profile['backend'], 'account': profile['projectRef'], 'workflow': workflow, 'environment': profile['environment'], 'request': request_id, 'payload': payload}
    return 'job_' + hashlib.sha256(canonical(material).encode()).hexdigest()[:48]

def decrypt_secrets(path):
    if not path: return {}
    result = subprocess.run(['sops', 'decrypt', '--output-type', 'json', str(path)], capture_output=True, text=True)
    if result.returncode: raise AdapterError('Cannot decrypt the supplied SOPS file; check the configured age/KMS identity')
    try: values = json.loads(result.stdout)
    except json.JSONDecodeError: raise AdapterError('SOPS plaintext must be a JSON object') from None
    if not isinstance(values, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in values.items()):
        raise AdapterError('SOPS plaintext must map environment names to strings')
    return values

class Client:
    def __init__(self, account, token):
        if not re.fullmatch(r'[a-f0-9]{32}', account): raise AdapterError('Cloudflare projectRef must be an account ID')
        if not token or '\r' in token or '\n' in token: raise AdapterError('Cloudflare API token is missing or invalid')
        self.account, self.token = account, token
        self.opener = urllib.request.build_opener(NoRedirect())
    def request(self, method, path, body=None):
        url = API_ORIGIN + '/accounts/' + self.account + '/workflows/' + path
        data = None if body is None else canonical(body).encode()
        request = urllib.request.Request(url, data=data, method=method, headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=30) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as error: raise ApiError(error.code) from None
        except urllib.error.URLError: raise AdapterError('Cloudflare API could not be reached; reconcile the same instance before resubmitting') from None
        if len(raw) > 2 * 1024 * 1024: raise AdapterError('Cloudflare response exceeded the adapter limit')
        try: value = json.loads(raw)
        except (ValueError, UnicodeError): raise AdapterError('Invalid Cloudflare response') from None
        if not isinstance(value, dict) or value.get('success') is not True: raise AdapterError('Cloudflare reported an API error; no success is assumed')
        return value.get('result')
    def get(self, workflow, run_id):
        path = urllib.parse.quote(workflow, safe='') + '/instances/' + urllib.parse.quote(run_id, safe='')
        return self.request('GET', path)
    def create(self, workflow, run_id, payload):
        return self.request('POST', urllib.parse.quote(workflow, safe='') + '/instances', {'instance_id': run_id, 'params': canonical(payload)})

def reconcile_or_create(client, workflow, run_id, payload):
    try:
        existing = client.get(workflow, run_id)
    except ApiError as error:
        if error.status != 404: raise
        return client.create(workflow, run_id, payload), False
    previous = existing.get('params')
    if isinstance(previous, str):
        try: previous = json.loads(previous)
        except ValueError: raise AdapterError('Existing run has an unreadable payload; refusing duplicate work') from None
    if canonical(previous) != canonical(payload): raise AdapterError('Existing instance payload differs; refusing to reuse it')
    return existing, True

def receipt(profile, workflow, run_id, result, reused=False):
    status = result.get('status', 'unknown')
    out = {'backend': 'cloudflare.workflows', 'profile': profile['profile'], 'environment': profile['environment'], 'workflow': workflow, 'runId': run_id, 'status': status, 'reused': reused, 'isSuccess': status == 'complete'}
    # No account IDs, credentials or input payloads are added to generic receipts.
    if status == 'complete':
        output = result.get('output')
        if isinstance(output, str):
            try: output = json.loads(output)
            except ValueError: pass
        out['output'] = output
    return out

def poll(client, workflow, run_id, timeout, interval=2):
    deadline = time.monotonic() + timeout
    while True:
        result = client.get(workflow, run_id)
        if result.get('status') in TERMINAL or result.get('status') == 'paused': return result, False
        if time.monotonic() >= deadline: return result, True
        time.sleep(min(interval, max(0, deadline - time.monotonic())))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default=os.environ.get('BACKGROUND_AGENT_PROFILES', 'agents.profiles.json'))
    parser.add_argument('--profile')
    parser.add_argument('--secrets-file', help='Optional SOPS-encrypted JSON; decrypted only in memory')
    parser.add_argument('--operation', default='run')
    sub = parser.add_subparsers(dest='command', required=True)
    submit = sub.add_parser('submit'); submit.add_argument('--payload-file', required=True); submit.add_argument('--request-id', required=True); submit.add_argument('--wait', action='store_true')
    status = sub.add_parser('status'); status.add_argument('--instance-id', required=True)
    try:
        args = parser.parse_args()
        secrets = decrypt_secrets(args.secrets_file)
        context = dict(os.environ); context.update(secrets)
        config = json.loads(Path(args.config).read_text())
        profile = resolve(config, args.profile, context)
        if profile['backend'] != 'cloudflare.workflows': raise AdapterError('This adapter only supports cloudflare.workflows; no backend fallback')
        workflow = profile['tasks'].get(args.operation)
        if not isinstance(workflow, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', workflow): raise AdapterError('Selected operation needs a valid Workflow name')
        token_name = profile.get('backendOptions', {}).get('apiTokenEnv', 'CLOUDFLARE_API_TOKEN')
        client = Client(profile['projectRef'], context.get(token_name))
        if args.command == 'status':
            result = client.get(workflow, args.instance_id); out = receipt(profile, workflow, args.instance_id, result)
        else:
            payload = json.loads(Path(args.payload_file).read_text())
            if len(canonical(payload).encode()) > 64000: raise AdapterError('Payload exceeds this adapter\'s 64 KB limit')
            run_id = instance_id(profile, workflow, payload, args.request_id)
            result, reused = reconcile_or_create(client, workflow, run_id, payload)
            out = receipt(profile, workflow, run_id, result, reused)
            if args.wait and result.get('status') not in TERMINAL:
                print(json.dumps(out), flush=True)
                result, timed_out = poll(client, workflow, run_id, profile.get('limits', {}).get('runTimeoutSeconds', 240))
                out = receipt(profile, workflow, run_id, result, reused); out['timedOut'] = timed_out
        print(json.dumps(out, ensure_ascii=False))
        if out['status'] in {'errored', 'terminated'}: return 1
        if out.get('timedOut') or out['status'] == 'paused': return 2
        return 0
    except (AdapterError, ProfileError, OSError, ValueError):
        # Do not echo decrypted values, payload contents, command environments or raw API responses.
        print('Cloudflare adapter stopped. Check profile, credential access, payload and instance status before retrying.', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
