"""Single source of truth for every tool: names, parameters, enums and the
four Dify UI languages (en_US, zh_Hans, ja_JP, pt_BR). `dev/gen_tools.py`
writes tools/*.yaml, tools/*.py and the provider's tool list from this file.

Parameter names, enums and limits follow the published API catalog
(https://api.useapi.net/v1/google-flow/models) and the public API reference
(https://useapi.net/docs/api-google-flow-v1). Only models the catalog lists as
active are offered. LLM-facing descriptions stay in English.
"""

from __future__ import annotations

from typing import Any


def L(en: str, zh: str, ja: str, pt: str) -> dict[str, str]:
    return {"en_US": en, "zh_Hans": zh, "ja_JP": ja, "pt_BR": pt}


def opt(value: str, label: dict[str, str]) -> dict[str, Any]:
    return {"value": value, "label": label}


def param(
    name: str,
    ptype: str,
    label: dict[str, str],
    human: dict[str, str],
    llm: str | None = None,
    *,
    required: bool = False,
    form: str = "llm",
    default: Any = None,
    options: list[dict[str, Any]] | None = None,
    min: int | None = None,
    max: int | None = None,
) -> dict[str, Any]:
    p: dict[str, Any] = {
        "name": name,
        "type": ptype,
        "required": required,
        "label": label,
        "human_description": human,
    }
    if form == "llm":
        p["llm_description"] = llm or human["en_US"]
    p["form"] = form
    if default is not None:
        p["default"] = default
    if options:
        p["options"] = options
    if min is not None:
        p["min"] = min
    if max is not None:
        p["max"] = max
    return p


def select(
    name: str,
    label: dict[str, str],
    human: dict[str, str],
    options: list[dict[str, Any]],
    llm: str | None = None,
    default: str | None = None,
    form: str = "llm",
) -> dict[str, Any]:
    values = ", ".join(o["value"] for o in options)
    return param(
        name,
        "select",
        label,
        human,
        llm or f"{human['en_US']} One of: {values}.",
        options=options,
        default=default,
        form=form,
    )


# ------------------------------------------------------------------ shared parameters

EMAIL_LABEL = L("Google account email", "Google 账号邮箱", "Google アカウントのメール", "E-mail da conta Google")


def EMAIL() -> dict[str, Any]:
    """For requests that useapi.net can route: empty means rotation across the healthy accounts."""
    return param(
        "email",
        "string",
        EMAIL_LABEL,
        L(
            "Optional. Leave empty to rotate across all connected accounts (useapi.net picks a healthy one). Default: the email in the credentials.",
            "可选。留空则在所有已连接账号间轮换（由 useapi.net 选择健康的账号）。默认：凭据中的邮箱。",
            "任意。空欄にすると接続済みの全アカウントでローテーションします（useapi.net が正常なアカウントを選びます）。既定は認証情報のメール。",
            "Opcional. Deixe vazio para alternar entre todas as contas conectadas (a useapi.net escolhe uma saudável). Padrão: o e-mail das credenciais.",
        ),
        "Optional Google account email. Leave empty to rotate across all connected accounts. Media ids already pin the request to their own account.",
    )


def EMAIL_READ(what_en: str) -> dict[str, Any]:
    """For reads of one account's data."""
    return param(
        "email",
        "string",
        EMAIL_LABEL,
        L(
            "The Google account to read. Optional when only one account is connected or a default email is set.",
            "要读取的 Google 账号。只连接了一个账号或已设置默认邮箱时可省略。",
            "読み取る Google アカウント。接続が 1 つだけ、または既定のメールを設定済みなら省略できます。",
            "A conta Google a ler. Opcional quando só uma conta está conectada ou há um e-mail padrão.",
        ),
        f"Email of the Google account whose {what_en} to list. Optional when only one account is connected or a default email is set.",
    )


JOBID = param(
    "jobid",
    "string",
    L("Job ID", "任务 ID", "ジョブ ID", "ID do job"),
    L(
        "The jobid returned by a video or image generation.",
        "视频或图片生成返回的任务 ID（jobid）。",
        "動画または画像の生成で返された jobid。",
        "O jobid retornado por uma geração de vídeo ou imagem.",
    ),
    "The jobid from Generate video, Extend video, Upscale video or Generate image, e.g. j1117...-u12345-email:john@gmail.com-bot:google-flow.",
    required=True,
)

WAIT = param(
    "wait",
    "boolean",
    L("Wait for the result", "等待结果", "結果を待つ", "Aguardar o resultado"),
    L(
        "Wait until the job finishes (up to the maximum wait). Off: return the job id at once.",
        "等待任务完成（不超过最长等待时间）。关闭时立即返回任务 ID。",
        "ジョブの完了まで待ちます（最大待機時間まで）。オフにするとすぐにジョブ ID を返します。",
        "Aguarda o job terminar (até o tempo máximo). Desligado: retorna o ID do job na hora.",
    ),
    form="form",
    default=True,
)


def MAX_WAIT(default: int = 120) -> dict[str, Any]:
    return param(
        "max_wait_seconds",
        "number",
        L("Maximum wait (seconds)", "最长等待（秒）", "最大待機時間（秒）", "Espera máxima (segundos)"),
        L(
            f"How long to wait, 10 to 420 seconds (default {default}). A job still running is returned with its id.",
            f"最长等待时间，10 到 420 秒（默认 {default}）。仍在运行的任务会连同 ID 一起返回。",
            f"待機時間は 10〜420 秒（既定 {default}）。実行中のジョブは ID とともに返されます。",
            f"Quanto esperar, de 10 a 420 segundos (padrão {default}). Um job ainda em execução é retornado com seu ID.",
        ),
        form="form",
        default=default,
        min=10,
        max=420,
    )


def RETURN_FILE(default: bool = True) -> dict[str, Any]:
    return param(
        "return_file",
        "boolean",
        L("Attach the files", "附加文件", "ファイルを添付", "Anexar os arquivos"),
        L(
            "Download the finished images or videos and return them as files (up to 150 MB each).",
            "下载生成的图片或视频并作为文件返回（每个最大 150 MB）。",
            "完成した画像や動画をダウンロードしてファイルとして返します（各 150 MB まで）。",
            "Baixa as imagens ou vídeos prontos e retorna como arquivos (até 150 MB cada).",
        ),
        form="form",
        default=default,
    )


REPLY_URL = param(
    "reply_url",
    "string",
    L("Webhook URL", "Webhook 地址", "Webhook URL", "URL de webhook"),
    L(
        "Optional public URL that receives the job status by POST.",
        "可选。通过 POST 接收任务状态的公开地址。",
        "任意。ジョブの状態を POST で受け取る公開 URL。",
        "URL pública opcional que recebe o status do job via POST.",
    ),
    form="form",
)

PROMPT_VIDEO = param(
    "prompt",
    "string",
    L("Prompt", "提示词", "プロンプト", "Prompt"),
    L(
        "What the video shows. You can name references inline: @referenceImage_1, @character_1, @referenceAudio_1.",
        "视频内容描述。可在文中引用：@referenceImage_1、@character_1、@referenceAudio_1。",
        "動画の内容。参照を本文で指定できます：@referenceImage_1、@character_1、@referenceAudio_1。",
        "O que o vídeo mostra. Você pode citar referências no texto: @referenceImage_1, @character_1, @referenceAudio_1.",
    ),
    "The video prompt. It may name the references inline as @referenceImage_N, @character_N or @referenceAudio_1; each named one must be given.",
    required=True,
)


def ID_PARAM(name: str, label: dict[str, str], human: dict[str, str], llm: str) -> dict[str, Any]:
    return param(name, "string", label, human, llm)


