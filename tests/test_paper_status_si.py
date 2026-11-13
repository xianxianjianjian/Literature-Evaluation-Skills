import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_paper_status_overview as status
import prepare_si_bundle as si
import zotero_attachment_contract as contract
from pypdf import PdfWriter, PdfReader

class StatusTests(unittest.TestCase):
    def test_import_twice_then_assign_week_and_preserve_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'baseline.md'
            source.write_text('\n'.join('| Paper %s | W33 | old | draft | committed | uploaded | published |'%i for i in range(13)),encoding='utf-8')
            mapping={f'Paper {i}':{'paper_id':f'paper-{i}'} for i in range(13)}
            status.import_history(root,source,mapping,True); status.import_history(root,source,mapping,True)
            self.assertEqual(status.rebuild(root)['rows'],13)
            p=root/'weekly_reviews/2026/2026-W33/workflow_manifest.yaml'
            status.save(p,{'paper_id':'paper-0','week':'2026-W33','custom':{'preserve':True},'stages':{'deep_reading':{'status':'COMPLETE'}}})
            self.assertEqual(status.rebuild(root)['rows'],13)
            status.refresh(root,[(p,status.load(p))],{})
            self.assertEqual(status.load(p)['stages']['deep_reading']['status'],'COMPLETE')
            self.assertTrue(status.load(p)['custom']['preserve'])
            self.assertIn('年份待核', (root/'knowledge/paper_status_overview.md').read_text(encoding='utf-8'))
    def test_unclaimed_can_be_resolved_without_extra_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'baseline.md'; source.write_text('| Paper | 未正式归周 | a | b | c | d | e |',encoding='utf-8')
            status.import_history(root,source,{},True)
            status.import_history(root,source,{'Paper':{'paper_id':'confirmed'}},True)
            self.assertEqual(status.rebuild(root)['rows'],1)
    def test_offline_keeps_last_observation(self):
        old=status.observation('VERIFIED','current','report'); doc={}
        status.record_observation(doc,'web',old)
        status.record_observation(doc,'web',status.observation('UNKNOWN','offline','live'))
        status.record_observation(doc,'web',status.observation('UNKNOWN','offline again','live'))
        self.assertEqual(doc['platform_status']['web']['last_observation'],old)
    def test_multiple_real_reviews_not_silently_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for week in ['2026-W33','2026-W34']:
                status.save(root/f'weekly_reviews/2026/{week}/workflow_manifest.yaml',{'paper_id':'same','week':week})
            self.assertEqual(status.rebuild(root)['rows'],1)
            self.assertIn('多个周次待核对',(root/'knowledge/paper_status_overview.md').read_text(encoding='utf-8'))
    def test_git_current_old_and_live_remote_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); repo=root/'repo'; repo.mkdir()
            status.git(repo,'init'); status.git(repo,'config','user.email','fixture@example.org'); status.git(repo,'config','user.name','Fixture')
            (repo/'c.md').write_text('old',encoding='utf-8'); status.git(repo,'add','c.md'); status.git(repo,'commit','-m','old')
            branch=status.git(repo,'branch','--show-current')
            doc={'outputs':{'C':{'git_path':'c.md'}}}; cfg={'research_git_root':str(repo),'remote_url':str(repo),'remote_branch':branch}
            self.assertEqual(status.probe_git(root,doc,cfg)['status'],'VERIFIED')
            (repo/'c.md').write_text('new',encoding='utf-8')
            self.assertEqual(status.probe_git(root,doc,cfg)['detail'],'旧版本已提交')
            self.assertEqual(status.probe_git(root,doc,cfg,True)['status'],'CONFLICT')
            status.git(repo,'add','c.md'); status.git(repo,'commit','-m','new')
            self.assertEqual(status.probe_git(root,doc,cfg,True)['status'],'VERIFIED')

