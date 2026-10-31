"""Small simulated source-update test. No model inference or network."""
from pathlib import Path
import importlib.util,json,hashlib,tempfile,sys,types

SCRIPT=Path(__file__).resolve().with_name('author_evidence_semantic.py')
HERE=Path(__file__).resolve().parent

def case(label,mutation_stage=None,availability_failure=False,index_mismatch=False,versions_mismatch=False):
 spec=importlib.util.spec_from_file_location('semantic_source_guard_'+label,SCRIPT)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 with tempfile.TemporaryDirectory(prefix='source-guard-') as directory:
  root=Path(directory);(root/'research').mkdir();(root/'assets').mkdir()
  paths=[root/'research/questions.json',root/'assets/evidence-search.json']
  for file in paths:file.write_text('{"generation":1}\n',encoding='utf-8')
  output=root/'result.json';calls=[]
  def update():
   # A coherent two-file generation upgrade must also fail mid-run.
   for file in paths:file.write_text('{"generation":2}\n',encoding='utf-8')
  def versions():
   result={'datasets':{}}
   for key,relative in module.SOURCE_PATHS.items():
    text=(root/relative).read_text(encoding='utf-8-sig').replace('\r\n','\n')
    result['datasets'][key]={'sha256_lf':hashlib.sha256(text.encode()).hexdigest()}
   if versions_mismatch:result['datasets']['questions']['sha256_lf']='0'*64
   return result
  def client(root,queries=None,ids=None):
   calls.append('client_initial' if len(calls)==0 else 'client_later')
   if mutation_stage=='initial':update()
   return {'source_versions':versions(),'packets':{},'rows':[]}
  class Index:
   def __init__(self,*args):
    captured=hashlib.sha256(paths[0].read_bytes()).hexdigest()
    self.index=types.SimpleNamespace(corpus_hash='0'*64 if index_mismatch else captured)
    if mutation_stage=='index':update()
    if mutation_stage=='availability':
     update();raise FileNotFoundError('Simulated model availability failure after source upgrade')
  def ranking(index,queries):
   if mutation_stage=='ranking':update()
   return {'rows':[{'id':q['id'],'ranked':[]} for q in queries]}
  module.original_client=client;module.ExploreIndex=Index;module.explore_candidates=ranking
  module.DEPENDENCY_ERROR='simulated optional dependency missing' if availability_failure else None
  argv=sys.argv
  sys.argv=[str(SCRIPT),'test query','--root',str(root),'--mode','explore','--on-unavailable','lexical','--output',str(output)]
  caught=None
  try:module.main()
  except module.SourceChangedError as exc:caught=str(exc)
  finally:sys.argv=argv
  expected_failure=bool(mutation_stage or index_mismatch or versions_mismatch)
  assert bool(caught)==expected_failure,(label,caught)
  assert output.exists()!=expected_failure,(label,'output policy')
  if mutation_stage=='availability':assert len(calls)==1,'Changed source must stop before invoking lexical fallback'
  if not expected_failure:
   result=json.loads(output.read_text(encoding='utf-8'))
   assert result['source_snapshot_verified'] is True
   assert result['semantic_executed'] is (not availability_failure)
  return {'case':label,'passed':True,'source_change_failed':bool(caught),'no_result_written_on_failure':not output.exists() if expected_failure else None,'node_bridge_calls':len(calls),'detail':caught}

cases=[case('stable_semantic'),case('stable_explicit_fallback',availability_failure=True),
       case('coherent_update_during_initial_validation','initial'),
       case('coherent_update_during_index_build','index'),
       case('coherent_update_between_ranking_and_packet_fetch','ranking'),
       case('changed_source_never_lexical_fallback','availability'),
       case('index_hash_mismatch',index_mismatch=True),case('client_version_mismatch',versions_mismatch=True)]
result={'status':'PASS','script_sha256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),'cases':cases,'passed':len(cases),'model_inference_calls':0,'network_calls':0,'scientific_source_modified':False}
print(json.dumps(result,ensure_ascii=False))
