"""One checked, allowlisted snapshot for controlled rc13 PDF/dashboard outputs."""
from pathlib import Path
from dataclasses import dataclass
from decimal import Decimal
import csv,hashlib,json,math

ALLOWED_THEMES={'WAML-001','WAML-002','WAML-003','WAML-004','WAML-005','WAML-010'}
PARENT_MANIFEST_SHA256='e3261931e6a29f85ca2e32a4d1b731117bebc56d6963319d77b95ffd65827932'
SOURCES={
 'synthetic':('examples/synthetic/waris_scored_oblast_sector.csv','synthetic_model_output','25 regions x 6 sectors; no empirical observation period'),
 'monte_carlo':('examples/synthetic/waris_monte_carlo_results.csv','synthetic_sensitivity','5000 assumed perturbation draws per row; no empirical probabilities'),
 'grp':('components/C04/grp/ukrstat_GRP_2021_benchmark_2026-10-18.csv','official_benchmark','2021 annual GRP; million UAH; 25 selected regions'),
 'procurement_observed':('components/C03/procurement/procurement_observed_summary.csv','review_only_observed_objects','20 October 2026 recorded API frame; two distinct procedure/unit domains'),
 'procurement_weighted':('components/C03/procurement/procurement_frame_weighted_estimates.csv','review_only_finite_frame_estimates','Same recorded frame; N/n cluster expansion, not national estimates'),
 'world_bank':('components/C04/world_bank/world_bank_national_context_2026-10-18.csv','national_context','Ukraine; four indicators, 1991-2024 slots; snapshot 18 October 2026'),
 'sfms':('components/C10/reviewed/sfms_q1_2026_selected_facts.csv','national_context','2026 Q1 referral documents/associated amounts; source-reported, text-only verification'),
 'literature':('components/C04/literature/waris_wartime_aml_typology_register.csv','conceptual_reference','Six selected attributed Utenkova themes; project mappings are interpretations'),
 'literature_pages':('reader/literature/conceptual_page_crosswalk_six_themes.csv','conceptual_reference','Printed-page crosswalk for six permitted themes only'),
 'controls':('components/C10/reviewed/qualified_operational_recount.json','historical_declarations','Historical workflow counts, not completed reviews or effectiveness'),
 'sfms_receipt':('components/C10/reviewed/sfms_verification_receipt.json','dated_verification_limit','Retained 22 October source-text check; no local PDF custody/visual verification'),
 'boundaries':('SOURCE_BOUNDARIES.json','methodology_policy','GRP benchmark-only; unverified FIU claims excluded; acquisition gated'),
}

@dataclass(frozen=True)
class Snapshot:
    root: Path
    contract: dict
    rows: dict[str,list[dict[str,str]]]
    metadata: dict[str,dict]

def digest(path: Path) -> str:return hashlib.sha256(path.read_bytes()).hexdigest()

def write_contract(root: Path) -> Path:
    parent=json.loads((root/'provenance/parent_ASSEMBLY_MANIFEST.json').read_text())
    inputs={}
    for key,(rel,kind,period) in SOURCES.items():
        path=root/rel;info=parent['files'][rel]
        if digest(path)!=info['sha256']:raise ValueError('Source differs from frozen assembled parent')
        inputs[key]={'path':rel,'sha256':info['sha256'],'source_class':kind,'scope_period':period}
    obj={'schema':'WARIS-controlled-presentation-1','build_id':'WARIS-rc13-controlled-report-dashboard-1','date_local':'2026-10-25','parent_candidate_sha256':'6df4c8c3ca5dbd19afce8ab1acdd61baeb593f3943ed60e9dfffb6b54f481272','model_version':'0.12.0','code_baseline':'0.12.0-rc13-methodology-review','inputs':inputs,'GRP':'benchmark_only','unverified_FIU_claims':'excluded','model_data_mode':'synthetic_only','publication':False}
    path=root/'presentation/data_contract.json';path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8');return path

