"""Design-only reduced free-energy derivative. No dynamics, heat bath or actor.

F is a declared dimensionless functional, NOT calibrated internal energy U,
delivered work, a reproduction of DIFA or a complete capillary converter.
Material sample coordinates participate in the derivative: they are not anchors.
"""
import math


def evaluate(samples, composition, solids, *, a=1/12, kappa=.4,
             lambda_a=.5, lambda_b=2.4, radius=1.):
    """Return F, chemical derivatives and reciprocal coordinate forces.

    Reduced law: sum a*c^2*(1-c)^2; adjacent composition gradient
    kappa*(c[j]-c[i])^2/(2*(s[j]-s[i])^2); each material/solid pair
    exp(-((s-X)/radius)^2)*(lambda_a*c^2+lambda_b*(1-c)^2).
    No wall, displacement, diffusion, cost price or trajectory is supplied.
    """
    values=(*samples,*composition,*solids,a,kappa,lambda_a,lambda_b,radius)
    if not values or any(not math.isfinite(x) for x in values):
        raise ValueError('Finite inputs required')
    if len(samples)!=len(composition) or len(samples)<2:
        raise ValueError('Identified matching material samples required')
    if radius<=0 or min(a,kappa,lambda_a,lambda_b)<0:
        raise ValueError('Nonnegative coefficients and positive radius required')
    if any(not 0<=c<=1 for c in composition):
        raise ValueError('No clipping of material composition')
    if any(y<=x for x,y in zip(samples,samples[1:])):
        raise ValueError('Distinct increasing material coordinates required')
    energy=0.; fluid=[0.]*len(samples);solid=[0.]*len(solids);mu=[0.]*len(samples)
    for i,c in enumerate(composition):
        energy+=a*c*c*(1-c)**2
        mu[i]+=2*a*c*(1-c)*(1-2*c)
    for i in range(len(samples)-1):
        d=samples[i+1]-samples[i];delta=composition[i+1]-composition[i]
        energy+=kappa*delta*delta/(2*d*d)
        force=kappa*delta*delta/(d*d*d)
        fluid[i]-=force;fluid[i+1]+=force
        mu[i]-=kappa*delta/(d*d);mu[i+1]+=kappa*delta/(d*d)
    for i,(s,c) in enumerate(zip(samples,composition)):
        weight=lambda_a*c*c+lambda_b*(1-c)**2
        for j,x in enumerate(solids):
            d=s-x;shape=math.exp(-(d/radius)**2)
            energy+=shape*weight
            force=2*d*shape*weight/(radius*radius)
            fluid[i]+=force;solid[j]-=force
            mu[i]+=shape*(2*lambda_a*c-2*lambda_b*(1-c))
    return dict(free_energy=energy,material_force=fluid,solid_force=solid,
                chemical_derivative=mu,internal_energy=None,net_work=None,
                physical_cost=None,dynamics_executed=False,admitted=False)
