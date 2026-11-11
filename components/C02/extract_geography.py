"""Read selected top-level cells from retained XLSX without executing formulas."""
from pathlib import Path
import argparse,json,zipfile
from xml.etree import ElementTree as ET

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def extract(path:Path)->list[dict]:
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            tree=ET.fromstring(z.read('xl/sharedStrings.xml'))
            strings=[''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in tree.findall('m:si',NS)]
        rows=[]
        tree=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        for row in tree.findall('.//m:sheetData/m:row',NS):
            values={}
            for cell in row.findall('m:c',NS):
                location=cell.attrib['r'];column=''.join(x for x in location if x.isalpha())
                value=cell.find('m:v',NS)
                if cell.attrib.get('t')=='s' and value is not None:value=strings[int(value.text)]
                elif cell.attrib.get('t')=='inlineStr':value=''.join(x.text or '' for x in cell.findall('.//m:t',NS))
                else:value=value.text if value is not None else None
                values[column]=value
            code=values.get('A')
            if isinstance(code,str) and code.startswith('UA') and all(values.get(c) in (None,'') for c in ('B','C','D','E')):
                rows.append({'code':code,'category':values.get('F'),'name':values.get('G'),'worksheet_row':int(row.attrib['r'])})
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Do not overwrite retained extraction')
    a.output.write_text(json.dumps(extract(a.input),indent=2,ensure_ascii=False)+'\n',encoding='utf8')
