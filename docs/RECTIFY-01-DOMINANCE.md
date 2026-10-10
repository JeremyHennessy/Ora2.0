# RECTIFY-01 — analytic post-damage stop decision

Read-only follow-up to the frozen negative panel; no new law, costs, seeds,
horizons, simulation, acceptance criteria or positive capability.

Let `d` be the declared forward drop, `m` upkeep per live diode/store per slot,
and `p=c+2*b` the replacement price. For the existing two-polarity cycle, the
intact bridge produces `(9-6*d)/2` usable work and costs `10*m` upkeep.
Two independent converters produce `(9-3*d)/2` and cost `8*m`. Their intact
cycle surplus advantage is therefore `3*d/2+2*m`.

If damage hits one of the two independent live sites, both arms pay `p`.
The damaged-cycle advantage is `3*d/4+2*m`; adding the registered two restored
cycles gives the exact post-damage advantage:

`post_independent2 - post_bridge = 15*d/4 + 6*m`.

If damage hits bridge site 2 or 3, that site was unused by the independent pair.
The independent arm loses no component and pays no replacement. Damaged-cycle
work differs by `9/4`, upkeep ties, and the complete post-damage advantage is:

`post_independent2 - post_bridge = 3*d + 4*m + 9/4 + c + 2*b`.

These identities require both arms to fund and complete the registered schedule
with the original geometry, resistance, loads and storage limits. They do not
assert fundability for arbitrary parameter changes. For nonnegative prices,
drop and upkeep, the bridge cannot obtain a strictly positive post advantage;
the common-site expression ties only when both drop and upkeep vanish. The
registered positive values make both expressions strictly positive. Startup
duration and store capital overhead do not occur in this post endpoint.

A separately authored rational-arithmetic checker, importing neither producer
nor original auditor, verifies these identities against all **384** preserved
bridge/two-converter pairs. Minimum advantage is **9/8** usable-work units. The
earlier **381** denominator concerned cases funding *all four* arms; these are
different denominators, with no failed control discarded.

Evidence: `D:/OraLab/runs/budget-snapshot01-dominance-20261010`, pinned source
`c9523ecec89b702dc0cba8ac00081313c620cd0b`; preserved producer rows SHA-256
`13d8985a0a434c734891504a5f73fd400e2cc9ecc556aa7c785f4b4d7da0a9e4`.
Raw checker, bounded process exit, source archive, seal and restored archive
are retained. This is a stop decision for this law, not a universal statement
about directional conversion or autonomous self-maintenance.

The next candidate must change a causal interaction that improves usable work
or paid repair, and compare against the attainable independent implementation
of that same opportunity. Rearranging prices or extending this bridge panel
cannot satisfy its registered post-damage gate. Unknown realization costs remain
unknown; no natural-world sampling is admitted by this analysis.
