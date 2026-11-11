"""Controlled selected-snapshot reader; never calls legacy cache/live loaders."""
from pathlib import Path
import sys
import pandas as pd
import altair as alt
import streamlit as st

sys.path.insert(0,str(Path(__file__).resolve().parent))
from presentation_core import load_snapshot,metrics,world_bank_display

ROOT=Path(__file__).resolve().parents[1]
st.set_page_config(page_title='WARIS controlled research review',layout='wide')
st.title('WARIS | Controlled research review')
st.caption('rc13 / model 0.12.0 | frozen selected sources | local unpublished review')
st.warning('Synthetic WARIS scores are model illustrations, not observed misconduct or operationally validated risk. GRP is benchmark-only. Unverified FIU claims are excluded.')
try:
    snapshot=load_snapshot(ROOT);m=metrics(snapshot)
except Exception:
    st.error('Snapshot validation failed. No research results are displayed. Restore the exact approved inputs and data contract.');st.stop()
section=st.sidebar.radio('Section',['Overview','Synthetic illustration','Official GRP benchmark','Procurement study','National context','Literature','Provenance'])
st.sidebar.caption('Source families remain separate. Filters affect only the synthetic illustration.')
pdf=ROOT/'presentation/outputs/WARIS_Controlled_Research_Report_rc13.pdf'
if pdf.is_file():st.sidebar.download_button('Download controlled report',pdf.read_bytes(),file_name=pdf.name,mime='application/pdf')
st.sidebar.caption('Build '+snapshot.contract['build_id'])

if section=='Overview':
    st.header('What this research package supports')
    st.write('A reproducible synthetic scoring architecture, separate official benchmarks and carefully bounded descriptive research. These sources are not merged into an empirical AML score.')
    a,b,c=st.columns(3);a.metric('Synthetic region-sector rows',m['synthetic_rows']);b.metric('2021 GRP benchmark regions',m['GRP_regions']);c.metric('Permitted literature themes',m['permitted_literature_themes'])
    scope=pd.DataFrame([['WARIS scores and sensitivity','Wholly synthetic','No inference about actual misconduct'],['Official GRP','2021 annual benchmark','No scoring or economic sector allocation'],['Procurement','Two procedure/unit domains','Recorded-frame description; not national prevalence'],['World Bank and SFMS','National context','No regional or sector allocation'],['Literature','Six conceptual themes','Project indicators are interpretations'],['Workflow controls','Historical declarations','No measured effectiveness']],columns=['Material','Evidence class','Boundary'])
    st.dataframe(scope,hide_index=True,alt='Source families and their permitted interpretation')
    st.info('The controlled report/dashboard build is separate from the gated legacy live pipeline. Missing historical acquisition evidence remains unresolved. Full public-release readiness is not established by this presentation.')
elif section=='Synthetic illustration':
    st.header('Synthetic illustration | not empirical AML measurement')
    st.caption('Source: rc13 seeded generator, 25 regions x 6 sectors, seed 42. Real place names do not make these observed data. Model thresholds and perturbation distributions are uncalibrated.')
    source=pd.DataFrame(snapshot.rows['synthetic']);mc=pd.DataFrame(snapshot.rows['monte_carlo'])
    regions=st.multiselect('Regions',sorted(source.oblast.unique()),default=sorted(source.oblast.unique()),key='regions')
    sectors=st.multiselect('Sectors',sorted(source.sector.unique()),default=sorted(source.sector.unique()),key='sectors')
    threshold=st.slider('Minimum illustrative score',0.0,100.0,0.0,1.0,key='threshold')
    source['waris_aml_review_score']=pd.to_numeric(source['waris_aml_review_score'])
    filtered=source[source.oblast.isin(regions)&source.sector.isin(sectors)&source.waris_aml_review_score.ge(threshold)]
    st.metric('Selected synthetic rows',len(filtered))
    if filtered.empty:st.info('No synthetic rows match these filters. Broaden the selection to inspect the illustration.')
    else:
        joined=filtered[['oblast','sector','waris_aml_review_score','data_mode']].merge(mc[['oblast','sector','mc_p05_score','mc_mean_score','mc_p95_score']],on=['oblast','sector'],validate='one_to_one')
        for col in ['mc_p05_score','mc_mean_score','mc_p95_score']:joined[col]=pd.to_numeric(joined[col])
        hist=pd.cut(joined.waris_aml_review_score,bins=list(range(0,101,10)),include_lowest=True).value_counts(sort=False)
        histogram=pd.DataFrame({'Illustrative score range':[str(v) for v in hist.index],'Synthetic row count':hist.values})
        st.bar_chart(histogram,x='Illustrative score range',y='Synthetic row count',x_label='Illustrative score (0-100)',y_label='Synthetic rows',alt='Distribution of selected synthetic WARIS scores, not real-world risk')
        st.caption('Sensitivity columns are the 5th/95th percentiles of 5000 assumed perturbation draws, not empirical confidence intervals or money-laundering probabilities.')
        shown=joined.rename(columns={'oblast':'Region','sector':'Sector','waris_aml_review_score':'Illustrative score','mc_p05_score':'Assumed-draw p05','mc_mean_score':'Assumed-draw mean','mc_p95_score':'Assumed-draw p95'})
        st.dataframe(shown,hide_index=True,alt='Selected synthetic scores and assumed perturbation percentiles')
        st.download_button('Download selected synthetic rows',shown.to_csv(index=False).encode(),file_name='WARIS_SYNTHETIC_selected_rows.csv',mime='text/csv')
