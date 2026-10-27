#!/usr/bin/env python3
"""Validate/list/resolve agent profiles. No remote calls or credential reads."""
import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path

ROOT_FIELDS = {'schemaVersion', 'defaultBackend', 'defaultProfile', 'defaults', 'profiles'}
PROFILE_FIELDS = {'extends', 'enabled', 'backend', 'projectRef', 'environment', 'agent', 'tasks', 'capabilities', 'credentialsEnv', 'limits', 'output', 'backendOptions'}
LIMIT_FIELDS = {'concurrency', 'runTimeoutSeconds', 'maxAttempts', 'maxExternalRequestsPerRun'}
ENV_NAME = re.compile(r'^[A-Z][A-Z0-9_]*$')
SENSITIVE_REF = re.compile(r'(?:^|_)(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)(?:_|$)')
SECRET_LITERAL = re.compile(r'\b(?:sk-(?:or-)?[A-Za-z0-9_-]{16,}|tr_(?:dev|prod)_[A-Za-z0-9_-]{16,})\b')

class ProfileError(ValueError):
    pass

def merge(base, override):
    out = copy.deepcopy(base)
    for key, value in override.items():
        out[key] = merge(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else copy.deepcopy(value)
    return out

def check_no_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower().replace('_', '').replace('-', '') in {'apikey', 'secret', 'secretkey', 'token', 'accesstoken', 'password'}:
                raise ProfileError('Credential values do not belong in profile configuration; use credentialsEnv names')
            check_no_secrets(item)
    elif isinstance(value, list):
        for item in value: check_no_secrets(item)
    elif isinstance(value, str) and SECRET_LITERAL.search(value):
        raise ProfileError('A credential-like literal was found; remove it from configuration')

def text(value, label):
    if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
        raise ProfileError(label + ' must be a nonempty single-line string')

def check_fields(profile):
    if not isinstance(profile, dict) or set(profile) - PROFILE_FIELDS: raise ProfileError('Unknown or invalid profile fields')
    for field in ('extends', 'backend', 'projectRef', 'environment'):
        if field in profile: text(profile[field], field)
    if 'enabled' in profile and type(profile['enabled']) is not bool: raise ProfileError('enabled must be boolean')
    agent = profile.get('agent', {})
    if not isinstance(agent, dict) or set(agent) - {'engine', 'provider', 'model'}: raise ProfileError('Invalid agent metadata')
    for key, value in agent.items(): text(value, 'agent.' + key)
    for field in ('tasks', 'output', 'backendOptions'):
        if field in profile and not isinstance(profile[field], dict): raise ProfileError(field + ' must be an object')
    for operation, task in profile.get('tasks', {}).items(): text(operation, 'operation'); text(task, 'task ID')
    for field in ('capabilities', 'credentialsEnv'):
        if field in profile:
            if not isinstance(profile[field], list): raise ProfileError(field + ' must be an array')
            for item in profile[field]:
                text(item, field)
                if field == 'credentialsEnv' and not ENV_NAME.fullmatch(item): raise ProfileError('credentialsEnv accepts environment names only')
    limits = profile.get('limits', {})
    if not isinstance(limits, dict) or set(limits) - LIMIT_FIELDS: raise ProfileError('Invalid limit fields')
    for value in limits.values():
        if type(value) is not int or value <= 0: raise ProfileError('Limits must be positive integers')

def inherited(config, name, stack=()):
    if name not in config['profiles']: raise ProfileError('Unknown selected or parent profile')
    if name in stack: raise ProfileError('Profile inheritance cycle')
    raw = config['profiles'][name]
    parent = inherited(config, raw['extends'], stack + (name,)) if raw.get('extends') else {}
    return merge(parent, {key: value for key, value in raw.items() if key != 'extends'})

def validate(config):
    if not isinstance(config, dict) or set(config) - ROOT_FIELDS: raise ProfileError('Unknown or invalid configuration fields')
    if type(config.get('schemaVersion')) is not int or config['schemaVersion'] != 1: raise ProfileError('Unsupported schemaVersion')
    if not isinstance(config.get('profiles'), dict) or not config['profiles']: raise ProfileError('profiles must be a nonempty object')
    check_no_secrets(config)
    check_fields(config.get('defaults', {}))
    if {'extends', 'enabled'} & set(config.get('defaults', {})): raise ProfileError('defaults cannot select inheritance or enabled state')
    if 'defaultBackend' in config: text(config['defaultBackend'], 'defaultBackend')
    for name, profile in config['profiles'].items():
        text(name, 'profile name'); check_fields(profile)
    if config.get('defaultProfile') not in config['profiles']: raise ProfileError('defaultProfile must name an existing profile')
    for name in config['profiles']:
        profile = merge(config.get('defaults', {}), inherited(config, name))
        check_fields(profile)
        if not profile.get('agent', {}).get('engine'): raise ProfileError('Each profile requires agent.engine')
        if not profile.get('tasks'): raise ProfileError('Each profile requires deployed task references')
    return config

def expand(value, env):
    if isinstance(value, str) and value.startswith('env:'):
        name = value[4:]
        if not ENV_NAME.fullmatch(name): raise ProfileError('Invalid environment reference')
        if SENSITIVE_REF.search(name): raise ProfileError('Credential-like references cannot be resolved into profile output')
        result = env.get(name)
        if not result: raise ProfileError('Required non-secret environment reference is unset: ' + name)
        text(result, 'Resolved reference')
        if SECRET_LITERAL.search(result): raise ProfileError('Resolved reference contains credential-like data')
        return result
    if isinstance(value, dict): return {key: expand(item, env) for key, item in value.items()}
    if isinstance(value, list): return [expand(item, env) for item in value]
    return value

def resolve(config, name=None, env=None):
    validate(config)
    name = name or config['defaultProfile']
    profile = merge(config.get('defaults', {}), inherited(config, name))
    if not profile.get('enabled', True): raise ProfileError('Selected profile is disabled')
    profile.setdefault('backend', config.get('defaultBackend', 'trigger.dev'))
    credential_names = profile.pop('credentialsEnv', [])
    profile = expand(profile, os.environ if env is None else env)
    profile['credentialsEnv'] = credential_names
    for field in ('projectRef', 'environment'): text(profile.get(field), field)
    check_fields(profile)
    if profile['backend'] == 'trigger.dev' and profile['environment'] not in {'dev', 'prod', 'staging', 'preview'}:
        raise ProfileError('Invalid Trigger.dev environment')
    return {'profile': name, **profile}

def list_profiles(config):
    validate(config)
    result = []
    for name in config['profiles']:
        p = merge(config.get('defaults', {}), inherited(config, name))
        result.append({'name': name, 'enabled': p.get('enabled', True), 'backend': p.get('backend', config.get('defaultBackend', 'trigger.dev')), 'engine': p['agent']['engine'], 'operations': sorted(p['tasks'])})
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', help='Project-owned JSON; otherwise BACKGROUND_AGENT_PROFILES or agents.profiles.json')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list'); sub.add_parser('validate')
    sub.add_parser('resolve').add_argument('profile', nargs='?')
    args = parser.parse_args()
    try:
        config_path = Path(args.config or os.environ.get('BACKGROUND_AGENT_PROFILES') or 'agents.profiles.json')
        config = json.loads(config_path.read_text())
        if args.command == 'validate': validate(config); result = {'valid': True, 'profiles': len(config['profiles'])}
        elif args.command == 'list': result = list_profiles(config)
        else: result = resolve(config, args.profile)
        print(json.dumps(result, indent=2))
    except (ProfileError, OSError, json.JSONDecodeError) as error:
        # Never print configuration bodies or environment values in diagnostics.
        message = str(error) if isinstance(error, ProfileError) else 'Cannot read a valid JSON profile configuration'
        print('Profile error: ' + message, file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
