"""Reproduce all reported field contrasts using only the Python standard library."""
from pathlib import Path
import argparse,csv,hashlib,json,math,statistics

BASE=Path(__file__).resolve().parent
T975_DF7=2.364624251592784

def records(name):
    with (BASE/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Optional new JSON receipt; existing files are never overwritten.')
    args=parser.parse_args()
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf8'))
    for name,expected in manifest['sha256'].items():
        actual=hashlib.sha256((BASE/name).read_bytes()).hexdigest()
        if actual!=expected:raise RuntimeError('SHA-256 mismatch: '+name)
    fields=records('field_effects.csv');summaries=records('contrast_summary.csv');lofo=records('leave_one_field_out.csv')
    assert (len(fields),len(summaries),len(lofo))==(192,24,192)
    groups={}
    for r in fields:
        key=(r['candidate_id'],r['contrast']);groups.setdefault(key,[]).append(r)
    assert len(groups)==24 and len({k[0] for k in groups})==8
    assert len({(r['candidate_id'],r['contrast']) for r in summaries})==24
    checked=[]
    def close(a,b):
        if not math.isfinite(a) or not math.isfinite(b) or abs(a-b)>1e-10:raise RuntimeError(f'Numeric mismatch: {a} != {b}')
    for r in summaries:
        key=(r['candidate_id'],r['contrast']);g=groups[key]
        assert len(g)==8 and len({(v['basin_id'],v['field_id']) for v in g})==8
        values=[float(v['gain']) for v in g]
        mean=statistics.fmean(values);half=T975_DF7*statistics.stdev(values)/math.sqrt(8)
        for actual,column in [(mean,'estimate'),(mean-half,'ci_low'),(mean+half,'ci_high')]:close(actual,float(r[column]))
        assert sum(v>0 for v in values)==int(r['positive_fields'])
        assert (mean-half>0)==(r['positive_mean_advantage'].lower()=='true')
        block=[v for v in lofo if (v['candidate_id'],v['contrast'])==key]
        assert len(block)==8 and len({(v['omitted_basin'],v['omitted_field']) for v in block})==8
        for v in block:
            remaining=[float(x['gain']) for x in g if (x['basin_id'],x['field_id'])!=(v['omitted_basin'],v['omitted_field'])]
            assert len(remaining)==7
            close(statistics.fmean(remaining),float(v['estimate']))
        if key==('ExtraTrees_depth18_leaf100','c_vs_frozen_et'):assert all(v==0 for v in values)
        checked.append({'candidate_id':key[0],'contrast':key[1],'estimate':mean,'ci_low':mean-half,'ci_high':mean+half,'positive_fields':sum(v>0 for v in values)})
    fits=records('fit_diagnostics.csv')
    assert len(fits)==26
    mlp=[x for x in fits if x['candidate_id'].startswith('MLP_')]
    assert len(mlp)==10 and all(int(x['n_iter'])==80 and 'ConvergenceWarning' in x['warning_categories'] for x in mlp)
    result={'status':'PASS_DERIVED_FIELD_TABLE_REPRODUCTION','scope':'Hashes, 24 field-equal t summaries, 192 LOFO values, self-contrast and recorded fit warnings; no model fitting or raw-data scoring.','not_independent_scientific_acceptance':True,'comparisons':checked}
    if args.output:
        with args.output.open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'status':result['status'],'contrasts':24,'field_effects':192,'LOFO':192,'MLP_warning_seeds':10}))

if __name__=='__main__':main()