def FILE_PARAM(name: str, label: dict[str, str], human: dict[str, str], llm: str, many: bool = False) -> dict[str, Any]:
    return param(name, "files" if many else "file", label, human, llm)


START_IMAGE = ID_PARAM(
    "start_image",
    L("Start image ID", "首帧图片 ID", "開始フレームの画像 ID", "ID da imagem inicial"),
    L(
        "Optional media id of the first frame (from Upload image or Generate image).",
        "可选。首帧图片的媒体 ID（来自“上传图片”或“生成图片”）。",
        "任意。最初のフレームにする画像のメディア ID（「画像をアップロード」または「画像を生成」から）。",
        "ID de mídia opcional do primeiro quadro (de Enviar imagem ou Gerar imagem).",
    ),
    "Optional media id of the image the video starts with (image-to-video).",
)
START_IMAGE_FILE = FILE_PARAM(
    "start_image_file",
    L("Start image file", "首帧图片文件", "開始フレームの画像ファイル", "Arquivo da imagem inicial"),
    L(
        "Optional. Or upload the first frame here (PNG, JPEG or WebP).",
        "可选。也可以在这里上传首帧图片（PNG、JPEG 或 WebP）。",
        "任意。最初のフレームをここでアップロードすることもできます（PNG、JPEG、WebP）。",
        "Opcional. Ou envie o primeiro quadro aqui (PNG, JPEG ou WebP).",
    ),
    "Optional image file for the first frame, used when start_image is empty.",
)
END_IMAGE = ID_PARAM(
    "end_image",
    L("End image ID", "尾帧图片 ID", "終了フレームの画像 ID", "ID da imagem final"),
    L(
        "Optional media id of the last frame. Needs a start image.",
        "可选。尾帧图片的媒体 ID。需要同时提供首帧。",
        "任意。最後のフレームの画像のメディア ID。開始フレームも必要です。",
        "ID de mídia opcional do último quadro. Exige uma imagem inicial.",
    ),
    "Optional media id of the image the video ends with. Needs a start image.",
)
END_IMAGE_FILE = FILE_PARAM(
    "end_image_file",
    L("End image file", "尾帧图片文件", "終了フレームの画像ファイル", "Arquivo da imagem final"),
    L(
        "Optional. Or upload the last frame here.",
        "可选。也可以在这里上传尾帧图片。",
        "任意。最後のフレームをここでアップロードすることもできます。",
        "Opcional. Ou envie o último quadro aqui.",
    ),
    "Optional image file for the last frame, used when end_image is empty.",
)


def REFERENCE_IMAGES(limit: int) -> dict[str, Any]:
    return ID_PARAM(
        "reference_images",
        L("Reference image IDs", "参考图片 ID", "参照画像 ID", "IDs de imagens de referência"),
        L(
            f"Optional media ids of reference images, one per line (up to {limit}).",
            f"可选。参考图片的媒体 ID，每行一个（最多 {limit} 个）。",
            f"任意。参照画像のメディア ID を 1 行に 1 つ（最大 {limit} 件）。",
            f"IDs de mídia opcionais de imagens de referência, um por linha (até {limit}).",
        ),
        f"Optional media ids of reference images, separated by new lines or commas (up to {limit}). Not together with start or end images.",
    )


def REFERENCE_IMAGE_FILES(limit: int) -> dict[str, Any]:
    return FILE_PARAM(
        "reference_image_files",
        L("Reference image files", "参考图片文件", "参照画像ファイル", "Arquivos de imagens de referência"),
        L(
            f"Optional. Or upload reference images here (with the ids, up to {limit} in all).",
            f"可选。也可以在这里上传参考图片（与 ID 合计最多 {limit} 张）。",
            f"任意。参照画像をここでアップロードすることもできます（ID と合わせて最大 {limit} 枚）。",
            f"Opcional. Ou envie imagens de referência aqui (com os IDs, até {limit} no total).",
        ),
        f"Optional image files used as reference images after the ids (up to {limit} in all).",
        many=True,
    )


def CHARACTERS(limit: int) -> dict[str, Any]:
    return ID_PARAM(
        "characters",
        L("Character IDs", "角色 ID", "キャラクター ID", "IDs de personagens"),
        L(
            f"Optional character ids from List characters, one per line (up to {limit}).",
            f"可选。来自“列出角色”的角色 ID，每行一个（最多 {limit} 个）。",
            f"任意。「キャラクター一覧」のキャラクター ID を 1 行に 1 つ（最大 {limit} 件）。",
            f"IDs de personagens opcionais de Listar personagens, um por linha (até {limit}).",
        ),
        f"Optional character ids from List characters, separated by new lines (up to {limit}). Name them in the prompt as @character_N.",
    )


VOICE = ID_PARAM(
    "voice",
    L("Voice", "声音", "音声", "Voz"),
    L(
        "Optional narration voice: a built-in voice name such as Kore, or a voice id from List voices. Needs a reference image or character.",
        "可选。旁白声音：内置声音名称（如 Kore）或来自“列出声音”的声音 ID。需要参考图片或角色。",
        "任意。ナレーションの音声：Kore などの組み込み音声名、または「音声一覧」の音声 ID。参照画像かキャラクターが必要です。",
        "Voz de narração opcional: um nome de voz embutida como Kore, ou um ID de voz de Listar vozes. Exige imagem de referência ou personagem.",
    ),
    "Optional voice for narration (referenceAudio_1): a built-in voice name (e.g. Kore, Puck, Charon) or a voice id from List voices. Needs a reference image or character.",
)


def VIDEO_ID(required_hint: str) -> list[dict[str, Any]]:
    return [
        ID_PARAM(
            "video",
            L("Video ID", "视频 ID", "動画 ID", "ID do vídeo"),
            L(
                "Media id of the video (from Generate video, List media or Upload).",
                "视频的媒体 ID（来自“生成视频”“列出媒体”或“上传”）。",
                "動画のメディア ID（「動画を生成」「メディア一覧」「アップロード」から）。",
                "ID de mídia do vídeo (de Gerar vídeo, Listar mídia ou Enviar).",
            ),
            f"Media id of the {required_hint}, e.g. user:12345-email:...-video:... Give this or video_file.",
        ),
        FILE_PARAM(
            "video_file",
            L("Video file", "视频文件", "動画ファイル", "Arquivo de vídeo"),
            L(
                "Or upload an MP4 here (up to 100 MB).",
                "也可以在这里上传 MP4（最大 100 MB）。",
                "または MP4 をここでアップロード（100 MB まで）。",
                "Ou envie um MP4 aqui (até 100 MB).",
            ),
            f"Optional MP4 file of the {required_hint}, used when video is empty.",
        ),
    ]


IMAGE_ID = [
    ID_PARAM(
        "image",
        L("Image ID", "图片 ID", "画像 ID", "ID da imagem"),
        L(
            "Media id of the image (from Generate image, List media or Upload image).",
            "图片的媒体 ID（来自“生成图片”“列出媒体”或“上传图片”）。",
            "画像のメディア ID（「画像を生成」「メディア一覧」「画像をアップロード」から）。",
            "ID de mídia da imagem (de Gerar imagem, Listar mídia ou Enviar imagem).",
        ),
        "Media id of the image to upscale, e.g. user:12345-email:...-image:... Give this or image_file.",
    ),
    FILE_PARAM(
        "image_file",
        L("Image file", "图片文件", "画像ファイル", "Arquivo de imagem"),
        L(
            "Or upload a PNG, JPEG or WebP here (up to 20 MB).",
            "也可以在这里上传 PNG、JPEG 或 WebP（最大 20 MB）。",
            "または PNG、JPEG、WebP をここでアップロード（20 MB まで）。",
            "Ou envie um PNG, JPEG ou WebP aqui (até 20 MB).",
        ),
        "Optional image file to upscale, used when image is empty.",
    ),
]

