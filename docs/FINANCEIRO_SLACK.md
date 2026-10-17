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

## Q-J · Theo · resposta 21:45 · nota de remessa e excesso da Mundo Aberto

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
- Theo 11:16: (1) Bridge/Mundo Aberto — cobra-se da contraparte se a condição está na planilha mesmo sem aviso?; (2) critério do alerta de antecipação (só lojista sem vendas antes do mês?); (3) valor da contestação do spread negativo (Spread R$ −687,52 ou diferença até o contrato −1.351,87).
- Desbravadores 11:07: como vem o ajuste de contestação no relatório da Ponte e como entra na nota.
- Leandro (Barte) encaminhou 11:04: pacote de outubro; ref_origem com "|"; quem_decide comparado por texto?; pendência de acompanhamento conta como alarme falso?


---

# 17/10 (fim da manhã): respostas Q-Z a Q-AH

Copiadas do `#duvidas-hackathon-ai` sem edição (lidas no Slack às 13h30, perguntas e respostas inteiras).

## Q-Z · Desbravadores · 11:07 · resposta 11:33 (ajuste da Ponte)

**Pergunta:**
> [Desbravadores] [Financeiro]: O ajuste de contestação que a Ponte manda no relatório do mês seguinte: como ele aparece? É uma linha com o mesmo Nº de Operação da original, ou com um número novo? Vem com alguma observação que identifique a operação contestada? E, ao registrar o ajuste no mês em que ele aparece, como ele entra na nota da Ponte: abate da comissão do mês, nota complementar ou outro tratamento?

**Resposta (11:33):**
> *[Financeiro] Resposta para Desbravadores*
> A Ponte manda o ajuste como uma linha nova, com Nº de Operação próprio e o Spread R$ negativo. A observação traz o número da operação original (“AJUSTE REF PC-…”).
> Ele entra no mês em que aparece. Abate a nossa participação daquele mês, dentro da nota única para a Ponte, e o rastro aponta para a operação original. Nota complementar não fazemos. Se o mês fechar zerado ou negativo, vale a regra que já está no canal: não emite e vira pendência para mim.
> No relatório de setembro não tem nenhum ajuste desse tipo. Isso conta para outubro em diante.
> — Helena

---

## Q-AA · Theo · 11:16 · resposta 11:37 (aviso × contrato, alerta, spread negativo)

**Pergunta:**
> [financeiro] Theo: três perguntas de regra, com exemplo.
>
> 1. Quando a contraparte não foi avisada. Na Casa a senhora disse que a Orbe cobrou certo pela planilha, porque ninguém avisou, e por isso não se cobra da Orbe. Dois casos ficam no meio:
> (a) Bridge: a planilha já dizia 2,19% a partir de 15/09, mas a Orbe só foi avisada dias depois e cobrou 2,59% em 5 vendas de 15 a 18/09 (R$ 29,95, ex.: TX88428053).
> (b) Mundo Aberto: o spread de 1,20% está na planilha desde julho, mas a Ponte nunca foi avisada (23 operações, R$ 1.418,85, ex.: PC-0926-0016).
> O que decide se cobramos da contraparte: (i) a condição estar na planilha, mesmo sem aviso, e aí Bridge e Mundo Aberto seguem como cobrança da Orbe e contestação com a Ponte; ou (ii) a contraparte ter sido avisada, e aí os dois viram devolução nossa ao lojista, como a Casa?
>
> 2. Alerta de antecipação. Na Atlas o alerta é claro: ela antecipou R$ 179.592,82 em 15/09 com R$ 55.357,50 vendidos desde que começou, em 10/09. Mas pela regra "antecipou mais do que vendeu no mês", outros 5 lojistas também acenderiam. Por exemplo, a Canguru antecipou R$ 31.765,12 em 01/09 com R$ 1.934,10 vendidos no mês, provavelmente sobre parcelas de vendas de agosto que o relatório não traz. Alertamos só quem não tem vendas antes do mês (em setembro, só a Atlas), ou existe outro limite que a senhora usa?
>
> 3. Spread negativo. Na pendência de contestação com a Ponte, o valor de cada operação é o spread negativo do relatório (ex.: PC-0926-0210, −R$ 687,52) ou a diferença até o spread do contrato (1,5% sobre a PTAX, −R$ 1.351,87)?

