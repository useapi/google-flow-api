# Privacy Policy

This privacy policy covers the "Google Flow by useapi.net" Dify plugin (`useapi/google_flow_useapi`).

## What the plugin sends, and where

The plugin contacts two places only:

- `https://api.useapi.net`, the useapi.net Google Flow API, for every tool call;
- `https://flow-content.google`, Google's server for Google Flow images and videos, only to download a finished image or video from the signed link the API returned. No token or other credential is sent there.

It does not send data to analytics services or to any other third party.

Each request to useapi.net carries:

- your useapi.net API token, in the `Authorization` header, so useapi.net can identify your subscription;
- the optional Google account email you set in the credentials or in a tool;
- the content of the tool call: prompts, messages to the Google Flow agent, media, job and chat ids, and any image or video file you attach, which is uploaded to your Google account.

useapi.net runs the request on the Google account you connected to it. Your prompts, uploads and generated images and videos are therefore processed by Google Flow in that Google account.

## What the plugin stores

The plugin stores nothing. It keeps no logs, no cache and no copy of your data, and holds a request only while the tool runs. Dify stores your API token as an encrypted credential; the plugin does not. Account details the API returns, such as sign-in cookies, are removed before a result is passed to Dify.

Files the plugin returns to Dify (for example a generated `.mp4`) are stored by your Dify instance like any other tool output file.

## Data handled by the services the plugin calls

- **useapi.net** receives the requests above and keeps job records for 7 days. How useapi.net collects, uses and shares data is described in its Terms of Service and Privacy Policy: https://useapi.net/docs/legal
- **Google** processes your prompts, uploads and generated content in your Google account, under Google's Privacy Policy: https://policies.google.com/privacy
- **Your captcha provider**, if you configured one at useapi.net, solves the captcha each generation needs. The plugin does not contact it.

useapi.net is a third-party service. It is not affiliated with, endorsed by or sponsored by Google.

## Personal data

The plugin does not collect personal data for its own use. Personal data inside the content you send (for example, a photo you upload or a prompt you write) is sent to useapi.net and Google as described above, only because you asked a tool to process it. Do not send content you are not allowed to share with these services.

## Contact

Questions about this policy: support@useapi.net
