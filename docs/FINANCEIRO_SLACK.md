# Perguntas e respostas do financeiro (Slack, literal)

Canal: `#duvidas-hackathon-ai` (o organizador liberou: "podem enviar aqui. explicitem na thread de duvida se é tarvo ou hackaton").
Quem responde: manuel.freitas (Barte), no papel de **Helena, financeiro da Tarvo**.
Texto copiado do Slack sem edição em 16/10/2026. Horários em -03.

---

## Q-A · Fox AI · 20:01 · base da comissão de checkout

**Pergunta:**
> Ficamos com uma duvida em relacao ao checkout. Para calcular a comissão de checkout de cada lojista, qual valor devemos usar?
> (a) a taxa que a Orbe efetivamente cobrou (valor_taxa do relatório), ou
> (b) o valor bruto × a taxa contratada na planilha?
> Quando as duas diferem, qual delas vai para a nota fiscal? E a diferença é devolvida ao lojista?

**Resposta (20:05):**
> A gente fatura pela taxa *contratada*: valor bruto × taxa da planilha, linha por linha. O `valor_taxa` do relatório é o que a Orbe cobrou, e nem sempre bate com o contrato.
> Na nota fiscal vai a comissão calculada pela taxa contratada.
> Quando a taxa aplicada é diferente da contratada, é divergência. Se a Orbe cobrou a mais, a diferença volta para o lojista e eu cobro a Orbe. Isso eu decido, não vai automático. Preciso ver cada caso com transação e valor.

---

## Q-B · MN AI · 20:04 · estorno de venda de agosto

**Pergunta:**
> Quando uma venda é estornada, a Tarvo devolve a taxa ao lojista e isso abate a comissão do mês? E se a venda original for de agosto? Ex.: TX88444848 (Oxford Prep, estorno de -R$ 2.193,16 em 01/09 de uma venda de 22/08, taxa -R$ 83,12). Entra em setembro, volta para agosto ou fica fora?

**Resposta (20:06):**
> Sim. Estorno devolve a taxa ao lojista e abate a comissão do mês.
> Venda de agosto estornada em setembro *entra em setembro*, que é o mês do estorno. Agosto já está fechado e não reabro. A taxa usada é a que valia *na data da venda original*.
> No exemplo da Oxford Prep, o estorno de 01/09 reduz a comissão de setembro da Oxford, pela taxa contratada que valia em 22/08.

---

## Q-C · Fox AI · 20:16 · ECs sem cadastro

**Pergunta:**
> 4 ECs da Orbe não estão na planilha de taxas vigente (290 transações em setembro):
> - 1043300981 HORIZONTE INTERCAMBIO
> - 1043396662 HORIZONTE VIAGENS TURISMO
> - 1076801732 ATLAS IDIOMAS
> - 1038867654 KIWI EXPERIENCE TURISMO
>
> Quais são o CNPJ e as taxas de cada um? Eles correspondem às linhas "Horizonte Viagens", "Novo Horizonte Intercambio" e "Kiwi Experience" da planilha (que estão com o EC em branco)? A Atlas só aparece na aba de 2025: ela ainda é cliente ativa?

**Resposta (20:24):**
> Boa pegada, o EC dessas três está faltando na planilha:
> • *1043300981 HORIZONTE INTERCAMBIO* é a *Novo Horizonte Intercâmbio*, a linha "Novo Horizonte Intercambio".
> • *1043396662 HORIZONTE VIAGENS TURISMO* é a *Horizonte Viagens e Turismo*, a linha "Horizonte Viagens". São duas empresas diferentes.
> • *1038867654 KIWI EXPERIENCE TURISMO* é a *Kiwi Experience*, a linha "Kiwi Experience".
> O CNPJ e as taxas dessas três estão nas linhas delas na aba vigente.
> A *Atlas* na aba de 2025 eu não sabia. Essa planilha passa por várias mãos. O que eu sei é que ela começou a transacionar com a gente em 10/09 e que não tenho contrato assinado dela na vigente. Não sei qual taxa vale. Não fatura a Atlas até o comercial confirmar.