**Resposta (11:37):**
> *[Financeiro] Resposta para Theo*
> 1. *O que decide é o contrato, não o aviso.* A Bridge tem aditivo assinado (2,19% a partir de 15/09). A Mundo Aberto tem o 1,20% negociado e registrado desde julho. Nos dois casos a contraparte cobrou diferente de uma condição contratada. Isso é divergência: eu contesto com a Orbe e com a Ponte, e o lojista é ressarcido. O aviso atrasado é problema nosso de processo, mas não muda quem deve.
>  A Casa é outra coisa. É uma concessão do comercial, fora do contrato, para segurar o cliente. A Orbe cobrou o que estava contratado. Quem abriu mão da receita fomos nós, então a devolução sai do nosso bolso.
> 2. *A antecipação é sobre a agenda inteira do lojista*, inclusive parcelas de vendas de meses anteriores que o relatório de setembro não traz. Por isso a comparação com as vendas do mês acende lojista demais. O que me preocupa é lojista novo, sem histórico, antecipando alto. Não temos um limite definido. O critério é de vocês: escrevam no `HIPOTESES.md`.
> 3. *Coloquem os dois na pendência*, deixando claro qual é qual: o spread negativo do relatório, que é o que aconteceu, e a diferença até o spread do contrato, que é o que eu vou pedir à Ponte, porque a trava deveria ter sido honrada.
> — Helena

---

## Q-AB · Southlands · 11:23 · resposta 11:38 (regras gerais)

**Pergunta:**
> [Southlands] [financeiro]
>
> 1. Estornos: quando o estorno é de uma venda de mês anterior, qual é a regra geral para achar a taxa contratada que vale? A taxa é a da data da venda original, e a faixa (modalidade e parcelas) vem da linha do próprio estorno?
>
> 2. Lojista sem contrato vigente ou com taxa não confirmada: qual é o tratamento padrão? Ele aparece na comissão com valor zero e uma pendência, ou fica fora do arquivo? O repasse segue normal e só a nota fica suspensa?
>
> 3. Cobrança acima do contrato: quem arca com o valor cobrado a mais, e como ele volta ao lojista? É devolução pela Tarvo, contestação à Orbe ou à Ponte, ou depende do caso? Na lista de divergências, entra transação por transação, mesmo quando venda e estorno se anulam?
>
> 4. Comissão do mês negativa ou zerada: quando estornos superam as vendas, ou quando há isenção comercial, o saldo vira pendência sem nota? Valores de devolução ao lojista ficam separados das divergências de contrato?
>
> 5. Ajustes de meses anteriores: créditos e débitos da Ponte (ou da Orbe) referentes a meses fechados entram na comissão e na nota do mês em que aparecem, ou só como pendência? Há algum critério geral de quem decide cada tipo de pendência?

**Resposta (11:38):**
> *[Financeiro] Resposta para Southlands*
> Quase tudo isso já está respondido no canal. Vale ler as respostas antes de seguir:
> 1. *Taxa do estorno:* sim. Vale a taxa da data da venda original, e a faixa sai da própria linha do estorno (modalidade e parcelas).
> 2. *Lojista sem contrato:* está no canal (Atlas). Não fatura, vira pendência, e o repasse continua normal. Se ele aparece com zero ou fica fora do arquivo de comissões é com vocês.
> 3. *Cobrança acima do contrato:* está no canal (resposta ao Theo). Sobre a lista: é transação por transação. O estorno de uma venda que veio com taxa errada também entra, com valor negativo.
> 4. *Zerado ou negativo:* está no canal (notas). Não emite nota e vira pendência. A devolução da Casa fica separada das divergências.
> 5. *Ajustes de meses anteriores:* estão no canal (estorno de agosto, ajuste da Ponte). Quem decide cada pendência também já foi respondido.
> — Helena

---

## Q-AC · Prime · 11:26 · resposta 11:41 (Atlas: identidade e apuração)

**Pergunta:**
> [Financeiro] [Prime]
>
> Bom dia! Duas questões sobre a Atlas Idiomas (EC 1076801732), para fechar setembro sem faturar o que não pode ser faturado.
>
> Entendemos a regra: sem contrato assinado na aba vigente, não emitimos nota e não calculamos divergência para ela. Faltam dois pontos para a saída ficar coerente:
>
> 1) Identidade: a aba "ANTIGO 2025" traz Atlas Idiomas Ltda com CNPJ 39.566.044/0001-19. Podemos usar esse CNPJ só para identificar a Atlas na saída (identidade, não taxa), ou prefere que ela apareça sem CNPJ até o comercial confirmar? São 57 transações e R$ 262.138,61 de volume bruto em setembro.
>
> 2) Apuração: "não faturar" nós lemos como não emitir nota. E a comissão? A Atlas sai em comissoes_por_lojista.csv com valor zero e pendência aberta, ou fica fora do arquivo? Hoje não temos taxa contra a qual apurar, então nossa premissa é deixá-la zerada, com as 57 transações no rastro e o valor que a Orbe cobrou (R$ 7.876,05) registrado na pendência para o comercial.
>
> Aproveitando: a Atlas antecipou R$ 235.943,10 em setembro contra R$ 135.428,90 de vendas no mesmo mês. Pela resposta que você deu ao Mateus, estamos tratando como alerta para você e o comercial, e não como erro de cálculo.

