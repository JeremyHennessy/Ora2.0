"""DATA-only prebuilt evaluation. No compile, load, patch or execution API.

No currently qualified reusable binding protocol/artifact exists. Matching
hashes and a claimed build receipt are NOT proof of source-to-binary custody
or of every helper attempt. Every result remains NO_GO for native admission.
"""
import hashlib
import json
import os
from pathlib import Path
from tools.eka1_cpu_grant_transport import plain,hexhash,read_exact

ROOT=Path(__file__).resolve().parents[1]
SOURCE_INPUTS=('experiments/native/eka1_probe_guardian.c',
               'experiments/native/eka1_probe_owner_watchdog.c',
               'tools/eka1_probe_child.py')
ARTIFACTS={'guardian':'eka1_probe_guardian.exe','watchdog':'eka1_owner_watchdog.dll',
           'header':'eka1_probe_pins.h'}
LEGACY_PROTOCOL='EKA-PER-ASSIGNMENT-COMPILED-v1'

def observe(path,expected):
    """Pin bytes/physical identity while reading; never map executable images."""
    plain(path);expected=hexhash(expected)
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        if not 0<before.st_size<=64*1024**2:raise ValueError('Bounded nonempty artifact required')
        h=hashlib.sha256();count=0
        while True:
            block=stream.read(65536)
            if not block:break
            count+=len(block)
            if count>64*1024**2:raise ValueError('Artifact grew beyond bound')
            h.update(block)
        after=os.fstat(stream.fileno());named=path.stat();plain(path)
        if ((before.st_dev,before.st_ino)!=(after.st_dev,after.st_ino) or
            (after.st_dev,after.st_ino)!=(named.st_dev,named.st_ino) or
            before.st_size!=after.st_size or count!=after.st_size or
            before.st_mtime_ns!=after.st_mtime_ns or h.hexdigest()!=expected):
            raise ValueError('Artifact identity/bytes changed')
    return {'sha256':expected,'file_identity':[after.st_dev,after.st_ino],'bytes':count,
            'scope':'READ_OBSERVATION_ONLY_NOT_EXECUTION_CUSTODY'}

def counter(value):
    if value is not None and (type(value) is not int or not 0<=value<2**63):
        raise ValueError('Missing costs stay unknown; invalid counters refused')
    return value

def evaluate(package_path,expected_sha256):
    """Evaluate fixed immutable package evidence, NEVER issue a capability."""
    package_path=Path(package_path)
    package,raw=read_exact(package_path,expected_sha256)
    if (type(package) is not dict or set(package)!={'schema','binding_protocol','source_sha256',
                                                   'artifact_sha256','build_receipt_sha256'} or
        package['schema']!='EKA-PREBUILT-CPU-CANDIDATE-v1' or
        type(package['binding_protocol']) is not str or
        type(package['source_sha256']) is not dict or set(package['source_sha256'])!=set(SOURCE_INPUTS) or
        type(package['artifact_sha256']) is not dict or set(package['artifact_sha256'])!=set(ARTIFACTS)):
        raise ValueError('Fixed prebuilt evidence schema required; no command/path input')
    sources={name:observe(ROOT/name,expected) for name,expected in package['source_sha256'].items()}
    package_files=[package_path.parent/name for name in ARTIFACTS.values()]
    for path in package_files:plain(path)
    if sum(path.stat().st_size for path in package_files)+len(raw)>64*1024**2:
        raise ValueError('Combined prebuilt package exceeds existing64MiB archive bound')
    files={name:observe(package_path.parent/filename,package['artifact_sha256'][name])
           for name,filename in ARTIFACTS.items()}
    receipt,receipt_raw=read_exact(package_path.parent/'separate-build-receipt.json',package['build_receipt_sha256'])
    if sum(item['bytes'] for item in files.values())+len(raw)+len(receipt_raw)>64*1024**2:
        raise ValueError('Combined package/evidence exceeds existing64MiB archive bound')
    if (type(receipt) is not dict or receipt.get('schema')!='EKA-SEPARATE-BUILD-OBSERVATION-v1' or
        receipt.get('source_sha256')!=package['source_sha256'] or
        receipt.get('artifact_sha256')!=package['artifact_sha256']):
        raise ValueError('Build receipt must bind these exact sources/header/artifacts')
    u=counter(receipt.get('root_USER_ticks'));k=counter(receipt.get('root_KERNEL_ticks'))
    costs=None if u is None or k is None else u+k
    attempts=receipt.get('attempts')
    if attempts is not None:
        if type(attempts) is not list:raise ValueError('Unknown or explicit attempted-birth records required')
        for index,item in enumerate(attempts):
            if (type(item) is not dict or type(item.get('sequence')) is not int or item['sequence']!=index or
                item.get('precharged_before_effect') is not True or
                item.get('outcome') not in ('created','failed','rejected')):
                raise ValueError('Failed/rejected attempts cannot be omitted or refunded')
    closure=receipt.get('closure')
    closure_claimed=(type(closure) is dict and closure.get('root_empty') is True and
                     closure.get('all_owned_births_signaled') is True and closure.get('EOF') is True and
                     type(closure.get('exit_code')) is int and closure['exit_code']==0)
    legacy=package['binding_protocol']==LEGACY_PROTOCOL
    return {'decision':'NO_GO','native_entry_enabled':False,'compiler_invoked':False,
            'package_sha256':expected_sha256,'sources':sources,'artifact_observations':files,
            'build_receipt_sha256':package['build_receipt_sha256'],
            'receipt_root_USER_plus_KERNEL_ticks':costs,
            'missing_root_costs_unresolved':costs is None,
            'reported_attempt_count':None if attempts is None else len(attempts),
            'attempted_birth_custody_verified':False,
            'build_closure_claimed':closure_claimed,'build_closure_independently_qualified':False,
            'fresh_assignment_binding':('INCOMPATIBLE_EMBEDDED_OWNER_LEDGER_DEADLINE' if legacy
                                        else 'UNKNOWN_UNQUALIFIED_BINDING_PROTOCOL'),
            'source_to_binary_execution_custody':'UNKNOWN_NOT_PROVED_BY_MATCHING_HASHES',
            'external_build_costs_settled':False,
            'remaining':['Reusable immutable runtime owner/ledger/deadline binding protocol and compatible artifact',
                         'Independent separate-build attempted-birth, dependency, final CPU and closure custody',
                         'External owner/observer/archive lifetime and post-archive settlement',
                         'Native grant integration and separate explicit human authorization'],
            'no_binary_patch_or_load':True,'historical_debt_refunded':False}
