"""Offline necessary bounds. No World imports, replay, seeds or grants."""


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(label)
    return value


def probe_floor(completed_own_turns, global_tick, energy, extra_spend=0):
    """Necessary reachability floor for READ, two delay dispatches, FORAGE.

    Energy statements condition on no incoming transfer, no other gain and
    the supplied extra expenditure. They never certify the control path.
    Probe at turn256 is observed before expiry; survival is a different claim.
    """
    age = integer(completed_own_turns, 0, 255, 'age')
    tick = integer(global_tick, 0, 4096, 'global tick')
    energy = integer(energy, 1, 64, 'energy')
    extra = integer(extra_spend, 0, 4096, 'extra spend')
    return {
        'own_dispatches_through_probe_minimum': 4,
        'own_dispatches_including_exposure_minimum': 5,
        'base_heat_through_probe_minimum': 4,
        'remaining_own_dispatches': 256 - age,
        'age_permits_probe': age <= 252,
        'age_permits_survival_past_probe': age <= 251,
        'probe_on_expiry_boundary': age == 252,
        'remaining_global_dispatches': 4096 - tick,
        'global_floor_permits_probe': tick <= 4092,
        'energy_floor_permits_probe_without_incoming_gain': energy >= 4 + extra,
        'energy_positive_after_no_intake_probe_before_expiry_if_path_completes': energy >= 5 + extra,
        'path_or_opportunity_qualified': False,
        'limits': 'Necessary floors only; no guarantee of scheduling, control path, food, READ provenance or useful target relation.'}


def three_replay_bill(prefix_tick, suffix_limit):
    """Three current restore-from-genesis branches, with equal tail ceilings.

    Initial stocks are separate World ledgers. Formation heat is already inside
    each initial energy balance, never added again as a new energy injection.
    This is not actual metering or a native resource budget.
    """
    prefix = integer(prefix_tick, 0, 4096, 'prefix')
    suffix = integer(suffix_limit, 4, 4096, 'suffix')
    if prefix + suffix > 4096:
        raise ValueError('original horizon exceeded')
    return {
        'branches': 3,
        'prefix_replay_dispatches': 3 * prefix,
        'suffix_dispatch_ceiling': 3 * suffix,
        'total_dispatch_ceiling': 3 * (prefix + suffix),
        'ordinary_treated_read_heat_all_branches': 3,
        'genesis_formation_heat_component_all_worlds': 3 * 43,
        'genesis_energy_stock_all_worlds': 3 * 1420,
        'material_capacity_all_separate_worlds': 3 * 512,
        'formation_already_in_genesis_balance': True,
        'includes_original_discovery_world': False,
        'covers_other_panels_or_references': False,
        'additional_opcode_costs_and_inflow_ledger_required': True,
        'host_fork_storage_cpu_wall_costs_measured': False,
        'pricing_qualified': False,
        'checkpoint_authority_granted': False,
        'execution_authorized': False}
