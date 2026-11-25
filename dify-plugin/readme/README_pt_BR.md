# Google Flow por useapi.net

**Autor:** useapi · **Versão:** 0.1.0 · **Tipo:** ferramenta · **Código-fonte:** https://github.com/useapi/google-flow-api/tree/main/dify-plugin · **Contato:** support@useapi.net

Use o Google Flow em workflows, chatflows e agentes do Dify. Gere vídeos com som com Veo 3.1 Lite e Omni 1.2 Flash, gere imagens com Nano Banana, estenda e edite vídeos, aumente a resolução até 4K, transforme em GIF, junte clipes e converse com o agente do Google Flow, o agente criativo do próprio Google, que planeja, escreve storyboards e gera para você. Imagens e vídeos voltam como arquivos do Dify.

**Conecte várias contas Google e deixe a useapi.net dividir o trabalho.** Com o e-mail vazio, a useapi.net envia cada job novo para uma conta saudável. Você roda mais jobs em paralelo, soma os créditos do Google Flow de todas as contas e o trabalho continua quando o Google limita uma conta ou ela atinge a cota. Um plugin com uma única chave da Gemini API não faz isso: essa chave é cobrada por chamada e não usa o seu plano Google AI. Veja [Várias contas Google](#várias-contas-google).

> Este plugin chama a [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) da useapi.net, uma API de terceiros. Não é feita, afiliada nem endossada pelo Google. Você precisa de uma assinatura da useapi.net (US$ 15/mês, inclui todas as APIs da useapi.net), uma conta Google com plano Google AI (o plano gratuito serve para Veo 3.1 Lite, Omni 1.2 Flash e Nano Banana) e resolução de captcha: 300 créditos grátis vêm com a primeira conta do Google Flow, depois você adiciona a chave do seu próprio provedor de captcha.

## Planos Google AI e Google Flow

Vídeos gastam os créditos do Google Flow da conta Google que os gera. Imagens não gastam créditos em nenhum plano.

| Plano | Preço por mês | Créditos do Google Flow | Modelos de vídeo | Extras | Vídeos Veo 3.1 Lite (8 s, 720p) |
|---|---|---|---|---|---|
| Gratuito | US$ 0 | 50 por dia | Veo 3.1 Lite (8 s), Omni 1.2 Flash (até 10 s) | Nano Banana 2.1 só com raciocínio alto; upscale de imagem para 2K | cerca de 5 por dia |
| Google AI Plus | US$ 4,99 | 200 por mês | Veo 3.1 Lite (8 s), Omni 1.2 Flash (3 a 15 s) | extensão com Omni 1.2 Flash; upscale de vídeo para 720p e 1080p | cerca de 20 por mês |
| Google AI Pro | US$ 19,99 | 1.000 por mês | como Google AI Plus | como Google AI Plus | cerca de 100 por mês |
| Google AI Ultra $99 | US$ 99,99 | 10.000 por mês | como Google AI Plus, mais vídeos Veo 3.1 Lite de 4 e 6 s | upscale de vídeo e imagem para 4K | cerca de 2.000 por mês |
| Google AI Ultra $199 | US$ 199,99 | 25.000 por mês | como Google AI Ultra $99, mais Veo 3.1 Lite Lower Priority a 0 créditos (só a conta do administrador do plano) | upscale de vídeo e imagem para 4K | cerca de 5.000 por mês |

Todos os planos geram imagens com Nano Banana 2 Lite, Nano Banana 2.1 e Nano Banana Pro. Preços do Google nos EUA em 2026-10-20, do catálogo da API da useapi.net (`https://api.useapi.net/v1/google-flow/models`, `plans`). Os créditos por plano vêm da [página de planos](https://gemini.google/subscriptions/) e da [página de créditos do Google Flow](https://support.google.com/flow/answer/16526234) do Google, como listados na [documentação do Google Flow](https://useapi.net/docs/api-google-flow-v1) da useapi.net em novembro de 2026. A contagem de vídeos divide esses créditos pelo preço do Veo 3.1 Lite no catálogo (10 créditos por 8 segundos, 5 no Google AI Ultra). A tabela mostra só o custo do plano do Google. A assinatura da useapi.net (US$ 15/mês) é à parte.

Por que importa: você usa os créditos que já estão no seu plano Google AI em vez de pagar ao Google por clipe, e pode combinar várias contas ([Várias contas Google](#várias-contas-google)).

## Início rápido

1. **Pegue um token de API da useapi.net.** Assine e copie o token: [Setup useapi.net](https://useapi.net/docs/start-here/setup-useapi?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin).
2. **Conecte uma conta Google.** Siga [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) (a configuração automática leva cerca de 5 minutos). A primeira conta vem com 300 créditos de captcha grátis, então você já pode gerar. Quando acabarem, adicione a chave de um provedor de captcha como a mesma página mostra em [Configure Captcha Providers](https://useapi.net/docs/start-here/setup-google-flow#configure-captcha-providers). O captcha custa cerca de US$ 0,80 a US$ 3,00 por 1.000 gerações, pagos ao provedor.
3. **Instale e autorize o plugin, depois gere um vídeo.** Instale pelo [Marketplace do Dify](https://marketplace.dify.ai/plugins/useapi/google_flow_useapi) ou envie o `.difypkg` das [releases no GitHub](https://github.com/useapi/google-flow-api/releases) em Plugins > Install plugin > Local package file. Em Tools, abra "Google Flow por useapi.net", clique em Authorize, cole o token e salve. Adicione **Gerar vídeo** a um workflow com o prompt "A paper boat floating on a calm pond at sunrise" e execute. O `.mp4` volta como arquivo.

| Credencial | Obrigatória | O que é |
|---|:-:|---|
| Token de API da useapi.net | Sim | O token do passo 1. O Dify guarda como segredo. |
| E-mail padrão da conta Google | Não | Deixe vazio para alternar entre todas as contas conectadas. Preencha só para fixar todas as ferramentas em uma conta Google. |

Ao salvar, o plugin faz uma chamada `GET /accounts` para confirmar o token e que há pelo menos uma conta Google conectada. Ela não chama o Google.

O plugin se conecta a `https://api.useapi.net/v1/google-flow` (token no cabeçalho `Authorization: Bearer`) e baixa as imagens e vídeos prontos dos links assinados do Google em `https://flow-content.google` (sem enviar o token). Um Dify auto-hospedado precisa de HTTPS de saída para os dois.

## Várias contas Google

Adicione cada conta Google do mesmo jeito que a primeira, com [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow). **Listar contas Google** mostra cada conta e se a saúde está OK, **Listar jobs por conta** mostra o que roda em cada uma e **Ver plano e créditos da conta** mostra o plano, os créditos restantes e os modelos de vídeo de uma conta.

**Como funciona o rodízio.** Com o e-mail vazio, Gerar vídeo, Gerar imagem, Enviar imagem ou vídeo e um chat novo com o agente deixam a escolha para a useapi.net. O [balanceador de carga](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs#load-balancing-algorithm) primeiro põe de lado as contas que o Google limitou recentemente ou que atingiram a cota, até o fim da espera. Entre as demais, escolhe a conta com menos jobs em execução e recentes; falhas e limites recentes pesam contra a conta. Se todas forem postas de lado para o modelo, você recebe `429` com a hora de tentar de novo. Com uma única conta nada é posto de lado: o pedido sempre vai para ela.

**O que você ganha.** Mais jobs em paralelo, porque cada job vai para a conta menos ocupada. Mais créditos, porque cada conta traz o próprio plano Google AI. Menos paradas, porque uma conta limitada ou esgotada é pulada e as outras continuam.

**Quando informar um e-mail.**
- Deixe os dois e-mails vazios para alternar. É o melhor padrão.
- Defina o **e-mail padrão nas credenciais** para fixar todas as ferramentas em uma conta. Um e-mail explícito pula o balanceador, então o pedido vai para essa conta mesmo quando ela está posta de lado.
- Informe o **e-mail em uma ferramenta** para mandar só aquela chamada para uma conta, por exemplo para usar os créditos de uma conta Google AI Ultra num upscale 4K.

**Referências fixam a conta.** Uma imagem, vídeo, personagem ou voz que você criou ou enviou pertence a uma conta Google, e todos os itens de um pedido precisam ser da mesma conta. Então um pedido com um ID de mídia roda na conta dessa mídia. Estender, upscale, GIF e juntar rodam na conta do vídeo de origem. Arquivos anexados a uma ferramenta são enviados para a conta dos outros IDs do mesmo pedido. Um chat com o agente fica na conta em que começou: continue com o `chat_id` e use referências dessa conta. Cada conta roda no máximo 3 turnos do agente ao mesmo tempo.

## Ferramentas

20 ferramentas. IDs de mídia têm a forma `user:12345-email:...-video:<id>`; passe-os entre nós como variáveis. Endpoints relativos a `https://api.useapi.net/v1/google-flow`.

| Ferramenta | Nome | Endpoint |
|---|---|---|
| `list_accounts` | Listar contas Google | `GET /accounts` |
| `get_account` | Ver plano e créditos da conta | `GET /accounts/{email}` |
| `list_jobs` | Listar jobs por conta | `GET /jobs` |
| `get_job` | Ver status do job | `GET /jobs/{jobid}` |
| `generate_video` | Gerar vídeo | `POST /videos` |
| `extend_video` | Estender vídeo | `POST /videos/extend` |
| `upscale_video` | Aumentar resolução do vídeo | `POST /videos/upscale` |
| `generate_image` | Gerar imagem | `POST /images` |
| `upscale_image` | Aumentar resolução da imagem | `POST /images/upscale` |
| `video_to_gif` | Vídeo para GIF | `POST /videos/gif` |
| `concatenate_videos` | Juntar vídeos | `POST /videos/concatenate` |
| `upload_image` | Enviar imagem ou vídeo | `POST /assets/{email}` |
| `list_media` | Listar mídia | `GET /assets/media/{email}` |
| `get_media` | Obter mídia | `GET /assets/{mediaGenerationId}` |
| `list_characters` | Listar personagens | `GET /characters` |
| `list_voices` | Listar vozes | `GET /voices` |
| `agent_chat` | Chat com o agente do Google Flow | `POST /agent/chats`, `POST /agent/chats/{chatId}/messages` |
| `agent_get_chat` | Ver chat do agente do Google Flow | `GET /agent/chats/{chatId}` |
| `agent_answer_approval` | Responder ao pedido de aprovação do agente | `POST /agent/chats/{chatId}/approval` |
| `agent_list_chats` | Listar chats do agente do Google Flow | `GET /agent/chats` |

Referências de imagem e vídeo aceitam um ID de mídia ou um arquivo do Dify (PNG, JPEG ou WebP até 20 MB, MP4 até 100 MB). Veo 3.1 Fast, Veo 3.1 Quality e Omni 1.1 Flash não são oferecidos: o Google os desativa em 2026-12-05. As ferramentas de geração retornam texto, JSON, variáveis (`jobid`, `status`, `media_ids`, `file_urls`) e arquivos; as do agente retornam `chat_id`, `status` e `reply`. Os links dos arquivos do Google expiram em cerca de 6 horas; **Obter mídia** dá um novo.

## Exemplos

### Workflow: de imagem para vídeo em dois nós

```
[Start: idea (texto)]
   -> [Google Flow > Gerar imagem]  prompt = {{Start.idea}}, quantidade = 1
   -> [Google Flow > Gerar vídeo]   modelo = Omni 1.2 Flash, start_image = {{Gerar imagem.media_ids}}, espera máxima = 420
   -> [End: video = {{Gerar vídeo.files}}]
```

### Agente: um assistente de vídeo com o agente do Google Flow

Adicione Chat com o agente do Google Flow, Ver chat do agente do Google Flow, Responder ao pedido de aprovação do agente, Gerar vídeo e Ver status do job, com instruções como: "Quando o agente pedir aprovação, diga ao usuário o que ele quer gerar e o custo em créditos do Google Flow, e só responda depois que o usuário concordar", "Se um job ou turno ainda estiver rodando, nunca o inicie de novo: consulte com wait=true", "Deixe o e-mail vazio, a menos que o usuário cite uma conta".

## Espera e limites

- **Limite de 600 segundos do Dify.** Uma chamada de plugin termina após 600 segundos. As ferramentas de vídeo enviam o job, consultam a cada 10 segundos e retornam após 120 segundos por padrão. Se o vídeo não estiver pronto, retornam o `jobid`: chame **Ver status do job** com ele (espera até 120 segundos por chamada). Em um workflow dá para subir a "Espera máxima" até 420 segundos. O job continua depois que a chamada retorna e fica guardado por 7 dias.
- **Tempo.** Um vídeo leva em geral de 60 a 180 segundos. Uma imagem volta em uma chamada. Um turno do agente leva em geral cerca de um minuto, e os vídeos dele ficam prontos um ou dois minutos depois.
- **Aprovações do agente.** Responda em cerca de 4 minutos, senão o Google fecha o pedido.
- **Captcha.** Cada pedido de imagem ou vídeo e cada turno do agente usa um captcha.

## Solução de problemas

| Código | O que significa | O que fazer |
|---|---|---|
| 400 | O pedido foi recusado: modelo ou opção que o plano não tem, combinação errada, ou os captchas grátis acabaram. | Corrija o que a mensagem diz. Para captcha, adicione a chave do provedor. |
| 401 | O token da useapi.net está errado. | Confira o token nas credenciais. |
| 402 | A assinatura da useapi.net não está ativa. | Renove. |
| 403 | O Google recusou o captcha em todas as tentativas (nada foi gerado nem cobrado), o plano não tem o modelo, a conta é tratada como menor de 18 anos, ou o ID é de outro usuário da useapi.net. | Use outra conta ou deixe o e-mail vazio. |
| 404 | A conta não está conectada, ou o job, mídia ou chat não existe. | Conecte a conta com Setup Google Flow. |
| 408 | O job ainda rodava quando a espera terminou. | Consulte **Ver status do job** antes de reenviar. |
| 409 | Um turno do agente está rodando neste chat, ou há uma aprovação pendente. | Responda a aprovação ou espere o turno terminar. |
| 410 | O job expirou. | Jobs ficam guardados por 7 dias. |
| 429 | O Google limita esta conta por ora, todas as contas foram postas de lado, ou a conta já roda 3 turnos do agente. | Espere a hora indicada, conecte mais contas ou deixe o e-mail vazio. |
| 502, 504 | O Google não respondeu com clareza ou a tempo. O pedido pode ter rodado. | Confira o job ou o chat antes de reenviar. |
| 503 | O Google está indisponível por instantes, a mídia não está pronta, ou o provedor de captcha falhou. | Tente de novo em alguns segundos; confira a chave e o saldo do provedor. |
| 596 | O Google rejeitou a sessão da conta. A useapi.net a reverifica sozinha. | Tente de novo em cerca de um minuto; se continuar, adicione a conta de novo. |

## Quanto custa

O plugin é grátis. useapi.net: US$ 15/mês, para todas as APIs. Google: o seu próprio plano Google AI, o gratuito incluído; vídeos gastam os créditos do Google Flow dele e imagens não gastam nada. Captcha: 300 créditos grátis com a primeira conta, depois o seu provedor, cerca de US$ 0,80 a US$ 3,00 por 1.000 gerações.

## Privacidade

O plugin envia pedidos só para `api.useapi.net`, baixa arquivos só de `flow-content.google` e não guarda nada. Veja [PRIVACY.md](../PRIVACY.md) e os [Termos e Política de Privacidade](https://useapi.net/docs/legal) da useapi.net.

## Suporte

- Referência da API: https://useapi.net/docs/api-google-flow-v1
- Exemplos: https://github.com/useapi/google-flow-api
- E-mail support@useapi.net, ou pergunte no [Discord](https://discord.gg/w28uK3cnmF) ou no [Telegram](https://t.me/use_api).
