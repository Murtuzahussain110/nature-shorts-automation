/**
 * TikTok OAuth backend for CN Fun Cartoons.
 * Secrets: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, AUTOMATION_SECRET
 * KV binding: TIKTOK_KV
 */
const API = "https://open.tiktokapis.com/v2";
const SITE_ORIGIN = "https://murtuzahussain110.github.io";

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extraHeaders
    }
  });
}
function safeEqual(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let out = 0;
  for (let i = 0; i < a.length; i++) out |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return out === 0;
}
async function exchangeToken(env, form) {
  const response = await fetch(API + "/oauth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(form)
  });
  const body = await response.json();
  if (!response.ok || body.error) throw new Error("TikTok token exchange failed: " + (body.error_description || body.error || response.status));
  return body;
}
async function getFreshToken(env) {
  const stored = await env.TIKTOK_KV.get("oauth_tokens", "json");
  if (!stored?.refresh_token) throw new Error("TikTok account has not authorized this app yet.");
  const expiry = Number(stored.expires_at || 0);
  if (Date.now() < expiry - 5 * 60 * 1000) return stored.access_token;
  const refreshed = await exchangeToken(env, {
    client_key: env.TIKTOK_CLIENT_KEY,
    client_secret: env.TIKTOK_CLIENT_SECRET,
    grant_type: "refresh_token",
    refresh_token: stored.refresh_token
  });
  const next = {
    access_token: refreshed.access_token,
    refresh_token: refreshed.refresh_token || stored.refresh_token,
    open_id: refreshed.open_id || stored.open_id,
    scope: refreshed.scope || stored.scope,
    expires_at: Date.now() + Number(refreshed.expires_in || 86400) * 1000,
    refresh_expires_at: Date.now() + Number(refreshed.refresh_expires_in || 0) * 1000
  };
  await env.TIKTOK_KV.put("oauth_tokens", JSON.stringify(next));
  return next.access_token;
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS" && url.pathname === "/public/status") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": SITE_ORIGIN,
          "Access-Control-Allow-Methods": "GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
          "Access-Control-Max-Age": "86400"
        }
      });
    }
    if (request.method === "GET" && url.pathname === "/health") return json({ ok: true, service: "cn-fun-cartoons-tiktok-oauth" });

    // Public endpoint reveals only whether a token is stored; never returns tokens or account identifiers.
    if (request.method === "GET" && url.pathname === "/public/status") {
      const stored = await env.TIKTOK_KV.get("oauth_tokens", "json");
      return json(
        { connected: Boolean(stored?.refresh_token) },
        200,
        { "Access-Control-Allow-Origin": SITE_ORIGIN, "Vary": "Origin" }
      );
    }

    if (request.method === "GET" && url.pathname === "/auth/tiktok/start") {
      const stateBytes = crypto.getRandomValues(new Uint8Array(32));
      const state = Array.from(stateBytes, b => b.toString(16).padStart(2, "0")).join("");
      await env.TIKTOK_KV.put("oauth_state:" + state, "1", { expirationTtl: 600 });
      const redirect = env.TIKTOK_REDIRECT_URI || (url.origin + "/auth/tiktok/callback");
      const auth = new URL("https://www.tiktok.com/v2/auth/authorize/");
      auth.search = new URLSearchParams({
        client_key: env.TIKTOK_CLIENT_KEY,
        scope: "user.info.basic,video.publish",
        response_type: "code",
        redirect_uri: redirect,
        state
      }).toString();
      return Response.redirect(auth.toString(), 302);
    }

    if (request.method === "GET" && url.pathname === "/auth/tiktok/callback") {
      const state = url.searchParams.get("state") || "";
      const valid = await env.TIKTOK_KV.get("oauth_state:" + state);
      if (!valid) return json({ error: "Invalid or expired OAuth state. Start authorization again." }, 400);
      await env.TIKTOK_KV.delete("oauth_state:" + state);
      const code = url.searchParams.get("code");
      if (!code) return json({ error: "TikTok authorization was cancelled or did not return a code." }, 400);
      try {
        const tokens = await exchangeToken(env, {
          client_key: env.TIKTOK_CLIENT_KEY,
          client_secret: env.TIKTOK_CLIENT_SECRET,
          code,
          grant_type: "authorization_code",
          redirect_uri: env.TIKTOK_REDIRECT_URI || (url.origin + "/auth/tiktok/callback")
        });
        const stored = {
          access_token: tokens.access_token,
          refresh_token: tokens.refresh_token,
          open_id: tokens.open_id,
          scope: tokens.scope,
          expires_at: Date.now() + Number(tokens.expires_in || 86400) * 1000,
          refresh_expires_at: Date.now() + Number(tokens.refresh_expires_in || 0) * 1000
        };
        await env.TIKTOK_KV.put("oauth_tokens", JSON.stringify(stored));
        return new Response("<!doctype html><meta name='viewport' content='width=device-width'><title>Connected</title><main style='font:16px system-ui;max-width:560px;margin:12vh auto;padding:24px'><h1>TikTok connected</h1><p>CN Fun Cartoons has authorized the TikTok connection. You can close this page.</p></main>", {
          headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" }
        });
      } catch (e) {
        return json({ error: String(e.message || e) }, 502);
      }
    }

    if (request.method === "GET" && url.pathname === "/internal/access-token") {
      const auth = request.headers.get("authorization") || "";
      if (!safeEqual(auth, "Bearer " + env.AUTOMATION_SECRET)) return json({ error: "Unauthorized" }, 401);
      try {
        const access_token = await getFreshToken(env);
        return json({ access_token });
      } catch (e) {
        return json({ error: String(e.message || e) }, 409);
      }
    }

    if (request.method === "GET" && url.pathname === "/internal/status") {
      const auth = request.headers.get("authorization") || "";
      if (!safeEqual(auth, "Bearer " + env.AUTOMATION_SECRET)) return json({ error: "Unauthorized" }, 401);
      const stored = await env.TIKTOK_KV.get("oauth_tokens", "json");
      return json({ connected: Boolean(stored?.refresh_token), open_id: stored?.open_id || null, scope: stored?.scope || null });
    }

    return json({ error: "Not found" }, 404);
  }
};