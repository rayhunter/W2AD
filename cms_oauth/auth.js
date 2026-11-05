// Cloudflare Pages Function: GET /auth
// Copied into each generated site's functions/ folder by scaffold_agent.py.
//
// Decap opens a popup here; we redirect to GitHub's login. GitHub sends the
// user back to /callback (see callback.js) on this same site.
//
// Pages environment variables: GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET (secret),
// optional GITHUB_SCOPE (default "repo")

export async function onRequestGet({ request, env }) {
  const url = new URL(request.url);
  const state = crypto.randomUUID();

  const authorize = new URL("https://github.com/login/oauth/authorize");
  authorize.searchParams.set("client_id", env.GITHUB_CLIENT_ID);
  authorize.searchParams.set("redirect_uri", `${url.origin}/callback`);
  authorize.searchParams.set("scope", env.GITHUB_SCOPE || "repo");
  authorize.searchParams.set("state", state);

  return new Response(null, {
    status: 302,
    headers: {
      Location: authorize.toString(),
      "Set-Cookie": `decap_oauth_state=${state}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=600`,
    },
  });
}
