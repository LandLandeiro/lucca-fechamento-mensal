import runpy,sys
from collections import defaultdict
from decimal import Decimal as D
src=open('conf.py').read().replace("for k,v in sorted","import builtins\nfor k,v in [] and sorted")
# reuse functions by exec
g={}; sys.argv=['x',sys.argv[1]]; exec(src,g)
lines=g['lines']; num=g['num']; dt=g['dt']; taxas=g['taxas']; trunc=g['trunc']; date=g['date']
diff={}; owner={}; ref={}
antec={}
for l in lines:
    ec=l['cod_estabelecimento']; t=l['tipo_lancamento']; b=num(l['valor_bruto'])
    if ec=='1076801732': continue
    r0=dt(l['data_venda_original']) if t=='ESTORNO' else dt(l['data_movimento'])
    row=taxas(ec,r0); mod=l['modalidade']; q=int(l['qtd_parcelas'] or 1)
    zero=row['cnpj']=='00520815000100' and date(2026,9,1)<=r0<=date(2026,12,31)
    if t in('VENDA','ESTORNO'):
        i={'DEBITO':0,'CREDITO A VISTA':1,'PIX':4}.get(mod,2 if q<=6 else 3); c=D(0) if zero else trunc(b*row['tx'][i])
    elif t=='ANTECIPACAO': c=D(0) if zero else trunc(b*row['tx'][5]); antec[l['id_transacao']]=c
    else: c=-antec[l['id_referencia']]
    d=num(l['valor_taxa'])-c
    key=l['id_referencia'] if t in('ESTORNO','REVERSAO ANTECIPACAO') and l['id_referencia'] in {x['id_transacao'] for x in lines if x['data_movimento'][3:5]=='09'} else l['id_transacao']
    diff[key]=diff.get(key,D(0))+d; owner[key]=row['nome']
agg=defaultdict(lambda:[0,D(0)])
for k,v in diff.items():
    if v!=0: agg[owner[k]][0]+=1; agg[owner[k]][1]+=v
for k,v in agg.items(): print(k,v)
print('n',sum(v[0] for v in agg.values()),'tot',sum(v[1] for v in agg.values()), 'neg',sum(1 for v in diff.values() if v<0))
