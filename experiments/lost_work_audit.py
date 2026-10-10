"""Independent rollback interpreter; does not import the loss calculator."""
import argparse
import json
from pathlib import Path
from experiments import heartbeat_world_audit as replay


def audit(acknowledged, restored, receipt, revision):
    ack = replay.inspect(acknowledged, revision)
    recovered = replay.inspect(restored, revision)
    endpoint = ack['report']['verified_simulation_tick']
    position = recovered['report']['verified_simulation_tick']
    if ack['manifest'] != recovered['manifest'] or not 0 <= position <= endpoint:
        raise ValueError('Different identity or future restore')
    for index, state in enumerate(recovered['states']):
        if replay.canonical(state) != replay.canonical(ack['states'][index]):
            raise ValueError('Acknowledged prefix divergence')
    missing = [state['simulation_tick'] for state in ack['states']
               if state['simulation_tick'] > position]
    expected = dict(schema='lost-work01-v1', source_revision=revision,
                    world_id=ack['report']['world_id'], run_id=ack['report']['run_id'],
                    acknowledged_tick=endpoint, recovered_tick=position,
                    missing_acknowledged_transitions=len(missing),
                    physically_durable=False, acceptable_loss_policy_defined=False,
                    recomputation_reverses_external_effects=False)
    if receipt != expected:
        raise ValueError('False acknowledgement, rollback or durability claim')
    return dict(verified=True, missing_ticks=missing, measurement=expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('acknowledged', 'restored', 'receipt', 'revision'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.acknowledged, args.restored,
                               json.loads(Path(args.receipt).read_bytes()), args.revision), sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'Rejected: {error}\n')
