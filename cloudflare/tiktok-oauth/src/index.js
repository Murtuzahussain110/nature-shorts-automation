/**
 * TikTok OAuth + Direct Post backend for CN Fun Cartoons.
 * Secrets: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, AUTOMATION_SECRET
 * KV binding: TIKTOK_KV
 */
const API = "https://open.tiktokapis.com/v2";
const SITE_ORIGIN = "https://murtuzahussain110.github.io";
const MAX_VIDEO_BYTES = 64 * 1024 * 1024;
const MIN_CHUNK_BYTES = 5 * 1024 * 1024;
const CHUNK_BYTES = 10 * 1024 * 1024;

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": SITE_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin"
  };
}
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
  if (Date.now() < Number(stored.expires_at || 0) - 5 * 60 * 1000) return stored.access_token;
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
async function tiktokJson(path, token, init = {}) {
  const response = await fetch(API + path, {
    ...init,
    headers: { Authorization: "Bearer " + token, ...(init.headers || {}) }
  });
  const body = await response.json();
  if (!response.ok || body.error?.code && body.error.code !== "ok") {
    throw new Error(body.error?.message || body.error?.code || "TikTok API error " + response.status);
  }
  return body;
}
function errorMessage(e) {
  return String(e?.message || e || "Unknown error").slice(0, 700);
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS" && ["/public/status", "/public/creator-info", "/public/publish", "/public/publish-status"].includes(url.pathname)) {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }
    if (request.method === "GET" && url.pathname === "/health") return json({ ok: true, service: "cn-fun-cartoons-tiktok-oauth" });

    if (request.method === "GET" && url.pathname === "/public/status") {
      const stored = await env.TIKTOK_KV.get("oauth_tokens", "json");
      return json({ connected: Boolean(stored?.refresh_token) }, 200, corsHeaders());
    }

    if (request.method === "GET" && url.pathname === "/public/creator-info") {
      try {
        const token = await getFreshToken(env);
        const body = await tiktokJson("/post/publish/creator_info/query/", token, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
        const creator = body.data || {};
        return json({
          privacy_level_options: creator.privacy_level_options || [],
          max_video_post_duration_sec: creator.max_video_post_duration_sec || null,
          creator_username: creator.creator_username || null
        }, 200, corsHeaders());
      } catch (e) {
        return json({ error: errorMessage(e) }, 400, corsHeaders());
      }
    }

    if (request.method === "POST" && url.pathname === "/public/publish") {
      try {
        const form = await request.formData();
        const video = form.get("video");
        const title = String(form.get("title") || "").trim().slice(0, 150);
        const privacy = String(form.get("privacy_level") || "");
        if (!(video instanceof File)) return json({ error: "Please choose an MP4 video." }, 400, corsHeaders());
        if (video.type !== "video/mp4" && !video.name.toLowerCase().endsWith(".mp4")) return json({ error: "Please upload an MP4 video." }, 400, corsHeaders());
        if (video.size < 1 || video.size > MAX_VIDEO_BYTES) return json({ error: "Video must be smaller than 64 MB for this test upload." }, 400, corsHeaders());
        if (!title) return json({ error: "Please enter a video caption." }, 400, corsHeaders());
        if (!privacy) return json({ error: "Please choose a privacy option." }, 400, corsHeaders());

        const token = await getFreshToken(env);
        const creatorBody = await tiktokJson("/post/publish/creator_info/query/", token, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
        const creator = creatorBody.data || {};
        const privacyOptions = creator.privacy_level_options || [];
        if (!privacyOptions.includes(privacy)) {
          return json({ error: "That privacy option is not available for this TikTok account. Refresh the privacy options and try again." }, 400, corsHeaders());
        }

        // TikTok requires a 5 MB minimum declared chunk size. The final
        // transmitted chunk may be smaller when the entire video is shorter.
        const chunkSize = Math.max(MIN_CHUNK_BYTES, Math.min(CHUNK_BYTES, video.size));
        const chunkCount = Math.ceil(video.size / chunkSize);
        if (chunkCount < 1 || chunkCount > 1000) {
          return json({ error: "This video cannot be split into a valid TikTok upload." }, 400, corsHeaders());
        }
        const initBody = await tiktokJson("/post/publish/video/init/", token, {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=UTF-8" },
          body: JSON.stringify({
            post_info: {
              title,
              privacy_level: privacy,
              disable_duet: false,
              disable_comment: false,
              disable_stitch: false
            },
            source_info: {
              source: "FILE_UPLOAD",
              video_size: video.size,
              chunk_size: chunkSize,
              total_chunk_count: chunkCount
            }
          })
        });
        const uploadUrl = initBody.data?.upload_url;
        const publishId = initBody.data?.publish_id;
        if (!uploadUrl || !publishId) throw new Error("TikTok did not return an upload URL and publish ID.");
        const bytes = await video.arrayBuffer();
        for (let i = 0; i < chunkCount; i++) {
          const start = i * chunkSize;
          const endExclusive = Math.min(start + chunkSize, video.size);
          const chunk = bytes.slice(start, endExclusive);
          const upload = await fetch(uploadUrl, {
            method: "PUT",
            headers: {
              "Content-Type": "video/mp4",
              "Content-Length": String(endExclusive - start),
              "Content-Range": "bytes " + start + "-" + (endExclusive - 1) + "/" + video.size
            },
            body: chunk
          });
          if (!upload.ok) throw new Error("TikTok video upload failed on chunk " + (i + 1) + " (" + upload.status + ").");
        }
        return json({ ok: true, publish_id: publishId, message: "Video uploaded to TikTok for processing. Check the publishing status shortly." }, 200, corsHeaders());
      } catch (e) {
        return json({ error: errorMessage(e) }, 400, corsHeaders());
      }
    }

    if (request.method === "GET" && url.pathname === "/public/publish-status") {
      const publishId = url.searchParams.get("publish_id") || "";
      if (!/^[A-Za-z0-9_-]{5,200}$/.test(publishId)) return json({ error: "Invalid publish ID." }, 400, corsHeaders());
      try {
        const token = await getFreshToken(env);
        const body = await tiktokJson("/post/publish/status/fetch/", token, {
          method: "POST",
          headers: { "Content-Type": "application/json; charset=UTF-8" },
          body: JSON.stringify({ publish_id: publishId })
        });
        const data = body.data || {};
        return json({
          status: data.status || "PROCESSING",
          fail_reason: data.fail_reason || null,
          publicaly_available_post_id: data.publicaly_available_post_id || []
        }, 200, corsHeaders());
      } catch (e) {
        return json({ error: errorMessage(e) }, 400, corsHeaders());
      }
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
        return json({ error: errorMessage(e) }, 502);
      }
    }

    if (request.method === "GET" && url.pathname === "/internal/access-token") {
      const auth = request.headers.get("authorization") || "";
      if (!safeEqual(auth, "Bearer " + env.AUTOMATION_SECRET)) return json({ error: "Unauthorized" }, 401);
      try {
        const access_token = await getFreshToken(env);
        return json({ access_token });
      } catch (e) {
        return json({ error: errorMessage(e) }, 409);
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