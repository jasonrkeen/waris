"""Selected SDMX metadata and illustrative benchmark checks; no production writes."""
from collections import Counter
from pathlib import Path
from typing import Any
import csv, hashlib, json, math

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def write(path: Path, records: list[dict[str,Any]]) -> None:
    with path.open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)

def identity(item: dict[str,Any]) -> tuple[str,str,str,str]:
    return tuple(str(item[k]) for k in ('id','agencyID','version','name'))

def verify_reference(row: dict[str,str], objects: list[dict[str,Any]]) -> dict[str,Any]:
    wanted=(row.get('artifact_id',row.get('id')),row['agencyID'],row['version'],row['name'])
    matched=[item for item in objects if identity(item)==wanted]
    if not matched:
        raise ValueError('Exact metadata identity, version and title not verified')
    return {'id':wanted[0],'agency':wanted[1],'version':wanted[2],'name':wanted[3],'same_version_title_match':True}

def typed_components(dsd: dict[str,Any]) -> list[dict[str,Any]]:
    if identity(dsd)[:3]!=('DSD_REGIONAL_ACCOUNTS','SSSU','6.0.0'):
        raise ValueError('Unexpected DSD identity/version')
    components=dsd['dataStructureComponents']; result=[]
    groups=[('dimensionList','dimensions','series_dimension'),('dimensionList','timeDimensions','time_dimension'),('attributeList','attributes','attribute'),('measureList','measures','measure')]
    for container,collection,role in groups:
        for item in components.get(container,{}).get(collection,[]):
            result.append({'component_id':item['id'],'role':role,'position':item.get('position',''),'concept_identity_as_supplied':item.get('conceptIdentity',''),'source_path':f'data.dataStructures[0].dataStructureComponents.{container}.{collection}','key_axis':role in ('series_dimension','time_dimension'),'enumeration_resolution':'not_inferred','used_in_scoring':False})
    if Counter(x['role'] for x in result)!=Counter(series_dimension=4,time_dimension=1,attribute=15,measure=1):
        raise ValueError('Unexpected component cardinality')
    axes=sorted((x for x in result if x['key_axis']),key=lambda x:x['position'])
    if [x['component_id'] for x in axes]!=['INDICATOR','REGION','NACE','FREQ','TIME_PERIOD']:
        raise ValueError('Unexpected axes/order')
    return result

def benchmark(official: list[dict[str,str]], synthetic: list[dict[str,Any]], mapping: dict[str,str]) -> list[dict[str,Any]]:
    """Independent arithmetic from official 2021 GRP and synthetic prewar indices only."""
    if len(official)!=25 or len({r['region_code'] for r in official})!=25:
        raise ValueError('Expected 25 distinct WARIS regions')
    grouped={}
    for r in synthetic:
        name=str(r['oblast']);value=float(r['prewar_revenue_index_2021'])
        if not math.isfinite(value) or value<=0:raise ValueError('Invalid synthetic index')
        grouped.setdefault(name,[]).append((str(r['sector']),value))
    for values in grouped.values():
        if len(values)!=6 or len({x[0] for x in values})!=6:raise ValueError('Expected six unique synthetic sectors')
    names=[mapping[r['geography_label_from_retained_export']] for r in official]
    if len(set(names))!=25 or set(names)!=set(grouped):raise ValueError('Region mapping mismatch')
    values=[]
    for row in official:
        if (row['period'],row['unit_code'],row['scale_code'],row['indicator_code'],row['nace_code'],row['frequency'])!=('2021','1090','6','GRP','_Z','A'):
            raise ValueError('Period, unit, scale or series mismatch')
        value=float(row['value_million_UAH'])
        if not math.isfinite(value) or value<=0:raise ValueError('Invalid official observation')
        values.append(value)
    sums={name:sum(x[1] for x in entries) for name,entries in grouped.items()}
    def scale(v:float,seq:list[float])->float:
        if max(seq)==min(seq):raise ValueError('Constant baseline has no min-max interpretation')
        return 100*(v-min(seq))/(max(seq)-min(seq))
    result=[]
    for row,name,value in zip(official,names,values):
        official_share=value/sum(values);synthetic_share=sums[name]/sum(sums.values())
        official_index=scale(value,values);synthetic_index=scale(sums[name],list(sums.values()))
        result.append({'waris_oblast':name,'region_code':row['region_code'],'official_grp_million_uah':value,'official_grp_share_of_waris_total':official_share,'official_grp_index_0_100':official_index,'synthetic_prewar_revenue_index_mean':sums[name]/6,'synthetic_prewar_revenue_index_sum':sums[name],'synthetic_prewar_share_of_total':synthetic_share,'synthetic_prewar_index_0_100':synthetic_index,'official_to_synthetic_share_ratio':official_share/synthetic_share,'official_vs_synthetic_index_gap':official_index-synthetic_index,'sector_count':6})
    return sorted(result,key=lambda r:r['waris_oblast'])