CHAT_ID = param(
    "chat_id",
    "string",
    L("Chat ID", "对话 ID", "チャット ID", "ID do chat"),
    L(
        "The chat_id returned by Google Flow agent chat.",
        "“Google Flow 智能体对话”返回的对话 ID。",
        "「Google Flow エージェントとチャット」で返された chat_id。",
        "O chat_id retornado por Chat com o agente do Google Flow.",
    ),
    "The chat_id from agent_chat or agent_list_chats.",
    required=True,
)

PROJECT_ID = param(
    "project_id",
    "string",
    L("Project ID", "项目 ID", "プロジェクト ID", "ID do projeto"),
    L(
        "Optional Google Flow project id. Default: the account's current project.",
        "可选。Google Flow 项目 ID。默认：账号当前的项目。",
        "任意。Google Flow のプロジェクト ID。既定はアカウントの現在のプロジェクト。",
        "ID opcional de projeto do Google Flow. Padrão: o projeto atual da conta.",
    ),
    "Optional Google Flow project id. Leave empty for the account's default project.",
)

GEN_OUTPUT = {
    "jobid": {"type": "string"},
    "status": {"type": "string"},
    "media_ids": {"type": "array", "items": {"type": "string"}},
    "file_urls": {"type": "array", "items": {"type": "string"}},
}
CHAT_OUTPUT = {
    "chat_id": {"type": "string"},
    "status": {"type": "string"},
    "reply": {"type": "string"},
    "media_ids": {"type": "array", "items": {"type": "string"}},
    "file_urls": {"type": "array", "items": {"type": "string"}},
}

# ------------------------------------------------------------------ option sets

VIDEO_MODEL_OPTIONS = [
    opt(
        "veo-3.1-lite",
        L("Veo 3.1 Lite (every plan)", "Veo 3.1 Lite（所有方案）", "Veo 3.1 Lite（全プラン）", "Veo 3.1 Lite (todos os planos)"),
    ),
    opt(
        "omni-flash-1.2",
        L("Omni 1.2 Flash (every plan)", "Omni 1.2 Flash（所有方案）", "Omni 1.2 Flash（全プラン）", "Omni 1.2 Flash (todos os planos)"),
    ),
    opt(
        "veo-3.1-lite-low-priority",
        L(
            "Veo 3.1 Lite Lower Priority (Google AI Ultra $199 only)",
            "Veo 3.1 Lite 低优先级（仅限 Google AI Ultra $199）",
            "Veo 3.1 Lite 低優先度（Google AI Ultra $199 のみ）",
            "Veo 3.1 Lite Lower Priority (só Google AI Ultra $199)",
        ),
    ),
]
EXTEND_MODEL_OPTIONS = [
    opt(
        "omni-flash-1.2",
        L("Omni 1.2 Flash (paid plans)", "Omni 1.2 Flash（付费方案）", "Omni 1.2 Flash（有料プラン）", "Omni 1.2 Flash (planos pagos)"),
    ),
    opt(
        "veo-3.1-lite",
        L("Veo 3.1 Lite (every plan)", "Veo 3.1 Lite（所有方案）", "Veo 3.1 Lite（全プラン）", "Veo 3.1 Lite (todos os planos)"),
    ),
    VIDEO_MODEL_OPTIONS[2],
]
ASPECT_VIDEO = [
    opt("landscape", L("Landscape 16:9", "横向 16:9", "横向き 16:9", "Paisagem 16:9")),
    opt("portrait", L("Portrait 9:16", "纵向 9:16", "縦向き 9:16", "Retrato 9:16")),
]
RESOLUTION_VIDEO = [
    opt("720p", L("720p", "720p", "720p", "720p")),
    opt("360p", L("360p (Omni 1.2 Flash only)", "360p（仅 Omni 1.2 Flash）", "360p（Omni 1.2 Flash のみ）", "360p (só Omni 1.2 Flash)")),
]
UPSCALE_VIDEO = [
    opt("1080p", L("1080p (paid plans)", "1080p（付费方案）", "1080p（有料プラン）", "1080p (planos pagos)")),
    opt("720p", L("720p (paid plans)", "720p（付费方案）", "720p（有料プラン）", "720p (planos pagos)")),
    opt("4K", L("4K (Google AI Ultra)", "4K（Google AI Ultra）", "4K（Google AI Ultra）", "4K (Google AI Ultra)")),
]
IMAGE_MODEL_OPTIONS = [
    opt("nano-banana-2-lite", L("Nano Banana 2 Lite", "Nano Banana 2 Lite", "Nano Banana 2 Lite", "Nano Banana 2 Lite")),
    opt("nano-banana-2", L("Nano Banana 2.1", "Nano Banana 2.1", "Nano Banana 2.1", "Nano Banana 2.1")),
    opt("nano-banana-pro", L("Nano Banana Pro", "Nano Banana Pro", "Nano Banana Pro", "Nano Banana Pro")),
]
ASPECT_IMAGE = [
    opt("16:9", L("16:9", "16:9", "16:9", "16:9")),
    opt("4:3", L("4:3", "4:3", "4:3", "4:3")),
    opt("1:1", L("1:1", "1:1", "1:1", "1:1")),
    opt("3:4", L("3:4", "3:4", "3:4", "3:4")),
    opt("9:16", L("9:16", "9:16", "9:16", "9:16")),
    opt(
        "auto",
        L(
            "Auto (from the first reference)",
            "自动（按第一张参考图）",
            "自動（最初の参照画像に合わせる）",
            "Automático (da primeira referência)",
        ),
    ),
]
THINKING = [
    opt("high", L("High", "高", "高", "Alto")),
    opt("medium", L("Medium (paid plans)", "中（付费方案）", "中（有料プラン）", "Médio (planos pagos)")),
    opt("low", L("Low (paid plans)", "低（付费方案）", "低（有料プラン）", "Baixo (planos pagos)")),
]
UPSCALE_IMAGE = [
    opt("2k", L("2K", "2K", "2K", "2K")),
    opt("4k", L("4K (Google AI Ultra)", "4K（Google AI Ultra）", "4K（Google AI Ultra）", "4K (Google AI Ultra)")),
]
DECISIONS = [
    opt("approve", L("Approve", "批准", "承認", "Aprovar")),
    opt(
        "always", L("Always approve in this project", "在此项目中始终批准", "このプロジェクトでは常に承認", "Sempre aprovar neste projeto")
    ),
    opt("reject", L("Reject", "拒绝", "拒否", "Rejeitar")),
]
VOICE_SOURCES = [
    opt("system", L("Built-in voices", "内置声音", "組み込み音声", "Vozes embutidas")),
    opt("user", L("My voices", "我的声音", "自分の音声", "Minhas vozes")),
]
JOB_OPTIONS = [
    opt("summary", L("Summary", "摘要", "概要", "Resumo")),
    opt("executing", L("With running jobs", "包含运行中的任务", "実行中のジョブを含む", "Com jobs em execução")),
    opt("history", L("With recent jobs", "包含最近的任务", "最近のジョブを含む", "Com jobs recentes")),
]

COUNT_LABEL = L("Number of results", "生成数量", "生成数", "Quantidade")


def COUNT(what_en: str, what_zh: str, what_ja: str, what_pt: str) -> dict[str, Any]:
    return param(
        "count",
        "number",
        COUNT_LABEL,
        L(
            f"How many {what_en} to make, 1 to 4 (default 1).",
            f"生成多少个{what_zh}，1 到 4（默认 1）。",
            f"作成する{what_ja}の数、1〜4（既定 1）。",
            f"Quantos {what_pt} gerar, de 1 a 4 (padrão 1).",
        ),
        f"How many {what_en} to make, 1 to 4. Default 1.",
        default=1,
        min=1,
        max=4,
    )


