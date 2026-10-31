#!/usr/bin/env python3
"""Explore reviewed research questions with local multilingual embeddings.

Run --mode explore to retrieve related QA candidates and complete source packets.
Use the original lexical client for ordinary/exact lookup. The optional model is
never loaded by the website; query text stays local.
"""
from pathlib import Path
import argparse,json,time,re,hashlib,subprocess,collections,sys,os,urllib.request,importlib.metadata,unicodedata
try:
 import numpy as np
 import onnxruntime as ort
 from tokenizers import Tokenizer
 DEPENDENCY_ERROR=None
except ImportError as exc:
 DEPENDENCY_ERROR=str(exc)

BASE=Path(__file__).resolve().parent.parent
REVISION='614241f622f53c4eeff9890bdc4f31cfecc418b3'
MODEL_ID='intfloat/multilingual-e5-small'
MODEL_FILES={
 'onnx/model_qint8_avx512_vnni.onnx':{'bytes':118346824,'sha256':'dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88'},
 'tokenizer.json':{'bytes':17082730,'sha256':'0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39'}
}

def digest_file(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

class SourceChangedError(RuntimeError):
 """A source snapshot changed; never downgrade this failure to lexical output."""

SOURCE_PATHS={'questions':'research/questions.json','search':'assets/evidence-search.json'}

def source_snapshot(root):
 snapshot={}
 try:
  for key,relative in SOURCE_PATHS.items():
   raw=(Path(root)/relative).read_bytes()
   text=raw.decode('utf-8-sig').replace('\r\n','\n')
   snapshot[key]={'sha256':hashlib.sha256(raw).hexdigest(),
                  'sha256_lf':hashlib.sha256(text.encode('utf-8')).hexdigest()}
 except (OSError,UnicodeError) as exc:
  raise SourceChangedError('Cannot read a stable evidence source snapshot: '+str(exc)) from exc
 return snapshot

def assert_source_snapshot(root,expected,stage,index=None,client_versions=None):
 if source_snapshot(root)!=expected:
  raise SourceChangedError('Evidence datasets changed during '+stage+'; rerun against a stable source snapshot.')
 if index is not None and index.corpus_hash!=expected['questions']['sha256']:
  raise SourceChangedError('Semantic index does not match the captured questions snapshot during '+stage)
 if client_versions is not None:
  datasets=client_versions.get('datasets',{})
  if any(datasets.get(key,{}).get('sha256_lf')!=value['sha256_lf'] for key,value in expected.items()):
   raise SourceChangedError('Original client dataset versions do not match the captured snapshot during '+stage)

def verify_model(directory):
 for relative,expected in MODEL_FILES.items():
  file=Path(directory)/relative
  if not file.is_file() or file.stat().st_size!=expected['bytes'] or digest_file(file)!=expected['sha256']:
   raise FileNotFoundError('Pinned model file missing or checksum mismatch: '+str(file)+'; use --prepare-model explicitly or provide --model-dir.')

def prepare_model(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 for relative,expected in MODEL_FILES.items():
  target=directory/relative;target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists() and target.stat().st_size==expected['bytes'] and digest_file(target)==expected['sha256']:continue
  url='https://huggingface.co/'+MODEL_ID+'/resolve/'+REVISION+'/'+relative
  temporary=target.with_suffix(target.suffix+'.partial')
  request=urllib.request.Request(url,headers={'User-Agent':'DrGeZhang-OptIn-Evidence-Consumer/1.0'})
  with urllib.request.urlopen(request,timeout=120) as response,temporary.open('wb') as output:
   total=0
   while True:
    chunk=response.read(1024*1024)
    if not chunk:break
    total+=len(chunk)
    if total>expected['bytes']:raise ValueError('Model file exceeds pinned size')
    output.write(chunk)
  if temporary.stat().st_size!=expected['bytes'] or digest_file(temporary)!=expected['sha256']:
   raise ValueError('Downloaded model checksum mismatch: '+relative)
  os.replace(temporary,target)
 verify_model(directory)
 return {'model':MODEL_ID,'revision':REVISION,'license':'MIT','model_dir':str(directory),'files':MODEL_FILES}

def original_client(root,queries=None,ids=None):
 # This is the existing strict source-bound client, not a second packet builder.
 program=r"""const fs=require('node:fs'),path=require('node:path');
 const v=JSON.parse(fs.readFileSync(0,'utf8'));
 const {createClient,loadLocal}=require(path.join(v.root,'scripts/author_evidence_client.cjs'));
 const d=loadLocal(v.root),c=createClient(d.questions,d.search,d.retrieval);
 const packets=Object.fromEntries((v.ids||[]).map(id=>[id,c.fetch(id)]));
 const rows=(v.queries||[]).map(q=>{const response=c.search(q.query,3);const hits=[...response.best_matches,...response.broader_related].slice(0,3);
 return {id:q.id,query:q.query,lexical_response:response,evidence_packets:hits.filter(h=>h.id).map(h=>c.fetch(h.id))};});
 console.log(JSON.stringify({packets,rows,source_versions:d.retrieval}));"""
 payload={'root':str(Path(root).resolve()),'queries':queries or [],'ids':ids or []}
 result=subprocess.run(['node','-e',program],input=json.dumps(payload,ensure_ascii=False),text=True,encoding='utf-8',capture_output=True,timeout=90,check=True)
 return json.loads(result.stdout)


TOPIC_LABELS={"source":"https://www.wikidata.org/wiki/Wikidata:Licensing","license":"CC0","purpose":"Term labels for topic support; not scientific claims or complete query translation.","entries":[{"zh":["乳癌","乳腺癌"],"en":"breast cancer","source":"https://www.wikidata.org/wiki/Q128581","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["心衰竭","心衰","心力衰竭"],"en":"heart failure","source":"https://www.wikidata.org/wiki/Q181754","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["青光眼"],"en":"glaucoma","source":"https://www.wikidata.org/wiki/Q159701","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["大腸癌","结直肠癌","大肠癌","結直腸癌"],"en":"colorectal cancer","source":"https://www.wikidata.org/wiki/Q188874","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["昼夜节律","晝夜節律","生物钟","生物鐘"],"en":"circadian rhythm","source":"https://www.wikidata.org/wiki/Q208353","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["免疫治疗","免疫治療"],"en":"immunotherapy","source":"https://www.wikidata.org/wiki/Q1427096","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["外部效度"],"en":"external validity","source":"https://www.wikidata.org/wiki/Q1057880","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["胶质母细胞瘤"],"en":"glioblastoma","source":"https://www.wikidata.org/wiki/Q282142","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["扩张型心肌病"],"en":"dilated cardiomyopathy","source":"https://www.wikidata.org/wiki/Q283656","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["随机对照试验","隨機對照試驗"],"en":"randomized controlled trial","source":"https://www.wikidata.org/wiki/Q1436668","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["腫瘤微環境","肿瘤微环境"],"en":"tumor microenvironment","source":"https://www.wikidata.org/wiki/Q1786433","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["回溯性研究","回顾性队列研究","回顧性隊列研究"],"en":"retrospective cohort study","source":"https://www.wikidata.org/wiki/Q2146302","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["动脉粥样硬化","動脈粥樣硬化"],"en":"atherosclerosis","source":"https://www.wikidata.org/wiki/Q12252367","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["細胞外囊泡","细胞外囊泡"],"en":"extracellular vesicle","source":"https://www.wikidata.org/wiki/Q21097485","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["微小RNA","微小核糖核酸"],"en":"microRNA","source":"https://www.wikidata.org/wiki/Q310899","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["纤维化"],"en":"fibrosis","source":"https://www.wikidata.org/wiki/Q605709","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["人類","人类"],"en":"human","source":"https://www.wikidata.org/wiki/Q5","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["基因表現","基因表达","基因表達"],"en":"gene expression","source":"https://www.wikidata.org/wiki/Q26972","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["心肌梗死","心梗","心肌梗塞"],"en":"myocardial infarction","source":"https://www.wikidata.org/wiki/Q12152","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["深度学习"],"en":"deep learning","source":"https://www.wikidata.org/wiki/Q197536","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["臨床試驗","临床试验"],"en":"clinical trial","source":"https://www.wikidata.org/wiki/Q30612","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["队列研究","隊列研究"],"en":"cohort study","source":"https://www.wikidata.org/wiki/Q1778788","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["机器学习"],"en":"machine learning","source":"https://www.wikidata.org/wiki/Q2539","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["组织学"],"en":"histology","source":"https://www.wikidata.org/wiki/Q7168","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["数据集","資料集"],"en":"data set","source":"https://www.wikidata.org/wiki/Q1172284","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["细胞培养"],"en":"cell culture","source":"https://www.wikidata.org/wiki/Q189082","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["蛋白质组学"],"en":"proteomics","source":"https://www.wikidata.org/wiki/Q471857","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["血管新生"],"en":"angiogenesis","source":"https://www.wikidata.org/wiki/Q539568","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["生存分析"],"en":"survival analysis","source":"https://www.wikidata.org/wiki/Q543310","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["观察性研究"],"en":"observational study","source":"https://www.wikidata.org/wiki/Q818574","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["风险评估","風險評估"],"en":"risk assessment","source":"https://www.wikidata.org/wiki/Q1058438","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["人工智能"],"en":"artificial intelligence","source":"https://www.wikidata.org/wiki/Q11660","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["癌症"],"en":"cancer","source":"https://www.wikidata.org/wiki/Q12078","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["铁死亡"],"en":"ferroptosis","source":"https://www.wikidata.org/wiki/Q24466962","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["炎症"],"en":"inflammation","source":"https://www.wikidata.org/wiki/Q101991","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["遠端轉移","远端转移","肿瘤转移","腫瘤轉移"],"en":"metastasis","source":"https://www.wikidata.org/wiki/Q181876","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["内皮细胞"],"en":"endothelial cell","source":"https://www.wikidata.org/wiki/Q3312341","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["靈敏度和特異度","灵敏度和特异度"],"en":"sensitivity and specificity","source":"https://www.wikidata.org/wiki/Q3808900","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["臨床顯著性","临床显著性"],"en":"clinical significance","source":"https://www.wikidata.org/wiki/Q5133848","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["線粒體","线粒体"],"en":"mitochondrion","source":"https://www.wikidata.org/wiki/Q39572","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["巨噬细胞"],"en":"macrophage","source":"https://www.wikidata.org/wiki/Q184204","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["生物標記","生物标志物"],"en":"biomarker","source":"https://www.wikidata.org/wiki/Q1069330","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["中性粒细胞"],"en":"neutrophil","source":"https://www.wikidata.org/wiki/Q188417","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["基因組學","基因组学"],"en":"genomics","source":"https://www.wikidata.org/wiki/Q222046","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["转录组学"],"en":"transcriptomics","source":"https://www.wikidata.org/wiki/Q28946449","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["基因过量表达","过表达","過表達"],"en":"overexpression","source":"https://www.wikidata.org/wiki/Q61643320","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["验证","验证","驗證"],"en":"validation","source":"https://www.wikidata.org/wiki/Q106425867","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["腎功能衰竭","肾功能衰竭","肾衰竭"],"en":"kidney failure","source":"https://www.wikidata.org/wiki/Q476921","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["预后","預後"],"en":"prognosis","source":"https://www.wikidata.org/wiki/Q592442","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["患者"],"en":"patient","source":"https://www.wikidata.org/wiki/Q181600","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."},{"zh":["預測","预测"],"en":"prediction","source":"https://www.wikidata.org/wiki/Q748250","basis":"Wikidata Chinese/English labels; listed extra variants are editorial simplification or common label variants, not scientific assertions."}]}

class SemanticIndex:
    def __init__(self, root=BASE, corpus_mode='qa_answer', model_dir=None, cache_dir=None):
        t=time.perf_counter(); self.root=Path(root); self.mode=corpus_mode
        self.model_dir=Path(model_dir);self.cache_dir=Path(cache_dir);self.cache_dir.mkdir(parents=True,exist_ok=True)
        verify_model(self.model_dir)
        raw=(self.root/'research/questions.json').read_bytes();self.corpus_hash=hashlib.sha256(raw).hexdigest()
        data=json.loads(raw);self.works={w['id']:w for w in data['works']};self.qas=data['all_questions']
        self.tokenizer=Tokenizer.from_file(str(self.model_dir/'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=512)
        self.tokenizer.enable_padding(pad_id=1,pad_token='<pad>')
        opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(self.model_dir/'onnx/model_qint8_avx512_vnni.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
        self.input_names={x.name for x in self.session.get_inputs()}
        self.model_load_seconds=time.perf_counter()-t
        cache=self.cache_dir/(corpus_mode+'-embeddings.npz');meta=self.cache_dir/(corpus_mode+'-index.json')
        key={'revision':REVISION,'dataset_sha256':self.corpus_hash,'mode':corpus_mode,'pooling':'attention-mask mean;L2 normalized','prefix':'passage: ','max_length':512,'qa_count':len(self.qas)}
        cached=False
        try:
            if meta.exists() and cache.exists() and json.loads(meta.read_text(encoding='utf-8'))['key']==key:
                self.embeddings=np.load(cache,allow_pickle=False)['embeddings']
                cached=self.embeddings.shape==(len(self.qas),384) and bool(np.isfinite(self.embeddings).all())
        except (OSError,ValueError,KeyError):
            cached=False
        if cached:
            self.build_seconds=0;self.cache_reused=True
        else:
            passages=[]
            for q in self.qas:
                w=self.works[q['work_id']]
                passages.append('passage: '+w['title']+'\n'+q['question']+('\n'+q['answer'] if corpus_mode=='qa_answer' else ''))
            started=time.perf_counter();self.embeddings=self.encode(passages,batch_size=8);self.build_seconds=time.perf_counter()-started;self.cache_reused=False
            temporary=cache.with_suffix('.partial-'+str(os.getpid()))
            with temporary.open('wb') as output:np.savez_compressed(output,embeddings=self.embeddings)
            os.replace(temporary,cache)
            temporary_meta=meta.with_suffix('.partial-'+str(os.getpid()))
            temporary_meta.write_text(json.dumps({'key':key,'build_seconds':self.build_seconds,'shape':list(self.embeddings.shape),'model_load_seconds':self.model_load_seconds,'package_versions':{x:importlib.metadata.version(x) for x in ['numpy','onnxruntime','tokenizers']}},indent=2),encoding='utf-8')
            os.replace(temporary_meta,meta)
        self.key=key

    def encode(self,texts,batch_size=8):
        all_embeddings=[]
        for start in range(0,len(texts),batch_size):
            encoded=self.tokenizer.encode_batch(texts[start:start+batch_size])
            inputs={'input_ids':np.asarray([e.ids for e in encoded],dtype=np.int64),'attention_mask':np.asarray([e.attention_mask for e in encoded],dtype=np.int64)}
            if 'token_type_ids' in self.input_names:inputs['token_type_ids']=np.zeros_like(inputs['input_ids'])
            outputs=self.session.run(None,{k:v for k,v in inputs.items() if k in self.input_names})
            hidden=outputs[0];mask=inputs['attention_mask'][...,None]
            embedding=(hidden*mask).sum(axis=1)/np.maximum(mask.sum(axis=1),1)
            embedding=embedding/np.maximum(np.linalg.norm(embedding,axis=1,keepdims=True),1e-12)
            all_embeddings.append(embedding.astype(np.float32))
            if len(texts)>16:print(f'Encoded {min(start+batch_size,len(texts))}/{len(texts)}',flush=True,file=sys.stderr)
        return np.concatenate(all_embeddings)

    def search_batch(self,queries,threshold=0.0,limit=3,candidates=None):
        t=time.perf_counter(); embeddings=self.encode(['query: '+q['query'] for q in queries],batch_size=8);seconds=time.perf_counter()-t
        scores=embeddings@self.embeddings.T; rows=[]
        for query,vector in zip(queries,scores):
            selection=candidates.get(query['id']) if candidates is not None else None
            allowed=set(selection['work_ids']) if selection is not None else None
            ids=[i for i in np.argsort(-vector) if allowed is None or self.qas[int(i)]['work_id'] in allowed][:limit]
            hits=[]
            for i in ids:
                q=self.qas[int(i)];w=self.works[q['work_id']];score=float(vector[i])
                if score<threshold:continue
                hits.append({'id':q['id'],'qa_id':q['id'],'work_id':q['work_id'],'doi':w['doi'],'url':q['answer_url'],'score':score,'question':q['question']})
            rows.append({'id':query['id'],'query':query['query'],'ranked':hits,**({'lexical_selection':selection} if selection is not None else {})})
        return {'rows':rows,'query_batch_seconds':seconds,'query_count':len(queries),'mean_query_seconds':seconds/max(len(queries),1)}


GENERIC=set('a an and are as at be by can do does for from how in is of on or the their these this to what which with within that those were was using use used study studies evidence analysis associated association research based data model models question questions answer answers review systematic meta cancer patient patients cell cells human clinical trial trials prediction risk disease diseases gene genes protein proteins molecular result results effects effect method methods new potential'.split())
def tokenize(value):return re.findall(r'[a-z0-9]+',str(value).lower())

class ExploreIndex:
 def __init__(self,root=BASE,model_dir=None,cache_dir=None):
  self.index=SemanticIndex(root,'qa_answer',model_dir,cache_dir); self.root=Path(root)
  source=json.loads((self.root/'assets/evidence-search.json').read_text(encoding='utf-8-sig'))
  self.topics=collections.defaultdict(set);self.work_tokens=collections.defaultdict(set)
  for d in source['documents']:
   if d.get('result_kind')!='paper' or not d.get('doi'):continue
   self.work_tokens[d['doi']].update(tokenize(d['text']))
   if d['category'] in ['Title','Concepts']:self.topics[d['doi']].update(tokenize(d['text']))
  self.topic_df=collections.Counter(token for tokens in self.topics.values() for token in tokens)
  self.topic_tokens={t for t,n in self.topic_df.items() if len(t)>=3 and t not in GENERIC}
  self.strong_tokens={t for t in self.topic_tokens if self.topic_df[t]<=2}
  adapter=TOPIC_LABELS
  self.medical_zh=[(term,e['en'],e['source']) for e in adapter['entries'] if e['source'].startswith('https://www.wikidata.org/')
                   and any(t in self.topic_tokens for t in tokenize(e['en'])) for term in e['zh']]
  # Exclude query-language and general method-only labels from topic support.
  general_ids={'Q1057880','Q106425867','Q1058438','Q543310','Q5133848','Q748250','Q5','Q181600','Q1778788','Q2146302','Q1436668','Q30612','Q818574','Q1172284'}
  self.medical_zh=[x for x in self.medical_zh if x[2].rsplit('/',1)[1] not in general_ids]

def explore_candidates(index,queries):
 result=index.index.search_batch(queries,threshold=0.0,limit=3)
 for row in result['rows']:
  text=row['query'];tokens=set(tokenize(text));evaluated=sorted(t for t in tokens if t not in GENERIC and len(t)>1)
  translated=[{'from':term,'to':en,'source':source} for term,en,source in index.medical_zh if term in text]
  for hit in row['ranked']:
   work_tokens=index.work_tokens[hit['doi']]
   hit.update(match_group='broader',record_kind='reviewed_question',query_coverage={
     'basis':'Whole-work original exported text; original ASCII words retained. Metadata disclosure only; no semantic rank change.',
     'evaluated_query_terms':evaluated,'matched_query_terms':[t for t in evaluated if t in work_tokens],
     'unmatched_query_terms':[t for t in evaluated if t not in work_tokens],
     'original_query':text,'chinese_topic_mappings':translated})
  row['decision']='exploratory_related_candidates'
  row['retrieval_policy']='Raw multilingual QA similarity; coverage metadata does not alter ranking.'
 return result

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('query',nargs='?');parser.add_argument('--queries');parser.add_argument('--output');parser.add_argument('--root',default=str(BASE))
 storage=Path.home()/'.cache'/'drgezhang-evidence-semantic'
 parser.add_argument('--model-dir',default=str(storage/'model'));parser.add_argument('--cache-dir',default=str(storage/'vectors'))
 parser.add_argument('--prepare-model',action='store_true');parser.add_argument('--on-unavailable',choices=['error','lexical'],default='error')
 parser.add_argument('--mode',choices=['explore'],help='Explicit opt-in to multilingual related-candidate exploration.')
 args=parser.parse_args()
 if args.prepare_model:
  print(json.dumps(prepare_model(args.model_dir),ensure_ascii=False));return
 if args.mode!='explore':parser.error('Add --mode explore to opt in, or use the original lexical client for ordinary search.')
 if bool(args.query)==bool(args.queries):parser.error('Provide one query or --queries JSON, not both.')
 if args.queries:
  v=json.loads(Path(args.queries).read_text(encoding='utf-8-sig'));queries=v if isinstance(v,list) else v['cases']
 else:queries=[{'id':'query-1','query':args.query}]
 if not queries or any(not isinstance(q.get('id'),str) or not isinstance(q.get('query'),str) or not q['query'].strip() or len(q['query'])>10000 for q in queries):
  raise ValueError('Queries require nonempty id/query strings; each query must be at most10000characters.')
 if len({q['id'] for q in queries})!=len(queries):raise ValueError('Duplicate query id')
 start=time.perf_counter()
 # Validate both original datasets before ranking or returning anything.
 snapshot=source_snapshot(args.root)
 validated=original_client(args.root)
 assert_source_snapshot(args.root,snapshot,'initial validation',client_versions=validated['source_versions'])
 index=None
 try:
  if DEPENDENCY_ERROR:raise ImportError('Semantic dependencies unavailable: '+DEPENDENCY_ERROR+'; install scripts/requirements-evidence-semantic.txt in an isolated environment.')
  index=ExploreIndex(args.root,args.model_dir,args.cache_dir)
  assert_source_snapshot(args.root,snapshot,'semantic index construction',index=index.index)
  result=explore_candidates(index,queries)
  ids=list(dict.fromkeys(hit['id'] for row in result['rows'] for hit in row['ranked']))
  fetched=original_client(args.root,ids=ids)
  assert_source_snapshot(args.root,snapshot,'packet retrieval',index=index.index,client_versions=fetched['source_versions'])
  for row in result['rows']:
   row['evidence_packets']=[fetched['packets'][hit['id']] for hit in row['ranked']]
  result.update(mode='explicit_explore_semantic_candidates',semantic_executed=True,model=MODEL_ID,model_license='MIT',model_revision=REVISION,
                use='Locate relevant research through ranked questions, then select the formal paper using the complete study identity, evidence scope, limitations and source locators in its packet.',
                candidate_note='Exploratory similarity may include unrelated material; scores are not probabilities. Check unmatched entities before citation.',
                coverage_note='Whole-work ASCII term coverage and sourced Chinese topic labels are retrieval metadata, not complete translation.')
 except (ImportError,FileNotFoundError) as exc:
  assert_source_snapshot(args.root,snapshot,'semantic availability check before fallback')
  if args.on_unavailable!='lexical':raise SystemExit(str(exc))
  fallback=original_client(args.root,queries=queries)
  assert_source_snapshot(args.root,snapshot,'explicit lexical fallback',client_versions=fallback['source_versions'])
  result={'rows':fallback['rows'],'mode':'explicit_lexical_fallback','semantic_executed':False,'semantic_unavailable_reason':str(exc)}
 assert_source_snapshot(args.root,snapshot,'final output',index=index.index if index is not None else None)
 result.update(channel='explicitly_connected_local_consumer',query_transmitted=False,natural_ai_adoption_proven=False,generated_answer=False,
               source_versions=validated['source_versions'],source_snapshot=snapshot,source_snapshot_verified=True,total_seconds=time.perf_counter()-start)
 output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if args.output:Path(args.output).write_text(output,encoding='utf-8')
 else:print(output,end='')

if __name__=='__main__':main()
