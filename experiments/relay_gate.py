"""Symbolic-accounting diagnostic; no autonomous dynamics or physical calibration."""
import itertools,json

def calculate():
    records=[]
    for n,c,m,b,damage in itertools.product(range(5),range(1,4),range(3),range(4),('U','V')):
        independent=6*n-3*c-2*m
        records.append(dict(n=n,c=c,m=m,b=b,damage=damage,independent_whole=independent,
            joined_whole=independent-2*b,independent_post=6*(n-1)-c-2*m,
            joined_post=6*(n-1)-c-2*m-b,opportunity=n>=2,
            joined_repair_fundable=n>=1 and c+b<=6))
    return records

if __name__=='__main__':print(json.dumps(calculate(),sort_keys=True))
