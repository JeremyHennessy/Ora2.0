"""Explicit operator command to publish one reviewed correction, without a model."""
import argparse
import json
import os
from pathlib import Path
from experiments.ora_ollama_feedback_v1 import configuration,sign


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('sequence',type=int)
    parser.add_argument('key')
    parser.add_argument('proposal_sha256')
    parser.add_argument('corrected_value')
    args=parser.parse_args()
    unused,key=configuration(args.directory)
    if key is None: raise ValueError('Ollama feedback mode is not configured')
    signed=sign(key,args.sequence,args.key,args.proposal_sha256,args.corrected_value)
    from experiments.ora_ollama_feedback_v1 import verify
    verify(key,args.sequence,args.key,signed)
    raw=json.dumps([dict(sequence=args.sequence,kind='approve',key=args.key,value=signed)]).encode()
    temporary=args.directory/'operator-inbox.next'
    with temporary.open('xb') as output:
        output.write(raw); output.flush(); os.fsync(output.fileno())
    os.replace(temporary,args.directory/'inbox.json')
    print('Published one explicitly operator-reviewed correction; awaiting service receipt.')


if __name__=='__main__': main()