**Resposta (11:41):**
> *[Financeiro] Resposta para Prime*
> 1. Sim, o CNPJ é da Atlas, é a mesma empresa. Podem usar para identificar. Só a taxa daquela aba é que não vale.
> 2. Zerada com pendência ou fora do arquivo, as duas formas servem. O que não pode é faturar. Escolham uma e registrem no `HIPOTESES.md`.
> 3. É alerta, como já está no canal. Os números ficam com vocês, eu não confiro.
> — Helena

---

## Q-AD · Prime · 11:27 · resposta 11:41 (Casa: data-base da isenção)

**Pergunta:**
> [Financeiro] [Prime]
>
> Sobre a tarifa zerada da Casa do Estudante (EC 1018325654), uma confirmação de data-base.
>
> Estamos aplicando a isenção pela data da VENDA, a partir de 01/09/2026, e não pela data do movimento. É o que torna coerente a sua resposta ao Mateus sobre o TX88445133: estorno em setembro de uma venda de 21/08, que mantém 1,49% porque em agosto a isenção ainda não valia.
>
> Com essa leitura, setembro da Casa fica assim:
> - 118 transações isentas, comissão contratada R$ 0,00;
> - o estorno da venda de 21/08 abate R$ 5,50 pela taxa de agosto;
> - comissão do mês: -R$ 5,50, portanto sem nota fiscal e com pendência para você, pela regra (b) das notas;
> - R$ 15.396,77 cobrados pela Orbe durante a isenção, que entram como devolução ao lojista, separados das divergências de contrato e fora da cobrança da Orbe, como você definiu com a Fox AI.
>
> Confirma a data-base pela data da venda? Se for pela data do movimento, o estorno também fica isento e a comissão da Casa vai a zero em vez de -R$ 5,50.

**Resposta (11:41):**
> *[Financeiro] Resposta para Prime*
> A regra já está no canal: a isenção vale para venda a partir de 01/09, e estorno de venda anterior segue a taxa da venda. Os números eu não confiro. Se o mês da Casa fechar negativo, vale a regra das notas.
> — Helena

---

## Q-AE · Datarmos · 11:47 · resposta 11:49 (Casa, provisão, alerta)

**Pergunta:**
> [Financeiro] [Datarmos]: três perguntas para fechar setembro.
>
> 1. Casa do Estudante: lista de divergências
> Na resposta para a Fox AI (17/10 10h58), a senhora aceitou as 118 transações também em divergencias_taxa.csv, marcadas como "isenção não informada à Orbe" e fora da cobrança da Orbe. Antes, tinha pedido para deixar separado das divergências de contrato. Hoje deixamos o total (R$ 15.396,77) só na pendência, com o detalhe por transação no rastro. A senhora precisa das 118 linhas em divergencias_taxa.csv, ou basta a pendência com o detalhe anexado?
>
> 2. Provisão de folha e impostos de setembro
> A senhora disse que todo mês a folha e os impostos do mês ficam provisionados no fechamento. O pacote só traz os pagamentos de agosto feitos em setembro, sem os valores de folha e impostos de setembro. O fechamento precisa gerar o lançamento de provisão de setembro? Se precisar, de onde vêm os valores? Ou isso fica com a senhora fora do fechamento automático?
>
> 3. Alerta de antecipação da Atlas: reversões contam?
> A Atlas antecipou R$ 179.592,82 até 15/09, com R$ 55.357,50 em vendas até essa data. Duas antecipações foram revertidas depois: AN88445637 (15/09, revertida em 17/09) e AN88446517 (24/09, revertida em 26/09). Para o alerta "antecipação acima das vendas", consideramos o que foi antecipado, mesmo que revertido depois, ou só o que ficou valendo depois das reversões?

**Resposta (11:49):**
> *[Financeiro] Resposta para Datarmos*
> 1. Basta a pendência com o total e o detalhe por transação. Se quiserem pôr as linhas também em divergências, marcadas como isenção, tudo bem, mas não precisa. O que importa é ficar separado das divergências de contrato e fora da cobrança da Orbe.
> 2. Fica fora do fechamento de vocês. A provisão de setembro quem faz é a contabilidade, comigo, com a folha e as guias, e isso não está no pacote. O fechamento de vocês classifica o que passou nos extratos.
> 3. Esse critério é de vocês. O alerta é para mim e para o comercial e não muda nenhum número. Registrem a escolha no `HIPOTESES.md`.
> — Helena

