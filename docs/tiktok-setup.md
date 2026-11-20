# TikTok Direct Post setup

This repository now includes an optional TikTok Content Posting API publisher. It is deliberately disabled unless the TikTok credentials are supplied as GitHub Actions secrets.

## App configuration

For this workflow, the intended TikTok products/scopes are:
- Content Posting API with `video.publish` for Direct Post.
- Login Kit with `user.info.basic` only if the app also displays the connected account's profile.

Remove `video.upload` if the app does not offer draft/inbox uploads. Do not request Share Kit or Display API unless the product actually uses them.

## GitHub Actions secrets

After TikTok approves the app and the TikTok account owner completes OAuth authorization, add these under repository Settings → Secrets and variables → Actions:

- `TIKTOK_ACCESS_TOKEN`: OAuth access token for the authorized TikTok account.
Never put tokens in source files, commits, screenshots, or chat. The current workflow does not refresh OAuth tokens automatically; access tokens expire, so a production-ready OAuth callback/token-refresh service is still required before unattended long-term publishing.

## What the workflow does

When all three secrets are present and a rendered MP4 exists at `output/daily_story.mp4`, the workflow calls TikTok Creator Info, chooses an allowed privacy level, initializes a Direct Post file upload, transfers the MP4, and checks publish status. If the secrets are absent, TikTok publishing is skipped.

## Review/demo requirements still outstanding

A GitHub Actions upload step is not by itself a complete end-to-end website integration demo. TikTok review requires a real user-facing web flow on the submitted domain, TikTok OAuth authorization, and a sandbox demonstration before first approval. This repository's GitHub Pages site is static and cannot safely exchange OAuth authorization codes because it has no server-side secret storage/callback. Do not submit a screen recording that claims this complete flow exists until a secure OAuth callback/backend and the sandbox test are implemented and recorded.
