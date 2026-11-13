#!/usr/bin/env python3
"""Rebuild private paper status from workflow/intake records; never publish or upload."""
from __future__ import annotations
import argparse, contextlib, csv, io, json, os, re, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from runtime_paths import resolve_data_root
from history_manager import normalize_doi

COLUMNS = ['文献名（简称）','阅读周','Zotero 情况','本地情况','Git 情况','GitHub 上传情况','网页发布']
PLATFORMS = ['zotero','local','git','github','web']
STATES = {'VERIFIED','PRESENT_UNVERIFIED','PENDING','MISSING','CONFLICT','UNKNOWN','NOT_APPLICABLE'}
def now(): return datetime.now(timezone.utc).isoformat()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False) as f:
        f.write(text); tmp=Path(f.name)
    os.replace(tmp,path)
def save(path, value): atomic(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
@contextlib.contextmanager
def locked(root):
    path=root/'knowledge'/'paper_status.lock'; path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as f:
        f.seek(0); f.write(b'0'); f.flush(); f.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(f,fcntl.LOCK_EX)
        try: yield
        finally:
            f.seek(0)
            if os.name=='nt': msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(f,fcntl.LOCK_UN)
def observation(state, detail, source, **extra):
    if state not in STATES: raise ValueError(state)
    return dict(status=state,detail=detail,source=source,checked_at=now(),**extra)
def record_observation(record, platform, value):
    old=record.setdefault('platform_status',{}).get(platform)
    if old and value['status']=='UNKNOWN':
        value['last_observation']=old.get('last_observation',old)
    record['platform_status'][platform]=value

def records(root):
    paths=list((root/'weekly_reviews').glob('*/*/workflow_manifest.yaml'))
    paths+=list((root/'knowledge/intake').glob('*/paper_status.json'))
    result=[]
    for path in sorted(paths):
        doc=load(path)  # repository manifests use JSON-compatible YAML
        if doc.get('paper_id') or doc.get('baseline_id'): result.append((path,doc))
    return result

def group_records(items):
    groups={}
    doi_ids={normalize_doi(d['doi']):d['paper_id'] for _,d in items if d.get('doi') and d.get('paper_id')}
    for path,d in items:
        identity=doi_ids.get(normalize_doi(d.get('doi',''))) or d.get('paper_id') or d['baseline_id']
        groups.setdefault(identity,[]).append((path,d))
    return groups

def select_current(items):
    marked=[p for p in items if p[1].get('status_current') is True]
    weekly=[p for p in items if p[0].name=='workflow_manifest.yaml' and p[1].get('week')]
    if len(marked)==1: return marked[0],False
    if len(weekly)==1: return weekly[0],False
    if len(weekly)>1: return weekly[-1],True
    return items[-1],False

def rebuild(root):
    rows=[]; pending=[]
    for identity,items in group_records(records(root)).items():
        (_,doc),ambiguous=select_current(items)
        base=next((d for _,d in items if d.get('historical_snapshot')),doc)
        baseline=base.get('historical_snapshot',{})
        week=doc.get('week') or base.get('week') or baseline.get(COLUMNS[1]) or '未正式归周'
        if re.fullmatch('W[0-9]{2}',week): week+='（年份待核）'
        if ambiguous: week='、'.join(sorted({d['week'] for _,d in items if d.get('week')}))+'（多个周次待核对）'
        row=[base.get('short_title') or doc.get('title') or identity,week]
        for platform,col in zip(PLATFORMS,COLUMNS[2:]):
            ev=doc.get('platform_status',{}).get(platform) or base.get('platform_status',{}).get(platform)
            if ev:
                display=ev['detail']
                if ev['status']=='UNKNOWN' and ev.get('last_observation'):
                    last=ev['last_observation']; display+=f"；上次 {last['checked_at']}：{last['detail']}"
                if ev['status'] not in {'VERIFIED','NOT_APPLICABLE'}: pending.append(f'{row[0]} / {col}：{display}')
            else:
                display='待核验'
                if baseline.get(col): display+='；历史：'+baseline[col]
                pending.append(f'{row[0]} / {col}：{display}')
            row.append(display)
        rows.append(row)
    rows.sort(key=lambda r:(r[1],r[0]))
    buf=io.StringIO(newline=''); writer=csv.writer(buf); writer.writerow(COLUMNS); writer.writerows(rows)
    atomic(root/'knowledge/paper_status_overview.csv',buf.getvalue())
    escape=lambda s: str(s).replace('|','\\|').replace('\n',' ')
    text='| '+' | '.join(COLUMNS)+' |\n| '+' | '.join(['---']*7)+' |\n'
    text+=''.join('| '+' | '.join(map(escape,r))+' |\n' for r in rows)
    text+='\n待处理\n\n'+''.join('- '+p+'\n' for p in pending)
    atomic(root/'knowledge/paper_status_overview.md',text)
    return {'rows':len(rows),'pending':len(pending)}

def import_history(root, markdown, mapping, apply=False):
    lines=markdown.read_text(encoding='utf-8-sig').splitlines(); entries=[]
    for line in lines:
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells)==7 and (re.fullmatch(r'W\d\d',cells[1]) or cells[1]=='未正式归周'):
            entries.append(dict(zip(COLUMNS,cells)))
    result={'matched':0,'pending':0,'conflicts':0,'rows':[]}
    for snapshot in entries:
        short=snapshot[COLUMNS[0]]; match=mapping.get(short,{})
        if isinstance(match,list): result['conflicts']+=1; continue
        pid=match.get('paper_id')
        # Unclaimed identities are persistent import IDs, never guessed from a short name.
        baseline_id='history-'+str(entries.index(snapshot)+1)
        target=root/'knowledge/intake'/(pid or baseline_id)/'paper_status.json'
        unclaimed=root/'knowledge/intake'/baseline_id/'paper_status.json'
        doc=load(target) if target.exists() else load(unclaimed) if unclaimed.exists() else {}
        doc.setdefault('baseline_id',baseline_id); doc.setdefault('historical_snapshot',snapshot)
        doc.setdefault('imported_at',now()); doc.setdefault('history_source',str(markdown.name))
        if not doc.get('paper_id'): doc.update(match)
        doc['short_title']=short
        result['matched' if pid else 'pending']+=1
        result['rows'].append({'short_title':short,'paper_id':pid,'path':str(target.relative_to(root))})
        if apply:
            save(target,doc)
            if pid and unclaimed.exists() and unclaimed!=target: unclaimed.unlink()
    return result

