"""Offline validation of the captured GPU child consumer graph and code hashes."""
import hashlib
import json
from pathlib import Path

capture = Path(__file__).resolve().parent.parent / 'private-captures/CAP0003.JSON'
d = json.loads(capture.read_text(encoding='utf-8-sig'))
p = d['platform']
if not p['complete'] or not d['unique_expected_identity_observed']:
    raise ValueError('Incomplete or ambiguous capture')
handles = {h['id']:h for h in p['handles']}
target = p['target']
children = [h for h in p['handles'] if h['gpu_descendant'] and h['id'] != target and h['active_opens']]
if len(children) != 1:
    raise ValueError(f'Expected one active child, got {len(children)}')
child = children[0]
text='c2777438c769d2118e3900a0c969723b'
gop='dea94290dc23384a96fb7aded080516a'
edid='f6340c1c80d3fa41a0498ad06c1a66aa'
edges = child['active_opens']
if len(edges)!=4:
    raise ValueError('Unexpected active consumer count')
def one(proto,attr,controller):
    found=[x for x in edges if x['protocol']==proto and int(x['attributes'],16)==attr
           and x['controller']==controller and x['count']==1]
    if len(found)!=1: raise ValueError('Missing or ambiguous child consumer')
    return found[0]['agent']
text_agent=one(text,16,child['id'])
if text_agent!=one(text,8,p['conout']): raise ValueError('Text consumer mismatch')
gop_agent=one(gop,16,child['id']);edid_agent=one(edid,16,child['id'])
if len({text_agent,gop_agent,edid_agent})!=3: raise ValueError('Consumers are not distinct')
agents={a['agent']:a for a in p['gpu_agents']}
expected={text_agent:'aa99a0e641b179cf56fd26f881a69e9256a62bdc453744977e6879fadbb266b9',
          gop_agent:'6a2fb1c4032d620497c99370441873f7c86788c73ac603f5c1ece1955c49ef8a',
          edid_agent:'70a1feba834e6b71ca42ad81bbb3bb960c92d00bad74a5b747fd874a158fdf18'}
for agent,digest in expected.items():
    code=agents[agent]['code'];raw=bytes.fromhex(code['hex'])
    if len(raw)!=code['length'] or hashlib.sha256(raw).hexdigest()!=digest or code['loaded_sha256']!=digest:
        raise ValueError('Driver code changed or is incomplete')
if child['id'] not in handles: raise ValueError('Child missing')
print('PASS: captured one GPU child; text, GOP and EDID consumer identities and code hashes match')
print('This offline inventory does not prove firmware disconnect or reconnect safety.')
