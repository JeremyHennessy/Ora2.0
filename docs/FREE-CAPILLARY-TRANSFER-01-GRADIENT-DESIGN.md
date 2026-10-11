# Free-body capillary dependency: conservative gradient only

2026-10-11. Prospective design registration before local helper execution.
No trajectory, repair sample, converter or controller is admitted by this file.

The primary question remains the [candidate card](FREE-CAPILLARY-TRANSFER-01-DECISION-CARD.md).
A reduced, declared one-dimensional free-energy functional makes both material
and solid coordinates explicit. Differentiate the entire functional: solid
forces require material recoil, including composition-gradient forces. Holding
the material sites fixed would introduce unaccounted reaction support. No fixed
wall or grid is an allowed source of free momentum in a later converter.

F = sum a*c_i^2*(1-c_i)^2 + sum kappa*(c_j-c_i)^2/(2*(s_j-s_i)^2)
  + sum exp(-((s_i-X_b)/radius)^2)*(lambda_A*c_i^2+lambda_B*(1-c_i)^2).
Adjacent material sites form the gradient terms; every solid/site pair wets.
Illustrative dimensionless coefficients a=1/12,kappa=.4,lambda_A=.5,
lambda_B=2.4,radius1 are definitions of this reduced helper, not measured prices,
calibrated chemistry, the full published functional or a successful policy.
Inputs keep material identity/order and composition; invalid states are refused,
never clipped or silently normalized. There is no transport/diffusion executor.

Register three algebra states: sites(-2,0,2),composition(.2,.6,.3),solids(-.7,.9);
sites(-3,-.3,2),composition(.4,.2,.7),solid(.5);
sites(-2,1,4),composition(.1,.8,.5),solids(-.5,2.7).
For every coordinate/composition, independently evaluate central free-energy
differences at1e-6. Require analytic force/derivative agreement1e-7 and total
reaction1e-12. Six focused tests include translation symmetry and invalid-state
refusal. Pin source before execution; existing operator lock;256MiB/60CPU/
90wall seconds/four processes/1MiB stdout;8MiB evidence/5GiB disk floor;
preserve exits, failure, raw source, seals, archive and exact restored replay.
Independent scalar functional evaluation imports no helper. These are algebra
verification states, not seeds, natural worlds or physical reproduction.

**First remaining complete-law dependency.** This helper computes F derivatives,
not internal energy U or useful work. The isothermal literature functional does
not supply our finite thermal state, entropy S or U=F+T*S. A future dynamics must
meter temperature-dependent material/free energy, finite internal stores, fluid
momenta, diffusion, viscous/thermal waste, load release and raw bridge formation
and renewal. Treating a fall in F as retained load work or deleting fluid recoil
would fabricate conversion. Physical prices, internal energy and net work remain
null. No surface, moving load or all-role repair transition has been measured.

Require a source-specified finite thermodynamic/dynamic closure and an actual
whole/fresh profitable simpler route before a bounded complete prototype.
The helper resolves only a conservative derivative dependency; it grants no
Stage3 credit. No fresh world, supplied-boundary simulation, controller, API,
legacy AgentTest edit or retuning of closed histories.
