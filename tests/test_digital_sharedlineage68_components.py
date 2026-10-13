"""Prepared component regressions only; not full24-case software admission."""
import ast,hashlib,inspect,json,unittest
from pathlib import Path
from unittest.mock import patch
from experiments import digital_sharedlineage68_population as p
from experiments import digital_sharedlineage68_interpret as referee
from experiments import evidence_write_grant68 as grant
ROOT=Path(__file__).resolve().parents[1]

class PreparedComponents(unittest.TestCase):
    def setUp(self):
        self.trap=patch.object(p.World,'__init__',side_effect=AssertionError('No World in prepared component tests'))
        self.spy=self.trap.start();self.addCleanup(self.trap.stop)
        self.addCleanup(lambda:self.assertEqual(self.spy.call_count,0))

    def test_mode_domain(self):
        for mode,inheritance in [('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy')]:
            p.validate_copy_configuration(1,mode,inheritance)
        for values in [(True,'faithful','parent_copy'),(-1,'faithful','parent_copy'),(1,'copy_disabled','parent_copy'),(1,'faithful','ancestor_copy'),(1,'mutating','unknown')]:
            with self.assertRaises(AssertionError):p.validate_copy_configuration(*values)

    def test_word_domain(self):
        for field,bad in [(1,True),(1,-1),(2,True),(2,-1),(2,32),(3,True),(3,-1),(3,27)]:
            values=[1,0,3,0,'mutating','parent_copy'];values[field]=bad
            with self.assertRaises(AssertionError):p.copy_result(*values)

    def test_parent_effective_source(self):
        for index in range(27):
            actual=(p.ANCESTOR_WORDS[index]+7)%32
            effective,draw,value=p.copy_result(1,index,actual,index,'faithful','parent_copy')
            self.assertEqual((effective,value),(actual,actual))

    def test_reset_effective_source(self):
        for index in range(27):
            actual=(p.ANCESTOR_WORDS[index]+7)%32
            effective,draw,value=p.copy_result(2,index,actual,index,'mutating','ancestor_copy')
            self.assertEqual(effective,referee.ANCESTOR_WORDS[index])
            self.assertNotEqual(effective,actual)

    def test_draw_and_value(self):
        seen=set()
        for seed in (1,2):
            for identity in range(256):
                index=identity%27;actual=(identity+9)%32
                expected_draw=int(hashlib.sha256(json.dumps([seed,'mutation',identity],sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16],16)
                for mode,source in [('faithful','parent_copy'),('mutating','parent_copy'),('mutating','ancestor_copy')]:
                    effective=actual if source=='parent_copy' else referee.ANCESTOR_WORDS[index]
                    expected=((effective+1+(expected_draw//100)%31)%32 if mode=='mutating' and expected_draw%100<8 else effective)
                    self.assertEqual(p.copy_result(seed,identity,actual,index,mode,source),(effective,expected_draw,expected))
                    if mode=='mutating':seen.add(expected!=effective)
        self.assertEqual(seen,{False,True})

    def test_cold_startup_units(self):
        code=[[v,i] for i,v in enumerate(referee.ANCESTOR_WORDS)];units=list(range(27,43))
        for pos in range(4):
            actual=p.World.body(8,3,2,code,units,pos)
            self.assertEqual(actual,referee.body(8,3,2,code,units,pos))
            self.assertEqual(actual['energy'],12);self.assertEqual(actual['memory'],[0]*8)
            self.assertEqual((actual['pc'],actual['cue'],actual['feedback'],actual['inbox'],actual['nursery']),(0,0,0,None,[]))

    def test_unchanged_vm_ast(self):
        def method(text,name):
            tree=ast.parse(text)
            return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name)
        old=(ROOT/'experiments/digital_renewable64.py').read_text(encoding='utf-8')
        new=(ROOT/'experiments/digital_sharedlineage68_population.py').read_text(encoding='utf-8')
        new=new.replace("source=e['code'][index]\n                    effective,draw,value=copy_result(self.seed,self.writes,source[0],index,self.mode,self.inheritance_mode)","source=e['code'][index];value=source[0];draw=int(h([self.seed,'mutation',self.writes])[:16],16)\n                    if self.mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%31)%32")
        new=new.replace('effective_source=self.inheritance_mode,effective_source_value=effective,mutation_draw=draw,','').replace('mutated=value!=effective','mutated=value!=source[0]')
        for name in ('step','input','check','body','run','snapshot'):
            self.assertEqual(ast.dump(method(old,name)),ast.dump(method(new,name)),name)
        ref=(ROOT/'experiments/digital_sharedlineage68_interpret.py').read_text(encoding='utf-8')
        self.assertNotIn('digital_sharedlineage68_population',ref)
        self.assertNotIn('from experiments',ref)
        oldref=(ROOT/'experiments/digital_renewable64_interpret.py').read_text(encoding='utf-8')
        ref=ref.replace("'genesis_program','inheritance_mode','checkpoint'","'genesis_program','checkpoint'")
        ref=ref.replace("'DIGITAL-SHARED-LINEAGE-68-v1'","'DIGITAL-RENEWABLE-ECOLOGY-64-v1'")
        ref=ref.replace("    inheritance_mode=row['inheritance_mode'];assert inheritance_mode in ('parent_copy','ancestor_copy')\n    assert inheritance_mode=='parent_copy' or row['mode']=='mutating'\n    assert row['route']=='ancestor'\n",'')
        ref=ref.replace("fuel_mode=row['fuel_mode'];assert fuel_mode=='renewed'","fuel_mode=row['fuel_mode'];assert fuel_mode in ('renewed','no_inflow')")
        ref=ref.replace('    assert sum(program,[])==ANCESTOR_WORDS\n','').replace("mode in ('mutating','faithful')","mode in ('mutating','faithful','copy_disabled')")
        ref=ref.replace('inheritance_mode=inheritance_mode,','')
        ref=ref.replace("source=e['code'][index]\n                    effective=source[0] if inheritance_mode=='parent_copy' else ANCESTOR_WORDS[index]\n                    draw=int(h([seed,'mutation',writes])[:16],16);value=effective\n                    if mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%31)%32", "source=e['code'][index];value=source[0];draw=int(h([seed,'mutation',writes])[:16],16)\n                    if mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%31)%32")
        ref=ref.replace('effective_source=inheritance_mode,effective_source_value=effective,mutation_draw=draw,','').replace('mutated=value!=effective','mutated=value!=source[0]').replace('mutations+=int(value!=effective)','mutations+=int(value!=source[0])')
        self.assertEqual(ast.dump(method(oldref,'audit')),ast.dump(method(ref,'audit')))

    def test_grant_prewrite_domain_refusals(self):
        class NoFiles:
            def create(self,*args,**kwargs):raise AssertionError('Invalid grant mutated filesystem')
        for cap in (0,-1,True,64*1024**2+1):
            with self.assertRaises(ValueError):grant.seal(NoFiles(),'raw','x',cap,'a'*64,'b'*64,'fixture')
        base=dict(version='sharedlineage68-file-grant-candidate-v1',root='unused',phase='raw',name='x',limit=64,source_sha='a'*64,config_sha='b'*64,role='fixture',device=0,inode=0)
        for key,value in [('limit',True),('phase','../raw'),('name','../x'),('source_sha','c'*64),('config_sha','d'*64),('role','other')]:
            item=dict(base);item[key]=value
            with self.assertRaises(ValueError):grant.record(item,grant.digest(item),'a'*64,'b'*64,'fixture',{})

if __name__=='__main__':unittest.main()
