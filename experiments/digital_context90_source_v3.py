"""Same supplied learner, compact typed completion layout; no task admission."""
CAPACITIES=(2,4,8)
ENTRIES=(27,1)
BOUNDARIES=((26,27),(26,1))

def programme(q,entry):
 if type(q) is not int or q not in CAPACITIES or type(entry) is not int or entry not in ENTRIES:raise ValueError('neutral descriptor')
 return [[7,q,entry],
 [0,1,0],[24,1,8],
 [0,0,0],[22,0,1],[6,0,0],[0,0,0],[1,0,0],
 [24,0,2],[8,0,26],[24,0,2],[8,0,18],
 [22,0,1],[8,0,15],[7,0,26],[4,0,2],[23,1,0],[7,0,26],
 [22,0,1],[8,0,24],[21,0,0],[24,1,8],[23,1,0],[7,0,26],
 [4,0,1],[23,1,0],[25,7,1],[0,1,0],[7,0,3]]

def completed_boundary(dispatch_pc,next_pc):
 if type(dispatch_pc) is not int or type(next_pc) is not int or (dispatch_pc,next_pc) not in BOUNDARIES:raise ValueError('full paid branch required')
 return next_pc
