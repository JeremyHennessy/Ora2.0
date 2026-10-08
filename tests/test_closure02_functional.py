"""CLOSURE-02: negative controls, mass accounting and exact old-physics equivalence."""
from dataclasses import asdict, replace
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments import closure_spatial as old
from experiments.closure02_functional import (
    ARMS, ORIGINS, advance, origin_core, run_world, run_study, summarize,
)


class PhysicsEquivalence(unittest.TestCase):
    def test_original_arms_exact_same_state_and_rng_after_one_step(self):
        reference_arms={
            "shell_effect":"intact",
            "shell_inert":"permeability_null",
            "no_shell":"no_M_synthesis",
        }
        p=old.Protocol()
        for arm,baseline_arm in reference_arms.items():
            for seed in (0,1,2):
                with self.subTest(arm=arm,seed=seed):
                    rng0=random.Random(seed)
                    fresh=old.initialize("dispersed",rng0,p)
                    for _ in range(5):
                        old.step(fresh,rng0,p,"intact")
                    w0,w1=fresh.duplicate(),fresh.duplicate()
                    x,y=random.Random(),random.Random()
                    x.setstate(rng0.getstate())
                    y.setstate(rng0.getstate())
                    target=old.select_target(fresh)
                    old.step(w0,x,p,baseline_arm,target=target)
                    counts=advance(w1,y,p,arm,core=origin_core(target))
                    self.assertEqual(asdict(w0),asdict(w1))
                    self.assertEqual(x.getstate(),y.getstate())
                    self.assertEqual(
                        counts["catalytic_s_consumed"],
                        counts["new_a"]+counts["new_r"]+
                        counts["new_m"]+counts["ghost_w"]
                    )

    def test_complete_dev_seed_matches_all_previous_reference_arms(self):
        from experiments.closure02_functional import run_world
        original,_=old.run_world(0,"clustered")
        current,_=run_world(0,"clustered")
        mapping={"shell_effect":"intact",
                 "shell_inert":"permeability_null",
                 "no_shell":"no_M_synthesis"}
        for ours, prior in mapping.items():
            a=next(r for r in original if r["arm"]==prior)
            b=next(r for r in current if r["arm"]==ours)
            self.assertEqual(a["final_grid"],b["final_grid"])
            self.assertEqual(a["core_recovery"],b["core_recovered"])
            self.assertEqual(a["target"],b["target"])
            self.assertEqual(a["eligible"],b["eligible"])

    def test_inert_ghost_products_deduct_one_S_and_preserve_mass(self):
        p=old.Protocol()
        base=old.initialize("clustered",random.Random(0),p)
        target=old.select_target(base)
        for arm in ("ghost_effect","ghost_inert"):
            w=base.duplicate()
            rng=random.Random(4)
            produced=0
            for _ in range(12):
                w._prior_ghost=produced
                stats=advance(w,rng,p,arm,core=origin_core(target))
                produced+=stats["ghost_w"]
                self.assertEqual(old.checked(w,old.CELLS*4),0)
                self.assertEqual(stats["new_m"],0)
                self.assertEqual(stats["new_a"]+stats["new_r"]+
                                 stats["ghost_w"],stats["catalytic_s_consumed"])
            self.assertGreater(produced,0)
            self.assertEqual(w.synth_m,0)
            self.assertEqual(sum(w.m),0)

    def test_shell_diffusion_effect_needs_shell_material(self):
        p=replace(old.Protocol(),reaction_rate=0.0,basal_p=0.0,decay_m=0.0)
        source=old.initialize("dispersed",random.Random(4),p)
        target=old.select_target(source)
        x,y=random.Random(6),random.Random(6)
        first,second=source.duplicate(),source.duplicate()
        s1=advance(first,x,p,"shell_effect",core=origin_core(target))
        s2=advance(second,y,p,"shell_inert",core=origin_core(target))
        self.assertEqual(asdict(first),asdict(second))
        self.assertEqual(x.getstate(),y.getstate())
        self.assertEqual(s1,s2)

    def test_wrong_arm_is_rejected(self):
        p=old.Protocol()
        w=old.initialize("clustered",random.Random(0),p)
        with self.assertRaisesRegex(ValueError,"Unknown arm"):
            advance(w,random.Random(0),p,"immortal",core=origin_core(40))


