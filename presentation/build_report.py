"""Deterministic, allowlisted controlled rc13 research presentation build."""
from pathlib import Path
import argparse,csv,hashlib,json,sys
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
sys.path.insert(0,str(Path(__file__).resolve().parent))
from presentation_core import load_snapshot,metrics,write_contract,digest,world_bank_display

ROOT=Path(__file__).resolve().parents[1]
BLUE='#24556B';GRAY='#53616B'

def build(output: Path) -> dict:
    snapshot=load_snapshot(ROOT);m=metrics(snapshot)
    if output.exists():raise ValueError('Refusing to overwrite existing presentation build')
    output.mkdir(parents=True);charts=output/'charts';charts.mkdir()
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    scores=[float(r['waris_aml_review_score']) for r in snapshot.rows['synthetic']]
    def csv_table(name: str,rows: list[dict]) -> None:
        with (charts/name).open('w',encoding='utf8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    counts,edges=np.histogram(scores,bins=list(range(0,101,10)))
    csv_table('synthetic_score_distribution.csv',[{'score_bin_lower':int(edges[i]),'score_bin_upper':int(edges[i+1]),'synthetic_rows':int(v),'data_mode':'synthetic_only'} for i,v in enumerate(counts)])
    fig,ax=plt.subplots(figsize=(8,3.5));ax.hist(scores,bins=list(range(0,101,10)),color=BLUE,edgecolor='white');ax.set(xlim=(0,100),xlabel='Illustrative WARIS score (0-100)',ylabel='Synthetic region-sector rows',title='Synthetic score distribution | 150 generated rows');fig.tight_layout();fig.savefig(charts/'synthetic_score_distribution.png',dpi=180);plt.close(fig)
    mc=snapshot.rows['monte_carlo'];widths=[float(r['mc_p95_score'])-float(r['mc_p05_score']) for r in mc]
    csv_table('assumed_sensitivity.csv',[{'region':r['oblast'],'sector':r['sector'],'synthetic_base_score':r['waris_aml_review_score'],'assumed_draw_p05':r['mc_p05_score'],'assumed_draw_p95':r['mc_p95_score'],'assumed_draw_p95_p05_width':float(r['mc_p95_score'])-float(r['mc_p05_score']),'data_mode':'synthetic_only'} for r in mc])
    fig,ax=plt.subplots(figsize=(8,3.5));ax.scatter([float(r['waris_aml_review_score']) for r in mc],widths,s=18,color=BLUE,alpha=.7);ax.set(xlabel='Synthetic base score (0-100)',ylabel='Assumed-draw p95-p05 width (score points)',title='Sensitivity to assumed perturbations | not empirical uncertainty');fig.tight_layout();fig.savefig(charts/'assumed_sensitivity.png',dpi=180);plt.close(fig)
    grp=sorted(snapshot.rows['grp'],key=lambda r:float(r['value_million_UAH']))
    csv_table('GRP_2021_benchmark.csv',[{'region_code':r['region_code'],'source_region_label':r['geography_label_from_retained_export'],'year':'2021','GRP_billion_UAH':float(r['value_million_UAH'])/1000,'use_scope':'benchmark_only'} for r in grp])
    fig,ax=plt.subplots(figsize=(8,6));ax.barh([r['geography_label_from_retained_export'] for r in grp],[float(r['value_million_UAH'])/1000 for r in grp],color=BLUE);ax.tick_params(axis='y',labelsize=9);ax.set(xlabel='Official 2021 GRP (billion UAH)',title='2021 regional GRP | benchmark-only, not a risk ranking');fig.tight_layout();fig.savefig(charts/'GRP_2021_benchmark.png',dpi=180);plt.close(fig)

    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyW',fontName='Helvetica',fontSize=10.1,leading=14.1,spaceAfter=8,textColor=colors.HexColor('#182A35')))
    styles.add(ParagraphStyle(name='SmallW',fontName='Helvetica',fontSize=8.1,leading=10.6,spaceAfter=6,textColor=colors.HexColor(GRAY)))
    styles.add(ParagraphStyle(name='TitleW',fontName='Helvetica-Bold',fontSize=29,leading=34,textColor=colors.HexColor(BLUE),spaceAfter=14))
    styles.add(ParagraphStyle(name='HeadW',fontName='Helvetica-Bold',fontSize=17,leading=21,textColor=colors.HexColor(BLUE),spaceAfter=12))
    styles.add(ParagraphStyle(name='SubW',fontName='Helvetica-Bold',fontSize=11.5,leading=15,spaceAfter=8))
    story=[]
    def p(text: str,style: str='BodyW') -> Paragraph:return Paragraph(text,styles[style])
    def add(text: str,style: str='BodyW') -> None:story.append(p(text,style))
    def page(title: str) -> None:
        if story:story.append(PageBreak())
        add(title,'HeadW')
    def table(headers: list[str],rows: list[list],widths: list[float],small: bool=False) -> None:
        style='SmallW' if small else 'BodyW'
        cells=[[p(escape(str(v)),'SmallW') for v in headers]]+[[p(escape(str(v)),style) for v in row] for row in rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor(BLUE)),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#DCE3E6')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t);story.append(Spacer(1,9))
    def image(name: str,width: float,height: float) -> None:story.append(Image(str(charts/name),width=width,height=height));story.append(Spacer(1,8))
    add('WARIS','TitleW');add('Controlled research report','HeadW');add('rc13 selected-snapshot presentation | 25 October 2026','SubW')
    add('<b>Local, unpublished review.</b> This report presents a reproducible synthetic scoring architecture alongside separate, attributed research evidence. It is not an empirical measurement of money laundering, an accusation tool or operational validation.')
    add('The full research package remains subject to final readiness gates. No provider collection, scoring integration, publication or push occurred in this build.')
    table(['Material','Evidence and permitted use'],[['WARIS results','150 wholly synthetic region-sector rows; assumed-model sensitivity'],['Ukrstat GRP','Official 2021 regional benchmark only; no score or sector allocation'],['Prozorro','Two descriptive procedure/unit domains in a bounded recorded frame'],['World Bank / SFMS','Dated national context only; no regional or sector allocation'],['Literature','Six selected conceptual themes; no validated numerical indicators'],['Workflow controls','Historical declarations; no measured effectiveness']],[115,390])
    add('<b>Central boundaries:</b> GRP remains benchmark-only. Unverified FIU annual/mixed claims remain excluded. The retired ACLED proxy/blend and numeric confidence averaging are not restored.')
    add('Build ID: '+snapshot.contract['build_id'],'SmallW')
    add('Model version 0.12.0; unchanged code baseline rc13-methodology-review. Parent assembled candidate SHA-256: '+snapshot.contract['parent_candidate_sha256'],'SmallW')
    add('The PDF and controlled dashboard read the same hash-locked, allowlisted data contract. Source notes, receipts, full selected tables and methods travel in the companion candidate.','SmallW')

    page('1 | Synthetic scoring illustration')
    add('Every numeric input in the 25-region x six-sector demonstration is generated. Real geographic and sector names do not convert the illustration into observed data. The seven inherited layers, weights and thresholds are research assumptions; regional patterns can be built into the generator.')
    image('synthetic_score_distribution.png',505,221)
    table(['Generated metric','Value'],[['Region-sector rows',150],['Mean illustrative score',f"{m['synthetic_mean_score']:.2f}"],['Range of illustrative scores',f"{m['synthetic_min_score']:.2f} to {m['synthetic_max_score']:.2f}"],['Random seed / Monte Carlo draws','42 / 5000 per row']],[270,235])
    add('These are relative model outputs, not probabilities of wrongdoing or grounds for adverse action. Sample-relative transformations mean rankings may change if the reference population changes. No official GRP, expanded procurement, literature or FIU input contributes to these synthetic scores.')
    add('Source: unchanged rc13 seeded generator and five labelled synthetic example CSVs. The dashboard allows inspection and filtered export of the same rows; exports retain data_mode=synthetic_only.','SmallW')

    page('2 | Assumed-model sensitivity')
    add('Monte Carlo perturbations examine the behavior of the prototype under configured assumptions. Their frequencies and percentiles are conditional simulation summaries, not empirically calibrated confidence intervals, forecasts or probabilities of money laundering.')
    image('assumed_sensitivity.png',505,221)
    add(f"The mean width between the assumed-draw 5th and 95th percentiles is <b>{m['mean_assumed_p05_p95_width']:.2f} score points</b> across the 150 synthetic rows. This describes the selected perturbation design only.")
    add('The illustration does not establish construct validity, predictive performance, fairness, a false-positive rate or external robustness. Qualitative confidence declarations remain categorical; no numerical confidence-adjusted priority is implemented.')
    add('Source: rc13 Monte Carlo output, seed 42, 5000 draws per row. The controlled dashboard exposes base score and assumed-draw p05/mean/p95 with the same source-boundary warning.','SmallW')

    page('3 | Official 2021 GRP benchmark')
    image('GRP_2021_benchmark.png',505,379)
    add('Selected annual observations cover 24 oblasts plus Kyiv City. They are official regional-scale benchmarks, not current productive capacity or a risk ranking. Unit code 1090 is UAH and scale 6 is millions; the chart converts million UAH to billion UAH by dividing by 1000.')
    add('Study coverage is not all Ukrainian territories. Source territorial/series notes apply, and identifiers do not establish historical boundary equivalence. The overlapping national aggregate must not be added to regional values. No sector-economic allocation, score or Monte Carlo integration is approved.')
    add('Source: State Statistics Service of Ukraine, selected official responses retrieved 18 October 2026. <link href="https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_REGIONAL_ACCOUNTS%28~%29" color="#24556B">Ukrstat regional accounts</link>; <link href="https://creativecommons.org/licenses/by/4.0/" color="#24556B">CC BY 4.0</link> default basis retained from the dated selected-source review, subject to source-specific exceptions. Older original acquisition dates remain unrecovered.','SmallW')

    page('4 | Procurement: finite-frame description')
    add('The separately frozen study recorded 1000 first-observed API IDs across ten descending pages on 20 October 2026. It is a bounded, mutable operational frame, not a national or complete-period procurement population. Tender clusters, explicit lots and no-explicit-lots tenders retain different roles.')
    observed=snapshot.rows['procurement_observed'];weighted=snapshot.rows['procurement_weighted']
    table(['Procedure / unit','Frame N / sample n','Eligible units','Exactly one active object','Share'],[[r['procedure']+' / '+r['unit_type'],r['domain_frame_tenders']+' / '+r['sampled_tenders'],r['observed_eligible_units'],r['observed_exactly_one_active_object_units'],f"{float(r['active_object_share'])*100:.2f}%"] for r in observed],[150,80,75,115,85],True)
    add('Finite-frame expansion estimates','SubW')
    table(['Procedure','Weight N/n','Expanded eligible units','Expanded one-object units'],[[r['procedure'],r['cluster_weight_fraction'],r['HT_eligible_unit_total'],r['HT_exactly_one_active_object_total']] for r in weighted],[140,85,140,140],True)
    add('The priceQuotation expanded one-object total of 22.575 is an estimate, not an observed fractional tender/person count. aboveThreshold is a census only of that domain within this recorded frame. Procedures and unit types must not be pooled; no confidence interval or national prevalence is claimed.')
    add('The measure is exactly one visible active linked bid object, not unique firms, valid offers, winners, low competition or wrongdoing. Missing or ambiguous links/states remain unknown; suppliers do not substitute for bidders. Lifecycle/lot eligibility is fixed. This evidence is descriptive/review-only and cannot alter WARIS scores or Monte Carlo.')
    add('Source: <link href="https://public.api.openprocurement.org/api/2.5/tenders" color="#24556B">Prozorro public procurement API</link>; frozen methods C02 and separately reviewed projections C03. Public arithmetic replay does not recover private frame/detail snapshots or authenticate the original acquisition. Attribution and qualifying reuse scope retain their dated review; no blanket attachment/privacy clearance is asserted.','SmallW')

    page('5 | World Bank national context')
    add('The retained Ukraine snapshot contains four indicators across 136 annual slots for 1991-2024, retrieved 18 October 2026. Missing values remain missing. The table selects the latest numeric observation separately within each retained indicator, not a common current-year cross-section.')
    table(['Indicator','Source year','Value','Display unit','Missing slots'],[[r['Indicator'],r['Source year'],r['Value'],r['Unit'],r['Missing slots']] for r in world_bank_display(m)],[210,55,65,120,55],True)
    add('Display conversion only: currency indicators are divided by one billion and shown as billion current US dollars; the tax ratio remains percent of GDP. Original values and units are preserved in the selected source tables.','SmallW')
    add('Different units and source years are not combined, averaged or allocated to regions/sectors. These data provide national background, not actual oblast AML risk, observed model inputs or evidence of government/control effectiveness. The dashboard shows one indicator at a time as points, without interpolating missing years.')
    for r in m['WB_latest_available_in_snapshot']:
        add(escape(r['indicator_code'])+': <link href="'+escape(r['source_url'])+'" color="#24556B">World Bank indicator page</link>. Underlying-source credit: '+escape(r['underlying_provider_credit'])+'.','SmallW')
    add('Source: World Bank WDI and named underlying providers. Selected indicator pages were reviewed under CC BY 4.0; source/series license and retrieval metadata remain in each row and the receipt. This build performs no new live retrieval or permission determination.','SmallW')

    page('6 | SFMS: selected national referral context')
    add('The selected Q1 2026 source reports referral documents, including additional referrals, and associated amounts. These are not unique persons, convictions, proven offences or independently established criminal loss. National categories are not mapped to model layers, sectors or oblasts.')
    sfms=snapshot.rows['sfms']
    table(['Source row','Published category / role','Referral documents','Associated funds (million UAH)'],[[r['source_row'],r['category_as_published']+(' [published total; do not add]' if r['row_role']!='category' else ''),r['referral_documents'],r['source_reported_associated_funds_million_UAH']] for r in sfms],[48,275,82,100],True)
    add('Rows 3 and 8 deliberately retain the same published category label and distinct source positions. Do not group by label. The published total is not added to category rows. A zero associated amount does not establish absence of risk.','SmallW')
    add('<b>Verification limit:</b> the retained 22 October check verified extracted source text only. Direct local retrieval returned 403 HTML; local PDF-byte custody and visual layout were not established. This quarterly check does not verify the unavailable 2023 annual report. Unverified FIU annual/mixed claims remain excluded.','SmallW')
    add('Source: State Financial Monitoring Service of Ukraine, <link href="https://fiu.gov.ua/assets/userfiles/440/2026/ENG_I%20quarter_NABU.pdf" color="#24556B">official Q1 2026 NABU referral PDF, p. 1</link>. Selected attributed facts retain the dated default CC BY scope; no raw PDF is redistributed.','SmallW')

    page('7 | Six literature themes, not validated indicators')
    pages={r['waris_id']:r['printed_pages'] for r in snapshot.rows['literature_pages']}
    table(['ID / pages','Selected conceptual theme'],[[r['typology_id']+' / '+pages[r['typology_id']],r['typology_name']] for r in snapshot.rows['literature']],[120,385])
    add('The themes support a conceptual research taxonomy only. Proposed indicators, layer assignments and confidence declarations are WARIS interpretations; they are not numerical measurements validated by the paper. No author/publisher endorsement or institutional operational validation is implied.')
    add('Four themes dependent on unverified underlying SFMS examples remain withheld. The digital-asset description omits the unverified recruitment example. Reading a secondary paper does not independently verify its underlying FIU claims. No literature field enters scoring or Monte Carlo.')
    add('Source: Karina Utenkova (2026), <i>Anti-money laundering as an instrument of economic security: Wartime adaptation of AML/CFT frameworks in Ukraine</i>, printed pp. 78-91. <link href="https://doi.org/10.65237/2336-3630-2026-3(1)-4" color="#24556B">DOI 10.65237/2336-3630-2026-3(1)-4</link>; <link href="https://phes.com.ua/ojs/index.php/www/en/article/view/112" color="#24556B">publisher record</link>. Copyright 2026 CENTRAL EUROPEAN JOURNAL OF SCIENCE AND RESEARCH; CC BY 4.0 basis retained from the dated review.','SmallW')
    add('Changes: project English paraphrase/taxonomy, selection of six themes and explicit page crosswalk. Preserve attribution and adaptation notices alongside exports. MIT for owned code does not relicense source material.','SmallW')

    page('8 | Provenance, limitations and release gates')
    add('This controlled build reads twelve allowlisted files from the exact assembled rc13 candidate, checking source hashes, classes, periods, units, row identities and use flags before displaying data. Report and dashboard share the same contract and build ID. No provider collection or legacy cache import occurs.')
    table(['Boundary','Current status'],[['Model/data','Wholly synthetic scoring and assumed-model sensitivity'],['GRP','Benchmark-only; no scoring, Monte Carlo or validated sector allocation'],['ACLED','Acquisition gated; old scoring/blend retired; no new events used'],['Procurement','Descriptive/review-only; frozen frame and private-replay limits'],['FIU/SFMS','Selected national context only; unverified annual/mixed claims excluded'],['Confidence / controls','Categorical declarations; zero historical completed analyst dispositions'],['Publication','Local unpublished review; later explicit instruction required']],[125,380],True)
    add('The parent assembled candidate passed 381 engineering tests plus three subtests and two identical offline/public-arithmetic replays on 25 October. Those prior results do not constitute verification of this new PDF/dashboard; presentation checks are recorded separately in the delivered build audit.')
    add('Remaining limits include missing historical acquisition authentication, unbundled private raw snapshots, uncalibrated model constructs, no empirical outcome/fairness validation and no measured false-positive/control effectiveness. Current source/date/file agreement does not manufacture missing historical execution evidence.')
    add('The controlled presentation closes a selected-snapshot report/dashboard build path while preserving the legacy live gate. It is not a new empirical wartime acquisition or release authorisation. Final advisory/security/platform evidence and any required methodological review remain separate gates.')
    add('Reproduce locally: presentation/build_report.py writes a new output directory from presentation/data_contract.json. Dashboard: python -m streamlit run presentation/dashboard.py. Exact source/receipt paths and SHA-256 values are in the data contract; selected companions remain in C01-C11.','SmallW')
    add('Build ID: '+snapshot.contract['build_id']+' | Contract SHA-256: '+digest(ROOT/'presentation/data_contract.json'),'SmallW')

    pdf=output/'WARIS_Controlled_Research_Report_rc13.pdf'
    def footer(canvas,doc):
        canvas.setTitle('WARIS rc13 controlled research report');canvas.setAuthor('WARIS research project');canvas.setFont('Helvetica',7.2);canvas.setFillColor(colors.HexColor(GRAY));canvas.drawString(44,25,'Controlled review | Synthetic model illustration | GRP benchmark-only | Unpublished');canvas.drawRightString(A4[0]-44,25,str(doc.page))
    doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=42,bottomMargin=46,title='WARIS rc13 controlled research report',author='WARIS research project',pageCompression=1,invariant=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    bundle={'build_id':snapshot.contract['build_id'],'contract_sha256':digest(ROOT/'presentation/data_contract.json'),'parent_candidate_sha256':snapshot.contract['parent_candidate_sha256'],'input_hashes':{k:v['sha256'] for k,v in snapshot.contract['inputs'].items()},'metrics':m,'outputs':{p.relative_to(output).as_posix():{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(output.rglob('*')) if p.is_file()},'full_legacy_live_pipeline_executed':False,'GRP':'benchmark_only','unverified_FIU_claims':'excluded','published':False}
    (output/'presentation_manifest.json').write_text(json.dumps(bundle,indent=2)+'\n',encoding='utf8')
    return bundle

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--initialise-contract',action='store_true');args=parser.parse_args()
    if args.initialise_contract:write_contract(ROOT)
    result=build(args.output_dir.resolve());print(json.dumps({'build_id':result['build_id'],'outputs':result['outputs']},indent=2))
