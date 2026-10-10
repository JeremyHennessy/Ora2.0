"""Read-only application rollback measurement; no durability or policy claim."""
import argparse
import json
from experiments.heartbeat_world_audit import inspect


def measure(acknowledged, restored, revision, acknowledgement_tick):
    observed = inspect(acknowledged, revision)
    backup = inspect(restored, revision)
    tick = observed['states'][-1]['simulation_tick']
    if type(acknowledgement_tick) is not int or acknowledgement_tick != tick:
        raise ValueError('Acknowledgement must match the preserved observed endpoint')
    if backup['manifest'] != observed['manifest']:
        raise ValueError('Different world, law or configuration')
    recovered = backup['states'][-1]['simulation_tick']
    if recovered > tick or backup['states'] != observed['states'][:recovered+1]:
        raise ValueError('Restore is not an acknowledged history prefix')
    return dict(schema='lost-work01-v1', source_revision=revision,
                world_id=observed['manifest']['identity']['world_id'],
                run_id=observed['manifest']['identity']['run_id'],
                acknowledged_tick=tick, recovered_tick=recovered,
                missing_acknowledged_transitions=tick-recovered,
                physically_durable=False, acceptable_loss_policy_defined=False,
                recomputation_reverses_external_effects=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acknowledged', required=True)
    parser.add_argument('--restored', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--acknowledgement-tick', required=True, type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(measure(args.acknowledged, args.restored, args.revision,
                                 args.acknowledgement_tick), sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'Rejected: {error}\n')
