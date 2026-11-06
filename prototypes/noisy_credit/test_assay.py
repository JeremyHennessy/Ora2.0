import unittest
import census as c


class AssayTests(unittest.TestCase):
    def test_delivery_is_delayed_and_no_free_tail(self):
        p = c.spec('a', 'constant', action=0)
        r = c.life(p, [[0, 0, 0.0]]*4, 3, retain=True)
        self.assertEqual(r['delivered_successes'], 1)
        self.assertEqual([e[4] for e in r['trace']], [0, 0, 0, 512])
        self.assertEqual(r['unresolved'], 3)

    def test_expensive_estimator_dies_before_food(self):
        p = c.spec('e', 'estimator')
        r = c.life(p, [[0, 0, 0.0]]*5, 2)
        self.assertFalse(r['alive'])
        self.assertEqual(r['death_reason'], 'formation')
        self.assertEqual(r['attempts'], 0)

    def test_credit_uses_original_cue_action(self):
        p = c.spec('w', 'wsls')
        rows = [[0, 1, .5], [1, 0, .5], [2, 0, .5], [0, 1, .5]]
        r = c.life(p, rows, 2, retain=True)
        self.assertEqual(r['trace'][-1][7], 1)
        self.assertEqual(r['costs']['feedback'], 128)

    def test_clamp_preserves_physical_food_for_identical_actions(self):
        p = c.spec('c', 'counter', width=2, drop=1)
        rows = [[0, 0, 0.0]]*8
        a = c.life(p, rows, 2)
        b = c.life(p, rows, 2, 'clamp')
        self.assertEqual(a['delivered_food'], b['delivered_food'])
        self.assertEqual(a['costs'], b['costs'])

    def test_energy_conservation_and_dead_actor_score(self):
        p = c.spec('c', 'counter', width=3, drop=2)
        r = c.life(p, [[0, 1, .99]]*100, 3, retain=True)
        self.assertFalse(r['alive'])
        self.assertEqual(r['score'], 0)
        for e in r['trace']:
            self.assertEqual(e[2], e[1]-e[3]+e[4]-e[5])

    def test_candidate_selection_uses_development_only(self):
        ps = c.candidates()
        rs = {p['name']: [{'score': 1}] for p in ps}
        self.assertEqual(c.choose(ps, rs)['name'], 'counter1-drop1')
        self.assertTrue(set(w['seed'] for w in c.worlds()).isdisjoint(w['seed'] for w in c.worlds(True)))


if __name__ == '__main__':
    unittest.main()