def load_snapshot(root: Path) -> Snapshot:
    root=root.resolve();contract=json.loads((root/'presentation/data_contract.json').read_text())
    parent_path=root/'provenance/parent_ASSEMBLY_MANIFEST.json'
    if digest(parent_path)!=PARENT_MANIFEST_SHA256:raise ValueError('Frozen parent inventory changed')
    parent=json.loads(parent_path.read_text())
    if set(contract['inputs'])!=set(SOURCES) or contract['GRP']!='benchmark_only' or contract['unverified_FIU_claims']!='excluded' or contract['model_data_mode']!='synthetic_only' or contract['publication']:
        raise ValueError('Unapproved presentation source/policy')
    rows={};meta={}
    for key,(rel,kind,period) in SOURCES.items():
        entry=contract['inputs'][key]
        if entry['path']!=rel or entry['source_class']!=kind or entry['sha256']!=parent['files'][rel]['sha256']:raise ValueError('Unapproved presentation path, class or parent hash')
        path=(root/rel).resolve()
        if not path.is_relative_to(root) or digest(path)!=entry['sha256']:raise ValueError('Frozen presentation source hash mismatch')
        if path.suffix=='.csv':
            with path.open(encoding='utf-8-sig',newline='') as handle:rows[key]=list(csv.DictReader(handle))
        else:meta[key]=json.loads(path.read_text())
    validate_rows(rows,meta)
    return Snapshot(root,contract,rows,meta)

def validate_rows(rows: dict, meta: dict) -> None:
    bounds=meta['boundaries']
    if bounds['official_GRP']!='benchmark_only' or bounds['unverified_FIU_claims']!='excluded':raise ValueError('Source boundary violation')
    for key in ('synthetic','monte_carlo'):
        table=rows[key]
        if len(table)!=150 or len({(r['oblast'],r['sector']) for r in table})!=150:raise ValueError('Model support/identity mismatch')
        if len({r['oblast'] for r in table})!=25 or len({r['sector'] for r in table})!=6:raise ValueError('Model universe mismatch')
        if any(r['data_mode']!='synthetic_only' for r in table):raise ValueError('Non-synthetic score input prohibited')
        for r in table:
            if not math.isfinite(float(r['waris_aml_review_score'])) or not 0<=float(r['waris_aml_review_score'])<=100:raise ValueError('Invalid score')
            for flag in ('official_baseline_used_in_scoring','official_baseline_used_in_monte_carlo','expanded_prozorro_used_in_scoring','expanded_prozorro_used_in_monte_carlo','fiu_context_used_in_scoring','fiu_context_used_in_monte_carlo'):
                if flag in r and r[flag]!='False':raise ValueError('Protected source promoted into model')
    if {(r['oblast'],r['sector']) for r in rows['synthetic']}!={(r['oblast'],r['sector']) for r in rows['monte_carlo']}:raise ValueError('Score/sensitivity identity mismatch')
    score_by_key={(r['oblast'],r['sector']):float(r['waris_aml_review_score']) for r in rows['synthetic']}
    for r in rows['monte_carlo']:
        if not math.isclose(float(r['waris_aml_review_score']),score_by_key[(r['oblast'],r['sector'])],abs_tol=1e-12):raise ValueError('Sensitivity base score misaligned')
        lo,mean,hi=[float(r[k]) for k in ('mc_p05_score','mc_mean_score','mc_p95_score')]
        if not all(math.isfinite(v) for v in (lo,mean,hi)) or not 0<=lo<=mean<=hi<=100:raise ValueError('Invalid assumed percentile interval')
    grp=rows['grp']
    if len(grp)!=25 or len({r['region_code'] for r in grp})!=25:raise ValueError('GRP universe mismatch')
    if any(r['period']!='2021' or r['unit_code']!='1090' or r['scale_code']!='6' or r['used_in_scoring']!='False' or r['used_in_monte_carlo']!='False' for r in grp):raise ValueError('GRP unit/time/use mismatch')
    obs=rows['procurement_observed'];weighted=rows['procurement_weighted']
    if len(obs)!=2 or len(weighted)!=2:raise ValueError('Procurement domains changed')
    for a,b in zip(obs,weighted):
        if (a['procedure'],a['unit_type'])!=(b['procedure'],b['unit_type']) or a['used_in_scoring']!='False' or b['used_in_scoring']!='False':raise ValueError('Procurement boundary violation')
        den=Decimal(a['observed_eligible_units']);num=Decimal(a['observed_exactly_one_active_object_units']);w=Decimal(a['domain_frame_tenders'])/Decimal(a['sampled_tenders'])
        if abs(num/den-Decimal(a['active_object_share']))>Decimal('0.000000001') or num*w!=Decimal(b['HT_exactly_one_active_object_total']) or den*w!=Decimal(b['HT_eligible_unit_total']):raise ValueError('Procurement arithmetic mismatch')
    if len(rows['sfms'])!=10 or any(r['context_only']!='True' or r['used_in_scoring']!='False' or r['used_in_monte_carlo']!='False' for r in rows['sfms']):raise ValueError('SFMS use/scope violation')
    categories=[r for r in rows['sfms'] if r['row_role']=='category'];totals=[r for r in rows['sfms'] if r['row_role']=='published_total_do_not_add']
    if len(categories)!=9 or len(totals)!=1:raise ValueError('SFMS row-role mismatch')
    for field in ('referral_documents','source_reported_associated_funds_million_UAH'):
        if sum(Decimal(r[field]) for r in categories)!=Decimal(totals[0][field]):raise ValueError('SFMS category/total mismatch')
    bypos={r['source_row']:r for r in categories}
    if bypos['3']['category_as_published']!=bypos['8']['category_as_published']:raise ValueError('SFMS repeated labels lost')
    receipt=meta['sfms_receipt']
    if receipt['annual_report_2023_verified'] or receipt['local_PDF_byte_custody'] or receipt['visual_layout_verified']:raise ValueError('Unapproved SFMS verification upgrade')
    for key,field in (('literature','typology_id'),('literature_pages','waris_id')):
        if len(rows[key])!=6 or {r[field] for r in rows[key]}!=ALLOWED_THEMES:raise ValueError('Withheld theme restored')
    wb=rows['world_bank']
    if len(wb)!=136 or len({r['indicator_code'] for r in wb})!=4 or any((r['value']=='')!=(r['value_status']=='missing_not_imputed') for r in wb):raise ValueError('World Bank missingness/snapshot scope mismatch')

