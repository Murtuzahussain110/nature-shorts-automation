# TikTok Content Posting API review pack

This document is an internal preparation checklist for the owner of CN Fun Cartoons Automation. It is not proof of TikTok approval.

## App details

- App name: CN Fun Cartoons Automation
- Website / demo: https://murtuzahussain110.github.io/nature-shorts-automation/
- Privacy policy: https://murtuzahussain110.github.io/nature-shorts-automation/privacy.html
- Terms of Service: https://murtuzahussain110.github.io/nature-shorts-automation/terms.html
- OAuth callback: https://cn-fun-cartoons-tiktok-oauth.baqar786abbs.workers.dev/auth/tiktok/callback
- Requested publishing scope: video.publish
- Account information scope: user.info.basic (only if retained as an enabled scope/product)

## Product description

CN Fun Cartoons prepares original short cartoon videos with narration, subtitles, captions, and hashtags. The account owner connects their own TikTok account through TikTok OAuth. The web demo lets the account owner select an MP4, preview it, edit the caption, choose one of the privacy settings returned by TikTok for that account, and explicitly confirm the publishing request. The service then sends the selected video to TikTok Content Posting API and can check its processing status.

The project also has a scheduled GitHub Actions pipeline that generates cartoon episodes and currently attempts Direct Post. Do not describe unattended publishing as a user-confirmed action. If TikTok's review guidelines require an explicit user confirmation for every post, the scheduled auto-post path must remain disabled until it is redesigned to meet those requirements.

## Demo recording checklist

Record a real screen capture of the deployed site and real TikTok account. Do not fabricate or edit evidence to imply an action succeeded when it did not.

1. Open the demo URL and show the app name and purpose.
2. Select **Connect TikTok**, complete TikTok OAuth, and return to the app.
3. Show the connected status and the publishing options loaded from TikTok Creator Info.
4. Select an original MP4 that you own. Show the in-page preview.
5. Enter or edit the caption.
6. Select a privacy option actually returned by TikTok.
7. Press **Publish test video** and confirm the action.
8. Show the actual API response and publishing status. If the account is sandbox-only or the post is private, state that accurately.

## Before submitting

- Confirm the website, privacy policy, terms, and OAuth callback are publicly reachable.
- Confirm the TikTok Developer Portal app has Content Posting API enabled and the required scope selected.
- Confirm the redirect URI exactly matches the Cloudflare callback URL configured in the app.
- Test the OAuth and publishing flow with the authorized account.
- Use the current TikTok Developer Portal review form and follow its requested evidence format. Review requirements can change; this checklist does not replace the portal's current instructions.
- Never include client secrets, access tokens, refresh tokens, or automation secrets in screenshots, screen recordings, or review text.
- Do not claim public posting is approved until TikTok has approved the app.
