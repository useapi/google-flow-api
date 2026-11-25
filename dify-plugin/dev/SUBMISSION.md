# Submitting to the Dify Marketplace

Local notes, not shipped in the package (`dev/` is in `.difyignore`). Rules as checked for `useapi/notebooklm_useapi` (accepted as 0.1.2) against `langgenius/dify-plugins` (README, `docs/plugin-submission-requirements.md`, `.github/pull_request_template.md`, `.github/workflows/pre-check-plugin.yaml`) and `langgenius/dify-marketplace-toolkit` (the validators the PR check runs). Re-check them before submitting.

## What the Marketplace requires

- **One file per PR**: the `.difypkg` only, at `useapi/google_flow_useapi/google_flow_useapi-0.1.0.difypkg`.
- **Public source repository**: `https://github.com/useapi/google-flow-api` (folder `dify-plugin/`), in `manifest.yaml` `repo` and linked in `README.md`. Push the folder before the PR, because the README links to it.
- **Manifest**: author, name, version, type `plugin`, icon in `_assets/`, privacy, repo, contact email, en_US label and description, runner. All present.
- **PRIVACY.md** in the package, referenced by `privacy:`. Present.
- **README in English**; localized READMEs in `readme/README_<locale>.md` (zh_Hans, ja_JP, pt_BR).
- **Dependencies**: `dify_plugin==0.10.2`, `requests==2.34.2`, pinned, no git or URL installs.
- **Paid services**: the plugin is free; the useapi.net subscription, the Google AI plan and captcha solving are disclosed in the description and README.
- **Brands**: "Google Flow" is a Google product. The label says "by useapi.net", the description says "not affiliated with Google", and the icon is our own logo. Answer any proof request the same way as for the Gemini Notebook plugin.
- **No duplicates**: search the Marketplace for "Google Flow", "Veo" and "Flow" before submitting.

## Media download decision

Generated images and videos come back from the API as Google's signed links on `https://flow-content.google` (no authentication, valid about 6 hours). The plugin downloads them and returns Dify files, because that is what workflows and agents can pass on (an expiring link is not). To keep the network surface small:

- `flow-content.google` is declared in `manifest.yaml` `network.domains`, next to `api.useapi.net`;
- `Client.download_media` refuses any URL that is not `https://flow-content.google/...`, does not follow redirects, and sends no token;
- each file is capped at 150 MB, and "Attach the files" (`return_file`) turns downloading off, leaving the links in `file_urls`.

Images that come back without a link carry the image as base64 instead; Upscale image, Video to GIF and Join videos always return base64. Those are decoded locally and need no download.

## Async mode

The API's sync mode can hold a video request for up to 600 seconds, which is all of Dify's plugin limit. Video tools therefore submit with `async: true` and poll `GET /jobs/{jobid}` every 10 seconds, up to "Maximum wait" (default 120, max 420), then return the `jobid`. Images, image upscale, GIF and join have no async mode in the catalog and answer within about 100 to 180 seconds.

## Steps

1. Review and commit `dify-plugin/` in `useapi/google-flow-api`, add a "Use in Dify" section to the repo README, then push.
2. Rebuild the package from the pushed tree (download `dify-plugin-linux-amd64` from https://github.com/langgenius/dify-plugin-daemon/releases):
   ```bash
   dify plugin package ./dify-plugin -o google_flow_useapi-0.1.0.difypkg
   ```
3. Attach it to a GitHub release (`gh release create dify-v0.1.0 google_flow_useapi-0.1.0.difypkg`), since the READMEs point to Releases for manual install.
4. Install it on Dify Cloud (Plugins > Install plugin > Local package file) and run List Google accounts, Generate image and Generate video, then tick the testing checkbox in `pr-body.md` and replace the limitation line.
5. Fill `TODO(owner): dated price comparison` in `pr-body.md`.
6. Fork `langgenius/dify-plugins`, add the single file `useapi/google_flow_useapi/google_flow_useapi-0.1.0.difypkg`, push to the fork.
7. Open the PR to `main`:
   - Title: `Add Google Flow by useapi.net tool plugin (useapi/google_flow_useapi) 0.1.0`
   - Body: `dev/pr-body.md`.
   - Risk: Medium.
8. Wait for `pre-check-plugin`. Once merged, the plugin is listed automatically.
9. Updates later: bump `version` in `manifest.yaml`, `USER_AGENT` in `useapi_flow/client.py` and the tests, add `CHANGELOG.md` notes, and send a PR with only the new `.difypkg`.

## Local checks to repeat before submitting

```bash
python -m pytest
ruff check .
python dev/routing_check.py      # read-only routes answer 401 with a fake token; never a real token, never a generation
python3 validator/validate-difypkg.py <pkg> --pr-body-file dev/pr-body.md --output-dir <dir>   # in dify-marketplace-toolkit
INSTALL_METHOD=serverless SERVERLESS_PORT=8080 SERVERLESS_HOST=127.0.0.1 python3 validator/test-plugin-install.py -d <unpacked pkg>
```

The validator's remaining warnings are expected and explained in the PR body: "token" appears as a word in docs and error messages, `useapi.net` documentation links are found by the domain scan, and "payment"/"charged" match the 402 message, the price disclosure and the agent approval text.