def git(repo,*args, binary=False):
    p=subprocess.run(['git','-C',str(repo),*args],capture_output=True,timeout=45)
    if p.returncode: raise ValueError(p.stderr.decode('utf-8',errors='replace').strip())
    return p.stdout if binary else p.stdout.decode('utf-8',errors='replace').strip()

def probe_git(root,doc,config,remote=False):
    c=doc.get('outputs',{}).get('C',{}); rel=c.get('git_path')
    if not rel: return observation('NOT_APPLICABLE','无 C','workflow record')
    repo=config.get('research_git_root')
    if not repo: return observation('UNKNOWN','待核验：研究 Git 目标未配置','configuration')
    repo=Path(repo)
    current_path=c.get('path') or c.get('local_path')
    path=root/current_path if current_path else root/rel if (root/rel).is_file() else repo/rel
    if not path.is_file(): return observation('MISSING','目标 C 文件未查见','filesystem',path=rel)
    body=path.read_bytes()
    if not remote:
        tracked=subprocess.run(['git','-C',str(repo),'ls-files','--error-unmatch',rel],capture_output=True).returncode==0
        if not tracked: return observation('PENDING','未跟踪','git index',path=rel)
        try: committed=git(repo,'show',f'HEAD:{rel}',binary=True)
        except ValueError: return observation('PENDING','已跟踪未提交','git index',path=rel)
        current=body.replace(b'\r\n',b'\n')==committed.replace(b'\r\n',b'\n')
        return observation('VERIFIED' if current else 'PENDING','当前版本已提交' if current else '旧版本已提交','git HEAD',path=rel,commit=git(repo,'log','-1','--format=%H','--',rel))
    url=config.get('remote_url'); branch=config.get('remote_branch')
    if not url or not branch: return observation('UNKNOWN','待核验：远端仓库或分支未配置','configuration')
    # Fetch into an ephemeral bare repository: no stale tracking ref can prove live status.
    with tempfile.TemporaryDirectory(prefix='paper-remote-') as tmp:
        git(tmp,'init','--bare'); git(tmp,'fetch','--depth=1',url,branch)
        sha=git(tmp,'rev-parse','FETCH_HEAD')
        try: published=git(tmp,'show',f'{sha}:{rel}',binary=True)
        except ValueError: return observation('MISSING','远端未查见目标 C','live git fetch',commit=sha,path=rel)
    same=published.replace(b'\r\n',b'\n')==body.replace(b'\r\n',b'\n')
    return observation('VERIFIED' if same else 'CONFLICT','当前 C 已上传' if same else '远端仍是旧 C','live git fetch',commit=sha,path=rel)

