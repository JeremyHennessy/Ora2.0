"""Supplied30-triple blank learner; no target/context/task/World access."""
CAPACITIES=(2,4,8)
ENTRIES=(1,3)
BOUNDARIES=((28,3),(29,1))

def programme(q,entry):
 if type(q) is not int or q not in CAPACITIES or type(entry) is not int or entry not in ENTRIES:raise ValueError('neutral descriptor')
 return [[7,q,entry],
 [0,1,0],[7,0,5],[0,1,0],[24,1,8],
 [0,0,0],[22,0,1],[6,0,0],[0,0,0],[1,0,0],
 [24,0,2],[8,0,28],[24,0,2],[8,0,20],
 [22,0,1],[8,0,17],[7,0,28],[4,0,2],[23,1,0],[7,0,28],
 [22,0,1],[8,0,26],[21,0,0],[24,1,8],[23,1,0],[7,0,28],
 [4,0,1],[23,1,0],[25,7,3],[7,0,1]]

def completed_boundary(dispatch_pc,next_pc):
 if type(dispatch_pc) is not int or type(next_pc) is not int or (dispatch_pc,next_pc) not in BOUNDARIES:raise ValueError('full paid branch required')
 return next_pc
