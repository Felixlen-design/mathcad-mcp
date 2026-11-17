import glob, io, sys, zipfile, re
from collections import defaultdict
from lxml import etree
NUM = re.compile(r'^-?[0-9.,eE+-]+$')
def harvest(path, acc):
    z = zipfile.ZipFile(path)
    for n in z.namelist():
        data = z.read(n)
        if n.endswith('.XamlPackage'):
            data = zipfile.ZipFile(io.BytesIO(data)).read('Xaml/Document.xaml'); key='XAML'
        elif n.endswith(('.xml', '.rels')):
            key = n.split('/')[-1]
        else: continue
        root = etree.fromstring(data)
        for el in root.iter():
            if not isinstance(el.tag, str): continue
            tag = etree.QName(el).localname
            for a, v in el.attrib.items():
                a = etree.QName(a).localname
                if a in ('item-idref', 'Id', 'Target', 'region-id', 'resultRef', 'result-id', 'NavigateUri', 'tag'): continue
                acc[(key if key in ('XAML','presentation.xml','app.xml') else 'ws', tag, a)].add('#' if NUM.match(v) else v)
real = defaultdict(set)
for f in glob.glob(sys.argv[2] + '/*.mcdx'): harvest(f, real)
mine = defaultdict(set); harvest(sys.argv[1], mine)
for k in sorted(mine):
    extra = mine[k] - real.get(k, set())
    if extra: print(k, 'neu:', sorted(extra)[:6], '| real:', sorted(real.get(k, set()))[:6])
