"""Tool -> API endpoint (catalog operation id), for the README tables and the routing check."""

ENDPOINTS = {
    "list_accounts": ("GET /accounts", "accounts-list"),
    "get_account": ("GET /accounts/{email}", "accounts-get"),
    "list_jobs": ("GET /jobs", "jobs-list"),
    "get_job": ("GET /jobs/{jobid}", "jobs-get"),
    "generate_video": ("POST /videos", "videos"),
    "extend_video": ("POST /videos/extend", "videos-extend"),
    "upscale_video": ("POST /videos/upscale", "videos-upscale"),
    "generate_image": ("POST /images", "images"),
    "upscale_image": ("POST /images/upscale", "images-upscale"),
    "video_to_gif": ("POST /videos/gif", "videos-gif"),
    "concatenate_videos": ("POST /videos/concatenate", "videos-concatenate"),
    "upload_image": ("POST /assets/{email}", "assets-upload"),
    "list_media": ("GET /assets/media/{email}", "assets-media-get"),
    "get_media": ("GET /assets/{mediaGenerationId}", "assets-get"),
    "list_characters": ("GET /characters", "characters-list"),
    "list_voices": ("GET /voices", "voices-list"),
    "agent_chat": ("POST /agent/chats, POST /agent/chats/{chatId}/messages", "agent-chats, agent-chats-messages"),
    "agent_get_chat": ("GET /agent/chats/{chatId}", "agent-chats-get"),
    "agent_answer_approval": ("POST /agent/chats/{chatId}/approval", "agent-chats-approval"),
    "agent_list_chats": ("GET /agent/chats", "agent-chats-list"),
}
