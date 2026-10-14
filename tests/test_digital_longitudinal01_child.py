"""Prospective role/config admission before source import or organism calls."""
import copy
import contextlib
import hashlib
import io
import json
import unittest
from unittest.mock import patch
from experiments import digital_longitudinal01_child as child
from experiments import digital_pressure71_scientific_child as boundary

class Admission(unittest.TestCase):
    def request(self,endpoint='raw'):
        r=dict(configuration=copy.deepcopy(child.CONFIG),seed=3,endpoint=endpoint,export='original',
            role=f'original:3:{endpoint}',source_files={n:'0'*64 for n in child.NEW_FILES},
            source_sha256='0'*64,configuration_sha256=hashlib.sha256(boundary.canonical(child.CONFIG)).hexdigest(),
            grant={},grant_seal='0'*64)
        if endpoint=='proof':r['input']={}
        return r
    def test_only_registered_roles(self):
        for endpoint in ('raw','proof'):self.assertEqual(child.validate_request(self.request(endpoint)),endpoint)
        for key,value in [('seed',1),('seed',True),('role','restored:3:raw'),('endpoint','fork')]:
            r=self.request();r[key]=value
            with self.assertRaises(AssertionError):child.validate_request(r)
    def test_configuration_and_exact_request_schema(self):
        for key,value in [('horizon',4096),('mode','mutating'),('dose',1),('dose',8.0),('software_only',False),('software_only',1)]:
            r=self.request();r['configuration'][key]=value
            with self.assertRaises(AssertionError):child.validate_request(r)
        r=self.request();r['input']={}
        with self.assertRaises(AssertionError):child.validate_request(r)
    def test_ordinary_failure_retains_attempt_counters(self):
        from experiments import digital_longitudinal01_population as candidate
        output=io.StringIO();request=self.request()
        with patch.object(child.sys,'argv',['child','prepared']),patch.object(boundary,'bounded_bytes',return_value=boundary.canonical(request)),\
             patch.object(boundary,'verify_source',return_value='0'*64),patch.object(boundary,'validate_grant'),\
             patch.object(boundary,'module_origins'),patch.object(candidate,'history',side_effect=AssertionError('prepared failure')),\
             contextlib.redirect_stdout(output):
            with self.assertRaises(AssertionError):child.main()
        failure=json.loads(output.getvalue())
        self.assertTrue(failure['engineering_failure'])
        self.assertEqual((failure['world_constructors'],failure['step_calls']),(0,0))
        self.assertTrue(failure['partial_state_unavailable'])
        r=self.request();r['source_files'].pop(next(iter(child.NEW_FILES)))
        with self.assertRaises(AssertionError):child.validate_request(r)

if __name__=='__main__':unittest.main()