# ------------------------------------------------------------------ tools

TOOLS: list[dict[str, Any]] = []


def tool(
    name: str, label: dict[str, str], human: dict[str, str], llm: str, params: list[dict[str, Any]], output: dict[str, Any] | None = None
) -> None:
    TOOLS.append({"name": name, "label": label, "human": human, "llm": llm, "params": params, "output": output})


# --- accounts and jobs

tool(
    "list_accounts",
    L("List Google accounts", "列出 Google 账号", "Google アカウント一覧", "Listar contas Google"),
    L(
        "List the Google accounts connected to Google Flow, with their health. Several healthy accounts share the work.",
        "列出已连接到 Google Flow 的 Google 账号及其状态。多个健康账号会分担任务。",
        "Google Flow に接続済みの Google アカウントを状態とともに一覧表示します。正常なアカウントが複数あれば作業を分担します。",
        "Lista as contas Google conectadas ao Google Flow, com a saúde de cada uma. Várias contas saudáveis dividem o trabalho.",
    ),
    "List the Google accounts connected to the useapi.net Google Flow API, with their health (OK or the reason an account does not work).",
    [],
    {"emails": {"type": "array", "items": {"type": "string"}}, "healthy_emails": {"type": "array", "items": {"type": "string"}}},
)

tool(
    "get_account",
    L("Get account plan and credits", "获取账号方案和积分", "アカウントのプランとクレジット", "Ver plano e créditos da conta"),
    L(
        "One Google account's Google AI plan, Google Flow credits left and the video models it can use.",
        "某个 Google 账号的 Google AI 方案、剩余 Google Flow 积分和可用的视频模型。",
        "Google アカウントの Google AI プラン、残りの Google Flow クレジット、使える動画モデル。",
        "O plano Google AI de uma conta, os créditos do Google Flow restantes e os modelos de vídeo que ela pode usar.",
    ),
    "Get one Google Flow account: its Google AI plan, Google Flow credits left and the video models it has today.",
    [EMAIL_READ("plan and credits")],
    {"plan": {"type": "string"}, "credits": {"type": "number"}, "video_models": {"type": "array", "items": {"type": "string"}}},
)

tool(
    "list_jobs",
    L("List jobs per account", "列出各账号的任务", "アカウントごとのジョブ一覧", "Listar jobs por conta"),
    L(
        "Running, finished and failed jobs on each Google account in the last 15 minutes: how useapi.net spreads the work.",
        "每个 Google 账号最近 15 分钟内运行中、已完成和失败的任务，可看出 useapi.net 如何分配任务。",
        "各 Google アカウントの直近 15 分間の実行中・完了・失敗ジョブ。useapi.net の振り分け状況がわかります。",
        "Jobs em execução, concluídos e com falha em cada conta Google nos últimos 15 minutos: como a useapi.net divide o trabalho.",
    ),
    "List the load on each Google Flow account: running, completed, failed and rate-limited jobs in the last 15 minutes, and the healthy accounts.",
    [
        select(
            "options",
            L("Detail", "详细程度", "詳細", "Detalhe"),
            L(
                "Optional. Summary (default), with running jobs, or with recent jobs.",
                "可选。摘要（默认）、包含运行中的任务，或包含最近的任务。",
                "任意。概要（既定）、実行中のジョブを含む、最近のジョブを含む。",
                "Opcional. Resumo (padrão), com jobs em execução ou com jobs recentes.",
            ),
            JOB_OPTIONS,
        )
    ],
)

tool(
    "get_job",
    L("Get job status", "获取任务状态", "ジョブの状態を取得", "Ver status do job"),
    L(
        "Check a video or image job, optionally wait for it, and return its images or videos as files.",
        "查询视频或图片任务，可选择等待完成，并以文件返回图片或视频。",
        "動画または画像のジョブを確認し、必要なら完了まで待って画像や動画をファイルで返します。",
        "Consulta um job de vídeo ou imagem, opcionalmente aguarda e retorna as imagens ou vídeos como arquivos.",
    ),
    "Get a Google Flow job by jobid. Returns its status; when completed, the media ids, the links and the files. Use it when a generation is still running.",
    [JOBID, WAIT, MAX_WAIT(120), RETURN_FILE()],
    GEN_OUTPUT,
)

# --- generation