---

## Q-D · MN AI · 20:26 · notas fiscais

**Pergunta:**
> Pela resposta de vocês, a nota de checkout usa a comissão pela taxa contratada. Qual é a regra fixa para montar as notas todo mês?
> (a) CHECKOUT: uma nota por lojista por mês, com valor = vendas − estornos (pela taxa da venda original)? A ANTECIPACAO (bruto × taxa contratada, ex.: AN88444882 da Canguru) entra na mesma nota ou em nota separada? A REVERSAO ANTECIPACAO (ex.: AN88445114 reverte a AN88444915 da Mundo Aberto) só anula a original?
> (b) Se o saldo do lojista no mês der zero ou negativo por causa de estornos, não emite? O negativo passa para o mês seguinte?
> (c) REMESSA: o e-mail da Ponte fala em "nota fiscal de intermediação" para liberar os 50% do spread. O tomador é sempre a Ponte Câmbio (uma nota pelo total) ou cada lojista?
> (d) Existe texto padrão para a discriminação?

**Resposta (20:47):**
> *(a)* Sim. No checkout é *uma nota por lojista por mês*, no valor da comissão do mês pela taxa contratada, como respondi à Fox AI. Estorno abate pela taxa da venda original, como respondi a vocês antes. A antecipação *entra na mesma nota*, e a reversão só anula a taxa da antecipação que ela reverte.
> *(b)* Zero ou negativo não emite nota. O negativo não passa para o mês seguinte automaticamente. Eu trato com o lojista, então coloca como pendência para mim.
> *(c)* Na remessa, quem paga a gente é a Ponte. É *uma nota só, com a Ponte Câmbio como tomadora*, pelo total da nossa participação no mês. Não tem nota por lojista.
> *(d)* Não temos texto padrão. Algo simples com o serviço e a competência resolve.

---

## Q-E · MN AI · 20:30 · remessa

**Pergunta:**
> No checkout vocês faturam pela taxa contratada e a diferença vira divergência. A remessa segue a mesma lógica?
> (a) A comissão da Tarvo é 50% do "Spread R$" realizado da Ponte ou 50% de valor × "Spread remessa" contratado na planilha? Quando a Ponte aplica mais que o contratado (ex.: Mundo Aberto, contrato de 1,2%, PC-0926-0011 a ~1,5%), isso é divergência a devolver ao lojista? Quanto vale o "padrão" quando a célula está em branco?
> (b) Para cada situação, a regra é fixa (conta / não conta) ou é decisão sua caso a caso?
>   - spread negativo com "Taxa travada no pedido (D-1)" (ex.: PC-0926-0210)
>   - mesmo Nº de operação repetido, um marcado "reprocessada" (ex.: PC-0926-0162)
>   - status "APROVADO C/ RESSALVA"
>   - contratada num mês e liquidada no seguinte (ex.: PC-0926-0002, liquidada em 01/10): vale a data de contratação ou a de liquidação?

**Resposta (20:48):**
> *(a)* Na remessa a lógica é outra. A nossa comissão é *50% do "Spread R$" realizado*, como está no e-mail da Ponte. A Mundo Aberto negociou 1,20% em julho e a Ponte já devia estar aplicando, então é divergência, e eu contesto com a Ponte. Célula em branco ou "padrão" é 1,5% sobre a PTAX de referência.
> *(b)* Essas eu já sei responder:
> • *Spread negativo:* não aceito. A trava vale 2 horas pelo contrato, e essas passaram do prazo. Fica fora da comissão e da nota, e eu contesto.
> • *Operação repetida:* o número da operação é único.
> • *"Aprovado c/ ressalva":* o status de compliance não muda nada para a gente.
> • *Data:* vale a data de contratação.
> Para o que aparecer fora disso, me digam como vocês tratariam e por quê.