def refresh(root,items,config):
    for path,doc in items:
        intake=root/'knowledge/intake'/str(doc.get('paper_id',''))/'paper_status.json'
        if intake.exists() and intake != path:
            metadata=load(intake)
            for field in ('doi','title','status_reports'):
                if field not in doc and field in metadata: doc[field]=metadata[field]
        for platform in PLATFORMS:
            try:
                if platform in {'git','github'}: value=probe_git(root,doc,config,platform=='github')
                elif platform=='local':
                    details=[]; states=[]; evidence=[]
                    for role in 'ABC':
                        out=doc.get('outputs',{}).get(role,{})
                        rel=out.get('path') or out.get('local_path') or out.get('local_paths',{}).get(doc.get('paper_id'))
                        if not rel and role in 'AB':
                            folder=root/'work'/str(doc.get('paper_id',''))/'handoff'
                            candidates=[p for p in folder.glob('*') if p.is_file() and p.suffix.lower() in {'.pdf','.docx'} and re.search(r'(?:^\['+role+r'\]|^'+role+r'_|_'+role+r'_)',p.name,re.I)]
                            preferred=[p for p in candidates if p.suffix.lower()==('.pdf' if role=='A' else '.docx')]
                            if len(preferred)==1: rel=str(preferred[0].relative_to(root))
                            elif len(candidates)==1: rel=str(candidates[0].relative_to(root))
                            elif candidates:
                                details.append(role+' 多个文件候选待核'); states.append('PRESENT_UNVERIFIED')
                                evidence.append({'role':role,'candidate_paths':[str(p.relative_to(root)) for p in candidates]}); continue
                        if not rel: details.append(role+' 未查见独立文件（路径未登记）'); states.append('UNKNOWN'); continue
                        p=root/rel
                        if not p.is_file(): details.append(role+' 目标缺失'); states.append('MISSING'); continue
                        if not p.stat().st_size: details.append(role+' 空文件'); states.append('CONFLICT'); continue
                        if p.suffix.lower()=='.pdf':
                            from pypdf import PdfReader
                            if not PdfReader(p).pages: raise ValueError(role+' PDF 无页')
                        report_path=out.get('validation_report') or out.get('validation_reports',{}).get(doc.get('paper_id'))
                        qc=load(root/report_path) if report_path and (root/report_path).is_file() else {}
                        from artifact_binding import fingerprint, same_content
                        actual=fingerprint(p)
                        bound=qc.get('pdf_binding') if p.suffix.lower()=='.pdf' else qc.get('source_docx') if p.suffix.lower()=='.docx' else qc.get('artifact_binding')
                        verified=qc.get('passed') is True and same_content(actual,bound or {})
                        details.append(role+(' 已验证' if verified else ' 仅发现草稿（需适用 QC）'))
                        states.append('VERIFIED' if verified else 'PRESENT_UNVERIFIED')
                        evidence.append({'role':role,'path':str(p.relative_to(root)) if p.is_relative_to(root) else str(p),'qc_report':report_path,'status':states[-1]})
                    state='CONFLICT' if 'CONFLICT' in states else 'MISSING' if 'MISSING' in states else 'PRESENT_UNVERIFIED' if 'PRESENT_UNVERIFIED' in states else 'VERIFIED' if all(x=='VERIFIED' for x in states) else 'UNKNOWN'
                    value=observation(state,'；'.join(details),'local files',evidence=evidence)
                else:
                    from paper_status_live import probe_web, probe_zotero
                    value=(probe_web if platform=='web' else probe_zotero)(root,doc,config)
            except Exception as exc: value=observation('UNKNOWN','本次待核验：'+str(exc),platform)
            record_observation(doc,platform,value)
        save(path,doc)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--workspace-root',type=Path)
    p.add_argument('--paper-id'); p.add_argument('--refresh',action='store_true'); p.add_argument('--rebuild-only',action='store_true')
    p.add_argument('--import-history',type=Path); p.add_argument('--identity-map',type=Path); p.add_argument('--apply',action='store_true')
    p.add_argument('--record',type=Path,help='Intake JSON with confirmed paper_id, DOI/title and relative output paths')
    a=p.parse_args(argv); root=resolve_data_root(a.workspace_root)
    with locked(root):
        if a.import_history:
            result=import_history(root,a.import_history,load(a.identity_map) if a.identity_map else {},a.apply)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            if not a.apply: return 0
        if a.record:
            doc=load(a.record); pid=doc['paper_id']
            if Path(pid).name!=pid: raise ValueError('paper_id must use existing safe workspace identity')
            target=root/'knowledge/intake'/pid/'paper_status.json'
            old=load(target) if target.exists() else {}; old.update(doc); save(target,old)
        if a.refresh:
            items=[(p,d) for p,d in records(root) if not a.paper_id or d.get('paper_id')==a.paper_id]
            config_path=root/'knowledge/paper_status_config.json'
            workspace=root/'workspace.json'
            config=load(workspace) if workspace.exists() else {}
            if config_path.exists(): config.update(load(config_path))
            current=[select_current(group)[0] for group in group_records(items).values()]
            refresh(root,current,config)
        print(json.dumps(rebuild(root),ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
