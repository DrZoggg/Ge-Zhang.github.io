"""Frozen contract and source mapping regressions, not new scientific verification."""
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import research_guides as g


class GuideTests(unittest.TestCase):
    def setUp(self): self.data = g.load()

    def rejected(self, edit):
        changed = copy.deepcopy(self.data); edit(changed)
        with self.assertRaises(ValueError): g.resolve(changed)

    def test_current_source_mapping_and_rendering(self):
        sources = g.resolve(self.data)
        page, md = g.render(self.data, sources)
        g.validate_page(page)
        for row in self.data['studies']:
            s = sources[row['id']]
            for ref in row['evidence_refs']:
                self.assertIn(s['url'] + '#' + ref.lower(), page)
                self.assertIn(s['findings'][ref]['source_locator'], md)
            for key, _ in g.FIELDS:
                if key in row: self.assertIn(row[key], md)
        self.assertEqual(g.render(self.data, sources), (page, md))

    def test_nonexistent_doi(self):
        self.rejected(lambda d: d['studies'][0].update(source_doi='10.9999/missing'))

    def test_nonexistent_kf(self):
        self.rejected(lambda d: d['studies'][0]['evidence_refs'].append('KF999'))

    def test_source_drift(self):
        self.rejected(lambda d: d['studies'][0].update(source_fingerprint='0'*64))

    def test_transcriptomic_not_plasma_replication(self):
        self.rejected(lambda d: d['studies'][0].update(boundary='Independent plasma-proteomic replication.'))

    def test_mirna_discovery_count_qualification(self):
        self.rejected(lambda d: d['studies'][1].update(boundary='miR-185-5p is not in the external panel.'))

    def test_circrna_platform_qualification(self):
        self.rejected(lambda d: d['studies'][2].update(boundary='No prospective diagnostic utility is established.'))

    def test_circrna_nine_ten_qualification(self):
        self.rejected(lambda d: d['studies'][2].update(follow_up='External qRT-PCR in 6 DCM patients and 4 controls.'))

    def test_no_synthetic_total_or_joint_model(self):
        for text in ['A combined clinical model is established.', 'The cross-study total is 137 participants.']:
            with self.subTest(text=text):
                self.rejected(lambda d: d['sections'][1].update(text=text))

    def test_guide_not_publication(self):
        master = json.loads((g.ROOT/'data/publications_master.json').read_text(encoding='utf-8'))
        master.append({'slug':g.SLUG,'title':self.data['title']})
        with self.assertRaisesRegex(ValueError, 'master'): g.resolve(self.data, master=master)

    def test_no_source_doi_impersonation(self):
        page, _ = g.render(self.data, g.resolve(self.data))
        with self.assertRaises(ValueError):
            g.validate_page(page.replace('</head>', '<meta name="citation_doi" content="10.1111/jcmm.17789"></head>'))
        with self.assertRaises(ValueError):
            g.validate_page(page.replace('rel="canonical" href="'+g.URL, 'rel="canonical" href="https://doi.org/10.1111/jcmm.17789'))
        self.rejected(lambda d: d.update(doi='10.1111/jcmm.17789'))