---

## Q-F · Lucca Landeiro · 20:36 · Rota Global, Casa do Estudante, competência, créditos sem origem

**Pergunta:**
> 1) Rota Global (EC 1074504011): a partir de 12/09 a Orbe passou a cobrar +0,50 p.p. em débito, crédito à vista e 2–6x (2,49/2,99/3,59% → 2,99/3,49/4,09%). A planilha vigente segue com as taxas antigas. Houve reajuste contratual ou é divergência?
>
> 2) Casa do Estudante (EC 1018325654): a linha tem a observação "cliente estratégico - ver c/ comercial" e um comentário "conversar com Diego (comercial) sobre condição especial". Existe condição especial valendo em setembro, ou fatura pela taxa da planilha?
>
> 3) Competência no extrato Aurora: folha, ISS, INSS, FGTS (identificados como 08/2026), IRRF, PIS e COFINS (sem competência no extrato) foram pagos em setembro. Também entrou em setembro o repasse de comissão 08/2026 da Ponte (MRD2026090132, R$ 61.884,12). Lanço tudo na competência agosto ou setembro?
>
> 4) Créditos sem origem clara no Aurora: (a) 16/09 PIX R$ 7.350,00 do CNPJ 38.686.002/0001-80 "SEM IDENTIFICACAO"; (b) 23/09 "DEVOLUCAO PIX - MUNDO ABERTO" +R$ 12.400,00 (enviamos 48.714,59 em 09/09 e 88.746,05 em 24/09); (c) 30/09 transferência de R$ 300.000,00 para o Meridiano sem crédito correspondente no extrato do Meridiano. Vocês sabem a origem desses três, ou ficam como pendência?

**Nota de autocorreção:** no item 1, os rótulos de modalidade estão trocados. 2,49/2,99/3,59% são as faixas **crédito à vista / 2–6x / 7–12x** da planilha (o débito é 1,49%). A resposta não muda: o contrato não mudou. O código compara por modalidade direto na planilha.

**Resposta (20:49):**
> 1. Não mudou nada no contrato da Rota este ano.
> 2. Existe, sim. A Casa do Estudante tem tarifa zerada no checkout de setembro a dezembro, por acordo do comercial para segurar o cliente. Vale para MDR e antecipação. Remessa segue normal. Ninguém avisou a Orbe, então ela cobrou. O que foi cobrado eu devolvo ao lojista, junto com o comercial.
> 3. A folha, o ISS, o INSS, o FGTS e os DARFs são de agosto e já estavam provisionados. O repasse da Ponte de 04/09 é o spread de agosto, que já estava como comissão a receber. Com isso, me diga como você lançaria.
> 4. (a) Não sei de quem é o Pix de R$ 7.350. Não é receita até alguém identificar. (b) A devolução é um Pix de repasse que voltou, e ainda não sei o motivo. (c) A transferência saiu do Aurora em 30/09 e cai no Meridiano em 01/10. O que fazer com cada um é decisão sua.

---

## Q-G · Fox AI · 20:52 · valor da divergência de remessa e tolerância

**Pergunta:**
> Proposta: divergência = (Spread % aplicado − contratado) × PTAX × valor em moeda estrangeira, valor cheio, porque é o que o lojista pagou a mais. Ex.: PC-0926-0011: (1,5007% − 1,20%) × 4,0315 × 2.438,46 = R$ 29,56. No mês, a Mundo Aberto soma R$ 1.418,85 em 23 operações.
> 1. A divergência é o valor cheio ou só a nossa metade (50%)?
> 2. Nos outros lojistas, o Spread % oscila ±0,002 p.p. em torno do contratado (ex.: 1,4984% a 1,5015% para quem tem 1,5%). Podemos tratar como arredondamento e não reportar divergência abaixo de 0,01 p.p.?

