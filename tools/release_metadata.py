"""Validate the explicitly unpublished assembled-root metadata and local links."""
from pathlib import Path
import hashlib,json,re
from urllib.parse import unquote

READER_DOCS=('README.md','SECURITY.md','CONTRIBUTING.md','MODEL_CARD.md','DATA_POLICY.md','THIRD_PARTY_NOTICES.md','RELEASE_NOTES.md','PUBLICATION_STATUS.md','GIT_DISTRIBUTION.md')
TITLE='WARIS Ukraine Wartime AML Revenue Integrity Scoring Model: controlled research package'
def citation_text(scope:dict)->str:
    return '\n'.join(['cff-version: 1.2.0','message: '+json.dumps('Unpublished controlled rc13 candidate. Cite this exact candidate version together with the external archive SHA-256 and source limitations; no public release date or repository URL is claimed.'),'title: '+json.dumps(TITLE),'type: software','authors:','  - family-names: Keen','    given-names: Jason','version: '+json.dumps(scope['citation_version']),'license: MIT','abstract: '+json.dumps('A reproducible synthetic AML research architecture with separate official GRP benchmarks, descriptive procurement research, national context and conceptual literature. GRP is benchmark-only; unverified FIU claims are excluded. This package is not an empirically validated AML decision system.')])+'\n'

def validate_release_metadata(root:Path)->dict:
    root=root.resolve();scope=json.loads((root/'RELEASE_SCOPE.json').read_text(encoding='utf8'));manifest=json.loads((root/'ASSEMBLY_MANIFEST.json').read_text(encoding='utf8'))
    if scope['schema']!='WARIS-release-scope-1' or scope['candidate']!=manifest['candidate'] or scope['candidate']!='WARIS-v'+scope['citation_version'] or not re.fullmatch(r'0\.12\.0-rc13-release-review-[1-9][0-9]*',scope['citation_version']):raise ValueError('Release/citation identity mismatch')
    expected={'model_version':'0.12.0','code_baseline':'0.12.0-rc13-methodology-review','presentation_build_id':'WARIS-rc13-controlled-report-dashboard-1','package_status':'unpublished_candidate','publication_authorized':False,'published':False,'author':{'family_names':'Keen','given_names':'Jason'},'code_license':'MIT','model_data_mode':'synthetic_only','official_GRP':'benchmark_only','unverified_FIU_claims':'excluded','full_live_pipeline':'gated_before_credentials_or_provider_access','selected_components':11,'selected_component_members':317,'remote_CI_executed':False,'empirical_AML_validation_claimed':False,'source_permission_upgrade_claimed':False}
    if any(scope[k]!=value for k,value in expected.items()):raise ValueError('Unapproved release scope or claim')
    if any(scope[key] is not None for key in ('public_release_date','repository_url','release_tag','doi')):raise ValueError('Unverified public identifier/date supplied')
    if scope['security_reporting']!={'selected_route':'github_private_vulnerability_reporting','configured':False,'verified_endpoint':None,'setup_requires_separate_repository_authorization':True}:raise ValueError('Unverified security reporting status')
    if scope['historical_ledger']!={'scoped_eligible_entries':23,'unique_included_historical_files':20,'aliases':3,'excluded_entries':152,'held_entries':0}:raise ValueError('Historical disposition drift')
    if hashlib.sha256((root/'SOURCE_BOUNDARIES.json').read_bytes()).hexdigest()!=scope['source_boundaries_sha256']:raise ValueError('Source policy drift')
    if (root/'CITATION.cff').read_text(encoding='utf8')!=citation_text(scope):raise ValueError('Citation fields differ from approved scope')
    links=0
    for rel in READER_DOCS:
        text=(root/rel).read_text(encoding='utf8')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
            if target.startswith(('https://','http://','#')):continue
            path=(root/Path(rel).parent/unquote(target.split('#')[0])).resolve()
            if not path.is_relative_to(root) or not path.is_file():raise ValueError('Broken or unsafe current reader link')
            links+=1
    return {'citation_version':scope['citation_version'],'current_reader_internal_links_checked':links,'public_release_claimed':False,'security_reporting_selected':'github_private_vulnerability_reporting','security_reporting_configured':False,'source_policy_preserved':True}
