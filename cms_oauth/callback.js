// Cloudflare Pages Function: GET /callback
// Copied into each generated site's functions/ folder by scaffold_agent.py.
//
// GitHub redirects here after login. We swap the code for a token and hand it
// to the /admin/ window via Decap's postMessage handshake. The popup and the
// CMS are on the same site, so the token is only ever sent to this origin.

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const state = url.searchParams.get("state");
  if (!state || state !== readCookie(request, "decap_oauth_state")) {
    return new Response("Invalid OAuth state", { status: 400 });
  }

  // The user clicked "Cancel" on GitHub's consent screen
  if (url.searchParams.get("error")) {
    return renderResult("error", { message: url.searchParams.get("error_description") || "Login cancelled" });
  }

  const tokenResponse = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code: url.searchParams.get("code"),
      redirect_uri: `${url.origin}/callback`,
    }),
  });
  const data = await tokenResponse.json();

  if (!data.access_token) {
    return renderResult("error", { message: data.error_description || "Token exchange failed" });
  }
  return renderResult("success", { token: data.access_token, provider: "github" });
}

// Decap's popup handshake: announce "authorizing:github", wait for the CMS
// window to answer, then send the result back only if it is on this origin.
function renderResult(status, content) {
  const message = `authorization:github:${status}:${JSON.stringify(content)}`;
  const html = `<!doctype html>
<html><body><script>
(function () {
  var message = ${safeJson(message)};
  function receive(e) {
    if (e.origin !== window.location.origin) return;
    window.removeEventListener("message", receive);
    window.opener.postMessage(message, e.origin);
  }
  window.addEventListener("message", receive);
  window.opener.postMessage("authorizing:github", window.location.origin);
})();
</script></body></html>`;

  return new Response(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Set-Cookie": "decap_oauth_state=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0",
    },
  });
}

function readCookie(request, name) {
  const cookies = request.headers.get("Cookie") || "";
  for (const part of cookies.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return rest.join("=");
  }
  return null;
}

// JSON that is safe to inline inside a <script> tag
function safeJson(value) {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
