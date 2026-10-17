import sys
from decimal import Decimal as D, ROUND_HALF_UP
from collections import defaultdict
src=open('conf.py').read().replace("for k,v in sorted","for k,v in [] and sorted").replace("print('TOTAL'","0 and print('TOTAL'")
src0=1
g={}; sys.argv=['x','/mnt/user-data/outputs/tarvo-fechamento/data']
src=src.replace("def trunc(v): s=-1 if v<0 else 1; return s*(abs(v)*100).to_integral_value(ROUND_DOWN)/100","def trunc(v): return v.quantize(D('0.01'),ROUND_HALF_UP)")
exec("from decimal import ROUND_HALF_UP\n"+src,g)
lines=g['lines']; num=g['num']; dt=g['dt']; taxas=g['taxas']; R=g['trunc']; date=g['date']
tot=defaultdict(D); div=defaultdict(D); own={}; antec={}; antecd={}; sept={l['id_transacao'] for l in lines}
sum_vt=D(0)
for l in lines:
    ec=l['cod_estabelecimento']; t=l['tipo_lancamento']; b=num(l['valor_bruto'])
    if ec=='1076801732': continue
    sum_vt+=num(l['valor_taxa'])
    r0=dt(l['data_venda_original']) if t=='ESTORNO' else dt(l['data_movimento'])
    row=taxas(ec,r0); mod=l['modalidade']; q=int(l['qtd_parcelas'] or 1)
    zero=row['cnpj']=='00520815000100' and date(2026,9,1)<=r0<=date(2026,12,31)
    ap=num(l['taxa_aplicada_pct'])/100
    if t in('VENDA','ESTORNO','ANTECIPACAO'):
        i=5 if t=='ANTECIPACAO' else {'DEBITO':0,'CREDITO A VISTA':1,'PIX':4}.get(mod,2 if q<=6 else 3)
        ct=D(0) if zero else row['tx'][i]; c=R(b*ct); d=R(b*(ap-ct)) if ap!=ct else D(0)
        if t=='ANTECIPACAO': antec[l['id_transacao']]=c; antecd[l['id_transacao']]=d
    else: c=-antec[l['id_referencia']]; d=-antecd[l['id_referencia']]
    tot[row['nome']]+=c
    key=l['id_referencia'] if t in('ESTORNO','REVERSAO ANTECIPACAO') and l['id_referencia'] in sept else l['id_transacao']
    div[key]+=d; own[key]=row['nome']
T=sum(tot.values()); print('CHECKOUT half-up',T)
for k in sorted(tot,key=lambda k:-tot[k]): print(' ',k,tot[k])
agg=defaultdict(lambda:[0,D(0)])
for k,v in div.items():
    if v!=0: agg[own[k]][0]+=1; agg[own[k]][1]+=v
print('DIV',dict(agg),'n',sum(a[0] for a in agg.values()),'tot',sum(a[1] for a in agg.values()))
print('residuo Σvt-(com+div)',sum_vt-T-sum(a[1] for a in agg.values()))
