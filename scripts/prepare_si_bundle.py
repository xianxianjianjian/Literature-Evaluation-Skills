#!/usr/bin/env python3
"""Bundle documentary SI with source page coverage; retain media numbering."""
from __future__ import annotations
import argparse, hashlib, json, tempfile
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from prepare_si_pdf import prepare
from build_paper_status_overview import load, save, locked

def fingerprint(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def verify_bundle(report, root):
    failures=[]; path=root/report['pdf_path']
    try:
        reader=PdfReader(path)
        for source in report.get('inputs', []):
            if fingerprint(root/source['path'])!=source['sha256']: failures.append('original SI input changed: '+source['source_id'])
        if fingerprint(path)!=report['sha256']: failures.append('bundle content changed')
        if len(reader.pages)!=report['pages']: failures.append('bundle page count changed')
        cursor=1
        for row in report['sources']:
            if row['start_page']!=cursor or row['end_page']-row['start_page']+1!=row['pages']: failures.append('source page coverage gap')
            cursor=row['end_page']+1
        if cursor-1!=report['pages']: failures.append('total coverage mismatch')
    except Exception as exc: failures.append(str(exc))
    return failures

def bundle(root, package_path, output, soffice=None):
    package=load(package_path); sources=package['sources']; ids=[s['source_id'] for s in sources]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate source_id')
    report_path=output.parent/'si_bundle_manifest.json'
    previous=load(report_path) if report_path.exists() else {}
    numbers=previous.get('media_numbers',{'VIDEO':{},'DATA':{}})
    reading=[]; media=[]; pending=[]
    for index,s in enumerate(sources):
        if s.get('source_type') not in {'SI','DATA'}: continue
        source=root/s['local_path'] if s.get('local_path') else None
        if not source or not source.is_file():
            if s.get('required'): pending.append({'action':'obtain_source','source_id':s['source_id']})
            continue
        ext=source.suffix.lower()
        kind=s.get('si_kind') or ('READING' if ext in {'.pdf','.doc','.docx'} else 'VIDEO' if ext in {'.mp4','.mov','.avi','.webm','.mkv'} else 'DATA')
        if kind=='READING': reading.append((s.get('publisher_order',index),index,s,source))
        elif kind in {'VIDEO','DATA'}:
            bucket=numbers.setdefault(kind,{})
            bucket.setdefault(s['source_id'],max(bucket.values(),default=0)+1)
            media.append(dict(source_id=s['source_id'],role=kind,si_number=bucket[s['source_id']],title=f"SI-{kind.title()}-{bucket[s['source_id']]}",path=str(source.relative_to(root)),sha256=fingerprint(source)))
        else: raise ValueError('unrecognized si_kind: '+kind)
    reading.sort(key=lambda r:(r[0],r[1]))
    inputs=[dict(source_id=s['source_id'],path=str(src.relative_to(root)),sha256=fingerprint(src)) for _,_,s,src in reading]
    if reading and previous.get('inputs')==inputs and previous.get('passed') and previous.get('pdf_path') and not verify_bundle(previous,root):
        previous.update(media_numbers=numbers,media=media,pending_zotero_actions=pending,passed=not pending)
        save(report_path,previous); return previous
    report=dict(schema_version=1,naming_version=2,inputs=inputs,media_numbers=numbers,media=media,sources=[],pending_zotero_actions=pending,passed=False)
    output.parent.mkdir(parents=True,exist_ok=True)
    if not reading:
        report.update(reading_status='NOT_APPLICABLE' if not pending else 'PENDING',passed=not pending)
        save(report_path,report); return report
    writer=PdfWriter(); cursor=1
    # Conversion files are recoverable on failure. Retain them until visual QC is approved.
    conversion_dir=output.parent/'si_conversion_pending'; conversion_dir.mkdir(exist_ok=True)
    for _,_,s,src in reading:
        converted=conversion_dir/(s['source_id']+'.pdf')
        try:
            same_input=any(row.get('source_id')==s['source_id'] and row.get('sha256')==fingerprint(src) for row in previous.get('inputs',[]))
            if src.suffix.lower() in {'.doc','.docx'} and converted.is_file() and same_input:
                conversion={'status':'SI_PDF_READY','reused_conversion':True,'original_retained':True}
            else:
                conversion=prepare(src,converted,soffice)
            reader=PdfReader(converted)
            conversion['source']=str(src.relative_to(root)); conversion['pdf_path']=None  # conversion copy is disposable
            if src.suffix.lower() in {'.doc','.docx'}:
                qc_path=s.get('conversion_qc_report'); qc=load(root/qc_path) if qc_path else {}
                if not (qc.get('passed') is True and qc.get('pdf_sha256')==fingerprint(converted) and qc.get('all_pages_visual_reviewed') is True):
                    raise ValueError('DOC/DOCX conversion requires independent all-page visual QC bound to converted PDF')
            count=len(reader.pages); writer.append(reader,outline_item=s['source_id']+' '+src.name)
            report['sources'].append(dict(source_id=s['source_id'],original_filename=src.name,source_sha256=fingerprint(src),conversion=conversion,conversion_qc_report=s.get('conversion_qc_report'),pages=count,start_page=cursor,end_page=cursor+count-1))
            cursor+=count
        except Exception as exc:
            report['pending_zotero_actions'].append(dict(action='prepare_si',source_id=s['source_id'],reason=str(exc)))
            save(report_path,report); return report
    with tempfile.NamedTemporaryFile(dir=output.parent,suffix='.pdf',delete=False) as f: tmp=Path(f.name)
    if len(reading)==1:
        import shutil
        shutil.copyfile(conversion_dir/(reading[0][2]['source_id']+'.pdf'),tmp)
    else: writer.write(tmp)
    tmp.replace(output)
    report.update(pdf_path=str(output.relative_to(root)),sha256=fingerprint(output),bytes=output.stat().st_size,pages=cursor-1,reading_status='VERIFIED')
    failures=verify_bundle(report,root)
    # Compare representative rendered pages before discarding conversion copies.
    import pymupdf as fitz
    visual=[]
    with fitz.open(output) as merged:
        for row in report['sources']:
            with fitz.open(conversion_dir/(row['source_id']+'.pdf')) as original:
                sample=sorted({0,len(original)//2,len(original)-1})
                for index in sample:
                    source_page=original[index].get_pixmap()
                    merged_page=merged[row['start_page']-1+index].get_pixmap()
                    equal=(source_page.width,source_page.height,source_page.samples)==(merged_page.width,merged_page.height,merged_page.samples)
                    visual.append({'source_id':row['source_id'],'source_page':index+1,'merged_page':row['start_page']+index,'passed':equal})
                    if not equal: failures.append('rendered page changed: '+row['source_id'])
    report['representative_page_checks']=visual
    report['validation_failures']=failures; report['passed']=not failures and not pending
    save(report_path,report)
    if report['passed']:
        for p in conversion_dir.glob('*.pdf'): p.unlink()
        conversion_dir.rmdir()
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace-root',type=Path,required=True); p.add_argument('--sources',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--soffice',type=Path)
    a=p.parse_args(argv)
    with locked(a.workspace_root): result=bundle(a.workspace_root.resolve(),a.sources,a.output.resolve(),a.soffice)
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result['passed'] else 2
if __name__=='__main__': raise SystemExit(main())