tool(
    "generate_video",
    L("Generate video", "生成视频", "動画を生成", "Gerar vídeo"),
    L(
        "Make videos with sound with Veo 3.1 Lite or Omni 1.2 Flash: from text, start and end frames, reference images, characters and a voice, or edit a video with Omni 1.2 Flash.",
        "使用 Veo 3.1 Lite 或 Omni 1.2 Flash 生成带声音的视频：可基于文本、首尾帧、参考图片、角色和声音，或用 Omni 1.2 Flash 编辑视频。",
        "Veo 3.1 Lite または Omni 1.2 Flash で音声付き動画を作成：テキスト、開始・終了フレーム、参照画像、キャラクター、音声から。Omni 1.2 Flash では動画の編集も可能。",
        "Gera vídeos com som com Veo 3.1 Lite ou Omni 1.2 Flash: a partir de texto, quadros inicial e final, imagens de referência, personagens e voz, ou edita um vídeo com Omni 1.2 Flash.",
    ),
    "Generate Google Flow videos with sound. Modes: text-to-video; start image (+ end image); reference images and characters (+ voice); or a video edit with reference_video (Omni 1.2 Flash). Spends the account's Google Flow credits. Waits up to max_wait, else returns a jobid for get_job.",
    [
        PROMPT_VIDEO,
        select(
            "model",
            L("Model", "模型", "モデル", "Modelo"),
            L(
                "Veo 3.1 Lite (default), Omni 1.2 Flash, or Veo 3.1 Lite Lower Priority (Google AI Ultra $199 only).",
                "Veo 3.1 Lite（默认）、Omni 1.2 Flash，或 Veo 3.1 Lite 低优先级（仅限 Google AI Ultra $199）。",
                "Veo 3.1 Lite（既定）、Omni 1.2 Flash、または Veo 3.1 Lite 低優先度（Google AI Ultra $199 のみ）。",
                "Veo 3.1 Lite (padrão), Omni 1.2 Flash ou Veo 3.1 Lite Lower Priority (só Google AI Ultra $199).",
            ),
            VIDEO_MODEL_OPTIONS,
            "Video model. veo-3.1-lite (default, every plan), omni-flash-1.2 (every plan; edits, 3 to 15 s, 360p), veo-3.1-lite-low-priority (Google AI Ultra $199 plan owner only, 0 credits).",
            default="veo-3.1-lite",
        ),
        select(
            "aspect_ratio",
            L("Aspect ratio", "画面比例", "アスペクト比", "Proporção"),
            L("Landscape (default) or portrait.", "横向（默认）或纵向。", "横向き（既定）または縦向き。", "Paisagem (padrão) ou retrato."),
            ASPECT_VIDEO,
        ),
        param(
            "duration",
            "number",
            L("Duration (seconds)", "时长（秒）", "長さ（秒）", "Duração (segundos)"),
            L(
                "Default 8. Veo 3.1: 4, 6 or 8 (4 and 6 on Google AI Ultra). Omni 1.2 Flash: 3 to 15 (above 10 on paid plans).",
                "默认 8。Veo 3.1：4、6 或 8（4 和 6 需 Google AI Ultra）。Omni 1.2 Flash：3 到 15（超过 10 需付费方案）。",
                "既定 8。Veo 3.1：4・6・8（4 と 6 は Google AI Ultra）。Omni 1.2 Flash：3〜15（10 超は有料プラン）。",
                "Padrão 8. Veo 3.1: 4, 6 ou 8 (4 e 6 no Google AI Ultra). Omni 1.2 Flash: 3 a 15 (acima de 10 em planos pagos).",
            ),
            "Seconds, default 8. Veo 3.1 Lite: 4, 6 or 8 (4 and 6 need Google AI Ultra; 8 with references). Omni 1.2 Flash: 3 to 15 (3 to 10 with start and end images; above 10 on paid plans). Ignored for a video edit.",
            min=3,
            max=15,
        ),
        select(
            "resolution",
            L("Resolution", "分辨率", "解像度", "Resolução"),
            L(
                "720p (default) or 360p on Omni 1.2 Flash.",
                "720p（默认），Omni 1.2 Flash 可选 360p。",
                "720p（既定）。Omni 1.2 Flash は 360p も可。",
                "720p (padrão) ou 360p no Omni 1.2 Flash.",
            ),
            RESOLUTION_VIDEO,
        ),
        COUNT("videos", "视频", "動画", "vídeos"),
        START_IMAGE,
        START_IMAGE_FILE,
        END_IMAGE,
        END_IMAGE_FILE,
        REFERENCE_IMAGES(10),
        REFERENCE_IMAGE_FILES(10),
        CHARACTERS(10),
        VOICE,
        ID_PARAM(
            "reference_video",
            L("Video to edit (ID)", "要编辑的视频（ID）", "編集する動画（ID）", "Vídeo a editar (ID)"),
            L(
                "Optional media id of a video to edit (Omni 1.2 Flash).",
                "可选。要编辑的视频的媒体 ID（Omni 1.2 Flash）。",
                "任意。編集する動画のメディア ID（Omni 1.2 Flash）。",
                "ID de mídia opcional de um vídeo a editar (Omni 1.2 Flash).",
            ),
            "Optional media id of a video to edit with omni-flash-1.2. Turns the request into a video edit; not with start or end images.",
        ),
        FILE_PARAM(
            "reference_video_file",
            L("Video to edit (file)", "要编辑的视频（文件）", "編集する動画（ファイル）", "Vídeo a editar (arquivo)"),
            L(
                "Optional. Or upload the MP4 to edit here.",
                "可选。也可以在这里上传要编辑的 MP4。",
                "任意。編集する MP4 をここでアップロードすることもできます。",
                "Opcional. Ou envie aqui o MP4 a editar.",
            ),
            "Optional MP4 file to edit, used when reference_video is empty.",
        ),
        param(
            "start_frame",
            "number",
            L("Edit start frame", "编辑起始帧", "編集の開始フレーム", "Quadro inicial da edição"),
            L(
                "Optional, video edit only. Start of the edited slice at 24 frames per second (24 = 1 s).",
                "可选，仅用于视频编辑。按每秒 24 帧计算的编辑起点（24 = 1 秒）。",
                "任意。動画編集のみ。毎秒 24 フレームでの編集開始位置（24 = 1 秒）。",
                "Opcional, só para edição. Início do trecho editado a 24 quadros por segundo (24 = 1 s).",
            ),
            "Optional, with reference_video only: first frame of the slice to edit on a 24 fps timeline (0 to 359).",
            min=0,
            max=359,
        ),
        param(
            "end_frame",
            "number",
            L("Edit end frame", "编辑结束帧", "編集の終了フレーム", "Quadro final da edição"),
            L(
                "Optional, video edit only. End of the edited slice (240 = 10 s, 360 = 15 s).",
                "可选，仅用于视频编辑。编辑终点（240 = 10 秒，360 = 15 秒）。",
                "任意。動画編集のみ。編集終了位置（240 = 10 秒、360 = 15 秒）。",
                "Opcional, só para edição. Fim do trecho editado (240 = 10 s, 360 = 15 s).",
            ),
            "Optional, with reference_video only: end frame of the slice on a 24 fps timeline (1 to 360; up to 240 on a free plan).",
            min=1,
            max=360,
        ),
        EMAIL(),
        WAIT,
        MAX_WAIT(120),
        RETURN_FILE(),
        REPLY_URL,
    ],
    GEN_OUTPUT,
)

tool(
    "extend_video",
    L("Extend video", "延长视频", "動画を延長", "Estender vídeo"),
    L(
        "Add 3 to 10 seconds to a video and get one continuous clip. Omni 1.2 Flash needs a paid plan; Veo 3.1 Lite works on every plan.",
        "为视频追加 3 到 10 秒，得到一段连续的视频。Omni 1.2 Flash 需付费方案；Veo 3.1 Lite 适用于所有方案。",
        "動画に 3〜10 秒を追加して 1 本の連続した動画にします。Omni 1.2 Flash は有料プラン、Veo 3.1 Lite は全プランで利用可。",
        "Acrescenta 3 a 10 segundos a um vídeo e devolve um clipe contínuo. Omni 1.2 Flash exige plano pago; Veo 3.1 Lite funciona em todos.",
    ),
    "Extend a Google Flow video (shorter than 30 s) with what happens next. omni-flash-1.2 (default, paid plans) adds duration 3 to 10 s and takes references; Veo models add a fixed length. Waits up to max_wait, else returns a jobid for get_job.",
    [
        param(
            "prompt",
            "string",
            L("What happens next", "接下来发生什么", "続きの内容", "O que acontece a seguir"),
            L("Describe what happens next.", "描述接下来发生的内容。", "続きの内容を書いてください。", "Descreva o que acontece a seguir."),
            "What happens next in the video.",
            required=True,
        ),
        *VIDEO_ID("video to extend (shorter than 30 seconds)"),
        select(
            "model",
            L("Model", "模型", "モデル", "Modelo"),
            L(
                "Omni 1.2 Flash (default, paid plans), Veo 3.1 Lite, or Veo 3.1 Lite Lower Priority (Google AI Ultra $199 only).",
                "Omni 1.2 Flash（默认，付费方案）、Veo 3.1 Lite，或 Veo 3.1 Lite 低优先级（仅限 Google AI Ultra $199）。",
                "Omni 1.2 Flash（既定、有料プラン）、Veo 3.1 Lite、または Veo 3.1 Lite 低優先度（Google AI Ultra $199 のみ）。",
                "Omni 1.2 Flash (padrão, planos pagos), Veo 3.1 Lite ou Veo 3.1 Lite Lower Priority (só Google AI Ultra $199).",
            ),
            EXTEND_MODEL_OPTIONS,
            "Extend model: omni-flash-1.2 (default, paid plans), veo-3.1-lite (every plan) or veo-3.1-lite-low-priority (Google AI Ultra $199 owner only).",
            default="omni-flash-1.2",
        ),
        param(
            "duration",
            "number",
            L("Seconds to add", "追加秒数", "追加する秒数", "Segundos a acrescentar"),
            L(
                "Omni 1.2 Flash only: 3 to 10 (default 8).",
                "仅 Omni 1.2 Flash：3 到 10（默认 8）。",
                "Omni 1.2 Flash のみ：3〜10（既定 8）。",
                "Só Omni 1.2 Flash: 3 a 10 (padrão 8).",
            ),
            "Omni 1.2 Flash only: seconds to add, 3 to 10. Default 8.",
            min=3,
            max=10,
        ),
        select(
            "resolution",
            L("Resolution", "分辨率", "解像度", "Resolução"),
            L(
                "Omni 1.2 Flash only. Default: the source's.",
                "仅 Omni 1.2 Flash。默认与原视频相同。",
                "Omni 1.2 Flash のみ。既定は元動画と同じ。",
                "Só Omni 1.2 Flash. Padrão: a do vídeo de origem.",
            ),
            RESOLUTION_VIDEO,
        ),
        REFERENCE_IMAGES(3),
        REFERENCE_IMAGE_FILES(3),
        CHARACTERS(3),
        VOICE,
        COUNT("extensions", "延长结果", "延長結果", "extensões"),
        WAIT,
        MAX_WAIT(120),
        RETURN_FILE(),
        REPLY_URL,
    ],
    GEN_OUTPUT,
)