elif section=='Official GRP benchmark':
    st.header('Official 2021 GRP | benchmark-only')
    st.caption('State Statistics Service of Ukraine (Ukrstat). Selected annual observations retrieved 18 October 2026; unit 1090 UAH, scale 6 (million). Default CC BY 4.0 basis retains the dated selected-source review. Territorial notes apply.')
    df=pd.DataFrame(snapshot.rows['grp']);df['GRP (billion UAH)']=pd.to_numeric(df.value_million_UAH)/1000
    shown=df[['geography_label_from_retained_export','GRP (billion UAH)']].rename(columns={'geography_label_from_retained_export':'Source region label'})
    st.bar_chart(shown,x='Source region label',y='GRP (billion UAH)',horizontal=True,x_label='Selected source region',y_label='GRP (billion UAH)',alt='Official 2021 regional GRP benchmark, not a risk ranking')
    st.dataframe(shown,hide_index=True,alt='Twenty-five selected official 2021 GRP observations')
    st.info('24 oblasts plus Kyiv City are a study universe, not all Ukrainian territories. No current-economy or historical-boundary-equivalence claim. National Ukraine must not be added to regional totals. No GRP scoring, Monte Carlo use or validated sector-economic allocation.')
    st.markdown('[Ukrstat regional accounts](https://stat.gov.ua/uk/explorer?urn=SSSU%3ADF_REGIONAL_ACCOUNTS%28~%29) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)')
elif section=='Procurement study':
    st.header('Procurement | separate recorded-frame domains')
    st.caption('Prozorro snapshot, 20 October 2026. Frame: 1000 first-observed API IDs across ten pages. Tender clusters, lot/lifecycle rules and missing-bid handling are frozen. No raw records or selected membership are displayed.')
    obs=pd.DataFrame(snapshot.rows['procurement_observed']);weighted=pd.DataFrame(snapshot.rows['procurement_weighted'])
    columns=['procedure','unit_type','domain_frame_tenders','sampled_tenders','observed_eligible_units','observed_exactly_one_active_object_units','active_object_share']
    observed_view=obs[columns].copy();observed_view['unit_type']=observed_view.unit_type.str.replace('_',' ');observed_view['active_object_share']=pd.to_numeric(observed_view.active_object_share)*100
    observed_view=observed_view.rename(columns={'procedure':'Procedure','unit_type':'Unit type','domain_frame_tenders':'Frame tenders','sampled_tenders':'Sampled tenders','observed_eligible_units':'Eligible sample units','observed_exactly_one_active_object_units':'Exactly-one active-object units','active_object_share':'Observed share (%)'})
    st.subheader('Observed sample objects')
    st.dataframe(observed_view,hide_index=True,alt='Two separate procedure and unit-type observed sample summaries')
    st.subheader('Finite-frame expansion estimates')
    weighted_view=weighted[['procedure','unit_type','cluster_weight_fraction','HT_eligible_unit_total','HT_exactly_one_active_object_total','ratio_of_HT_totals','total_status']].copy()
    weighted_view['unit_type']=weighted_view.unit_type.str.replace('_',' ');weighted_view['total_status']=weighted_view.total_status.str.replace('_',' ')
    weighted_view=weighted_view.rename(columns={'procedure':'Procedure','unit_type':'Unit type','cluster_weight_fraction':'Cluster weight (N/n)','HT_eligible_unit_total':'Expanded eligible units','HT_exactly_one_active_object_total':'Expanded exactly-one-object units','ratio_of_HT_totals':'Ratio of expanded totals','total_status':'Total status'})
    st.dataframe(weighted_view,hide_index=True,alt='Procedure-specific expanded totals, with census and estimate roles kept distinct')
    st.warning('Bid objects are not unique firms or proven valid offers. Fractional expanded totals are estimates, not observed tenders or people. Do not pool procedures/unit types or infer national prevalence, low competition, misconduct or WARIS scores.')
    st.markdown('[Prozorro public API source](https://public.api.openprocurement.org/api/2.5/tenders). Source attribution and selected reuse scope remain in component C03; no blanket attachment/privacy clearance is implied.')
