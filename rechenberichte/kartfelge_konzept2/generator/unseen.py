"""List element/attribute combinations in a generated .mcdx that never occur in real Prime-saved worksheets."""
import glob, io, sys, zipfile
from collections import defaultdict
from lxml import etree

def harvest(path, acc, parts_seen):
    z = zipfile.ZipFile(path)
    for n in z.namelist():
        data = z.read(n)
        if n.endswith('.XamlPackage'):
            inner = zipfile.ZipFile(io.BytesIO(data))
            docs = [('XAML', inner.read('Xaml/Document.xaml'))]
        elif n.endswith('.xml') or n.endswith('.rels'):
            key = 'rels' if n.endswith('.rels') else n.split('/')[-1]
            docs = [(key, data)]
        else:
            continue
        for key, d in docs:
            try:
                root = etree.fromstring(d)
            except Exception as e:
                print('PARSE', path, n, e); continue
            for el in root.iter():
                if not isinstance(el.tag, str): continue
                tag = etree.QName(el).localname
                parent = etree.QName(el.getparent()).localname if el.getparent() is not None else '-'
                acc[(key, tag)].update(etree.QName(a).localname if a.startswith('{') else a for a in el.attrib)
                parts_seen[(key, tag)].add(parent)

real, real_par = defaultdict(set), defaultdict(set)
for f in glob.glob(sys.argv[2] + '/*.mcdx'):
    harvest(f, real, real_par)
mine, mine_par = defaultdict(set), defaultdict(set)
harvest(sys.argv[1], mine, mine_par)
for k in sorted(mine):
    if k not in real:
        print('ELEMENT NIE GESEHEN:', k, 'parent', mine_par[k])
        continue
    extra = mine[k] - real[k]
    if extra:
        print('ATTRIBUT NIE GESEHEN:', k, sorted(extra))
    pextra = mine_par[k] - real_par[k]
    if pextra:
        print('ELTERN NIE GESEHEN:', k, sorted(pextra))
