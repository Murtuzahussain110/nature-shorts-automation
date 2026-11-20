# CN Fun Cartoons — TikTok OAuth backend

This Worker stores TikTok OAuth tokens in Cloudflare KV and exposes a protected endpoint for the scheduled GitHub workflow. It never sends credentials to the browser.

## Cloudflare setup (one-time)
1. In Cloudflare Dashboard, create a Workers & Pages Worker named `cn-fun-cartoons-tiktok-oauth`.
2. Create a KV namespace named `CN_FUN_CARTOONS_TIKTOK`.
3. Replace the placeholder KV namespace `id` in `wrangler.toml` with the namespace ID.
4. In GitHub repository Settings → Secrets and variables → Actions, add repository secrets `CF_WORKERS_API_TOKEN` and `CF_ACCOUNT_ID`. The API token needs permission to deploy Workers. Then run the GitHub Actions workflow named **Deploy TikTok OAuth Worker**. The Worker will deploy at your account's workers.dev domain.
5. In Worker Settings → Variables and Secrets, add encrypted secrets:
   - `TIKTOK_CLIENT_KEY`: TikTok app client key
   - `TIKTOK_CLIENT_SECRET`: TikTok app client secret
   - `AUTOMATION_SECRET`: generate a long random secret (32+ characters)
6. Set `TIKTOK_REDIRECT_URI` to the deployed Worker URL plus `/auth/tiktok/callback`.
7. In TikTok Developer app, add that exact callback URL as the Redirect URI. The app must be in Sandbox for initial testing and have Login Kit + Content Posting API enabled with `user.info.basic` and `video.publish`.

## Authorize the TikTok account
Open `https://YOUR-WORKER-DOMAIN/auth/tiktok/start` in a browser and approve the requested permissions. The callback saves access and refresh tokens in Cloudflare KV.

## GitHub Actions secrets
Add these repository secrets:
- `TIKTOK_WORKER_URL`: Worker base URL, e.g. `https://cn-fun-cartoons-tiktok-oauth.YOUR-SUBDOMAIN.workers.dev`
- `TIKTOK_AUTOMATION_SECRET`: same value as Worker secret `AUTOMATION_SECRET`

Deployment-only secrets (used by the manual deploy workflow):
- `CF_WORKERS_API_TOKEN`: Cloudflare API token with Workers Scripts Edit permission
- `CF_ACCOUNT_ID`: Cloudflare account ID

The daily workflow calls the Worker for a fresh access token before TikTok publishing. The access token is passed only to the publishing process and is not stored in GitHub.

## Endpoints
- `GET /health`: public health check
- `GET /auth/tiktok/start`: begin TikTok OAuth
- `GET /auth/tiktok/callback`: OAuth callback
- `GET /internal/access-token`: protected, returns a valid access token for GitHub Actions
- `GET /internal/status`: protected connection status

Do not expose the Worker secrets, tokens, or KV contents. Do not submit a TikTok app review until the Sandbox flow has been tested end-to-end and the demo recording shows the real authorization and publishing experience.
