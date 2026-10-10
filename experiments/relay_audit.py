"""Independent transaction and potential ledger; never imports producer."""
import itertools,json

def audit():
    rows=[]
    for fuel in range(5):
      for price in (1,2,3):
       for upkeep in (0,1,2):
        for joining in (0,1,2,3):
         for lost in ('U','V'):
          result={'n':fuel,'c':price,'m':upkeep,'b':joining,'damage':lost,'opportunity':fuel>=2,'joined_repair_fundable':fuel>=1 and price+joining<=6}
          for name,linked in (('independent',False),('joined',True)):
            # Oracle certificate: primitive fabrication and optional joining are
            # paid from finite matched startup assistance; no installed founders.
            start=2*price+joining;work=start;raw=3;active=0;waste=0;cost=0
            for _ in range(2):work-=price;cost+=price;raw-=1;active+=1
            if linked:work-=joining;cost+=joining
            assert work>=0
            capture=0;spent=0;after_loss=None;feasible=True
            for unit in range(fuel):
                # F potential6 -> I potential4 + work2 -> Z0 + work4.
                environment=6*(fuel-unit);before=work+environment
                work+=2;intermediate=4;environment-=6
                assert work+environment+intermediate==before
                work+=4;intermediate=0;assert work+environment==before
                capture+=6;spent+=1
                if unit==0:
                    active-=1;waste+=1;after_loss=work
                    required=price+(joining if linked else 0)
                    if work<required:feasible=False
                    # Negative balances here denote an unfundable *bound*, not
                    # an executable trajectory. No certificate is claimed.
                    work-=price;cost+=price;raw-=1;active+=1
                    if linked:work-=joining;cost+=joining
            if fuel==0:
                # Conditional endpoint ceiling charges required replacement;
                # actual reconstruction is underexposed and cannot pass.
                work-=price;cost+=price
                if linked:work-=joining;cost+=joining
                after_loss=start-2*price-(joining if linked else 0)+6
            work-=2*upkeep;cost+=2*upkeep
            result[name+'_whole']=work-start
            result[name+'_post']=work-after_loss
            assert result[name+'_whole']==capture-cost
            if fuel>0:assert raw+active+waste==3 and active==2
            if fuel>=2 and feasible and work>=0 and result[name+'_whole']>0 and result[name+'_post']>0:
                assert spent>=2 and raw==0 and waste==1
          assert result['joined_whole']<=result['independent_whole'] and result['joined_post']<=result['independent_post']
          rows.append(result)
    return rows

if __name__=='__main__':print(json.dumps(audit(),sort_keys=True))