**Resposta (20:58):**
> É o valor cheio. Quem pagou a mais foi a Mundo Aberto, e é o total que eu contesto com a Ponte. A nossa metade é só como a Ponte divide o spread com a gente.
> O critério de tolerância é de vocês. Se ele estiver escrito, com o motivo, eu sigo. O que eu preciso é não receber alarme de centavo, e também não deixar passar diferença de verdade.

---

## Q-H · Fox AI · resposta 21:13 · arredondamento

**Pergunta:** texto da pergunta não copiado aqui (consultar o Slack). Itens (a)–(d) da resposta.

**Resposta (21:13):**
> Isso mesmo: a Orbe trunca os centavos. A gente não trunca. (a) Arredondamento comum para o centavo. Meio centavo vai para cima, e no negativo vale a mesma regra com o sinal: -0,005 vira -0,01. (b) Linha por linha, e depois soma. (c) Divergência é quando a taxa aplicada é diferente da contratada. Diferença de centavo por causa do truncamento da Orbe não é divergência. O valor da divergência eu quero como valor bruto × (taxa aplicada − contratada). (d) Por operação, com o mesmo arredondamento. No seu exemplo, R$ 131,01.

---

## Q-I · Fox AI · resposta 21:14 · plano de contas

**Pergunta:** texto da pergunta não copiado aqui (consultar o Slack). Itens (a)–(b) da resposta.

**Resposta (21:14):**
> (a) Quero a contrapartida do movimento no banco. Se o valor já estava registrado, o pagamento ou recebimento baixa a conta onde ele estava, e não vira receita ou despesa de novo. Como respondi ao Lucca, a folha, os tributos de agosto e o repasse da Ponte de 04/09 já estavam registrados. (b) Além desses, nada estava provisionado: tarifas, aluguel, cloud, assinaturas e serviços entram direto na despesa do mês. Quando o extrato não deixar claro, declarem a premissa no HIPOTESES.md e sigam.

---

## Q-J · Theo Garcia · resposta 21:45 · nota de remessa e excesso da Mundo Aberto

**Pergunta:** sobre o excesso de spread da Mundo Aberto na nota de remessa (texto da pergunta não copiado aqui; consultar o Slack).

**Resposta (21:45):**
> Entra. A nota de setembro sai pelo realizado, porque é o que a Ponte vai repassar para a gente agora. A contestação é um processo à parte. Se a Ponte devolver a diferença para a Mundo Aberto, a nossa metade sai no mês em que o ajuste acontecer. Deixar como pendência para mim é o caminho certo.

---

## Q-K · Lucca Landeiro · resposta 22:33 · remessa: número e conferência do repasse

**Pergunta:** mensagem do Lucca sobre a remessa (texto da pergunta não copiado aqui; consultar o Slack).

**Resposta (22:33):**
> Número eu não valido. Quem fecha é você, e a banca vai olhar o rastro. Sobre o raciocínio, duas coisas que eu sei: • Não sei ainda como a Ponte vai pagar, porque a contestação nem foi aberta. Não conte que ela vai descontar nada do repasse. • Conferir o TED quando ele cair é uma pendência boa. Fica comigo.

---

## Q-L · Insper AI · resposta 22:34 · contestação com a Ponte

**Pergunta:** sobre a contestação com a Ponte (texto da pergunta não copiado aqui; consultar o Slack).

**Resposta (22:34):**
> Ainda não contestei nada. É para isso que eu preciso do fechamento de vocês. Considerem que estamos dentro do prazo: o fechamento é esta semana. Mantenham como pendência de contestação, com o valor e as operações, porque é isso que eu mando para a Ponte. A duplicada vocês contam uma vez no fechamento, e ela também entra na lista para a Ponte corrigir o relatório.

---

## Q-M · Insper AI · resposta 22:34 · Aurora e Orbe

**Pergunta:** sobre os créditos da Orbe no Aurora e o saldo negativo (texto da pergunta não copiado aqui; consultar o Slack).

