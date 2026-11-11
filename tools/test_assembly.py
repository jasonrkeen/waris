from pathlib import Path
import hashlib,json,shutil,tempfile,unittest
from validate_assembly import validate
from check_controlled_release import prepare_clean_tree

ROOT=Path(__file__).resolve().parents[1]

class AssemblyChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'candidate';shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__'))
    def reseal(self,rel):
        p=self.root/rel;m=json.loads((self.root/'ASSEMBLY_MANIFEST.json').read_text())
        m['files'][rel]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        (self.root/'ASSEMBLY_MANIFEST.json').write_text(json.dumps(m))
    def test_exact_materialisation(self):
        result=validate(self.root);self.assertEqual(result['selected_component_files'],317);self.assertEqual(result['unchanged_runtime_files'],108);self.assertEqual(result['git_attribute_packaging_overrides'],2)
    def test_missing_companion_rejected(self):
        (self.root/'plan/companions/C03.md').unlink()
        with self.assertRaises(ValueError):validate(self.root)
    def test_extra_provider_input_rejected(self):
        (self.root/'unreviewed_provider.csv').write_text('x\n1\n')
        with self.assertRaises(ValueError):validate(self.root)
    def test_runtime_mutation_even_after_reseal(self):
        p=self.root/'runtime/main.py';p.write_bytes(p.read_bytes()+b'\n# drift\n');self.reseal('runtime/main.py')
        with self.assertRaises(ValueError):validate(self.root)
    def test_restored_ten_row_reader_crosswalk_rejected(self):
        rel='components/C04/docs/typology_conceptual_page_crosswalk.csv';p=self.root/rel;p.parent.mkdir(exist_ok=True);p.write_text('waris_id\nWAML-006\n');self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_benchmark_scoring_promotion_rejected(self):
        p=self.root/'SOURCE_BOUNDARIES.json';x=json.loads(p.read_text());x['official_GRP']='scoring';p.write_text(json.dumps(x));self.reseal('SOURCE_BOUNDARIES.json')
        with self.assertRaises(ValueError):validate(self.root)
    def test_example_missing_synthetic_label_rejected(self):
        rel='examples/synthetic/synthetic_inputs.csv';p=self.root/rel;p.write_text(p.read_text().replace('synthetic_only','observed'));self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_extra_code_override_even_after_reseal_rejected(self):
        rel='GIT_METADATA_OVERRIDES.json';p=self.root/rel;x=json.loads(p.read_text());x['overrides']['runtime/main.py']=x['overrides']['runtime/.gitattributes'];p.write_text(json.dumps(x));self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_git_replacement_mutation_even_after_reseal_rejected(self):
        rel='runtime/.gitattributes';(self.root/rel).write_bytes(b'* text=auto\n');self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_git_original_mutation_even_after_reseal_rejected(self):
        rel='provenance/git_attributes/runtime.original.gitattributes';p=self.root/rel;p.write_bytes(p.read_bytes()+b'\n');self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_missing_git_override_ledger_rejected(self):
        (self.root/'GIT_METADATA_OVERRIDES.json').unlink()
        with self.assertRaises(ValueError):validate(self.root)
    def test_archival_code_mutation_even_after_reseal_rejected(self):
        rel='components/C11/main.py';p=self.root/rel;p.write_bytes(p.read_bytes()+b'\n# drift\n');self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_git_original_path_traversal_rejected(self):
        rel='GIT_METADATA_OVERRIDES.json';p=self.root/rel;x=json.loads(p.read_text());x['overrides']['runtime/.gitattributes']['archived_original']='../outside';p.write_text(json.dumps(x));self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_distribution_provenance_mutation_even_after_reseal_rejected(self):
        rel='DISTRIBUTION_MEMBER_LIST.csv';p=self.root/rel;p.write_text(p.read_text().replace('unchanged','git_metadata_only',1));self.reseal(rel)
        with self.assertRaises(ValueError):validate(self.root)
    def test_local_git_worktree_metadata_is_not_distribution_input(self):
        path=self.root/'.git';path.mkdir();(path/'HEAD').write_text('ref: refs/heads/local-check\n')
        self.assertEqual(validate(self.root)['git_attribute_packaging_overrides'],2)
    def test_documented_local_environment_is_not_distribution_input(self):
        path=self.root/'.venv';path.mkdir();(path/'pyvenv.cfg').write_text('local test environment\n')
        self.assertEqual(validate(self.root)['git_attribute_packaging_overrides'],2)
    def test_clean_checker_snapshot_excludes_local_tools(self):
        for name in ('.git','.venv'):
            path=self.root/name;path.mkdir();(path/'local-marker').write_text('local test metadata\n')
        clean=prepare_clean_tree(self.root,Path(self.tmp.name)/'clean')
        self.assertFalse((clean/'.git').exists());self.assertFalse((clean/'.venv').exists())
        self.assertEqual(validate(clean)['selected_component_files'],317)
    def test_clean_checker_snapshot_rejects_unreviewed_input(self):
        (self.root/'unreviewed.csv').write_text('x\n1\n')
        with self.assertRaises(ValueError):prepare_clean_tree(self.root,Path(self.tmp.name)/'clean')

if __name__=='__main__':unittest.main()
