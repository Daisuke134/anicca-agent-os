import copy, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
root=Path('/home/hatch/workspace/tools')
results=[]
for name,script,total in [('receptivity-check','receptivity_check.py',8),('onboarding-adaptation-check','onboarding_adaptation_check.py',6)]:
 d=root/name
 spec=importlib.util.spec_from_file_location('checker',d/script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 good=json.loads((d/'fixtures/compliant.json').read_text())
 assert all(m.check(good).values())
 assert not any(m.check({}).values())
 # Removing any populated required leaf from the active compliant branches must fail a gate.
 def leaves(v,path=()):
  if isinstance(v,dict):
   for k,x in v.items():
    if not k.startswith('_'):yield from leaves(x,path+(k,))
  elif isinstance(v,list):
   for i,x in enumerate(v):yield from leaves(x,path+(i,))
  else:yield path
 checks=2
 for path in leaves(good):
  # Individual horizon values may be removed while retaining multiple horizons.
  if 'horizons_minutes' in path or 'first_run_signals' in path or 'assignments' in path:continue
  state=copy.deepcopy(good);parent=state
  for k in path[:-1]:parent=parent[k]
  del parent[path[-1]]
  assert not all(m.check(state).values()),path
  checks+=1
 if total==8:
  for key in ['period','individual_threshold_method','exclusion_rules','refractory_period']:
   s=copy.deepcopy(good);s['calibration'][key]=' ';assert not m.check(s)['TR-1'];checks+=1
  s=copy.deepcopy(good);s['transfer']={'used':False};assert m.check(s)['CG-0'] and m.check(s)['CG-1'];checks+=1
  s=copy.deepcopy(good);s['self_trigger']={'present':False};assert m.check(s)['TR-5'];checks+=1
  s=copy.deepcopy(good);s['receptivity'].update(form='multi_horizon',cross_horizon_stability='Synthetic stability evaluation');assert m.check(s)['TR-3'];checks+=1
  s=copy.deepcopy(good);s['transfer']['transfer_measured']=False;assert not m.check(s)['CG-1'];checks+=1
  s=copy.deepcopy(good);s['rates']['usable_decision_fraction']=True;assert not m.check(s)['TR-2'];checks+=1
 else:
  for tier,source in [('low','self'),('high','algorithm')]:
   s=copy.deepcopy(good);s['routing']['assignments'][tier]=[source]
   for row in s['goals']['users']:
    if row['tier']==tier:row['source']=source
   assert not m.check(s)['OG-2'];checks+=1
  s=copy.deepcopy(good);s['adaptation']={'used':False};assert m.check(s)['OG-4'];checks+=1
  s=copy.deepcopy(good);s['evaluation']={'effects_present':False,'effects':[]};assert m.check(s)['OG-5'];checks+=1
  s=copy.deepcopy(good);s['algorithm']={'used':False};assert not m.check(s)['OG-3'];checks+=1
  for sources in s['routing']['assignments'].values():
   if 'algorithm' in sources:sources.remove('algorithm')
  s['goals']['users'][0]['source']='default-unchanged';assert m.check(s)['OG-3'];checks+=1
 for fixture in sorted((d/'fixtures').glob('*.json')):
  p=subprocess.run([sys.executable,str(d/script),str(fixture)],capture_output=True,text=True)
  output=json.loads(p.stdout);assert output['total']==total
  expected_fail=0 if fixture.stem=='compliant' else (5 if fixture.stem=='control' else total)
  assert output['failed']==expected_fail and p.returncode==(1 if expected_fail else 0),(fixture,output)
  again=subprocess.run([sys.executable,str(d/script),str(fixture)],capture_output=True,text=True)
  assert (again.returncode,again.stdout)==(p.returncode,p.stdout)
  results.append({'checker':name,'fixture':fixture.name,'command':[sys.executable,str(d/script),str(fixture)],'exit_code':p.returncode,'output':output})
 with tempfile.TemporaryDirectory() as tmp:
  f=Path(tmp)/'bad.json'
  for data in ['{','[]','{"x":1,"x":2}','{"x":NaN}']:
   f.write_text(data);p=subprocess.run([sys.executable,str(d/script),str(f)],capture_output=True,text=True)
   assert p.returncode==2 and json.loads(p.stdout)['result']=='ERROR';checks+=1
  # Valid JSON with wrong field types must fail closed without crashing.
  for value in [None,[],{},True,0,'',10**400]:
   f.write_text(json.dumps({k:value for k in good if not k.startswith('_')}))
   p=subprocess.run([sys.executable,str(d/script),str(f)],capture_output=True,text=True)
   assert p.returncode==1 and json.loads(p.stdout)['failed']==total;checks+=1
 (d/'run-results-2026-11-18.json').write_text(json.dumps({'runs':[r for r in results if r['checker']==name],'additional_assertions_passed':checks},indent=2)+'\n')
 print(name, 'additional assertions passed:',checks)
(root/'paper-loop-jitai2-onboarding2-run-results-2026-11-18.json').write_text(json.dumps(results,indent=2)+'\n')
for r in results:print(r['checker'],r['fixture'],r['exit_code'],r['output']['result'],r['output']['passed'],r['output']['failed'],','.join(r['output']['failed_gates']))
