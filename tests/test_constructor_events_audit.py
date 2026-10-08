import copy
import tempfile
import unittest
from pathlib import Path

from experiments import constructor_events_audit as audit
from experiments import constructor_event_fixtures as fixtures


def rehash(row):
    chain = audit.digest(row["initial"])
    before = row["initial"]
    for seq, event in enumerate(row["events"]):
        event["seq"] = seq
        event["previous_sha256"] = chain
        event["before_sha256"] = audit.digest(before)
        event["sha256"] = audit.digest({k: v for k, v in event.items() if k != "sha256"})
        chain, before = event["sha256"], event["after"]
    row["terminal"] = copy.deepcopy(before)
    return row


class ConstructorEventTests(unittest.TestCase):
    def test_all_authored_endpoints_and_shortcuts(self):
        reports = {r["case"]: audit.audit_receipt(r) for r in fixtures.fixtures()}
        self.assertEqual(len(reports), 16)
        self.assertEqual(sorted(name for name, r in reports.items() if r["renewed_chain_conversions"]), ["fixed_renewed", "renewed"])
        self.assertEqual(reports["renewed"]["renewed_chain_external_roots"], ["A0"])
        self.assertEqual(reports["one_C"]["internal_C_births"], 1)
        self.assertEqual(reports["external_rescue"]["internal_C_births"], 1)
        self.assertEqual(reports["external_rescue"]["external_or_direct_births"], 1)
        self.assertEqual(reports["direct"]["supplied_I_conversions"], 1)
        self.assertEqual(reports["supplied_I"]["internal_C_births"], 0)
        self.assertEqual(reports["ghost_renewed"]["local_conversions"], 0)
        self.assertEqual(reports["external_source"]["external_conversions"], 1)
        self.assertEqual(reports["work4"]["local_conversions"], 0)
        self.assertEqual(reports["work1"]["unavailable_attempts"], 1)
        for r in reports.values():
            self.assertEqual((r["material_residual"], r["potential_residual"]), (0, 0))

    def test_coherently_rehashed_identity_ancestry_and_cost_forgeries(self):
        for change in ("dead_parent", "wrong_parent", "roots", "free_build", "material", "heat", "function", "ID_reuse", "site", "opportunity", "external_as_internal", "reorder", "missing"):
            row = fixtures.renewed("bad")
            if change == "dead_parent":
                row["events"][4]["result"]["producer_id"] = "A0"
                row["events"][4]["after"]["objects"]["C3"]["producer_id"] = "A0"
            elif change == "wrong_parent":
                row["events"][0]["result"]["producer_id"] = "D0"
            elif change == "roots":
                row["events"][5]["after"]["objects"]["I4"]["roots"] = ["I4"]
            elif change == "free_build":
                row["events"][0]["result"]["charged_W"] = 0
                row["events"][0]["after"]["W"] += 2
                row["events"][0]["after"]["heat"] -= 2
            elif change == "material":
                row["events"][0]["after"]["P"] += 4
            elif change == "heat":
                row["events"][-1]["after"]["heat"] -= 1
            elif change == "function":
                row["events"][5]["after"]["objects"]["I4"]["functional"] = False
            elif change == "ID_reuse":
                row["events"][4]["request"]["new_id"] = "C1"
            elif change == "site":
                row["initial"]["S"].append(1)
                row["events"][5]["request"]["site"] = 1
            elif change == "opportunity":
                row["events"][0]["opportunities"]["funded_internal_build"] = False
            elif change == "external_as_internal":
                row = fixtures.renewed("bad", rescue=True)
                row["events"][4]["result"]["origin"] = "internal"
            elif change == "reorder":
                row["events"][3], row["events"][4] = row["events"][4], row["events"][3]
            else:
                del row["events"][3]
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit.audit_receipt(rehash(row))

    def test_partial_contact_and_corrupt_hash_rejected(self):
        partial = next(r for r in fixtures.fixtures() if r["case"] == "work1")
        partial["events"][0]["result"]["process_W"] = 1
        with self.assertRaises(ValueError):
            audit.audit_receipt(rehash(partial))
        row = fixtures.renewed("bad")
        row["events"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            audit.audit_receipt(row)

    def test_mode_unknown_fields_boolean_counts_and_genesis_ancestry(self):
        for change in ("mode", "extra", "bool", "genesis"):
            row = fixtures.renewed("bad")
            if change == "mode":
                row["mode"] = "ghost"
            elif change == "extra":
                row["events"][0]["request"]["free_constructor"] = True
            elif change == "bool":
                row["events"][0]["request"]["site"] = False
            else:
                row["initial"]["objects"]["A0"]["origin"] = "internal"
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit.audit_receipt(rehash(row))

    def test_terminal_tamper_and_manifest_revision_rejected(self):
        row = fixtures.renewed("bad")
        row["terminal"]["W"] += 1
        with self.assertRaises(ValueError):
            audit.audit_receipt(row)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures.write(root / "input", "a" * 40)
            with self.assertRaises(ValueError):
                audit.audit(root / "input", root / "wrong", "b" * 40)
            report = audit.audit(root / "input", root / "valid", "a" * 40)
            self.assertEqual(report["validated_authored_receipts"], 16)
            with self.assertRaises(ValueError):
                audit.audit(root / "input", root / "valid", "a" * 40)

    def test_valid_missing_and_unaffordable_impairment_attempts(self):
        f = fixtures.Authored("attempts", work=0)
        f.step("impair", "C")
        f.step("impair", "A")
        f.step("decay", "D")
        summary = audit.audit_receipt(f.receipt())
        self.assertEqual(summary["unavailable_attempts"], 3)
        self.assertEqual(f.state["heat"], 0)
        self.assertEqual(f.state["waste"], 0)

    def test_retained_old_constructor_is_not_renewed_chain(self):
        f = fixtures.Authored("retained_C", material=16, work=10)
        f.step("build", "C", "C1")
        f.step("decay", "A")
        f.step("build", "A", "A2")
        f.step("build", "C", "C3")  # occupied by old C1, no new C
        f.step("build", "I", "I4")
        f.step("contact")
        summary = audit.audit_receipt(f.receipt())
        self.assertEqual(summary["internal_I_conversions"], 1)
        self.assertEqual(summary["renewed_chain_conversions"], 0)
        self.assertEqual(summary["internal_C_births"], 1)


if __name__ == "__main__":
    unittest.main()
