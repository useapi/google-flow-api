# Google Flow，由 useapi.net 提供

**作者：** useapi · **版本：** 0.1.0 · **类型：** 工具 · **源代码：** https://github.com/useapi/google-flow-api/tree/main/dify-plugin · **联系方式：** support@useapi.net

在 Dify 的工作流、Chatflow 和 Agent 中使用 Google Flow。用 Veo 3.1 Lite 和 Omni 1.2 Flash 生成带声音的视频，用 Nano Banana 生成图片，延长和编辑视频，超分到最高 4K，转成 GIF，拼接片段，还可以与 Google Flow 智能体对话：这是 Google 自己的创作智能体，会为你规划、编写分镜并生成内容。图片和视频以 Dify 文件形式返回。

**连接多个 Google 账号，由 useapi.net 分配任务。** 邮箱留空时，useapi.net 会把每个新任务发给健康的账号。这样可以并行运行更多任务，汇集每个账号的 Google Flow 积分，并且当 Google 限制某个账号或其额度用完时，工作仍能继续。基于单个 Gemini API 密钥的插件做不到这一点：那个密钥按调用计费，也不使用你的 Google AI 方案。详见[多个 Google 账号](#多个-google-账号)。

> 本插件调用 useapi.net 提供的 [Google Flow API](https://useapi.net/docs/api-google-flow-v1?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin)，这是第三方 API，并非由 Google 开发，与 Google 无关联，也未获得 Google 认可。使用前需要：useapi.net 订阅（每月 15 美元，包含 useapi.net 的全部 API）；一个有 Google AI 方案的 Google 账号（免费方案可用 Veo 3.1 Lite、Omni 1.2 Flash 和 Nano Banana）；以及验证码服务：第一个 Google Flow 账号赠送 300 个免费验证码额度，之后需添加你自己的验证码服务商密钥。

## Google AI 方案与 Google Flow

视频消耗生成它的 Google 账号的 Google Flow 积分。任何方案生成图片都不消耗积分。

| 方案 | 月费 | Google Flow 积分 | 视频模型 | 其他 | Veo 3.1 Lite 视频（8 秒，720p） |
|---|---|---|---|---|---|
| 免费 | $0 | 每天 50 | Veo 3.1 Lite（8 秒）、Omni 1.2 Flash（最长 10 秒） | Nano Banana 2.1 仅“高”思考强度；图片超分到 2K | 每天约 5 个 |
| Google AI Plus | $4.99 | 每月 200 | Veo 3.1 Lite（8 秒）、Omni 1.2 Flash（3 到 15 秒） | Omni 1.2 Flash 延长；视频超分到 720p 和 1080p | 每月约 20 个 |
| Google AI Pro | $19.99 | 每月 1,000 | 同 Google AI Plus | 同 Google AI Plus | 每月约 100 个 |
| Google AI Ultra $99 | $99.99 | 每月 10,000 | 同 Google AI Plus，另有 4 秒和 6 秒 Veo 3.1 Lite 视频 | 视频和图片超分到 4K | 每月约 2,000 个 |
| Google AI Ultra $199 | $199.99 | 每月 25,000 | 同 Google AI Ultra $99，另有 0 积分的 Veo 3.1 Lite 低优先级（仅方案管理者的账号） | 视频和图片超分到 4K | 每月约 5,000 个 |

所有方案都能用 Nano Banana 2 Lite、Nano Banana 2.1 和 Nano Banana Pro 生成图片。价格为 Google 截至 2026-10-20 的美国价格，来自 useapi.net API 目录（`https://api.useapi.net/v1/google-flow/models` 的 `plans`）。各方案积分来自 Google 的[方案页面](https://gemini.google/subscriptions/)和 [Google Flow 积分页面](https://support.google.com/flow/answer/16526234)，见 2026 年 11 月的 useapi.net [Google Flow 文档](https://useapi.net/docs/api-google-flow-v1)。视频数量按目录中 Veo 3.1 Lite 的价格计算（8 秒 10 积分，Google AI Ultra 为 5 积分）。表中只列 Google 方案的费用，useapi.net 订阅（每月 15 美元）另计。

意义：你使用 Google AI 方案中已有的积分，而不是按片段向 Google 付费，并且可以合并多个账号（见[多个 Google 账号](#多个-google-账号)）。

## 快速开始

1. **获取 useapi.net API 令牌**：订阅后复制令牌，见 [Setup useapi.net](https://useapi.net/docs/start-here/setup-useapi?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin)。
2. **连接 Google 账号**：按照 [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow?utm_source=marketplace.dify.ai&utm_medium=referral&utm_campaign=dify-plugin) 操作（自动设置约 5 分钟）。第一个账号赠送 300 个免费验证码额度，可以立即生成。用完后，按同一页面 [Configure Captcha Providers](https://useapi.net/docs/start-here/setup-google-flow#configure-captcha-providers) 添加验证码服务商密钥。验证码费用约为每 1,000 次生成 0.80 到 3.00 美元，付给服务商。
3. **安装并授权插件，然后生成视频**：在 [Dify 插件市场](https://marketplace.dify.ai/plugins/useapi/google_flow_useapi)安装，或在“插件 > 安装插件 > 本地插件包”中上传 [GitHub releases](https://github.com/useapi/google-flow-api/releases) 里的 `.difypkg`。在“工具”中打开 “Google Flow，由 useapi.net 提供”，点击授权，粘贴令牌并保存。然后在工作流中添加“生成视频”，提示词写 “A paper boat floating on a calm pond at sunrise” 并运行，`.mp4` 会以文件形式返回。

| 凭据 | 必填 | 说明 |
|---|:-:|---|
| useapi.net API 令牌 | 是 | 第 1 步获得的令牌，由 Dify 加密保存。 |
| 默认 Google 账号邮箱 | 否 | 留空则在所有已连接账号间轮换。只有要把所有工具固定到一个 Google 账号时才填写。 |

保存凭据时会调用一次 `GET /accounts`，确认令牌有效且至少已连接一个 Google 账号，不会调用 Google。

插件只连接 `https://api.useapi.net/v1/google-flow`（令牌放在 `Authorization: Bearer` 请求头中），并从 `https://flow-content.google` 上 Google 的签名链接下载生成的图片和视频（不发送令牌）。自托管的 Dify 需要能访问这两个地址。

## 多个 Google 账号

每个 Google 账号都按 [Setup Google Flow](https://useapi.net/docs/start-here/setup-google-flow) 添加。“列出 Google 账号”显示每个账号及其状态是否正常，“列出各账号的任务”显示每个账号上运行的任务，“获取账号方案和积分”显示某个账号的方案、剩余积分和视频模型。

**轮换方式**：邮箱留空时，“生成视频”“生成图片”“上传图片或视频”和新的智能体对话由 useapi.net 选择账号。它的[负载均衡](https://useapi.net/docs/api-google-flow-v1/get-google-flow-jobs#load-balancing-algorithm)会先暂时排除最近被 Google 限流或额度已满的账号，直到冷却结束；在其余账号中选择运行中和最近任务最少的账号，最近的失败和限流会降低账号的优先级。如果所有账号都被排除，会返回 `429` 和重试时间。只有一个账号时不会排除，请求总是发给它。

**好处**：任务发给最空闲的账号，可并行运行更多任务；每个账号都有自己的 Google AI 方案，积分更多；被限流或额度用完的账号会被跳过，其他账号继续工作。

**何时填写邮箱**：
- 两处邮箱都留空即可轮换，这是最好的默认设置。
- 在凭据中设置**默认邮箱**，所有工具都固定到一个账号。指定邮箱会跳过负载均衡，即使该账号被暂时排除，请求也会发给它。
- 在**单个工具**中填写邮箱，只把这次调用发给某个账号，例如用 Google AI Ultra 账号的积分做 4K 超分。

**引用会固定账号**：你生成或上传的图片、视频、角色或声音属于某一个 Google 账号，一个请求中的所有引用必须属于同一账号。因此使用媒体 ID 的请求会在该媒体所在的账号上运行。延长、超分、GIF 和拼接在源视频所在的账号上运行。附加到工具的文件会上传到同一请求中其他 ID 所属的账号。智能体对话始终在开始时的账号上进行，请用 `chat_id` 继续对话，并使用该账号的引用。每个账号同时最多运行 3 个智能体回合。

## 工具

共 20 个工具。媒体 ID 形如 `user:12345-email:...-video:<id>`，可作为变量在节点间传递。接口路径相对于 `https://api.useapi.net/v1/google-flow`。

| 工具 | 名称 | 接口 |
|---|---|---|
| `list_accounts` | 列出 Google 账号 | `GET /accounts` |
| `get_account` | 获取账号方案和积分 | `GET /accounts/{email}` |
| `list_jobs` | 列出各账号的任务 | `GET /jobs` |
| `get_job` | 获取任务状态 | `GET /jobs/{jobid}` |
| `generate_video` | 生成视频 | `POST /videos` |
| `extend_video` | 延长视频 | `POST /videos/extend` |
| `upscale_video` | 视频超分 | `POST /videos/upscale` |
| `generate_image` | 生成图片 | `POST /images` |
| `upscale_image` | 图片超分 | `POST /images/upscale` |
| `video_to_gif` | 视频转 GIF | `POST /videos/gif` |
| `concatenate_videos` | 拼接视频 | `POST /videos/concatenate` |
| `upload_image` | 上传图片或视频 | `POST /assets/{email}` |
| `list_media` | 列出媒体 | `GET /assets/media/{email}` |
| `get_media` | 获取媒体 | `GET /assets/{mediaGenerationId}` |
| `list_characters` | 列出角色 | `GET /characters` |
| `list_voices` | 列出声音 | `GET /voices` |
| `agent_chat` | Google Flow 智能体对话 | `POST /agent/chats`, `POST /agent/chats/{chatId}/messages` |
| `agent_get_chat` | 获取 Google Flow 智能体对话 | `GET /agent/chats/{chatId}` |
| `agent_answer_approval` | 答复智能体的批准请求 | `POST /agent/chats/{chatId}/approval` |
| `agent_list_chats` | 列出 Google Flow 智能体对话 | `GET /agent/chats` |

图片和视频引用可以填媒体 ID，也可以直接附加 Dify 文件（PNG、JPEG、WebP 最大 20 MB，MP4 最大 100 MB）。Veo 3.1 Fast、Veo 3.1 Quality 和 Omni 1.1 Flash 不提供：Google 将于 2026-12-05 停用它们。生成工具返回文本、JSON、变量（`jobid`、`status`、`media_ids`、`file_urls`）和文件；智能体工具返回 `chat_id`、`status`、`reply`。Google 文件链接约 6 小时后过期，“获取媒体”可获取新链接。

## 使用示例

### 工作流：两个节点从图片到视频

```
[开始：idea（文本）]
   -> [Google Flow > 生成图片]  prompt = {{开始.idea}}，数量 = 1
   -> [Google Flow > 生成视频]  模型 = Omni 1.2 Flash，start_image = {{生成图片.media_ids}}，最长等待 = 420
   -> [结束：video = {{生成视频.files}}]
```

### Agent：使用 Google Flow 智能体的视频助手

添加“Google Flow 智能体对话”“获取 Google Flow 智能体对话”“答复智能体的批准请求”“生成视频”“获取任务状态”，并在指令中写明：“智能体请求批准时，先告诉用户要生成什么及消耗的 Google Flow 积分，用户同意后再答复”“任务或回合仍在运行时不要重新开始，用 wait=true 查询”“除非用户指定，邮箱留空”。

## 等待与限制

- **Dify 的 600 秒限制**：插件调用最长 600 秒。视频工具提交任务后每 10 秒查询一次，默认 120 秒后返回；若视频未完成，会返回 `jobid`，用“获取任务状态”继续查询（每次最长等待 120 秒）。工作流中可把“最长等待”调到 420 秒。任务在调用返回后继续运行，保留 7 天。
- **耗时**：视频通常需要 60 到 180 秒；图片一次调用即返回；智能体一个回合通常约 1 分钟，其视频会在回合结束后一两分钟完成。
- **智能体批准**：请在约 4 分钟内答复，否则 Google 会关闭该请求。
- **验证码**：每次图片、视频请求和每个智能体回合使用一次验证码。

## 故障排查

| 代码 | 含义 | 处理 |
|---|---|---|
| 400 | 请求被拒绝：方案不支持的模型或选项、组合错误，或免费验证码额度已用完。 | 按提示修改；验证码用完请添加服务商密钥。 |
| 401 | useapi.net 令牌错误。 | 检查插件凭据中的令牌。 |
| 402 | useapi.net 订阅未生效。 | 续订。 |
| 403 | Google 每次都拒绝了验证码（未生成、未扣费）、方案不含该模型、账号被视为未满 18 岁，或 ID 属于其他 useapi.net 用户。 | 换一个账号，或邮箱留空让 useapi.net 选择。 |
| 404 | 账号未连接，或任务、媒体、对话不存在。 | 用 Setup Google Flow 连接账号。 |
| 408 | 等待结束时任务仍在运行。 | 重发前先用“获取任务状态”查询。 |
| 409 | 该对话的回合正在运行，或在等待批准。 | 答复批准或等待回合结束。 |
| 410 | 任务已过期。 | 任务保留 7 天。 |
| 429 | Google 暂时限制该账号、所有账号都被排除，或该账号已运行 3 个智能体回合。 | 等到重试时间，连接更多账号，或邮箱留空。 |
| 502、504 | Google 未明确或未及时答复，请求可能已运行。 | 重发前先查询任务或对话。 |
| 503 | Google 暂时不可用、媒体尚未就绪，或验证码服务商出错。 | 几秒后重试；检查服务商密钥和余额。 |
| 596 | Google 拒绝了账号会话，useapi.net 会自动重新验证。 | 约 1 分钟后重试；持续出现则重新添加账号。 |

## 费用

插件免费；useapi.net 每月 15 美元（包含全部 API）；你自己的 Google AI 方案（含免费方案），视频消耗其 Google Flow 积分，图片不消耗；验证码：第一个账号赠送 300 个，之后使用你自己的服务商，约每 1,000 次生成 0.80 到 3.00 美元。

## 隐私

插件只向 `api.useapi.net` 发送请求，只从 `flow-content.google` 下载文件，不保存任何数据。详见 [PRIVACY.md](../PRIVACY.md) 和 useapi.net 的[服务条款与隐私政策](https://useapi.net/docs/legal)。

## 支持

- API 文档：https://useapi.net/docs/api-google-flow-v1
- 示例代码：https://github.com/useapi/google-flow-api
- 邮件 support@useapi.net，或在 [Discord](https://discord.gg/w28uK3cnmF)、[Telegram](https://t.me/use_api) 提问。
