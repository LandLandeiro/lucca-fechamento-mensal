import csv, re, sys, openpyxl
from decimal import Decimal as D, ROUND_DOWN
from datetime import date
from collections import defaultdict
dd=sys.argv[1]
def pct(v):
    if v is None or v=='padrão': return None
    if isinstance(v,str): return D(v.replace('%','').replace(',','.'))/100
    return D(str(v))
def dt(s):
    d,m,y=s.split('/'); return date(int(y),int(m),int(d))
ws=openpyxl.load_workbook(dd+'/02_tabela_taxas_contratadas.xlsx')['Taxas vigentes']
rows=[]
for r in list(ws.iter_rows(values_only=True))[5:30]:
    if not r[0] or r[3] is None: continue
    cnpj=re.sub(r'\D','',str(r[1])).zfill(14)
    vig=str(r[10] or '')
    ini,fim=date(2000,1,1),date(2100,1,1)
    m=re.search(r'(\d\d/\d\d/\d{4})',vig)
    if 'até' in vig: fim=dt(m.group(1))
    elif m: ini=dt(m.group(1))
    rows.append(dict(nome=r[0],cnpj=cnpj,ec=r[2],tx=[pct(x) for x in r[3:9]],ini=ini,fim=fim,inativo='INATIVO' in str(r[11])))
mapa={'1043300981':'Novo Horizonte Intercambio','1043396662':'Horizonte Viagens','1038867654':'Kiwi Experience'}
def taxas(ec,ref):
    if ec in mapa: c=[x for x in rows if x['nome']==mapa[ec]]
    else: c=[x for x in rows if x['ec']==ec]
    c=[x for x in c if x['ini']<=ref<=x['fim']]
    assert len(c)<=1,(ec,ref); return c[0] if c else None
def trunc(v): s=-1 if v<0 else 1; return s*(abs(v)*100).to_integral_value(ROUND_DOWN)/100
lines=list(csv.DictReader(open(dd+'/01_orbe_relatorio_comissoes_set2026.csv',encoding='utf-8'),delimiter=';'))
num=lambda s:D(s.replace(',','.'))
antec={}
tot=defaultdict(D); pend=0; nomes={}
for l in lines:
    ec=l['cod_estabelecimento']; t=l['tipo_lancamento']; b=num(l['valor_bruto'])
    if ec=='1076801732': pend+=1; continue
    ref=dt(l['data_venda_original']) if t=='ESTORNO' else dt(l['data_movimento'])
    row=taxas(ec,ref); assert row,(l['id_transacao'],ec,ref)
    mod=l['modalidade']; q=int(l['qtd_parcelas'] or 1)
    if t in('VENDA','ESTORNO'):
        i={'DEBITO':0,'CREDITO A VISTA':1,'PIX':4}.get(mod, 2 if q<=6 else 3)
        r=row['tx'][i]
    elif t=='ANTECIPACAO': r=row['tx'][5]
    else: r=None
    zero = row['cnpj']=='00520815000100' and date(2026,9,1)<=ref<=date(2026,12,31)
    if t=='REVERSAO ANTECIPACAO':
        c=-antec[l['id_referencia']]
    else:
        c=D(0) if zero else trunc(b*r)
    if t=='ANTECIPACAO': antec[l['id_transacao']]=c
    tot[row['cnpj']]+=c; nomes[row['cnpj']]=row['nome']
for k,v in sorted(tot.items(),key=lambda x:-x[1]): print(k,nomes[k],v)
print('TOTAL',sum(tot.values()),'lojistas',len(tot),'pend',pend,'linhas',len(lines))