elif section=='National context':
    st.header('National context | no regional or score allocation')
    st.subheader('World Bank snapshot')
    latest=pd.DataFrame(world_bank_display(m))
    st.dataframe(latest,hide_index=True,alt='Latest available observation per indicator within the retained World Bank snapshot')
    st.caption('Display conversion only: currency values are divided by one billion; the tax ratio remains percent of GDP. Original values stay in the source tables.')
    wb=pd.DataFrame(snapshot.rows['world_bank']);names=sorted(wb.indicator_name.unique());chosen=st.selectbox('National indicator',names)
    selected=wb[wb.indicator_name.eq(chosen)].copy();selected['year']=pd.to_numeric(selected.year);selected['value']=pd.to_numeric(selected.value,errors='coerce')
    money=selected.unit.iloc[0]=='current_USD';selected['Display value']=selected.value/(1e9 if money else 1)
    unit='billion current US$' if money else '% of GDP'
    point_chart=alt.Chart(selected).mark_point(filled=True,size=55).encode(x=alt.X('year:Q',title='Source year',scale=alt.Scale(zero=False),axis=alt.Axis(format='d')),y=alt.Y('Display value:Q',title=unit),tooltip=[alt.Tooltip('year:Q',title='Source year',format='d'),alt.Tooltip('Display value:Q',title=unit,format='.2f')]).properties(height=280)
    st.altair_chart(point_chart,alt='Source-year points for one national World Bank indicator; missing values are not imputed')
    st.caption('Four indicators, 136 year slots, 1991-2024. Snapshot 18 October 2026. Points only; missing values are not interpolated. Units differ across indicators and are never combined. Latest means latest available in this snapshot, not current global latest.')
    st.markdown(f"[Selected indicator source]({selected.source_url.iloc[0]}) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)")
    st.write('Underlying-source credit: '+selected.underlying_provider_credit.iloc[0])
    st.subheader('SFMS Q1 2026 referral context')
    sfms=pd.DataFrame(snapshot.rows['sfms'])
    st.dataframe(sfms[['source_row','category_as_published','row_role','referral_documents','source_reported_associated_funds_million_UAH']],hide_index=True,alt='Published SFMS national referral categories and separately labelled total')
    st.caption('Rows 3 and 8 intentionally retain repeated published labels. Keep source row positions. The published total is not added to categories. Referral documents and associated amounts are not unique persons, convictions or independently established criminal loss; zero amounts do not establish absence of risk.')
    st.warning('Dated verification was source-text only. Local PDF custody and visual layout were not established. This quarterly source does not verify the missing 2023 annual report; unverified FIU claims remain excluded.')
    st.markdown('[SFMS official quarterly PDF](https://fiu.gov.ua/assets/userfiles/440/2026/ENG_I%20quarter_NABU.pdf). Selected source facts retain SFMS attribution and the dated default CC BY scope; no raw PDF is bundled.')
elif section=='Literature':
    st.header('Six conceptual themes | reference-only')
    pages={r['waris_id']:r['printed_pages'] for r in snapshot.rows['literature_pages']}
    for r in snapshot.rows['literature']:
        with st.expander(r['typology_id']+' | '+r['typology_name']):
            st.write(r['description']);st.caption('Printed pages '+pages[r['typology_id']]+'; conceptual support only. Project indicators and layer assignments are interpretations, not validated measurements.')
    st.markdown('Karina Utenkova (2026), *Anti-money laundering as an instrument of economic security: Wartime adaptation of AML/CFT frameworks in Ukraine*, pp. 78-91. [DOI](https://doi.org/10.65237/2336-3630-2026-3(1)-4) | [Publisher](https://phes.com.ua/ojs/index.php/www/en/article/view/112) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Copyright 2026 CENTRAL EUROPEAN JOURNAL OF SCIENCE AND RESEARCH. WARIS condenses and maps selected themes; no author or publisher endorsement.')
    st.info('Four FIU-dependent themes and the unverified recruitment example remain excluded. Six permitted IDs do not independently verify secondary studies. Literature does not enter scores or Monte Carlo.')
else:
    st.header('Provenance and release boundaries')
    st.code(snapshot.contract['build_id'])
    entries=[{'Dataset':key,'Evidence class':value['source_class'],'Scope':value['scope_period'],'SHA-256':value['sha256']} for key,value in snapshot.contract['inputs'].items()]
    st.dataframe(pd.DataFrame(entries),hide_index=True,alt='Twelve allowlisted input identities, scopes and exact hashes')
    st.download_button('Download data contract',(ROOT/'presentation/data_contract.json').read_bytes(),file_name='WARIS_presentation_data_contract.json',mime='application/json')
    st.write('Historical workflow: 25 not-started queue rows, 200 not-started checklist rows, zero completed analyst dispositions. Documentation counts are not measured control effectiveness. Confidence labels remain categorical declarations.')
    st.info('The report/dashboard is a controlled selected-snapshot build, not a replay of missing historical acquisitions or a validated empirical AML system. Original code, weights and source gates remain unchanged. Final security/advisory/platform checks and publication approval remain separate gates. Nothing has been published.')
