"""Independent AL02 executed-copy lineage certificate verifier.

Reads only event/receipt dictionaries. Does not call the simulator, mutate
world state, or trust labels like "alive", "successful" or "self-replicating".
"""
from __future__ import annotations

from experiments.executed_heredity import ALPHABET, canonical, genotype_hash


def audit_births(births: list[dict], events: list[dict]) -> dict:
    errors: list[dict] = []
    event_map: dict[int, dict] = {}
    seen_birth_receipts: set[int] = set()
    seen_child_ids: set[int] = set()
    for event in events:
        seq = event.get("event_id")
        if not isinstance(seq, int) or seq in event_map:
            errors.append({"event_id": seq, "reason": "invalid_or_duplicate_event_identifier"})
            continue
        event_map[seq] = event
    write_used_by_birth: set[int] = set()
    for ordinal, birth in enumerate(births):
        problems: list[str] = []
        birth_seq = birth.get("event_id")
        parent = birth.get("parent_id")
        child = birth.get("child_id")
        birth_event = event_map.get(birth_seq)
        if birth_seq in seen_birth_receipts:
            problems.append("reused_birth_event_id")
        seen_birth_receipts.add(birth_seq)
        if not birth_event or birth_event.get("kind") != "BIRTH":
            problems.append("missing_birth_execution_event")
        else:
            for key in (
                "parent_id", "child_id", "child_genome_ops", "copy_event_ids",
                "parent_genome_ops", "child_material_units",
                "parent_genome_hash", "child_genome_hash",
            ):
                if birth.get(key) != birth_event.get(key):
                    problems.append(f"birth_event_receipt_mismatch:{key}")
        if child in seen_child_ids:
            problems.append("duplicate_child_id")
        seen_child_ids.add(child)
        if not isinstance(parent, int) or not isinstance(child, int) or child <= parent:
            problems.append("invalid_parent_child_id")
        parent_ops = birth.get("parent_genome_ops")
        child_ops = birth.get("child_genome_ops")
        unit_ids = birth.get("child_material_units")
        write_ids = birth.get("copy_event_ids")
        if (not isinstance(parent_ops, list) or not parent_ops
            or not isinstance(child_ops, list)
            or not isinstance(unit_ids, list)
            or not isinstance(write_ids, list)):
            problems.append("missing_genome_material_or_write_list")
        else:
            size = len(parent_ops)
            if not (size == len(child_ops) == len(unit_ids) == len(write_ids)):
                problems.append("incomplete_child_tape")
            if (any(not isinstance(op, int) or op not in ALPHABET
                    for op in parent_ops + child_ops)):
                problems.append("invalid_opcode_in_birth")
            if len(set(unit_ids)) != len(unit_ids):
                problems.append("duplicate_material_in_daughter")
            if len(set(write_ids)) != len(write_ids):
                problems.append("duplicate_child_write_ref")
            if genotype_hash(parent_ops) != birth.get("parent_genome_hash"):
                problems.append("parent_genotype_hash_mismatch")
            if genotype_hash(child_ops) != birth.get("child_genome_hash"):
                problems.append("daughter_genotype_hash_mismatch")
            for index, write_id in enumerate(write_ids):
                if write_id in write_used_by_birth:
                    problems.append("copy_write_reused_by_different_birth")
                write_used_by_birth.add(write_id)
                write = event_map.get(write_id)
                if write is None or write.get("kind") != "COPY_WRITE":
                    problems.append(f"slot_{index}:no_executed_write")
                    continue
                if (not isinstance(birth_seq, int) or
                    not isinstance(write_id, int) or
                    write_id >= birth_seq):
                    problems.append(f"slot_{index}:write_not_before_birth")
                if write.get("parent_id") != parent:
                    problems.append(f"slot_{index}:wrong_executing_parent")
                if write.get("parent_genome_hash") != birth.get("parent_genome_hash"):
                    problems.append(f"slot_{index}:wrong_parent_program")
                if write.get("nursery_index") != index or write.get("source_index") != index:
                    problems.append(f"slot_{index}:wrong_source_or_destination_index")
                if index < len(parent_ops) and write.get("source_op") != parent_ops[index]:
                    problems.append(f"slot_{index}:incorrect_source_opcode")
                if index < len(child_ops) and write.get("written_op") != child_ops[index]:
                    problems.append(f"slot_{index}:incorrect_written_opcode")
                if index < len(unit_ids) and write.get("material_unit") != unit_ids[index]:
                    problems.append(f"slot_{index}:wrong_allocated_material_unit")
                if write.get("mutated") != (
                    write.get("source_op") != write.get("written_op")
                ):
                    problems.append(f"slot_{index}:inconsistent_mutation_receipt")
                if write.get("paid_energy") != 2:
                    problems.append(f"slot_{index}:unpaid_write")
                if (not isinstance(write.get("source_material_unit"), int) or
                    not isinstance(write.get("material_unit"), int)):
                    problems.append(f"slot_{index}:no_material_identity")
        if birth.get("transferred_energy") != 4:
            problems.append("unfunded_or_wrong_child_endowment")
        if problems:
            errors.append({
                "birth_index": ordinal,
                "birth_event": birth_seq,
                "child_id": child,
                "reasons": problems,
            })
    raw_birth_event_ids = {e["event_id"] for e in events if e.get("kind") == "BIRTH"}
    if raw_birth_event_ids != seen_birth_receipts:
        errors.append({
            "reason": "events_and_birth_receipts_differ",
            "unpaired_event_ids": sorted(raw_birth_event_ids - seen_birth_receipts),
            "unpaired_receipt_ids": sorted(seen_birth_receipts - raw_birth_event_ids),
        })
    audited_valid = len(births) - sum("birth_index" in e for e in errors)
    return {
        "total_births": len(births),
        "valid_births": audited_valid,
        "invalid_births": len(errors),
        "executed_write_events": sum(e.get("kind") == "COPY_WRITE" for e in events),
        "errors": errors,
        "meaning": "Causal byte-copy receipts within this interpreter, not evidence of organismhood",
    }
