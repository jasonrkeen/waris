"""Private sample-context inspection; no ACLED intensity score, weights or imputation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Literal
import re
import numpy as np
import pandas as pd

EVENT_TYPES = frozenset(('Battles','Explosions/Remote violence','Violence against civilians','Riots','Protests','Strategic developments'))


@dataclass(frozen=True)
class SampleScope:
    source_class: Literal['retained_provider_sample','synthetic_fixture']
    source_sha256: str | None = None


@dataclass(frozen=True)
class SampleContext:
    regions: pd.DataFrame
    audit: dict[str, object]


def normalized(value: object) -> str:
    if pd.isna(value):
        return ''
    return ' '.join(str(value).strip().casefold().replace('’',"'").split())


def assess_sample(events: pd.DataFrame, universe: tuple[str, ...], aliases: Mapping[str,str], scope: SampleScope) -> SampleContext:
    """Describe a supplied sample. Region presence never measures population coverage."""
    if scope.source_class not in ('retained_provider_sample','synthetic_fixture'):
        raise ValueError('Explicit retained sample or synthetic fixture required')
    if scope.source_class=='retained_provider_sample' and not re.fullmatch(r'[a-f0-9]{64}',scope.source_sha256 or ''):
        raise ValueError('Retained source fingerprint required; it is not an acquisition receipt')
    if not isinstance(universe,tuple) or not universe or len(set(universe))!=len(universe) or any(not isinstance(r,str) or not r.strip() for r in universe):
        raise ValueError('Explicit unique nonblank model region universe required')
    required={'event_id_cnty','event_date','event_type','country','admin1','fatalities'}
    if not required.issubset(events.columns):
        raise ValueError('Missing sample columns; no default values will be invented')
    frame=events.copy(deep=True)
    ids=frame.event_id_cnty.astype('string').str.strip()
    if ids.isna().any() or ids.eq('').any() or ids.duplicated().any():
        raise ValueError('Missing/duplicate event IDs; source grain requires review')
    if not frame.country.eq('Ukraine').fillna(False).all() or not frame.event_type.isin(EVENT_TYPES).all():
        raise ValueError('Country or event-type outside the frozen inspection scope')
    dates=frame.event_date.astype('string')
    parsed=pd.to_datetime(dates,format='%Y-%m-%d',errors='coerce')
    if not dates.str.fullmatch(r'\d{4}-\d{2}-\d{2}',na=False).all() or parsed.isna().any():
        raise ValueError('Invalid source event date; no inferred dates')
    if 'year' in frame:
        years=pd.to_numeric(frame.year,errors='coerce')
        if years.isna().any() or not years.eq(parsed.dt.year).all():
            raise ValueError('Event year/date conflict or missing year')
    source_fatalities=frame.fatalities.astype('string').str.strip()
    missing=source_fatalities.isna() | source_fatalities.eq('')
    fatalities=pd.to_numeric(source_fatalities.mask(missing),errors='coerce').astype('Float64')
    if (fatalities.isna() & ~missing).any() or (fatalities.dropna()<0).any() or not np.isfinite(fatalities.dropna().astype(float)).all():
        raise ValueError('Invalid reported fatality value; no coercion to zero')
    registry={normalized(k):v for k,v in aliases.items()}
    for region in universe:
        key=normalized(region)
        if key in registry and registry[key]!=region:
            raise ValueError('Canonical-region alias collision')
        registry[key]=region
    for key,value in aliases.items():
        if registry[normalized(key)]!=value:
            raise ValueError('Normalized alias collision')
    mapped=frame.admin1.map(lambda v:registry.get(normalized(v)))
    inside=mapped.isin(universe)
    frame['_region']=mapped.where(inside)
    frame['_reported_fatalities']=fatalities
    records=[]
    for region in universe:
        group=frame.loc[frame._region.eq(region)]
        observed=not group.empty
        missing_count=int(group._reported_fatalities.isna().sum()) if observed else None
        known=group._reported_fatalities.dropna()
        known_sum=float(known.sum()) if len(known) else None
        total=known_sum if observed and missing_count==0 else None
        records.append(dict(oblast=region,sample_membership='observed_in_retained_sample' if observed else 'not_observed_in_retained_sample',sample_event_count=len(group) if observed else None,reported_fatalities_sum=total,known_reported_fatalities_partial_sum=known_sum,missing_fatality_rows=missing_count,source_zero_fatality_rows=int(group._reported_fatalities.eq(0).sum()) if observed else None,source='ACLED (Armed Conflict Location & Event Data); https://acleddata.com; acquisition date unverified',population_coverage_verified=False,used_in_scoring=False,used_in_monte_carlo=False))
    regions=pd.DataFrame(records)
    for col in ('sample_event_count','missing_fatality_rows','source_zero_fatality_rows'):
        regions[col]=regions[col].astype('Int64')
    for col in ('reported_fatalities_sum','known_reported_fatalities_partial_sum'):
        regions[col]=regions[col].astype('Float64')
    observed_count=int(regions.sample_membership.eq('observed_in_retained_sample').sum())
    audit=dict(methodology_policy='acled-context-only-1',source_class=scope.source_class,source_sha256=scope.source_sha256,input_rows=len(frame),mapped_sample_rows=int(inside.sum()),unmapped_or_outside_universe_rows=int((~inside).sum()),blank_admin1_rows=int(frame.admin1.map(normalized).eq('').sum()),modeled_regions=len(universe),modeled_regions_with_sample_records=observed_count,modeled_regions_without_sample_records=len(universe)-observed_count,missing_fatality_rows=int(missing.sum()),source_zero_fatality_rows=int(fatalities.eq(0).sum()),event_date_min=None if frame.empty else str(dates.min()),event_date_max=None if frame.empty else str(dates.max()),event_date_precision_independently_verified=False,historical_acquisition_time_verified=False,population_coverage_verified=False,sampling_probabilities_known=False,rights_cleared=False,synthetic_blend_performed=False,used_in_scoring=False,used_in_monte_carlo=False,interpretation='Sample context only. Source zero reported fatalities need not mean no deaths. No records in a model region does not mean zero events or low risk.')
    return SampleContext(regions=regions,audit=audit)