---

## Q-AF · Turma do Barulho · 12:27 · resposta 12:31 (o que muda de um mês para outro)

**Pergunta:**
> [financeiro] Turma do Barulho: para entender como o fechamento muda de um mês para outro, em outubro podemos receber arquivos com colunas, abas ou formatos diferentes, novas fontes, arquivos ausentes ou correções de arquivos já enviados? Ou a estrutura permanece igual e mudam apenas os registros, lojistas e condições comerciais?
> Quando faltar uma fonte ou chegar uma informação nova sem regra definida, vocês esperam que o fechamento inteiro aguarde ou que as partes independentes sejam concluídas, deixando explícitos os resultados provisórios, os bloqueios e as pendências? Quem decide quando esses casos podem ser liberados?

**Resposta (12:31):**
> *[Financeiro] Resposta para Turma do Barulho*
> A estrutura é a mesma todo mês: mesmas fontes, mesmas colunas. Mudam os registros, os lojistas e as condições. Mas na prática acontece de arquivo chegar atrasado, de a Orbe mandar ajuste depois do relatório, e já teve parceiro mudando o layout sem avisar. Prefiro que a solução avise a que quebre sem ninguém perceber.
> Quando falta alguma coisa, eu não seguro o mês inteiro. Fecha o que não depende daquilo, marca o que é provisório e deixa claro o que está bloqueado e por quê. Quem libera sou eu. Se for taxa ou cadastro, o comercial decide antes.
> — Helena

---

## Q-AG · Fox AI · 12:36 · resposta 12:50 (alerta pelo pico)

**Pergunta:**
> [financeiro] Fox AI: alerta de antecipação (Atlas). Em 15/09 ela tinha R$ 179.592,82 antecipados contra R$ 55.357,50 vendidos desde que começou (10/09). Depois, duas antecipações foram revertidas (17/09 e 26/09), e no fim do mês o antecipado líquido (R$ 127.230,96) fica abaixo das vendas (R$ 135.428,90). Propomos alertar pelo pico (o risco existiu quando o dinheiro foi adiantado) e citar as reversões no alerta. Confere, ou o alerta considera só o saldo do fim do mês?

**Resposta (12:50):**
> *[Financeiro] Resposta para Fox AI*
> O critério do alerta é de vocês, como já está no canal. A proposta é razoável: registrem no `HIPOTESES.md` e sigam.
> — Helena

---

## Q-AH · Lucca Landeiro · 12:44 · resposta 12:50 (valor da devolução)

**Pergunta:**
> [Financeiro] Lucca Landeiro: na devolução ao lojista, usamos o que a Orbe descontou de fato (valor_taxa) menos a comissão contratada, porque o lojista recebeu o líquido (Q-U 4). Na Casa isso dá R$ 15.396,77, contra R$ 15.397,42 pela fórmula da divergência (bruto × diferença de taxa), que mantivemos em divergencias_taxa.csv como a senhora definiu. A diferença é o truncamento da Orbe. A devolução segue esse valor cobrado de fato?

**Resposta (12:50):**
> *[Financeiro] Resposta para Lucca Landeiro*
> Devolvo o que saiu do bolso do lojista, o que foi descontado de fato. A diferença para a fórmula é centavo: segue como você fez.
> — Helena

---

## Q-AI · David · 13:19 · resposta 13:34 (Casa: data-base da antecipação)

**Pergunta:**
> *[Financeiro]* 
> A isenção da Casa do Estudante inclui antecipação de setembro a dezembro. Para essa tarifa, a isenção vale pela data da antecipação ou pela data das vendas que geraram os recebíveis?
> Ex: a AN88445172 ocorreu em 09/09, mas não traz referência nem data das vendas originais. Se ela antecipou recebíveis de agosto, a tarifa também fica zerada? Ou precisamos identificar essas vendas antes de calcular a comissão e a devolução?

**Resposta (13:34):**
> *[Financeiro] Resposta para David*
> Vale pela data da antecipação. A antecipação é um serviço que a gente presta no dia em que ela acontece: se foi em setembro, está dentro da isenção. Não precisa ir atrás das vendas de origem.
> — Helena

---

## Q-AJ · Lucca Landeiro · 13:19 · resposta 13:34 (arquivo de ajustes tardios)