class FunctionalMetrics(unittest.TestCase):
    def test_all_origins_and_treatments_have_matched_fork_and_null_outcomes(self):
        for origin in ORIGINS:
            records,traces=run_world(0,origin)
            self.assertEqual(len(records),len(ARMS))
            self.assertEqual(len(traces),len(ARMS)*60)
            self.assertEqual([r["arm"] for r in records],list(ARMS))
            self.assertEqual(len({r["checkpoint_sha256"] for r in records}),1)
            self.assertEqual(len({r["eligible"] for r in records}),1)
            self.assertEqual(len({(
                r["post_damage_region"]["core_a"],
                r["post_damage_region"]["core_r"],
                r["post_damage_region"]["ring_coverage"],
            ) for r in records}),1)
            for r in records:
                self.assertEqual(r["max_mass_residual"],0)
                self.assertEqual(len(r["final_grid"]["s"]),old.CELLS)
                f=r["flow"]
                self.assertLessEqual(f["outward_moves"],f["outward_proposals"])
                self.assertLessEqual(f["inward_moves"],f["inward_proposals"])
                self.assertEqual(f["catalytic_s_consumed"],
                                 f["new_a"]+f["new_r"]+f["new_m"]+f["ghost_w"])
                if r["arm"] in ("ghost_effect","ghost_inert","no_shell"):
                    self.assertEqual(f["new_m"],0)
                if r["arm"] in ("shell_effect","shell_inert","no_shell"):
                    self.assertEqual(f["ghost_w"],0)

    def test_zero_eligibility_is_explicit_and_no_false_life_claim(self):
        p=replace(old.Protocol(),min_pre_a=100000)
        records,_=run_world(0,"nutrient_only",p)
        self.assertTrue(all(not r["eligible"] for r in records))
        self.assertTrue(all(r["core_recovered"] is None for r in records))
        self.assertTrue(all(r["ineligible_reason"] for r in records))

    def test_failed_and_unqualified_conditions_cannot_be_dropped(self):
        r=[]
        for origin in ORIGINS:
            data,_=run_world(0,origin)
            r.extend(data)
        totals=summarize(r,[0],old.Protocol())
        self.assertEqual(totals["total_treatments"],15)
        self.assertEqual(totals["three_origin_worlds"],3)
        with self.assertRaises(AssertionError):
            summarize(r[:-1],[0],old.Protocol())
        with self.assertRaises(AssertionError):
            summarize(r+[r[0]],[0],old.Protocol())

    def test_complete_run_byte_for_byte_replay_and_manifest_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            x=run_study(root,[0],revision="dev-revision")
            files={p.name:p.read_bytes() for p in root.iterdir()}
            y=run_study(root,[0],revision="dev-revision")
            self.assertEqual(x,y)
            self.assertEqual(files,{p.name:p.read_bytes() for p in root.iterdir()})
            self.assertEqual(x["total_treatments"],15)
            self.assertEqual(x["trace_rows"],900)
            self.assertEqual(len((root/"worlds.jsonl").read_text().splitlines()),15)
            self.assertEqual(len((root/"traces.jsonl").read_text().splitlines()),900)
            self.assertEqual(json.loads((root/"summary.json").read_text())["source_revision"],
                             "dev-revision")

    def test_replaying_same_dev_seed_world_is_deterministic(self):
        w1,t1=run_world(1,"dispersed")
        w2,t2=run_world(1,"dispersed")
        self.assertEqual(w1,w2)
        self.assertEqual(t1,t2)


if __name__=="__main__":
    unittest.main()
