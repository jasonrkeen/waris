"""Compare a first-party geography check with retained official top-level codes."""
from pathlib import Path
import csv,json,hashlib

EXPECTED={
 'Cherkasy':'Черкаська','Chernihiv':'Чернігівська','Chernivtsi':'Чернівецька',
 'Dnipropetrovsk':'Дніпропетровська','Donetsk':'Донецька','Ivano-Frankivsk':'Івано-Франківська',
 'Kharkiv':'Харківська','Kherson':'Херсонська','Khmelnytskyi':'Хмельницька','Kirovohrad':'Кіровоградська',
 'Kyiv':'Київська','Kyiv City':'Київ','Luhansk':'Луганська','Lviv':'Львівська','Mykolaiv':'Миколаївська',
 'Odesa':'Одеська','Poltava':'Полтавська','Rivne':'Рівненська','Sumy':'Сумська','Ternopil':'Тернопільська',
 'Vinnytsia':'Вінницька','Volyn':'Волинська','Zakarpattia':'Закарпатська','Zaporizhzhia':'Запорізька','Zhytomyr':'Житомирська'}

def reconcile(legacy:list[dict],official:list[dict])->list[dict]:
    if len(legacy)!=25 or {r['waris_oblast'] for r in legacy}!=set(EXPECTED):raise ValueError('Unexpected WARIS geography universe')
    if len({r['code'] for r in official})!=len(official):raise ValueError('Duplicate official code')
    codes={r['code']:r for r in official};output=[]
    for row in legacy:
        ref=codes.get(row['region_code'])
        if not ref or ref['name'].strip()!=EXPECTED[row['waris_oblast']] or ref['category']!=('K' if row['waris_oblast']=='Kyiv City' else 'O'):
            raise ValueError('Geography identity/category mismatch')
        output.append({'waris_oblast':row['waris_oblast'],'ukrstat_label_from_historical_check':row['ukrstat_oblast'],
            'region_code':row['region_code'],'official_name':ref['name'].strip(),'official_category':ref['category'],
            'official_sheet':'Кодифікатор','code_cell':f"A{ref['worksheet_row']}",'name_cell':f"G{ref['worksheet_row']}",
            'verification_scope':'top_level_code_name_identity_at_retained_2026_publication; not historical boundary equivalence',
            'source_url':'https://mininfra.gov.ua/storage/app/sites/1/uploaded-files/kodifikator-07-07.xlsx',
            'source_sha256':'5c5317759b2b90208e9b00338bc3db3c5e694272a166acf73f1543b3e18ecbea',
            'license':'CC BY 4.0; Ministry site default, no selected-table exception identified',
            'used_in_scoring':False,'sector_allocation_approved':False})
    return output

if __name__=='__main__':
    root=Path.cwd();work=root/'work/procurement_frame_20261020'
    source=root/'work/original/waris_ukraine_aml_risk_model_publish/outputs/tables/official_baseline_geography_crosswalk_check.csv'
    rows=list(csv.DictReader(source.open(encoding='utf8',newline='')))
    official=json.loads((work/'katottg_top_level_PRIVATE.json').read_text(encoding='utf8'))
    result=reconcile(rows,official)
    with (work/'verified_top_level_geography_20261020.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=result[0].keys());w.writeheader();w.writerows(result)
    receipt={'historical_artifact_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'official_top_level_records':len(official),
       'waris_code_name_pairs_verified':len(result),'source_workbook_sha256':result[0]['source_sha256'],
       'excluded_from_WARIS_universe':['Crimea','Sevastopol'],'scope':'mapping-control documentation only; no historical boundary, sector or scoring approval',
       'source_header_base_edition':'2024-01-19 order 48','landing_link_label':'2026-07-07; retained October 20, 2026',
       'historical_http_acquisition_recovered':False}
    (work/'geography_reconciliation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2))
