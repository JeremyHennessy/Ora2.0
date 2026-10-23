"""New software wire regression; no old readiness role, World or guardian rerun."""
import io,json,os,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import digital_pilot74_entrypoint_v2 as entry
from experiments import digital_pilot74_publication_reader_v2 as physical
class Lines(unittest.TestCase):
 def streams(self):
  a,b=io.BytesIO(),io.BytesIO();return a,b,io.TextIOWrapper(a,encoding='ascii',newline='\r\n'),io.TextIOWrapper(b,encoding='ascii',newline='\r\n')
 def test_observed_crlf_control_is_refused_by_unchanged_parser(self):
  raw=physical.encode(dict(worlds=0,vm_steps=0))+b'\r\n'
  with self.assertRaises(AssertionError):physical.parse_host(raw[:-1],65536)
 def test_stdout_and_stderr_emit_one_exact_lf(self):
  a,b,out,err=self.streams()
  try:
   with patch.object(entry.sys,'stdout',out),patch.object(entry.sys,'stderr',err):
    entry.canonical_output_lines();print('{"ok":true}');print('{"failed":true}',file=err);out.flush();err.flush()
   self.assertEqual(a.getvalue(),b'{"ok":true}\n');self.assertEqual(b.getvalue(),b'{"failed":true}\n')
  finally:out.detach();err.detach()
 def test_strict_canonical_parser_accepts_corrected_emission(self):
  a,b,out,err=self.streams();value=dict(worlds=0,vm_steps=0)
  try:
   with patch.object(entry.sys,'stdout',out),patch.object(entry.sys,'stderr',err):
    entry.canonical_output_lines();print(physical.encode(value).decode('ascii'));out.flush()
   self.assertEqual(physical.parse_host(a.getvalue()[:-1],65536),value)
  finally:out.detach();err.detach()
 def test_real_subprocess_emits_exact_lf_without_role_execution(self):
  code="from experiments.digital_pilot74_entrypoint_v2 import canonical_output_lines; canonical_output_lines(); print('{\"fixture\":true}')"
  p=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
  self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stdout,b'{"fixture":true}\n')
 def test_authorized_targets_unchanged(self):
  self.assertEqual(entry.TARGETS,{'digital_pilot74_child','digital_pilot74_source_ready_v2','digital_pilot74_journal_observed_child_v2','digital_pilot74_closed_audit_child_v2'})
if __name__=='__main__':unittest.main()