tool(
    "upscale_video",
    L("Upscale video", "视频超分", "動画をアップスケール", "Aumentar resolução do vídeo"),
    L(
        "Upscale a video of up to 15 seconds to 720p or 1080p (paid plans), or 4K (Google AI Ultra).",
        "将最长 15 秒的视频超分到 720p 或 1080p（付费方案），或 4K（Google AI Ultra）。",
        "15 秒以内の動画を 720p・1080p（有料プラン）または 4K（Google AI Ultra）にアップスケールします。",
        "Aumenta um vídeo de até 15 segundos para 720p ou 1080p (planos pagos) ou 4K (Google AI Ultra).",
    ),
    "Upscale a Google Flow video of up to 15 s. 720p promotes a 360p Omni clip; 720p and 1080p on paid plans; 4K on Google AI Ultra. Waits up to max_wait, else returns a jobid for get_job.",
    [
        *VIDEO_ID("video to upscale (up to 15 seconds)"),
        select(
            "resolution",
            L("Resolution", "分辨率", "解像度", "Resolução"),
            L("1080p (default), 720p or 4K.", "1080p（默认）、720p 或 4K。", "1080p（既定）、720p、4K。", "1080p (padrão), 720p ou 4K."),
            UPSCALE_VIDEO,
        ),
        WAIT,
        MAX_WAIT(120),
        RETURN_FILE(),
        REPLY_URL,
    ],
    GEN_OUTPUT,
)

tool(
    "generate_image",
    L("Generate image", "生成图片", "画像を生成", "Gerar imagem"),
    L(
        "Make images with Nano Banana 2 Lite, Nano Banana 2.1 or Nano Banana Pro, from text and up to 10 reference images or characters. Images use no Google Flow credits.",
        "使用 Nano Banana 2 Lite、Nano Banana 2.1 或 Nano Banana Pro 生成图片，可基于文本和最多 10 张参考图片或角色。图片不消耗 Google Flow 积分。",
        "Nano Banana 2 Lite・Nano Banana 2.1・Nano Banana Pro で画像を作成。テキストと最大 10 枚の参照画像やキャラクターから。画像は Google Flow クレジットを消費しません。",
        "Gera imagens com Nano Banana 2 Lite, Nano Banana 2.1 ou Nano Banana Pro, a partir de texto e até 10 imagens de referência ou personagens. Imagens não gastam créditos do Google Flow.",
    ),
    "Generate Google Flow images (no Google Flow credits used). Returns the images as files, their media ids (usable as start or reference images for videos) and links.",
    [
        param(
            "prompt",
            "string",
            L("Prompt", "提示词", "プロンプト", "Prompt"),
            L(
                "What the image shows. You can name references inline: @reference_1, @character_1.",
                "图片内容描述。可在文中引用：@reference_1、@character_1。",
                "画像の内容。参照を本文で指定できます：@reference_1、@character_1。",
                "O que a imagem mostra. Você pode citar referências: @reference_1, @character_1.",
            ),
            "The image prompt. It may name the references inline as @reference_N or @character_N.",
            required=True,
        ),
        select(
            "model",
            L("Model", "模型", "モデル", "Modelo"),
            L(
                "Nano Banana 2 Lite (default), Nano Banana 2.1 or Nano Banana Pro.",
                "Nano Banana 2 Lite（默认）、Nano Banana 2.1 或 Nano Banana Pro。",
                "Nano Banana 2 Lite（既定）、Nano Banana 2.1、Nano Banana Pro。",
                "Nano Banana 2 Lite (padrão), Nano Banana 2.1 ou Nano Banana Pro.",
            ),
            IMAGE_MODEL_OPTIONS,
            "Image model: nano-banana-2-lite (default), nano-banana-2 (Nano Banana 2.1) or nano-banana-pro. All on every plan.",
            default="nano-banana-2-lite",
        ),
        select(
            "aspect_ratio",
            L("Aspect ratio", "画面比例", "アスペクト比", "Proporção"),
            L(
                "Default 16:9. Auto takes the shape of the first reference.",
                "默认 16:9。自动按第一张参考图的形状。",
                "既定 16:9。自動は最初の参照画像の形に合わせます。",
                "Padrão 16:9. Automático usa o formato da primeira referência.",
            ),
            ASPECT_IMAGE,
        ),
        COUNT("images", "图片", "画像", "imagens"),
        param(
            "seed",
            "number",
            L("Seed", "随机种子", "シード", "Semente"),
            L(
                "Optional seed for repeatable results.",
                "可选。用于复现结果的随机种子。",
                "任意。結果を再現するためのシード。",
                "Semente opcional para resultados repetíveis.",
            ),
            "Optional integer seed.",
            min=0,
        ),
        select(
            "thinking_level",
            L("Thinking level", "思考强度", "思考レベル", "Nível de raciocínio"),
            L(
                "Nano Banana 2.1 only. High (default); low and medium on paid plans.",
                "仅 Nano Banana 2.1。高（默认）；低和中需付费方案。",
                "Nano Banana 2.1 のみ。高（既定）。低・中は有料プラン。",
                "Só Nano Banana 2.1. Alto (padrão); baixo e médio em planos pagos.",
            ),
            THINKING,
            "Only with nano-banana-2: how long it reasons before it draws. high (default); low and medium need a paid Google AI plan.",
        ),
        REFERENCE_IMAGES(10),
        REFERENCE_IMAGE_FILES(10),
        CHARACTERS(7),
        EMAIL(),
        RETURN_FILE(),
        REPLY_URL,
    ],
    GEN_OUTPUT,
)

tool(
    "upscale_image",
    L("Upscale image", "图片超分", "画像をアップスケール", "Aumentar resolução da imagem"),
    L(
        "Upscale a Google Flow image to 2K, or 4K on Google AI Ultra. Returns the file.",
        "将 Google Flow 图片超分到 2K，Google AI Ultra 可到 4K。返回文件。",
        "Google Flow の画像を 2K（Google AI Ultra は 4K）にアップスケールし、ファイルを返します。",
        "Aumenta uma imagem do Google Flow para 2K, ou 4K no Google AI Ultra. Retorna o arquivo.",
    ),
    "Upscale a Google Flow image to 2k (every plan) or 4k (Google AI Ultra). Returns the JPEG file.",
    [
        *IMAGE_ID,
        select(
            "resolution",
            L("Resolution", "分辨率", "解像度", "Resolução"),
            L("2K (default) or 4K.", "2K（默认）或 4K。", "2K（既定）または 4K。", "2K (padrão) ou 4K."),
            UPSCALE_IMAGE,
        ),
    ],
)

tool(
    "video_to_gif",
    L("Video to GIF", "视频转 GIF", "動画を GIF に", "Vídeo para GIF"),
    L(
        "Turn a Google Flow video into an animated GIF file.",
        "将 Google Flow 视频转换为 GIF 动图文件。",
        "Google Flow の動画をアニメーション GIF ファイルにします。",
        "Transforma um vídeo do Google Flow em um arquivo GIF animado.",
    ),
    "Make an animated GIF of a Google Flow video. Returns the GIF file.",
    VIDEO_ID("video"),
)

