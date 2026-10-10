# Drop Hunter 🎯 - @prints.raros

> Bot serverless que monitora drops raros na Artwalk e notifica em tempo real no Telegram. Primeiro a saber, primeiro a postar.

**Status:** 🟢 v1.0 em produção - `ARTWALK DUNK LOW PANDA - DD1391-100` com detecção de `Tam 42: 100 un`

[Telegram](https://img.shields.io/badge/Telegram-Drop%20Hunter%20Raros-26A5E4?style=flat&logo=telegram)
[AWS](https://img.shields.io/badge/AWS-SAM%20%7C%20Lambda%20%7C%20EventBridge%20%7C%20DynamoDB-FF9900?style=flat&logo=amazonaws)
[Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)

---

### 🚨 Como funciona

```
[EventBridge - a cada 2min] → ArtwalkScraper → DynamoDB (drop-hunter-stock) 
    → EventBus (drop-hunter-events) → NotifierFunction → Telegram @prints.raros
```

1. **Scraper** bate na página `https://www.artwalk.com.br/tenis-nike-dunk-low-retro-masculino-dd139-1-100/p`
2. Extrai `productId` do HTML e consulta `api/catalog_system/pub/products/search`
3. Soma `AvailableQuantity` de todos os SKUs
4. Compara com DynamoDB: se `old=0` e `new>0` → RARO DETECTADO
5. **Notifier** envia mensagem formatada com tamanhos disponíveis e link direto

Exemplo real que já recebemos:

```
🚨 RARO DETECTADO!

ARTWALK DUNK LOW PANDA - DD1391-100
Voltou com 140 unidades!

📦 Disponíveis:
• Tam 38: 10
• Tam 39: 10
• Tam 41: 10
• Tam 42: 100
• Tam 43: 10

🔗 Comprar: https://www.artwalk.com.br/tenis-nike-dunk-low-retro-masculino-dd139-1-100/p

@prints.raros
```

### 📁 Estrutura

```
drop-hunter/
├── template.yaml              # SAM - 1 EventBus + 1 DynamoDB + 2 Lambdas
├── src/
│   ├── artwalk/
│   │   └── artwalk_scraper.py # Scraper VTEX + PutEvents
│   └── notifier/
│       ├── app.py             # Formatação Telegram
│       └── requirements.txt   # requests
└── .gitignore
```

### 🚀 Deploy

Pré-requisitos: `aws cli`, `sam cli` configurado em `us-east-1`

```bash
# 1. Criar bot no @BotFather e pegar token
# 2. Pegar chat_id (grupo ou seu id)

aws ssm put-parameter --name /drop-hunter/bot-token --value "SEU_TOKEN" --type String --overwrite --region us-east-1
aws ssm put-parameter --name /drop-hunter/chat-id --value "SEU_CHAT_ID" --type String --overwrite --region us-east-1

# 3. Deploy
sam build
sam deploy --stack-name drop-hunter --capabilities CAPABILITY_IAM --resolve-s3 --region us-east-1

# 4. Testar forçando drop (zera estoque e roda scraper)
aws dynamodb delete-item --table-name drop-hunter-stock --key '{"sku": {"S": "ARTWALK DUNK LOW PANDA - DD1391-100"}}' --region us-east-1
aws lambda invoke --function-name drop-hunter-artwalk-scraper --region us-east-1 out.json
cat out.json # {"status":"notified","old":0,"new":140}
```

### 🔧 Variáveis

| Lambda | Env | Descrição |
|--------|-----|-----------|
| `ArtwalkScraper` | `TABLE_NAME` | `drop-hunter-stock` |
| | `EVENT_BUS_NAME` | `drop-hunter-events` |
| `NotifierFunction` | `BOT_TOKEN` | `{{resolve:ssm:/drop-hunter/bot-token}}` |
| | `CHAT_ID` | `{{resolve:ssm:/drop-hunter/chat-id}}` |

### 🐛 Fixes que já passamos (v1.0)

- `404 SEU_TOKEN_NOVO_AQUI` → token placeholder → revogado via @BotFather
- `AccessDeniedException events:PutEvents on default` → faltava `Source`, `DetailType`, `EventBusName` no `put_events`
- `TÃªnis` → encoding `latin1` → `utf8`
- `Ver no site` → `sizes_simple` filtrado `qty>0` pra não estourar limite do EventBridge

### 🗺️ Roadmap v1.1

- [ ] Loop de múltiplos SKUs (Dunk High, AJ1, New Balance)
- [ ] Dashboard `/stats` no Telegram
- [ ] Filtro por tamanho (só notificar se 42 voltar)
- [ ] Histórico de drops no DynamoDB + gráfico

---

Feito por [@jairocandrade](https://instagram.com/jairocandrade) para [@prints.raros](https://instagram.com/prints.raros)

> Se o 42 voltar, você sabe primeiro.