def metrics(snapshot: Snapshot) -> dict:
    scores=[float(r['waris_aml_review_score']) for r in snapshot.rows['synthetic']]
    widths=[float(r['mc_p95_score'])-float(r['mc_p05_score']) for r in snapshot.rows['monte_carlo']]
    latest=[]
    for code in sorted({r['indicator_code'] for r in snapshot.rows['world_bank']}):
        allrows=[r for r in snapshot.rows['world_bank'] if r['indicator_code']==code]
        numeric=[r for r in allrows if r['value']!='']
        last=max(numeric,key=lambda r:int(r['year']))
        latest.append({**last,'missing_slots':sum(r['value']=='' for r in allrows)})
    total=next(r for r in snapshot.rows['sfms'] if r['row_role']=='published_total_do_not_add')
    return {'synthetic_rows':len(scores),'synthetic_mean_score':sum(scores)/len(scores),'synthetic_min_score':min(scores),'synthetic_max_score':max(scores),'mean_assumed_p05_p95_width':sum(widths)/len(widths),'WB_latest_available_in_snapshot':latest,'SFMS_published_total':total,'GRP_regions':len(snapshot.rows['grp']),'permitted_literature_themes':6,'historical_completed_analyst_dispositions':snapshot.metadata['controls']['nonblank_dispositions']}

def world_bank_display(m: dict) -> list[dict]:
    result=[]
    for r in m['WB_latest_available_in_snapshot']:
        money=r['unit']=='current_USD'
        result.append({'Indicator':r['indicator_name'],'Source year':r['year'],'Value':f"{float(r['value'])/(1e9 if money else 1):.2f}",'Unit':'billion current US$' if money else '% of GDP','Missing slots':r['missing_slots']})
    return result