tool(
    "concatenate_videos",
    L("Join videos", "拼接视频", "動画を結合", "Juntar vídeos"),
    L(
        "Join 2 to 10 Google Flow videos, in order, into one MP4 file.",
        "按顺序将 2 到 10 个 Google Flow 视频拼接成一个 MP4 文件。",
        "2〜10 本の Google Flow 動画を順番どおりに 1 つの MP4 ファイルに結合します。",
        "Junta de 2 a 10 vídeos do Google Flow, em ordem, em um único arquivo MP4.",
    ),
    "Concatenate 2 to 10 Google Flow videos (all landscape or all portrait) into one MP4 file.",
    [
        param(
            "videos",
            "string",
            L("Video IDs", "视频 ID", "動画 ID", "IDs dos vídeos"),
            L(
                "Media ids of the videos in order, one per line.",
                "按顺序填写视频的媒体 ID，每行一个。",
                "動画のメディア ID を順番に 1 行に 1 つ。",
                "IDs de mídia dos vídeos em ordem, um por linha.",
            ),
            "Media ids of the videos to join, in order, separated by new lines.",
        ),
        FILE_PARAM(
            "video_files",
            L("Video files", "视频文件", "動画ファイル", "Arquivos de vídeo"),
            L(
                "Optional MP4 files, added after the ids.",
                "可选。MP4 文件，排在 ID 之后。",
                "任意。MP4 ファイル（ID の後に追加）。",
                "Arquivos MP4 opcionais, adicionados após os IDs.",
            ),
            "Optional MP4 files added after the ids, in order.",
            many=True,
        ),
        param(
            "media_json",
            "string",
            L("Trims (JSON)", "裁剪（JSON）", "トリム（JSON）", "Cortes (JSON)"),
            L(
                'Optional. Instead of the ids: [{"mediaGenerationId": "...", "trimStart": 0.5, "trimEnd": 0}] in seconds.',
                '可选。替代 ID：[{"mediaGenerationId": "...", "trimStart": 0.5, "trimEnd": 0}]，单位为秒。',
                '任意。ID の代わりに：[{"mediaGenerationId": "...", "trimStart": 0.5, "trimEnd": 0}]（秒）。',
                'Opcional. No lugar dos IDs: [{"mediaGenerationId": "...", "trimStart": 0.5, "trimEnd": 0}] em segundos.',
            ),
            'Optional JSON array replacing videos: [{"mediaGenerationId": "...", "trimStart": 0, "trimEnd": 0}], trims in seconds (0 to 60).',
        ),
    ],
)

# --- media

tool(
    "upload_image",
    L("Upload image or video", "上传图片或视频", "画像・動画をアップロード", "Enviar imagem ou vídeo"),
    L(
        "Upload a PNG, JPEG or WebP image (up to 20 MB) or an MP4 video (up to 100 MB) to a Google account and get its media id.",
        "将 PNG、JPEG、WebP 图片（最大 20 MB）或 MP4 视频（最大 100 MB）上传到 Google 账号，并获取媒体 ID。",
        "PNG・JPEG・WebP 画像（20 MB まで）または MP4 動画（100 MB まで）を Google アカウントにアップロードし、メディア ID を取得します。",
        "Envia uma imagem PNG, JPEG ou WebP (até 20 MB) ou um vídeo MP4 (até 100 MB) para uma conta Google e retorna o ID de mídia.",
    ),
    "Upload an image or MP4 to Google Flow and get its media id, for start_image, reference_images, reference_video or video in the other tools. Media work only with the same Google account.",
    [
        FILE_PARAM(
            "file",
            L("File", "文件", "ファイル", "Arquivo"),
            L("The image or video to upload.", "要上传的图片或视频。", "アップロードする画像または動画。", "A imagem ou vídeo a enviar."),
            "The image or MP4 file to upload.",
        )
        | {"required": True},
        EMAIL(),
    ],
    {"media_id": {"type": "string"}, "email": {"type": "string"}},
)

tool(
    "list_media",
    L("List media", "列出媒体", "メディア一覧", "Listar mídia"),
    L(
        "List the images and videos in a Google account's Google Flow project, newest first, with their media ids.",
        "列出 Google 账号的 Google Flow 项目中的图片和视频（按时间倒序），包括媒体 ID。",
        "Google アカウントの Google Flow プロジェクトにある画像と動画を新しい順に、メディア ID とともに一覧表示します。",
        "Lista as imagens e vídeos do projeto do Google Flow de uma conta Google, mais novos primeiro, com seus IDs de mídia.",
    ),
    "List the images and videos in a Google Flow project with their media ids and whether each is an upload.",
    [EMAIL_READ("media"), PROJECT_ID],
    {"media_ids": {"type": "array", "items": {"type": "string"}}},
)

tool(
    "get_media",
    L("Get media", "获取媒体", "メディアを取得", "Obter mídia"),
    L(
        "Get a fresh link (valid about 6 hours) for an image or video, and optionally the file.",
        "获取图片或视频的新链接（约 6 小时有效），可选返回文件。",
        "画像や動画の新しいリンク（約 6 時間有効）を取得し、必要ならファイルも返します。",
        "Obtém um link novo (válido por cerca de 6 horas) de uma imagem ou vídeo e, se quiser, o arquivo.",
    ),
    "Get a fresh signed link for a Google Flow image or video by media id. Links expire about 6 hours after they are made.",
    [
        param(
            "media_id",
            "string",
            L("Media ID", "媒体 ID", "メディア ID", "ID de mídia"),
            L(
                "The media id of an image or video.",
                "图片或视频的媒体 ID。",
                "画像または動画のメディア ID。",
                "O ID de mídia de uma imagem ou vídeo.",
            ),
            "The media id, e.g. user:12345-email:...-video:...",
            required=True,
        ),
        RETURN_FILE(),
    ],
    {"file_url": {"type": "string"}},
)

tool(
    "list_characters",
    L("List characters", "列出角色", "キャラクター一覧", "Listar personagens"),
    L(
        "List the characters saved on a Google account, with their ids and voices.",
        "列出 Google 账号中保存的角色，包括 ID 和声音。",
        "Google アカウントに保存されたキャラクターを ID と音声とともに一覧表示します。",
        "Lista os personagens salvos em uma conta Google, com IDs e vozes.",
    ),
    "List the Google Flow characters of an account. Pass a character id in 'characters' and name it @character_N in the prompt.",
    [EMAIL_READ("characters")],
    {"character_ids": {"type": "array", "items": {"type": "string"}}},
)

tool(
    "list_voices",
    L("List voices", "列出声音", "音声一覧", "Listar vozes"),
    L(
        "List the built-in voices and your own voices on a Google account.",
        "列出 Google 账号中的内置声音和你自己的声音。",
        "Google アカウントの組み込み音声と自分の音声を一覧表示します。",
        "Lista as vozes embutidas e as suas próprias vozes em uma conta Google.",
    ),
    "List Google Flow voices: built-in ones (pass the name) and the account's own (pass the voice id) as 'voice' or 'voices'.",
    [
        EMAIL_READ("voices"),
        select(
            "source",
            L("Which voices", "声音类型", "音声の種類", "Quais vozes"),
            L(
                "Optional. Built-in or my voices only.",
                "可选。仅内置或仅我的声音。",
                "任意。組み込みのみ、または自分の音声のみ。",
                "Opcional. Só embutidas ou só minhas.",
            ),
            VOICE_SOURCES,
        ),
    ],
    {"voices": {"type": "array", "items": {"type": "string"}}},
)

# --- Google Flow agent

AGENT_WAIT = param(
    "wait",
    "boolean",
    L("Wait for the reply", "等待回复", "返信を待つ", "Aguardar a resposta"),
    L(
        "Wait until the agent's turn ends (up to the maximum wait).",
        "等待智能体本轮结束（不超过最长等待时间）。",
        "エージェントのターンが終わるまで待ちます（最大待機時間まで）。",
        "Aguarda o turno do agente terminar (até o tempo máximo).",
    ),
    form="form",
    default=True,
)