class TaskWorkspaceTests(unittest.TestCase):
    """Behavior checks use synthetic reviewed rows, never a new science fixture."""
    def setUp(self):
        self.url = 'https://drgezhang.com/research/workspace-regression.html'
        self.studies = []
        for wid in ('study-one', 'study-two', 'study-three'):
            self.studies.append({'id':wid, 'doi':'10.1000/'+wid, 'title':'Fixture '+wid,
                                 'task':'Fixture task '+wid,
                                 'paper_url':'https://drgezhang.com/papers/'+wid+'.html',
                                 'doi_url':'https://doi.org/10.1000/'+wid,
                                 'study_profile':{'study_design':'Fixture design', 'evidence_type':'Fixture type'},
                                 'selected_questions':[], 'evidence_scope':'Fixture scope', 'limitations':[]})
        sources = [{'id':s['id'], 'doi':s['doi'], 'title':s['title'], 'url':s['doi_url'], 'locator':'Fixture locator'}
                   for s in self.studies]
        sources.append({'id':'external-source', 'doi':'10.1000/external', 'title':'External fixture source',
                        'url':'https://doi.org/10.1000/external', 'locator':'External fixture locator'})
        self.use = {'id':'fixture-use', 'question':'Fixture question?', 'question_zh':'示例问题？',
                    'answer':'Fixture source-linked answer.', 'answer_zh':'示例来源说明。',
                    'answer_source_ids':['external-source'], 'sources':sources,
                    'checklist':[{'dimension':'Fixture dimension', 'text':'Fixture check.', 'source_ids':['external-source']}],
                    'study_roles':[{'work_id':s['id'], 'role':'Fixture role', 'text':'Fixture use.', 'source_ids':[s['id']]}
                                   for s in self.studies],
                    'comparison':{'caption':'Existing three-study comparison', 'rows':[
                        {'work_id':s['id'], 'design':'Fixture design', 'population':'Fixture population',
                         'endpoint':'Fixture endpoint', 'validation':'Fixture validation', 'metrics':'Fixture metric',
                         'doi':s['doi'], 'source_ids':[s['id']]} for s in self.studies]},
                    'comparison_note':'Fixture comparison note.', 'comparison_note_source_ids':['external-source'],
                    'research_uses':[{'use':'Fixture research use', 'text':'Fixture task.', 'source_ids':['external-source']}]}
        ids = ['study','population','prediction-time','outcome','horizon','model-state','validation-data',
               'discrimination','calibration','utility','missing-data','overlap','references','notes']
        columns = [{'id':key, 'label':'Field '+key} for key in ids]
        columns[0]['label'] = 'Model, study'
        self.workspace = {'title':'Comparison workspace', 'intro':'Fixture <scope & evidence>.',
                          'columns':columns, 'display_columns':['study','population','outcome','horizon','model-state','calibration'],
                          'examples':[
                              {'cells':{key:('Fixture internal study' if key=='study' else 'Value '+key) for key in ids}, 'source_ids':['study-one']},
                              {'cells':{key:('Example, "external"' if key=='study' else 'HIDDEN_DETAIL_KEEP_IN_EXPORT' if key=='notes' else 'Value '+key) for key in ids}, 'source_ids':['external-source']}],
                          'decisions':[{'rule':'Fixture decision', 'text':'Use the specified comparison conditions.', 'source_ids':['external-source']}]}

    def with_workspace(self):
        use = copy.deepcopy(self.use); use['task_workspace'] = copy.deepcopy(self.workspace)
        return use

    def packet(self, use):
        return {'title':'Workspace regression', 'question':'Fixture task?', 'scope':'Fixture scope.',
                'reading_rule':'Fixture reading rule.', 'canonical_url':self.url, 'studies':self.studies,
                'research_use':g.research_use_packet(use,self.studies)}

    def test_optional_section_preserves_original_packet_and_render_behavior(self):
        packet = g.research_use_packet(self.use,self.studies)
        self.assertEqual(packet, {'kind':'source_linked_methodological_synthesis', **self.use})
        old_html, old_md = g.render_research_use(packet,self.studies)
        self.assertEqual(g.render_research_use(packet,self.studies,self.url), (old_html,old_md))
        self.assertNotIn('.worksheet.csv',old_html)
        self.assertNotIn('task-workspace',old_html)
        self.assertEqual([row['work_id'] for row in packet['comparison']['rows']],
                         [s['id'] for s in self.studies])

    def test_external_example_and_all_export_fields_with_compact_visible_table(self):
        packet = self.packet(self.with_workspace())
        page, md, exported = g.render_comparison(packet)
        g.validate_page(page,self.url)
        use = json.loads(exported)['research_use']
        self.assertEqual(use['task_workspace'],self.workspace)
        self.assertEqual([row['work_id'] for row in use['comparison']['rows']],
                         [s['id'] for s in self.studies])
        self.assertNotIn('work_id',use['task_workspace']['examples'][1])
        self.assertIn('fixture-use-source-external-source',page)
        self.assertIn('[4](https://doi.org/10.1000/external)',md)
        self.assertIn('Fixture &lt;scope &amp; evidence&gt;.',page)
        self.assertNotIn('HIDDEN_DETAIL_KEEP_IN_EXPORT',page)
        self.assertNotIn('HIDDEN_DETAIL_KEEP_IN_EXPORT',md)
        for suffix in ('worksheet.csv','blank.csv'):
            url = self.url[:-5]+'.'+suffix
            self.assertIn('href="'+url+'"',page)
            self.assertIn(']('+url+')',md)
        self.assertEqual(len(use['task_workspace']['columns']),14)
        self.assertEqual(len(use['task_workspace']['display_columns']),6)
        self.assertIn('External fixture locator',md)

    def test_csv_roundtrip_all_columns_external_row_and_blank_template(self):
        use = g.research_use_packet(self.with_workspace(),self.studies)
        workspace = use['task_workspace']
        rows = list(csv.reader(io.StringIO(g.task_workspace_csv(workspace))))
        self.assertEqual(rows[0],[c['label'] for c in workspace['columns']])
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[2][0],'Example, "external"')
        self.assertEqual(rows[2][-1],'HIDDEN_DETAIL_KEEP_IN_EXPORT')
        blank = list(csv.reader(io.StringIO(g.task_workspace_csv(workspace,blank=True))))
        self.assertEqual(blank,[rows[0],['']*14])
        self.assertNotIn('\r',g.task_workspace_csv(workspace))

    def test_snake_case_column_contract_exports_without_relaxing_source_ids(self):
        use=self.with_workspace();workspace=use['task_workspace']
        rename={'prediction-time':'prediction_time','references':'formal_doi'}
        for column in workspace['columns']:
            column['id']=rename.get(column['id'],column['id'])
            if column['id']=='formal_doi':column['label']='Formal DOI'
            if column['id']=='prediction_time':column['label']='Prediction time'
        workspace['display_columns']=['study','population','outcome','prediction_time','model-state','formal_doi']
        for index,example in enumerate(workspace['examples']):
            example['cells']={rename.get(key,key):value for key,value in example['cells'].items()}
            example['cells']['prediction_time']='At study entry'
            example['cells']['formal_doi']='10.1000/study-one' if index==0 else '10.1000/external'
        packet=self.packet(use);page,md,exported=g.render_comparison(packet)
        self.assertEqual(json.loads(exported)['research_use']['task_workspace'],workspace)
        rows=list(csv.DictReader(io.StringIO(g.task_workspace_csv(packet['research_use']['task_workspace']))))
        self.assertEqual(rows[1]['Formal DOI'],'10.1000/external')
        self.assertEqual(rows[1]['Prediction time'],'At study entry')
        self.assertIn('10.1000/external',page)
        self.assertIn('Prediction time',md)
        invalid=copy.deepcopy(use);invalid['sources'][-1]['id']='external_source'
        with self.assertRaisesRegex(ValueError,'Unsafe research-use ID'):
            g.research_use_packet(invalid,self.studies)

    def test_reject_invalid_workspace_shape_identity_bounds_and_references(self):
        edits = [
            lambda w:w['columns'][1].update(id='study'),
            lambda w:w['columns'][0].update(id='../outside'),
            lambda w:w['columns'][0].update(id=''),
            lambda w:w['columns'][0].update(id='prediction time'),
            lambda w:w['columns'][0].update(id='formal/doi'),
            lambda w:w['columns'].extend([{'id':'extra-'+str(n),'label':'Extra'} for n in range(3)]),
            lambda w:w.update(columns=[]),
            lambda w:w.update(display_columns=[]),
            lambda w:w.update(display_columns=['missing']),
            lambda w:w.update(display_columns=['study','study']),
            lambda w:w.update(examples=[]),
            lambda w:w.update(examples=w['examples']*7),
            lambda w:w['examples'][0]['cells'].pop('notes'),
            lambda w:w['examples'][0]['cells'].update(unknown='Extra'),
            lambda w:w['examples'][1].update(source_ids=['missing']),
            lambda w:w['examples'][1].update(source_ids=['external-source','external-source']),
            lambda w:w['examples'][0]['cells'].update(notes='Tabbed\ttext'),
            lambda w:w['decisions'][0].update(source_ids=['missing']),
            lambda w:w['decisions'][0].update(rule=''),
            lambda w:w.update(unexpected='not in contract'),
        ]
        for index,edit in enumerate(edits):
            with self.subTest(case=index):
                use=self.with_workspace();edit(use['task_workspace'])
                with self.assertRaises(ValueError):g.research_use_packet(use,self.studies)

    def test_reject_spreadsheet_formulas_without_changing_numeric_values(self):
        for value in ['=1+1','+SUM(A1:A2)','@SUM(A1:A2)','-2+3','-CMD()']:
            with self.subTest(value=value):
                use=self.with_workspace();use['task_workspace']['examples'][0]['cells']['calibration']=value
                with self.assertRaises(ValueError):g.research_use_packet(use,self.studies)
                with self.assertRaises(ValueError):g.task_workspace_csv(use['task_workspace'])
        use=self.with_workspace();use['task_workspace']['columns'][0]['label']='=HYPERLINK(A1)'
        with self.assertRaises(ValueError):g.research_use_packet(use,self.studies)
        use=self.with_workspace();use['task_workspace']['examples'][0]['cells']['calibration']='-0.21'
        valid=g.research_use_packet(use,self.studies)
        self.assertIn('-0.21',g.task_workspace_csv(valid['task_workspace']))

    def test_static_outputs_generate_and_validate_in_isolated_directory(self):
        packet=self.packet(self.with_workspace())
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'research').mkdir()
            with patch.object(g,'load_comparisons',return_value=[{'slug':'workspace-regression'}]), \
                 patch.object(g,'comparison_packet',return_value=packet):
                self.assertEqual(g.build_comparisons(root),{self.url:True})
                self.assertEqual({p.name for p in (root/'research').iterdir()},
                                 {'workspace-regression.'+ext for ext in ['html','md','json','worksheet.csv','blank.csv']})
                self.assertEqual(g.build_comparisons(root),{self.url:False})
                g.build_comparisons(root,validate_only=True)
                worksheet=root/'research/workspace-regression.worksheet.csv'
                worksheet.write_bytes(worksheet.read_bytes()+b'tampered\n')
                with self.assertRaisesRegex(ValueError,'worksheet.csv'):g.build_comparisons(root,validate_only=True)
                g.build_comparisons(root)
                blank=root/'research/workspace-regression.blank.csv';blank.write_bytes(b'tampered\n')
                with self.assertRaisesRegex(ValueError,'blank.csv'):g.build_comparisons(root,validate_only=True)

    def test_no_csv_outputs_for_legacy_nonworkspace_packet(self):
        packet=self.packet(self.use)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'research').mkdir()
            with patch.object(g,'load_comparisons',return_value=[{'slug':'workspace-regression'}]), \
                 patch.object(g,'comparison_packet',return_value=packet):
                g.build_comparisons(root)
                self.assertEqual({p.suffix for p in (root/'research').iterdir()},{'.html','.md','.json'})
                g.build_comparisons(root,validate_only=True)


if __name__ == '__main__': unittest.main()
