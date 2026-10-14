"""Actual model-channel interventions; truthful feedback and branch flow retained."""
import json
from experiments.digital_cognitive76_source import OPS

VERSION = 'DIGITAL-COGNITIVE76-CONTROLS-v1'
MODES = ('intact', 'model_disabled', 'history_misbound')
def clone(value): return json.loads(json.dumps(value))

def validate(code, state):
    if type(code) is not list or not 1 <= len(code) <= 32 or any(
        type(t) is not list or len(t) != 3 or any(type(v) is not int or not 0 <= v < 32 for v in t)
        or t[0] not in OPS for t in code
    ): raise ValueError('Immutable typed programme required')
    if type(state) is not dict or set(state) != {'r','m','pc','feedback'}:
        raise ValueError('Typed local state required')
    if type(state['r']) is not list or type(state['m']) is not list or len(state['r']) != 2 or len(state['m']) != 8 or any(type(v) is not int or not 0 <= v < 16 for v in state['r'] + state['m']) or type(state['pc']) is not int or not 0 <= state['pc'] < len(code) or type(state['feedback']) is not int or state['feedback'] not in (0,1):
        raise ValueError('Malformed local state')

class Control:
    def __init__(self, code, state, mode, seed):
        validate(code,state)
        if mode not in MODES or type(seed) is not int or seed < 0:
            raise ValueError('Unregistered control configuration')
        self.code = clone(code); self.mode = mode; self.seed = seed
        self.reads = 0; self.epoch = 0

    def apply(self, before, after, current_cue=0):
        validate(self.code,before); validate(self.code,after)
        if type(current_cue) is not int or current_cue not in (0,1):
            raise ValueError('Cue bit required')
        op,a,b = self.code[before['pc']]; result = clone(after); rewrites = []
        if op == 1: self.reads += 1
        if op == 6: self.epoch += 1
        if op == 20:
            index = before['r'][a%2] % 8
            if index not in (0,1): raise ValueError('Model control scope is slots zero/one')
            if self.mode == 'model_disabled':
                result['m'][0:2] = [0,0]
            elif self.mode == 'history_misbound':
                result['m'][index] = before['m'][index]
                result['m'][index^1] = after['m'][index]
            if result['m'] != after['m']:
                rewrites.append(dict(channel='m', original=clone(after['m']), value=clone(result['m'])))
        return result, dict(mode=self.mode, epoch=self.epoch, read_count=self.reads, rewrites=rewrites)