tool(
    "agent_chat",
    L("Google Flow agent chat", "Google Flow 智能体对话", "Google Flow エージェントとチャット", "Chat com o agente do Google Flow"),
    L(
        "Chat with the Google Flow agent: it plans, writes storyboards and makes images and videos with the Google Flow models. Start a chat or continue one.",
        "与 Google Flow 智能体对话：它会规划、编写分镜，并用 Google Flow 模型生成图片和视频。可开始新对话或继续已有对话。",
        "Google Flow エージェントとチャット：企画や絵コンテを作り、Google Flow のモデルで画像や動画を作ります。新しいチャットも続きも可能。",
        "Converse com o agente do Google Flow: ele planeja, escreve storyboards e cria imagens e vídeos com os modelos do Google Flow. Comece ou continue um chat.",
    ),
    "Send a message to the Google Flow agent (Google's own creative agent: it plans, writes storyboards and generates images and videos). Without chat_id a new chat starts; with chat_id the message continues it (one turn at a time). Give images, a video, voices and characters as references and name them in the message as @referenceImage_1, @referenceVideo_1, @referenceAudio_1, @character_1. Returns the agent's reply, the status (idle / waiting_approval / failed / running), media ids and links. Chatting uses one captcha per turn; what the agent generates costs Google Flow credits, and in ask mode it asks first: then call agent_answer_approval after asking the user.",
    [
        param(
            "message",
            "string",
            L("Message", "消息", "メッセージ", "Mensagem"),
            L("What you say to the agent.", "你要对智能体说的话。", "エージェントへのメッセージ。", "O que você diz ao agente."),
            "What to say to the agent (up to 20,000 characters).",
            required=True,
        ),
        param(
            "chat_id",
            "string",
            L("Chat ID", "对话 ID", "チャット ID", "ID do chat"),
            L(
                "Optional. Continue this chat. Empty: start a new chat.",
                "可选。继续此对话。留空：开始新对话。",
                "任意。このチャットを続けます。空欄なら新しいチャット。",
                "Opcional. Continua este chat. Vazio: começa um novo.",
            ),
            "Optional chat_id from an earlier agent_chat to continue that chat. Leave empty for a new chat.",
        ),
        REFERENCE_IMAGES(7),
        REFERENCE_IMAGE_FILES(7),
        ID_PARAM(
            "reference_video",
            L("Reference video ID", "参考视频 ID", "参照動画 ID", "ID do vídeo de referência"),
            L("Optional media id of a video.", "可选。视频的媒体 ID。", "任意。動画のメディア ID。", "ID de mídia opcional de um vídeo."),
            "Optional media id of a video, named @referenceVideo_1 in the message.",
        ),
        FILE_PARAM(
            "reference_video_file",
            L("Reference video file", "参考视频文件", "参照動画ファイル", "Arquivo do vídeo de referência"),
            L(
                "Optional. Or upload an MP4 here.",
                "可选。也可以在这里上传 MP4。",
                "任意。MP4 をここでアップロードすることもできます。",
                "Opcional. Ou envie um MP4 aqui.",
            ),
            "Optional MP4 file used as the reference video when reference_video is empty.",
        ),
        param(
            "voices",
            "string",
            L("Voices", "声音", "音声", "Vozes"),
            L(
                "Optional built-in voice names or voice ids, one per line (up to 5).",
                "可选。内置声音名称或声音 ID，每行一个（最多 5 个）。",
                "任意。組み込み音声名または音声 ID を 1 行に 1 つ（最大 5 件）。",
                "Nomes de vozes embutidas ou IDs de voz opcionais, um por linha (até 5).",
            ),
            "Optional voices (built-in names like Kore, or voice ids from list_voices), up to 5, named @referenceAudio_N in the message.",
        ),
        CHARACTERS(7),
        EMAIL(),
        PROJECT_ID,
        AGENT_WAIT,
        MAX_WAIT(120),
        RETURN_FILE(False),
        REPLY_URL,
    ],
    CHAT_OUTPUT,
)

tool(
    "agent_get_chat",
    L(
        "Get Google Flow agent chat",
        "获取 Google Flow 智能体对话",
        "Google Flow エージェントのチャットを取得",
        "Ver chat do agente do Google Flow",
    ),
    L(
        "Read an agent chat: its status, the latest reply, the approval it waits for, and the images and videos with fresh links.",
        "读取智能体对话：状态、最新回复、等待的批准，以及带新链接的图片和视频。",
        "エージェントのチャットを読み取ります：状態、最新の返信、承認待ちの内容、新しいリンク付きの画像と動画。",
        "Lê um chat do agente: status, última resposta, a aprovação pendente e as imagens e vídeos com links novos.",
    ),
    "Read a Google Flow agent chat. With wait=true, waits until the running turn ends and its videos finish (up to max_wait). Videos usually finish a minute or two after the turn.",
    [
        CHAT_ID,
        param(
            "wait",
            "boolean",
            L("Wait for the turn and videos", "等待本轮和视频", "ターンと動画を待つ", "Aguardar o turno e os vídeos"),
            L(
                "Wait until the turn ends and its videos are ready (up to the maximum wait).",
                "等待本轮结束且视频就绪（不超过最长等待时间）。",
                "ターンが終わり動画ができるまで待ちます（最大待機時間まで）。",
                "Aguarda o turno terminar e os vídeos ficarem prontos (até o tempo máximo).",
            ),
            "true to wait until the turn ends and queued videos finish.",
            default=False,
        ),
        MAX_WAIT(120),
        RETURN_FILE(False),
    ],
    CHAT_OUTPUT,
)

tool(
    "agent_answer_approval",
    L(
        "Answer the agent's approval request",
        "答复智能体的批准请求",
        "エージェントの承認リクエストに回答",
        "Responder ao pedido de aprovação do agente",
    ),
    L(
        "Approve or reject what the agent wants to generate (it states the cost in Google Flow credits). Answer within about 4 minutes.",
        "批准或拒绝智能体想要生成的内容（它会说明消耗的 Google Flow 积分）。请在约 4 分钟内答复。",
        "エージェントが生成しようとしている内容（Google Flow クレジットの消費量を提示）を承認または拒否します。約 4 分以内に回答してください。",
        "Aprova ou rejeita o que o agente quer gerar (ele informa o custo em créditos do Google Flow). Responda em cerca de 4 minutos.",
    ),
    "Answer the agent's permission request (status waiting_approval). approve: generate it (charged in Google Flow credits); always: approve and stop asking in this project; reject: do not generate. Ask the user first. Answer within about 4 minutes, after that Google closes the request.",
    [
        CHAT_ID,
        select(
            "decision",
            L("Decision", "决定", "回答", "Decisão"),
            L(
                "Approve, always approve, or reject.",
                "批准、始终批准或拒绝。",
                "承認、常に承認、拒否。",
                "Aprovar, sempre aprovar ou rejeitar.",
            ),
            DECISIONS,
            "approve, always or reject.",
        )
        | {"required": True},
        AGENT_WAIT,
        MAX_WAIT(120),
        RETURN_FILE(False),
    ],
    CHAT_OUTPUT,
)

tool(
    "agent_list_chats",
    L(
        "List Google Flow agent chats",
        "列出 Google Flow 智能体对话",
        "Google Flow エージェントのチャット一覧",
        "Listar chats do agente do Google Flow",
    ),
    L(
        "List the agent chats of a Google account, with their ids and titles.",
        "列出 Google 账号的智能体对话，包括 ID 和标题。",
        "Google アカウントのエージェントチャットを ID とタイトルとともに一覧表示します。",
        "Lista os chats do agente de uma conta Google, com IDs e títulos.",
    ),
    "List the Google Flow agent chats of an account: chat_id, title, updated, and whether a turn is running.",
    [EMAIL_READ("agent chats"), PROJECT_ID],
    {"chat_ids": {"type": "array", "items": {"type": "string"}}},
)