**Resposta (22:34):**
> A Orbe deposita tudo no Aurora. Ela não paga lojista direto. Débito e Pix caem no dia seguinte. Crédito e parcelado caem ao longo dos meses seguintes, conforme as parcelas. Por isso o que entra no banco em setembro não bate com o líquido do relatório de setembro. O saldo negativo é a conta garantida que a gente tem no Aurora para pagar os lojistas antes de a Orbe liquidar. Conciliar a Orbe contra o banco, parcela por parcela, não é o que eu preciso neste fechamento. Os créditos da Orbe vocês classificam, e o resto fica para quando tivermos a agenda de recebíveis.

---

## Organização · 17/10 09:21 · requisito de entrega

**Mensagem da organização do hackathon** (não é resposta da Helena; texto como repassado pelo Lucca):
> A banca vai rodar a solução com os arquivos do case e comparar com o saida/ entregue. O mínimo: (1) recebe a pasta do mês, nada fixo para setembro; (2) um comando; (3) mostra o resultado e gera os 6 arquivos; (4) o README explica como rodar e ONDE CONFIGURAR A CHAVE DE API.

---

# 17/10 (manhã): respostas Q-N a Q-Y

Copiadas do `#duvidas-hackathon-ai` sem edição (incorporadas de `docs/_novas_respostas_17-10.md`, que foi apagado). Entre parênteses, quando houver, o resumo da pergunta como registrado na hora.

## Q-N · Barteman (Mateus) · 09:09 · resposta 09:44
**Pergunta (resumo das 7):** Casa × divergência; o que é divergência na remessa e spread negativo; venda cobrada a mais e estornada (Rota TX88446419); estorno TX88445133 da Casa de venda de 21/08; PIX de 18.240 da Ponte Aérea; antecipação da Atlas (R$ 179.592,82 em 15/09 com R$ 55.357,50 vendidos); Orbe cobrando abaixo do contrato.
**Resposta:**
> 1. É diferente de uma divergência comum. A Orbe cobrou certo pela planilha, porque ninguém avisou da isenção. Não há o que cobrar da Orbe: é devolução ao lojista, pendência minha com o comercial. Deixem separado das divergências de contrato, com o valor.
> 2. A divergência na remessa é quando o lojista paga um spread diferente do contratado. O spread negativo eu respondi para a MN AI agora há pouco.
> 3. A venda e o estorno se anulam. Cobro da Orbe só o que sobrou de diferença líquida.
> 4. Vale a taxa da data da venda original, como já está no canal. Em 21/08 a isenção ainda não valia.
> 5. É a Ponte Aérea mandando dinheiro de uma remessa que ainda não foi feita. A operação sai em outubro. A Ponte Aérea Estudantil é lojista e não tem nada a ver com a Ponte Câmbio.
> 6. Isso não deveria acontecer. A antecipação é sobre o que o lojista já vendeu, e a gente não tem trava para isso. Coloquem como alerta: quem precisa saber sou eu e o comercial, e ainda mais com a Atlas sem contrato assinado.
> 7. Também é divergência e eu decido caso a caso. Não aconteceu em setembro, então não gastem tempo nisso.

---

## Q-O · MN AI · 08:43 · resposta 09:44 (spread negativo)
**Pergunta:** os 4 spreads negativos também entram em divergências de taxa, ou só como pendência de contestação?
**Resposta:**
> Para mim, divergência é quando o *lojista* pagou diferente do contrato. No spread negativo o lojista não pagou a mais. O prejuízo é nosso com a Ponte, então é pendência de contestação. Se quiserem listar também nas divergências, tudo bem, desde que fique claro que é outra natureza.

---

## Q-P · Desbravadores · 09:17 · resposta 09:45
**Pergunta:** PIX de 18.240 sem operação; operação na Ponte de CNPJ fora da planilha.
**Resposta:**
> 1. Respondi agora para o Mateus: é dinheiro de uma remessa que sai em outubro.
> 2. Não aconteceu em setembro. Se acontecer, o tratamento que vocês propuseram é razoável. Registrem como premissa.
(Proposta deles no item 2: calcular a metade do spread mesmo assim e abrir pendência de cadastro para o comercial.)

