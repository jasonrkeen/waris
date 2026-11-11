from pathlib import Path
from copy import deepcopy
from dataclasses import replace
import csv,hashlib,json,shutil,tempfile,unittest
from presentation_core import load_snapshot,validate_rows,metrics,world_bank_display

ROOT=Path(__file__).resolve().parents[1]

class PresentationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.snapshot=load_snapshot(ROOT)
    def test_valid_snapshot_and_source_counts(self):
        m=metrics(self.snapshot);self.assertEqual(m['synthetic_rows'],150);self.assertEqual(m['GRP_regions'],25);self.assertEqual(m['historical_completed_analyst_dispositions'],0)
    def test_score_sensitivity_key_join_not_position(self):
        rows=deepcopy(self.snapshot.rows);rows['monte_carlo'].reverse();validate_rows(rows,self.snapshot.metadata)
        self.assertEqual(metrics(replace(self.snapshot,rows=rows)),metrics(self.snapshot))
    def test_misaligned_sensitivity_base_rejected(self):
        rows=deepcopy(self.snapshot.rows);rows['monte_carlo'][0]['waris_aml_review_score']='10'
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_GRP_scoring_flag_rejected(self):
        rows=deepcopy(self.snapshot.rows);rows['grp'][0]['used_in_scoring']='True'
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_FIU_total_not_treated_as_category(self):
        rows=deepcopy(self.snapshot.rows);next(r for r in rows['sfms'] if r['row_role']!='category')['row_role']='category'
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_SFMS_bad_total_rejected(self):
        rows=deepcopy(self.snapshot.rows);rows['sfms'][-1]['referral_documents']='1'
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_repeated_SFMS_label_cannot_be_deduplicated(self):
        rows=deepcopy(self.snapshot.rows);rows['sfms']=[r for r in rows['sfms'] if r['source_row']!='8']
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_unverified_theme_rejected(self):
        rows=deepcopy(self.snapshot.rows);rows['literature'][0]['typology_id']='WAML-006'
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_missing_World_Bank_value_cannot_be_zero(self):
        rows=deepcopy(self.snapshot.rows);next(r for r in rows['world_bank'] if r['value']=='')['value']='0'
        with self.assertRaises(ValueError):validate_rows(rows,self.snapshot.metadata)
    def test_verification_cannot_be_upgraded(self):
        meta=deepcopy(self.snapshot.metadata);meta['sfms_receipt']['annual_report_2023_verified']=True
        with self.assertRaises(ValueError):validate_rows(self.snapshot.rows,meta)
    def test_rehashed_input_does_not_override_parent(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for r in self.snapshot.contract['inputs'].values():
                p=root/r['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/r['path'],p)
            (root/'presentation').mkdir();(root/'provenance').mkdir()
            shutil.copy2(ROOT/'provenance/parent_ASSEMBLY_MANIFEST.json',root/'provenance/parent_ASSEMBLY_MANIFEST.json')
            contract=deepcopy(self.snapshot.contract);entry=contract['inputs']['synthetic'];p=root/entry['path'];p.write_bytes(p.read_bytes()+b'\n');entry['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            (root/'presentation/data_contract.json').write_text(json.dumps(contract))
            with self.assertRaises(ValueError):load_snapshot(root)
    def test_chart_scatter_keeps_region_sector_alignment(self):
        with (ROOT/'presentation/outputs/charts/assumed_sensitivity.csv').open(encoding='utf8') as f:plotted=list(csv.DictReader(f))
        scores={(r['oblast'],r['sector']):float(r['waris_aml_review_score']) for r in self.snapshot.rows['synthetic']}
        self.assertEqual(len(plotted),150)
        for r in plotted:self.assertAlmostEqual(float(r['synthetic_base_score']),scores[(r['region'],r['sector'])],places=10)
    def test_histogram_support_and_labels(self):
        with (ROOT/'presentation/outputs/charts/synthetic_score_distribution.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
        self.assertEqual(sum(int(r['synthetic_rows']) for r in rows),150);self.assertTrue(all(r['data_mode']=='synthetic_only' for r in rows))
    def test_currency_display_units_are_explicit(self):
        display=world_bank_display(metrics(self.snapshot));self.assertEqual(len(display),4)
        self.assertEqual(sum(r['Unit']=='billion current US$' for r in display),3);self.assertEqual(sum(r['Unit']=='% of GDP' for r in display),1)
    def test_presentation_manifest_is_bound_to_shared_contract(self):
        output=json.loads((ROOT/'presentation/outputs/presentation_manifest.json').read_text())
        self.assertEqual(output['contract_sha256'],hashlib.sha256((ROOT/'presentation/data_contract.json').read_bytes()).hexdigest())
        self.assertEqual(output['input_hashes'],{k:v['sha256'] for k,v in self.snapshot.contract['inputs'].items()})

if __name__=='__main__':unittest.main()
