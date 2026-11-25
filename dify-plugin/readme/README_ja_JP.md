# Google Flow by useapi.net

**作者：** useapi · **バージョン：** 0.1.0 · **種類：** ツール · **ソース：** https://github.com/useapi/google-flow-api/tree/main/dify-plugin · **連絡先：** support@useapi.net

Dify のワークフロー、チャットフロー、エージェントから Google Flow を使えます。Veo 3.1 Lite と Omni 1.2 Flash で音声付き動画を作り、Nano Banana で画像を作り、動画の延長や編集、最大 4K へのアップスケール、GIF 変換、クリップの結合ができます。Google Flow エージェント（企画や絵コンテを作り、生成まで行う Google 自身のクリエイティブエージェント）とのチャットも可能です。画像と動画は Dify のファイルとして返ります。

**複数の Google アカウントを接続し、作業を useapi.net に振り分けさせられます。** メールを空欄にすると、useapi.net が新しいジョブを正常なアカウントに送ります。並行して動かせるジョブが増え、各アカウントの Google Flow クレジットをまとめて使え、Google が 1 つのアカウントを制限したり上限に達したりしても作業が続きます。1 つの Gemini API キーを使うプラグインではできません。そのキーは呼び出しごとの課金で、Google AI プランも使いません。詳しくは[複数の Google アカウント](#複数の-google-アカウント)をご覧ください。

> 本プラグインは useapi.net の [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin)（サードパーティ API）を呼び出します。Google が作成・提携・承認したものではありません。必要なもの：useapi.net のサブスクリプション（月額 15 ドル、useapi.net の全 API を含む）、Google AI プランのある Google アカウント（無料プランでも Veo 3.1 Lite・Omni 1.2 Flash・Nano Banana を利用可）、キャプチャ解決（最初の Google Flow アカウントに無料 300 回分、その後はご自身のキャプチャサービスのキー）。

## Google AI プランと Google Flow

動画は、それを作る Google アカウントの Google Flow クレジットを消費します。画像はどのプランでもクレジットを消費しません。

| プラン | 月額 | Google Flow クレジット | 動画モデル | その他 | Veo 3.1 Lite 動画（8 秒、720p） |
|---|---|---|---|---|---|
| 無料 | $0 | 1 日 50 | Veo 3.1 Lite（8 秒）、Omni 1.2 Flash（10 秒まで） | Nano Banana 2.1 は思考レベル「高」のみ。画像の 2K アップスケール | 1 日約 5 本 |
| Google AI Plus | $4.99 | 月 200 | Veo 3.1 Lite（8 秒）、Omni 1.2 Flash（3〜15 秒） | Omni 1.2 Flash の延長。動画の 720p・1080p アップスケール | 月約 20 本 |
| Google AI Pro | $19.99 | 月 1,000 | Google AI Plus と同じ | Google AI Plus と同じ | 月約 100 本 |
| Google AI Ultra $99 | $99.99 | 月 10,000 | Google AI Plus に加え、4 秒・6 秒の Veo 3.1 Lite | 動画と画像の 4K アップスケール | 月約 2,000 本 |
| Google AI Ultra $199 | $199.99 | 月 25,000 | Google AI Ultra $99 に加え、0 クレジットの Veo 3.1 Lite 低優先度（プラン管理者のアカウントのみ） | 動画と画像の 4K アップスケール | 月約 5,000 本 |

どのプランでも Nano Banana 2 Lite・Nano Banana 2.1・Nano Banana Pro で画像を作れます。価格は 2026-10-20 時点の Google の米国価格で、useapi.net API カタログ（`https://api.useapi.net/v1/google-flow/models` の `plans`）によります。プランごとのクレジットは Google の[プランページ](https://gemini.google/subscriptions/)と [Google Flow クレジットのページ](https://support.google.com/flow/answer/16526234)によるもので、2026 年 11 月の useapi.net [Google Flow ドキュメント](https://useapi.net/docs/api-google-flow-v1)に掲載されています。本数はカタログの Veo 3.1 Lite の価格（8 秒 10 クレジット、Google AI Ultra は 5）で割った値です。表は Google のプラン料金のみで、useapi.net のサブスクリプション（月額 15 ドル）は別です。

ポイント：クリップごとに Google に支払うのではなく、Google AI プランに含まれるクレジットを使います。複数のアカウントを組み合わせることもできます（[複数の Google アカウント](#複数の-google-アカウント)）。

## クイックスタート

1. **useapi.net の API トークンを取得**：サブスクリプションを開始してトークンをコピーします。[Setup useapi.net](https://useapi.net/docs/start-here/setup-useapi?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin)
2. **Google アカウントを接続**：[Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) に従います（自動セットアップで約 5 分）。最初のアカウントには無料のキャプチャ 300 回分が付くので、すぐに生成できます。使い切ったら、同じページの [Configure Captcha Providers](https://useapi.net/docs/start-here/setup-google-flow#configure-captcha-providers) に従ってキャプチャサービスのキーを追加します。費用は生成 1,000 回あたり約 0.80〜3.00 ドルで、サービスに支払います。
3. **プラグインをインストールして認証し、動画を作る**：[Dify マーケットプレイス](https://marketplace.dify.ai/plugins/useapi/google_flow_useapi)からインストールするか、[GitHub releases](https://github.com/useapi/google-flow-api/releases) の `.difypkg` を「プラグイン > プラグインをインストール > ローカルパッケージファイル」からアップロードします。「ツール」で「Google Flow by useapi.net」を開き、認証してトークンを保存します。ワークフローに「動画を生成」を追加し、プロンプト「A paper boat floating on a calm pond at sunrise」で実行すると `.mp4` がファイルで返ります。

| 認証情報 | 必須 | 内容 |
|---|:-:|---|
| useapi.net API トークン | はい | 手順 1 のトークン。Dify が暗号化して保存します。 |
| 既定の Google アカウントのメール | いいえ | 空欄にすると接続済みの全アカウントでローテーションします。すべてのツールを 1 つのアカウントに固定したい場合のみ入力します。 |

保存時に `GET /accounts` を 1 回呼び出し、トークンが有効で Google アカウントが 1 つ以上接続されていることを確認します（Google は呼び出しません）。

プラグインは `https://api.useapi.net/v1/google-flow`（トークンは `Authorization: Bearer` ヘッダー）に接続し、完成した画像と動画を `https://flow-content.google` の Google 署名付きリンクからダウンロードします（トークンは送りません）。セルフホストの Dify では両方への HTTPS 接続が必要です。

## 複数の Google アカウント

各 Google アカウントは [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow) で追加します。「Google アカウント一覧」で各アカウントの状態、「アカウントごとのジョブ一覧」で各アカウントの実行状況、「アカウントのプランとクレジット」でプラン・残りクレジット・動画モデルを確認できます。

**ローテーションの仕組み**：メールが空欄のとき、「動画を生成」「画像を生成」「画像・動画をアップロード」と新しいエージェントチャットはアカウント選びを useapi.net に任せます。その[ロードバランサー](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs#load-balancing-algorithm)は、最近 Google に制限されたアカウントや上限に達したアカウントをクールダウンが終わるまで外し、残りの中から実行中・最近のジョブが最も少ないアカウントを選びます。最近の失敗やレート制限はそのアカウントに不利に働きます。すべてのアカウントが外れている場合は `429` と再試行時刻が返ります。アカウントが 1 つだけなら外されず、常にそのアカウントに送られます。

**メリット**：最も空いているアカウントに送るので並行ジョブが増え、各アカウントの Google AI プランの分だけクレジットが増え、制限されたアカウントを飛ばして他のアカウントが作業を続けます。

**メールを指定するとき**：
- 両方とも空欄ならローテーション。これが最適な既定です。
- 認証情報の**既定のメール**を設定すると、すべてのツールが 1 つのアカウントに固定されます。メールを指定するとロードバランサーを通らないため、外されているアカウントにも送られます。
- **ツールごとのメール**は、その呼び出しだけを特定のアカウントに送ります（例：4K アップスケールに Google AI Ultra アカウントのクレジットを使う）。

**参照はアカウントを固定します**：作成・アップロードした画像、動画、キャラクター、音声は 1 つの Google アカウントに属し、1 つのリクエスト内の参照はすべて同じアカウントのものである必要があります。メディア ID を使うリクエストは、そのメディアのアカウントで実行されます。延長・アップスケール・GIF・結合は元動画のアカウントで実行されます。ツールに添付したファイルは、同じリクエストの他の ID のアカウントにアップロードされます。エージェントチャットは開始したアカウントのまま続くので、`chat_id` で続け、そのアカウントの参照を使ってください。1 アカウントで同時に実行できるエージェントのターンは 3 つまでです。

## ツール

20 個のツール。メディア ID は `user:12345-email:...-video:<id>` の形で、変数としてノード間で受け渡せます。エンドポイントは `https://api.useapi.net/v1/google-flow` からの相対パスです。

| ツール | 名前 | エンドポイント |
|---|---|---|
| `list_accounts` | Google アカウント一覧 | `GET /accounts` |
| `get_account` | アカウントのプランとクレジット | `GET /accounts/{email}` |
| `list_jobs` | アカウントごとのジョブ一覧 | `GET /jobs` |
| `get_job` | ジョブの状態を取得 | `GET /jobs/{jobid}` |
| `generate_video` | 動画を生成 | `POST /videos` |
| `extend_video` | 動画を延長 | `POST /videos/extend` |
| `upscale_video` | 動画をアップスケール | `POST /videos/upscale` |
| `generate_image` | 画像を生成 | `POST /images` |
| `upscale_image` | 画像をアップスケール | `POST /images/upscale` |
| `video_to_gif` | 動画を GIF に | `POST /videos/gif` |
| `concatenate_videos` | 動画を結合 | `POST /videos/concatenate` |
| `upload_image` | 画像・動画をアップロード | `POST /assets/{email}` |
| `list_media` | メディア一覧 | `GET /assets/media/{email}` |
| `get_media` | メディアを取得 | `GET /assets/{mediaGenerationId}` |
| `list_characters` | キャラクター一覧 | `GET /characters` |
| `list_voices` | 音声一覧 | `GET /voices` |
| `agent_chat` | Google Flow エージェントとチャット | `POST /agent/chats`, `POST /agent/chats/{chatId}/messages` |
| `agent_get_chat` | Google Flow エージェントのチャットを取得 | `GET /agent/chats/{chatId}` |
| `agent_answer_approval` | エージェントの承認リクエストに回答 | `POST /agent/chats/{chatId}/approval` |
| `agent_list_chats` | Google Flow エージェントのチャット一覧 | `GET /agent/chats` |

画像・動画の参照には、メディア ID か Dify のファイル（PNG・JPEG・WebP は 20 MB、MP4 は 100 MB まで）を指定できます。Veo 3.1 Fast・Veo 3.1 Quality・Omni 1.1 Flash は Google が 2026-12-05 に終了するため提供していません。生成ツールはテキスト、JSON、変数（`jobid`・`status`・`media_ids`・`file_urls`）、ファイルを返し、エージェントツールは `chat_id`・`status`・`reply` を返します。Google のファイルリンクは約 6 時間で失効します。「メディアを取得」で新しいリンクを得られます。

## 使用例

### ワークフロー：2 つのノードで画像から動画へ

```
[開始：idea（テキスト）]
   -> [Google Flow > 画像を生成]  prompt = {{開始.idea}}、生成数 = 1
   -> [Google Flow > 動画を生成]  モデル = Omni 1.2 Flash、start_image = {{画像を生成.media_ids}}、最大待機時間 = 420
   -> [終了：video = {{動画を生成.files}}]
```

### エージェント：Google Flow エージェントを使う動画アシスタント

「Google Flow エージェントとチャット」「Google Flow エージェントのチャットを取得」「エージェントの承認リクエストに回答」「動画を生成」「ジョブの状態を取得」を追加し、指示に「エージェントが承認を求めたら、作る内容と Google Flow クレジットをユーザーに伝え、同意を得てから回答する」「ジョブやターンが実行中なら再実行せず、wait=true で確認する」「ユーザーが指定しない限りメールは空欄」と書きます。

## 待機と制限

- **Dify の 600 秒制限**：プラグインの呼び出しは最長 600 秒です。動画ツールはジョブを送信して 10 秒ごとに確認し、既定では 120 秒で戻ります。完成していなければ `jobid` を返すので、「ジョブの状態を取得」で確認します（1 回最大 120 秒待機）。ワークフローでは「最大待機時間」を 420 秒まで上げられます。ジョブは呼び出し後も続き、7 日間保存されます。
- **所要時間**：動画は通常 60〜180 秒。画像は 1 回の呼び出しで返ります。エージェントのターンは通常約 1 分で、その動画はターン終了の 1〜2 分後に完成します。
- **エージェントの承認**：約 4 分以内に回答してください。過ぎると Google がリクエストを閉じます。
- **キャプチャ**：画像・動画のリクエストとエージェントのターンごとに 1 回使います。

## トラブルシューティング

| コード | 意味 | 対処 |
|---|---|---|
| 400 | リクエストが拒否されました（プランにないモデルやオプション、組み合わせの誤り、無料キャプチャの使い切り）。 | メッセージに従って修正。キャプチャはサービスのキーを追加。 |
| 401 | useapi.net のトークンが誤っています。 | 認証情報のトークンを確認。 |
| 402 | useapi.net のサブスクリプションが有効ではありません。 | 更新してください。 |
| 403 | Google がすべての試行でキャプチャを拒否（生成・課金なし）、プランにモデルがない、18 歳未満と判定、または別の useapi.net ユーザーの ID。 | 別のアカウントを使うか、メールを空欄に。 |
| 404 | アカウント未接続、またはジョブ・メディア・チャットが存在しません。 | Setup Google Flow で接続。 |
| 408 | 待機終了時にジョブが実行中でした。 | 再送前に「ジョブの状態を取得」で確認。 |
| 409 | このチャットでターンが実行中か、承認待ちです。 | 承認に回答するか、ターンの終了を待つ。 |
| 410 | ジョブの期限切れ。 | ジョブは 7 日間保存されます。 |
| 429 | Google がこのアカウントを制限中、全アカウントが外れている、またはエージェントのターンが既に 3 つ実行中。 | 再試行時刻まで待つ、アカウントを追加する、メールを空欄に。 |
| 502、504 | Google の応答が不明確か時間切れ。リクエストは実行された可能性があります。 | 再送前にジョブやチャットを確認。 |
| 503 | Google が一時的に利用不可、メディア未準備、またはキャプチャサービスの失敗。 | 数秒後に再試行。キャプチャサービスのキーと残高を確認。 |
| 596 | Google がアカウントのセッションを拒否。useapi.net が自動で再確認します。 | 約 1 分後に再試行。続く場合はアカウントを追加し直す。 |

## 費用

プラグインは無料。useapi.net は月額 15 ドル（全 API）。Google はご自身の Google AI プラン（無料プランを含む）で、動画はその Google Flow クレジットを消費し、画像は消費しません。キャプチャは最初のアカウントに無料 300 回分、その後はご自身のサービスで生成 1,000 回あたり約 0.80〜3.00 ドルです。

## プライバシー

プラグインは `api.useapi.net` にのみリクエストを送り、`flow-content.google` からのみファイルをダウンロードし、データを保存しません。詳細は [PRIVACY.md](../PRIVACY.md) と useapi.net の[利用規約とプライバシーポリシー](https://useapi.net/docs/legal)をご覧ください。

## サポート

- API リファレンス：https://useapi.net/docs/api-google-flow-v1
- サンプルコード：https://github.com/useapi/google-flow-api
- メール support@useapi.net、または [Discord](https://discord.gg/w28uK3cnmF)／[Telegram](https://t.me/use_api) でお問い合わせください。