**Pergunta:**
> [Financeiro] Lucca Landeiro: sobre o 06_orbe_ajustes_tardios: (1) esse arquivo de ajustes tardios vem todo mês e sempre fecha junto com o mês dele, mesmo chegando depois do relatório? (2) Se um ajuste trouxer um id_transacao que já está no relatório principal (correção de uma linha), vale a linha do ajuste e a original sai? Em setembro não acontece; é para outubro não depender de adivinhação.

**Resposta (13:34):**
> *[Financeiro] Resposta para Lucca Landeiro*
> 1. Vem quando a Orbe tem ajuste, não todo mês. Se chega antes de eu aprovar o fechamento, entra no mês do movimento, como agora. Se chegar depois da aprovação, entra no mês seguinte.
> 2. Correção de uma linha com o mesmo id nunca aconteceu. Se acontecer, o critério é de vocês: deixem claro no `HIPOTESES.md` e mostrem a pendência para mim.
> — Helena

---

## Q-AK · Turma do Barulho · 13:35 · resposta 14:08 (bandeira diferente no estorno)

**Pergunta:**
> [financeiro]
> Helena, encontramos sete estornos no `06` com bandeira diferente da venda referenciada (estorno → venda):
> • `TX88447011` → `TX88413573`: AMEX → VISA
> • `TX88447030` → `TX88438558`: ELO → VISA
> • `TX88447044` → `TX88425142`: HIPERCARD → ELO
> • `TX88447057` → `TX88430977`: AMEX → ELO
> • `TX88447070` → `TX88424537`: ELO → VISA
> • `TX88447093` → `TX88416714`: VISA → AMEX
> • `TX88447109` → `TX88428997`: VISA → ELO
> As bandeiras acima estão na ordem *venda → estorno*. EC, data original, modalidade, parcelas e taxa aplicada conferem; bruto, taxa e líquido são opostos exatos, sem outra anulação referenciada.
> Propomos manter esses vínculos e incluir os estornos em setembro pela taxa contratada da venda original, preservando os dados e registrando a divergência de bandeira para correção com a Orbe. Como bandeira não determina a taxa nas regras informadas, ela não alteraria o cálculo. Você confirma esse tratamento?

**Resposta (14:08):**
> *[Financeiro] Resposta para Turma do Barulho*
> Bandeira não muda a taxa para a gente. A Orbe às vezes troca a bandeira no estorno; não precisa contestar nem abrir pendência. Sigam com o vínculo pela referência, como vocês fizeram.
> — Helena

---

## Q-AL · Desbravadores · 13:36 · resposta 14:10 (ajuste sem a transação original)

**Pergunta:**
> [Desbravadores] [Financeiro] duas dúvidas sobre os arquivos de ajustes que a Orbe manda depois do relatório:
> 1. Se uma mesma transação (mesmo id_transacao) aparecer no relatório e no arquivo de ajustes, como devemos tratar? E se ela aparecer com valores diferentes em cada arquivo?
> 2. Se o arquivo de ajustes trouxer o estorno, ou a reversão de antecipação, de uma transação deste mesmo mês que não está em nenhum arquivo da Orbe que recebemos, como devemos tratar?

**Resposta (14:10):**
> *[Financeiro] Resposta para Desbravadores*
> 1. Já está no canal, na resposta ao Lucca.
> 2. Em setembro isso não acontece: todas as referências do arquivo de ajustes estão no relatório. Se um dia acontecer, o ajuste entra pelo valor que veio e vira pendência para eu pedir a original à Orbe.
> — Helena

---

## Q-AM · Turma do Barulho · 13:48 · resposta 14:11, da Organização (auditabilidade do rastro)

**Pergunta:**
> Qual a estrutura de rastro desejada e existe algum padrão nice-to-have para ser adotado para ser auditavel para a equipe tanto da Tarvo quanto da Barte?

**Resposta (14:11):**
> *[Logística] Resposta para Turma do Barulho*
> O mínimo é o `rastro.csv` no formato das instruções (`id_saida; arquivo_origem; ref_origem; valor`): toda comissão e toda nota com um `id_saida`, e a soma de `valor` por `id_saida` batendo com o número reportado.
> Para ficar auditável de verdade, ajuda ter:
> • rastro também das divergências e da nota da Ponte;
> • um registro de cada execução: quais arquivos entraram, quantas linhas de cada, data e hora;
> • em cada linha, a regra aplicada (taxa contratada usada, isenção, estorno pela venda original).
> Quem abrir tem que conseguir refazer qualquer número sem perguntar para vocês.
> — Organização

---

## Ainda sem resposta (17/10 ~15h10)

- Desbravadores 12:04: o Spread R$ negativo da linha "AJUSTE REF PC-…" é o spread inteiro (a participação cai pela metade) ou já é a participação?