---

## Q-Q · MN AI · 09:21 · resposta 09:47 (Atlas em outubro)
**Pergunta:** quando o comercial confirmar a taxa da Atlas, as 57 transações de setembro são faturadas em outubro?
**Resposta:**
> Quando o comercial confirmar, a taxa vale desde o começo (10/09) e eu faturo setembro junto com outubro. Então sim, outubro precisa puxar as linhas da Atlas de setembro que ficaram pendentes.

---

## Q-R · Desbravadores · 09:29 · resposta 09:48
**Pergunta:** negativos em divergência?; devolução do PIX de 12.400 em 2.1.01.001 ou 2.1.01.002?; folha e impostos sempre provisionados?
**Resposta:**
> 1. Já está no canal, na resposta para a MN AI das 8h43.
> 2. As duas contas fazem sentido. Escolham uma, mantenham o mesmo critério e escrevam o motivo.
> 3. Sempre. Todo mês a folha e os impostos do mês ficam provisionados no fechamento, e o pagamento no mês seguinte baixa a provisão.

---

## Q-S · MN AI · 09:35 · resposta 09:49 (quem aprova regra)
> Taxa e condição comercial, quem aprova é o comercial, e eu registro. Regra de como fechar, aprovo eu. Nas minhas férias, hoje ninguém fecha. É exatamente por isso que vocês estão aqui. Registrar quem aprovou e quando é ótimo.

---

## Q-T · MN AI · 09:33 · resposta 09:53 (avisos e contestação)
**Pergunta:** quem avisa a Orbe/Ponte quando o comercial fecha condição nova?; um rascunho de e-mail de contestação por contraparte serve?
**Resposta:**
> 1. Ninguém tem essa função hoje. O comercial fecha e, quando lembra, manda um e-mail para a Orbe ou a Ponte. A Bridge foi avisada alguns dias depois de 15/09, e a Casa do Estudante e a Mundo Aberto não foram avisadas.
> 2. Serve, e muito. Um rascunho por contraparte, com as operações anexadas, eu reviso e envio. Quantas operações vão em cada um é com vocês.

---

## Q-U · Turma do Barulho · 10:32 · resposta 10:44 (como o financeiro trabalha)
> *1.* A sequência é esta: baixar o relatório da Orbe e o e-mail da Ponte, e exportar os dois extratos; casar as transações da Orbe com a planilha de taxas e calcular a comissão por lojista; fazer o mesmo com a remessa; classificar os extratos no ERP; montar as notas. Quem executa são as duas analistas, e quem confere e aprova sou eu. O registro de que uma etapa terminou é uma aba de controle na mesma planilha, onde cada uma marca "ok" e a data. Não tem nada além disso.
> *2.* A Bia cuida do checkout e da planilha de taxas. O Caio cuida dos bancos e das remessas. Eu confiro, decido as exceções e falo com o comercial, a Orbe e a Ponte. O que mais pesa nos 8 dias:
> • *Comissão de checkout, uns 3 dias.* Metade é trabalho manual, casando nome com EC e CNPJ. A outra metade é retrabalho, quando a planilha está desatualizada.
> • *Remessa e Ponte, uns 2 dias.* A maior parte é espera: perguntar à Ponte e ao comercial e aguardar a resposta.
> • *Classificar os extratos, uns 2 dias.* Quase tudo manual, linha por linha.
> O último dia é para as notas e a minha revisão.
> *3.* Quase tudo que vocês já descobriram aqui no canal estava só na minha cabeça: as condições que o comercial combinou, quem é quem entre os nomes da Orbe e os CNPJs, o que aceito ou contesto da Ponte e o que já estava provisionado. Aparece na comissão, na remessa e na classificação. Se eu faltar, ninguém sabe essas regras.
> *4.* A Orbe já liquida o líquido: a taxa é descontada na hora em que ela paga, e o lojista vê no extrato de repasse que a gente manda. A nota só documenta a taxa que já foi descontada e não gera cobrança nova. Por isso, quando a Orbe cobra a mais, o lojista já recebeu a menos e eu preciso devolver.
> *5.* A gente repassa duas vezes por mês, perto do dia 10 e perto do dia 24, o que a Orbe já liquidou até ali. A regra está no contrato de adesão de cada lojista, que fica numa pasta do comercial.
> *6.* A Ponte responde por e-mail e manda o ajuste no relatório do mês seguinte, como crédito ou débito. Eu confiro e registro no fechamento do mês em que o ajuste aparece.

