"""Synthetic-only tests: no actual GT, results or production data needed."""
from __future__ import annotations
import csv
import hashlib
from http.client import HTTPConnection
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import zipfile
from PIL import Image

SERVER=Path(__file__).resolve().parents[1]/'scripts'/'paper_a_mobile_review_server.py'
spec=importlib.util.spec_from_file_location('local_audit_server',SERVER)
srv=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=srv
spec.loader.exec_module(srv)


def jwrite(p,doc):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(doc,indent=2),encoding='utf-8')


def cwrite(p,rows,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader();w.writerows(rows)


class ReviewServerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base=Path(self.temp.name)
        self.root=base/'MFI-Edge';self.data=base/'MultiCue'
        self.root.mkdir();self.data.mkdir()
        self.signoff=self.data/'paper_a_completion/scientific_signoff'
        b=self.root/'datasets/BIPEDv2/edges/imgs/train/rgbr/real'
        m=self.data/'source_frames_only'
        b.mkdir(parents=True);m.mkdir(parents=True)
        self.gt=self.root/'datasets/BIPEDv2/edges/edge_maps/train/rgbr/real'
        self.gt.mkdir(parents=True)
        (self.gt/'CANARY_NAO_LER.png').write_bytes(b'PROTEGIDO_XY_F1_GT')
        selected_b=[f'RGB_{i:03d}' for i in range(1,126)]
        initial_b=selected_b[:83]+[f'RGB_{i:03d}' for i in range(140,182)]
        selected_m=[f'{4000+i}_left_0001' for i in range(94)]
        old_m=selected_m+['4586_left_0080']
        roster=[]
        for ds,names,basepath in [('BIPED',selected_b+initial_b[83:],b),('MultiCue',old_m,m)]:
            for idx,iid in enumerate(names):
                p=basepath/(iid+'.jpg')
                im=Image.new('RGB',(40,25),(idx%256,(idx*3)%256,(idx*7)%256))
                im.save(p)
        def row(ds,iid):
            p=(b if ds=='BIPED' else m)/(iid+'.jpg')
            return {'dataset':ds,'image_id':iid,'relative_path':p.name,
                'image_sha256':srv.sha_file(p),'independence_review':'pending',
                'prior_exposure_review':'pending','scene_group':'NOT_INDEPENDENTLY_ATTESTED_'+iid,
                'notes':'DRAFT'}
        roster=[row('BIPED',x) for x in selected_b]+[row('MultiCue',x) for x in selected_m]
        old=[row('BIPED',x) for x in initial_b]+[row('MultiCue',x) for x in old_m]
        cwrite(self.signoff/'COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv',roster,srv.FIELDS)
        cwrite(self.signoff/'REVIEW_220_IMAGES_PENDING.csv',old,srv.FIELDS)
        review=[{**r,**{k:'' for k in ('reviewer_independence_decision','reviewer_prior_exposure_decision','evidence_for_both_decisions','reviewer_name','reviewed_utc','historical_attention')}} for r in roster]
        fields=list(srv.FIELDS)+['reviewer_independence_decision','reviewer_prior_exposure_decision','evidence_for_both_decisions','reviewer_name','reviewed_utc','historical_attention']
        cwrite(self.signoff/'CANDIDATE_A_N219_SCIENCE_REVIEW_NOT_ACTIVE/REVIEW_A_N219_ALL_PENDING.csv',review,fields)
        roster_digest=hashlib.sha256(''.join(sorted(f"{r['dataset']}|{r['image_id']}|{r['image_sha256']}\n" for r in roster)).encode('utf-8')).hexdigest()
        jwrite(self.root/'docs/paper_a_confirmation/COORTE_A_N219_PROPOSTA_NAO_CONGELADA.json',{
            'status':'PROPOSAL_NOT_FROZEN_NOT_APPROVED','counts':{'BIPED':125,'MultiCue':94,'N':219},
            'images':{'BIPED':','.join(selected_b),'MultiCue':','.join(selected_m)},
            'quarantine_BIPED_ids':','.join(f'RGB_{i:03d}' for i in range(220,236)),
            'roster_sha256_sorted_dataset_id_source_sha':roster_digest,
            'source_cohort_sha256':srv.sha_file(self.signoff/'REVIEW_220_IMAGES_PENDING.csv')})
        jwrite(self.signoff/'COORTE_A_N219_READINESS_NOT_APPROVED.json',{
            'status':'A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN',
            'counts':{'BIPED':125,'MultiCue':94,'N':219},
            'review_roster_sha256':srv.sha_file(self.signoff/'COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv'),
            'scientific_signoff':False,'GT_accessed':False})
        jwrite(self.root/'docs/paper_a_confirmation/protocol.json',{'status':'draft_not_frozen','confirmatory_outcomes_opened':False})
        jwrite(self.signoff/'FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json',{'cohort':{'target_n_independent_images':219},'freeze_commit':None})
        jwrite(self.signoff/'PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json',{
            'GT_opened':False,'H1_H2_executed':False,'effects':[{'assumed_abs_population_Spearman_rho':.2,'candidate_A':{'joint_rejection_rate':.815}}]})
        jwrite(self.root/'results/automation/stage13c_biped_preflight/summary.json',{'stage':'stage13c','checks':{'train':{'images':200,'ground_truth':200}}})
        self.review=srv.ReviewData(self.root,self.data)
        self.auth=srv.Auth(pin='123456789012')
        self.server=srv.AppServer(('127.0.0.1',0),self.review,self.auth)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self,method,path,body=None,cookie=None,csrf=None,headers=None):
        client=HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=10)
        h={'Host':'127.0.0.1:'+str(self.server.server_address[1])}
        if body is not None:
            h['Content-Type']='application/json'
            body=json.dumps(body)
        if cookie:h['Cookie']=cookie
        if csrf:h['X-CSRF-Token']=csrf
        if headers:h.update(headers)
        client.request(method,path,body=body,headers=h)
        r=client.getresponse()
        content=r.read()
        result=(r.status,dict(r.getheaders()),content)
        client.close()
        return result

    def signin(self):
        status,headers,body=self.request('POST','/api/login',{'pin':'123456789012'})
        self.assertEqual(status,200,body)
        return headers['Set-Cookie'].split(';')[0],json.loads(body)['csrf']

    def test_authentication_origin_csrf_and_security(self):
        status,_,body=self.request('GET','/api/summary')
        self.assertEqual(status,401)
        self.assertEqual(self.request('POST','/api/login',{'pin':'bad'})[0],403)
        cookie,csrf=self.signin()
        status,headers,body=self.request('GET','/api/summary',cookie=cookie)
        self.assertEqual(status,200)
        self.assertEqual(headers['Content-Security-Policy'].split(';')[0],"default-src 'self'")
        self.assertEqual(json.loads(body)['counts']['total'],219)
        self.assertEqual(self.request('POST','/api/save-topic',{'topic':'scenes','decision':'PENDING'},cookie=cookie)[0],403)
        self.assertEqual(self.request('POST','/api/save-topic',{'topic':'scenes','decision':'PENDING'},cookie=cookie,csrf=csrf,headers={'Origin':'https://evil.example'})[0],403)

    def test_all_origins_are_original_rgb_no_gt_leak(self):
        cookie,csrf=self.signin()
        for uri in ['/api/items?set=A219','/api/items?set=biped_train','/api/items?set=multicue_pool']:
            status,_,body=self.request('GET',uri,cookie=cookie)
            self.assertEqual(status,200,body)
        status,_,jpeg=self.request('GET','/api/thumb/BIPED:RGB_001',cookie=cookie)
        self.assertEqual(status,200)
        self.assertTrue(jpeg.startswith(b'\xff\xd8'))
        self.assertEqual(self.request('GET','/api/thumb/pool:biped_train:CANARY_NAO_LER',cookie=cookie)[0],409)
        self.assertIn(self.request('GET','/api/thumb/../../GT',cookie=cookie)[0],(404,409))
        self.assertNotIn(b'PROTEGIDO_XY_F1_GT',jpeg)

    def test_decisions_are_drafts_and_state_is_hash_bound(self):
        cookie,csrf=self.signin()
        request={'key':'BIPED:RGB_001','scene':'APPEARS_INDEPENDENT','exposure':'PENDING',
            'group':'rua_teste_01','note':'Comparei com os vizinhos e nao reconheci repeticao visual.'}
        status,_,body=self.request('POST','/api/save-item',request,cookie,csrf)
        self.assertEqual(status,200,body)
        self.assertEqual(self.request('POST','/api/save-topic',{'topic':'exposure',
            'decision':'PRELIMINARY_APPROVE','note':'curto'},cookie,csrf)[0],409)
        status,_,body=self.request('POST','/api/save-topic',{'topic':'scenes',
            'decision':'NEEDS_EVIDENCE','note':'Faltam logs de execucao e agrupamentos de cenas. Necessario confrontar fontes antes da atestacao.'},cookie,csrf)
        self.assertEqual(status,200,body)
        file=self.signoff/'MOBILE_A219_RASCUNHO/decisions_DRAFT.json'
        doc=json.loads(file.read_text(encoding='utf-8'))
        self.assertEqual(doc['status'],'DRAFT_NOT_INDEPENDENT_SCIENTIFIC_SIGNOFF')
        self.assertFalse((self.signoff/'FINAL_INDEPENDENT_REVIEW.json').exists())
        status,_,zipblob=self.request('GET','/api/export',cookie=cookie)
        self.assertEqual(status,200)
        with zipfile.ZipFile(io.BytesIO(zipblob)) as bundle:
            self.assertIn('PARECER_RASCUNHO.md',bundle.namelist())
            self.assertIn('DRAFT_NOT_INDEPENDENT_SCIENTIFIC_SIGNOFF',bundle.read('DECISOES_A219_RASCUNHO_NAO_APROVADO.json').decode())
        # A change to the canonical manifest must lock future writes.
        with (self.signoff/'COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv').open('ab') as f:f.write(b'\n')
        self.assertEqual(self.request('POST','/api/save-topic',{'topic':'scenes','decision':'PENDING'},cookie,csrf)[0],409)

    def test_metadata_history_is_not_proof_and_similarity_is_visual_only(self):
        hits=self.review.history_for('BIPED:RGB_001')
        self.assertTrue(any('Stage13c' in x.get('meaning','') for x in hits))
        nearest=self.review.similarity('BIPED:RGB_001','biped_train',5)
        self.assertLessEqual(len(nearest),5)
        self.assertTrue(all(x['interpretation']=='TRIAGEM_VISUAL_NAO_CERTIFICACAO' for x in nearest))


if __name__=='__main__':
    import zipfile
    unittest.main()