class BundleTests(unittest.TestCase):
    def pdf(self,path,pages):
        w=PdfWriter()
        for _ in range(pages): w.add_blank_page(width=100,height=100)
        w.write(path)
    def test_merge_coverage_reuse_and_stable_media_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.pdf(root/'a.pdf',2); self.pdf(root/'b.pdf',1)
            (root/'v.mp4').write_bytes(b'video'); (root/'d.csv').write_text('x,y')
            rows=[{'source_id':'SRC-S1','source_type':'SI','local_path':'a.pdf'},{'source_id':'SRC-S2','source_type':'SI','local_path':'b.pdf'}, {'source_id':'V','source_type':'SI','local_path':'v.mp4'},{'source_id':'D','source_type':'DATA','local_path':'d.csv'}]
            source=root/'source.json'; status.save(source,{'sources':rows})
            out=root/'handoff/si.pdf'; report=si.bundle(root,source,out)
            self.assertTrue(report['passed']); self.assertEqual(report['pages'],3)
            self.assertEqual(report['sources'][1]['start_page'],3)
            self.assertEqual(report['media'][0]['title'],'SI-Video-1')
            mtime=out.stat().st_mtime_ns
            rows.reverse(); status.save(source,{'sources':rows})
            report=si.bundle(root,source,out)
            self.assertEqual(report['media_numbers']['VIDEO']['V'],1)
            self.assertEqual(len(PdfReader(out).outline),2)
            status.save(source,{'sources':rows}); si.bundle(root,source,out)
            self.assertEqual(si.verify_bundle(report,root),[])
    def test_no_reading_si_and_missing_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/'sources.json'; status.save(p,{'sources':[]})
            report=si.bundle(root,p,root/'handoff/si.pdf'); self.assertEqual(report['reading_status'],'NOT_APPLICABLE')
            status.save(p,{'sources':[{'source_id':'S','source_type':'SI','required':True,'local_path':'absent.pdf'}]})
            report=si.bundle(root,p,root/'handoff/si.pdf'); self.assertFalse(report['passed'])
    def test_document_conversion_cannot_pass_without_visual_qc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'s.docx').write_bytes(b'doc'); self.pdf(root/'converted.pdf',1)
            source=root/'sources.json'; status.save(source,{'sources':[{'source_id':'S','source_type':'SI','local_path':'s.docx'}]})
            def convert(src,out,soffice): out.write_bytes((root/'converted.pdf').read_bytes()); return {'pages':1}
            with patch.object(si,'prepare',convert): report=si.bundle(root,source,root/'handoff/si.pdf')
            self.assertFalse(report['passed']); self.assertIn('visual QC',report['pending_zotero_actions'][0]['reason'])
    def test_corrupted_bundle_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); self.pdf(root/'s.pdf',1); source=root/'sources.json'
            status.save(source,{'sources':[{'source_id':'S','source_type':'SI','local_path':'s.pdf'}]})
            report=si.bundle(root,source,root/'handoff/si.pdf'); self.pdf(root/'handoff/si.pdf',2)
            self.assertTrue(si.verify_bundle(report,root))
    def test_names_and_legacy_contract_are_independent(self):
        self.assertEqual(contract.role_title('MAIN'),'Main Article')
        self.assertEqual(contract.role_title('MAIN',naming_version=1),'pdf')
        self.assertEqual(contract.role_title('SI'),'Support Information')
        self.assertEqual(contract.role_title('VIDEO',2),'SI-Video-2')
        self.assertEqual(contract.role_title('DATA',1),'SI-Data-1')
if __name__=='__main__': unittest.main()

class RoleEntryTests(unittest.TestCase):
    def test_a_requires_real_pdf_and_bound_qc(self):
        import argparse, zotero_bridge as bridge
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/'bad.pdf'; path.write_bytes(b'not PDF')
            args=argparse.Namespace(role='A',si_number=None,data_si=False,file=path,qc_report=None)
            with self.assertRaises(bridge.ZoteroBridgeError): bridge.command_attach_role(args)
            writer=PdfWriter(); writer.add_blank_page(width=100,height=100); writer.write(path)
            with self.assertRaisesRegex(bridge.ZoteroBridgeError,'qc-report'): bridge.command_attach_role(args)
            qc=root/'qc.json'; status.save(qc,{'passed':True,'pdf_binding':{'sha256':'wrong'}}); args.qc_report=qc
            with self.assertRaisesRegex(bridge.ZoteroBridgeError,'does not bind'): bridge.command_attach_role(args)
    def test_si_input_change_invalidates_verified_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'sources.json'; writer=PdfWriter(); writer.add_blank_page(width=100,height=100); writer.write(root/'s.pdf')
            status.save(source,{'sources':[{'source_id':'S','source_type':'SI','local_path':'s.pdf'}]})
            report=si.bundle(root,source,root/'handoff/si.pdf')
            self.assertTrue(report['passed']); self.assertTrue(all(x['passed'] for x in report['representative_page_checks']))
            (root/'s.pdf').write_bytes((root/'s.pdf').read_bytes()+b'\n%new version')
            self.assertTrue(si.verify_bundle(report,root))
    def test_migration_conflict_has_no_write(self):
        import argparse, zotero_bridge as bridge, hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); path=root/'a.pdf'; path.write_bytes(b'fake fixture bytes')
            spec=root/'spec.json'; status.save(spec,{'parent_key':'P','attachments':[{'role':'MAIN','key':'A','local_path':str(path),'sha256':si.fingerprint(path)}]})
            parent={'key':'P'}; children=[{'key':'A','data':{'parentItem':'P','title':'pdf','md5':hashlib.md5(path.read_bytes()).hexdigest(),'contentType':'application/pdf'}},{'key':'B','data':{'title':'Main Article'}}]
            args=argparse.Namespace(spec=spec,parent_key='P',yes=False)
            with patch.object(bridge,'_parent_children',return_value=(parent,children)),patch.object(bridge.local_write.LocalWriteClient,'connect') as connect:
                with self.assertRaisesRegex(bridge.ZoteroBridgeError,'another child'): bridge.command_normalize_titles(args)
                connect.assert_not_called()
