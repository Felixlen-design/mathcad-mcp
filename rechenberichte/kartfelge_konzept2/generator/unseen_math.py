"""Compare math 'shapes' (operator + kinds of children) of a generated file with real Prime files."""
import glob, sys, zipfile
from collections import defaultdict
from lxml import etree
ML = '{http://schemas.mathsoft.com/math50}'
def kind(el):
    t = etree.QName(el).localname
    if t == 'id': return 'id:' + el.get('labels', '-')
    if t == 'apply':
        head = el[0]; ht = etree.QName(head).localname
        return 'apply:' + (ht if ht != 'id' else 'id:' + head.get('labels', '-'))
    return t
def shapes(path, acc):
    z = zipfile.ZipFile(path)
    for part in ('mathcad/worksheet.xml',):
        root = etree.fromstring(z.read(part))
        for m in root.iter('{http://schemas.mathsoft.com/worksheet50}math'):
            top = m[0]
            acc[('region', kind(top))].add(path)
            for el in m.iter():
                if not isinstance(el.tag, str) or not el.tag.startswith(ML): continue
                children = [kind(c) for c in el if isinstance(c.tag, str) and c.tag.startswith(ML)]
                t = kind(el)
                if t.startswith('apply:'):
                    acc[(t, len(children) - 1)].add(path)
                elif t in ('define', 'eval', 'unitOverride', 'sequence', 'boundVars', 'function', 'parens', 'scale'):
                    acc[(t, tuple(sorted(set(children))))].add(path)
real = defaultdict(set)
for f in glob.glob(sys.argv[2] + '/*.mcdx'): shapes(f, real)
mine = defaultdict(set); shapes(sys.argv[1], mine)
for k in sorted(mine, key=str):
    if k not in real:
        print('NIE GESEHEN:', k)
