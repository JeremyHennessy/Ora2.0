"""Static diagnostic scope; no organism, World, sample or resource queries."""
def contract():
    return dict(version='DIGITAL-HISTORY-46-FIRST-EFFECT-AGE-v1',
        classification='software_registration_only',prepared_tests=16,
        world_histories_executed=0,closed_histories_queried=0,
        intended_closed_histories=6408,intended_external_samples=list(range(256)),
        intended_consumed_contexts=list(range(44200,44208)),
        reserved_unopened=list(range(44300,44308)),
        first_effect_only=True,alternative_outcomes_predicted=False,
        strict_intervening_actions=True,empty_actions_replace_latch=True,
        repeated_reads_are_not_independent=True,
        full_original_vm_proof_is_prior_precondition=True,
        whole_census_execution_requires_separate_review=True,
        developer_supplied_diagnostic=True,learned_policy_installed=False,
        learning=False,evolution=False,repair=False,stage_credit=False)