---

## Q-V · Fox AI · 10:50 · resposta 10:58 (Casa do Estudante)
**Pergunta:** Casa (R$ 15.397,42): (a) uma pendência para Helena e comercial com o total a devolver; (b) as linhas também em divergencias_taxa marcadas "isenção não informada à Orbe", sem entrar no total a cobrar da Orbe?
**Resposta:**
> Do jeito que vocês propuseram serve: uma pendência com o total e o detalhe por transação marcado. Só não pode entrar na cobrança da Orbe.

---

## Q-W · Turma do Barulho · 10:55 · resposta 10:59 (repasse e conta garantida)
> Pela regra, o repasse é do que a Orbe já liquidou. Na prática, quando um lojista pressiona, a Bia às vezes paga antes de a Orbe liquidar, e aí entra a conta garantida. Isso não está escrito em lugar nenhum e não tem limite. É mais uma coisa que depende de quem está fazendo.

---

## Q-X · Casa Barton · 10:56 · resposta 11:01
> 1. Para mim, uma pendência por contraparte e por lojista, com o detalhe das transações anexado. É o que vira o rascunho de contestação que a MN AI propôs. Cadastro e contrato quem decide é o comercial. A Bia mantém a planilha, mas não decide taxa.
> 2. Conta por conta eu não valido. O critério está no canal, na resposta para a Fox AI sobre o plano de contas: se já estava registrado, baixa a conta onde estava, e o resto vai para a natureza.
> 3. A gente não vende acima de 12x. Se aparecer, é pendência.
> 4. São três centavos. Escolham um critério e escrevam qual.
(O item 4 era: divergência da Mundo Aberto pelo Spread % (1.418,85) ou pelo Spread R$ (1.418,88).)

---

## Q-Y · Lucca Landeiro · 11:01 · resposta 11:03 (contas dos fluxos e Atlas)
**Pergunta:** confirmar as contas dos fluxos do dia a dia (repasse 2.1.01.001; TED Orbe 1.1.03.001; aporte para remessa e TED à Ponte 2.1.02.001; transferência entre contas 1.1.09.001) e se o repasse à Atlas segue normal.
**Resposta:**
> Conta por conta eu não valido. Respondi isso para a Casa Barton agora há pouco, e o critério está na resposta para a Fox AI sobre o plano de contas.
> Sobre a Atlas: o repasse não para. O dinheiro é do lojista, e o que fica suspenso é só o faturamento da nossa taxa.

---

## Ainda sem resposta (17/10 ~11h20, como registrado nessa hora)
- Theo Garcia 11:16: (1) Bridge/Mundo Aberto — cobra-se da contraparte se a condição está na planilha mesmo sem aviso?; (2) critério do alerta de antecipação (só lojista sem vendas antes do mês?); (3) valor da contestação do spread negativo (Spread R$ −687,52 ou diferença até o contrato −1.351,87).
- Desbravadores 11:07: como vem o ajuste de contestação no relatório da Ponte e como entra na nota.
- Leandro (Barte) encaminhou 11:04: pacote de outubro; ref_origem com "|"; quem_decide comparado por texto?; pendência de acompanhamento conta como alarme falso?
