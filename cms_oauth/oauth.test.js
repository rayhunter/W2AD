// Run with: cd cms_oauth && node --test   (Node 18+; no dependencies)
import { test, afterEach } from "node:test";
import assert from "node:assert/strict";
import { onRequestGet as auth } from "./auth.js";
import { onRequestGet as callback } from "./callback.js";

const env = { GITHUB_CLIENT_ID: "test-client-id", GITHUB_CLIENT_SECRET: "test-client-secret" };
const SITE = "https://my-site.pages.dev";
const realFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = realFetch;
});

function callCallback(query, cookieState) {
  const headers = cookieState ? { Cookie: `decap_oauth_state=${cookieState}` } : {};
  return callback({ request: new Request(`${SITE}/callback?${query}`, { headers }), env });
}

function mockGitHubToken(body) {
  globalThis.fetch = async (url, init) => {
    assert.equal(url, "https://github.com/login/oauth/access_token");
    assert.equal(JSON.parse(init.body).client_secret, "test-client-secret");
    assert.equal(JSON.parse(init.body).redirect_uri, `${SITE}/callback`);
    return Response.json(body);
  };
}

test("/auth redirects to GitHub with client id, scope, this site's callback and state", async () => {
  const res = await auth({ request: new Request(`${SITE}/auth?provider=github`), env });
  assert.equal(res.status, 302);

  const location = new URL(res.headers.get("Location"));
  assert.equal(location.origin + location.pathname, "https://github.com/login/oauth/authorize");
  assert.equal(location.searchParams.get("client_id"), "test-client-id");
  assert.equal(location.searchParams.get("scope"), "repo");
  assert.equal(location.searchParams.get("redirect_uri"), `${SITE}/callback`);
  assert.ok(!res.headers.get("Location").includes("test-client-secret"));

  const state = location.searchParams.get("state");
  assert.ok(state);
  assert.match(res.headers.get("Set-Cookie"), new RegExp(`decap_oauth_state=${state};.*HttpOnly`));
});

test("GITHUB_SCOPE overrides the default scope", async () => {
  const res = await auth({ request: new Request(`${SITE}/auth`), env: { ...env, GITHUB_SCOPE: "public_repo" } });
  assert.equal(new URL(res.headers.get("Location")).searchParams.get("scope"), "public_repo");
});

test("/callback rejects a missing or mismatched state", async () => {
  assert.equal((await callCallback("code=abc&state=s1")).status, 400);
  assert.equal((await callCallback("code=abc&state=s1", "other")).status, 400);
});

test("/callback returns the Decap success message, sent only to this site's origin", async () => {
  mockGitHubToken({ access_token: "gho_test_token" });
  const res = await callCallback("code=abc&state=s1", "s1");
  const html = await res.text();

  assert.equal(res.status, 200);
  assert.ok(html.includes("authorizing:github"));
  assert.ok(html.includes("authorization:github:success:"));
  assert.ok(html.includes("gho_test_token"));
  assert.ok(html.includes("e.origin !== window.location.origin"));
  assert.ok(!html.includes('"*"'));
  assert.ok(!html.includes("test-client-secret"));
});

test("/callback returns an error message when GitHub rejects the code", async () => {
  mockGitHubToken({ error: "bad_verification_code", error_description: "The code is incorrect" });
  const html = await (await callCallback("code=bad&state=s1", "s1")).text();
  assert.ok(html.includes("authorization:github:error:"));
  assert.ok(html.includes("The code is incorrect"));
});

test("/callback returns an error message when the user cancels on GitHub", async () => {
  globalThis.fetch = () => assert.fail("should not exchange a token");
  const html = await (await callCallback("error=access_denied&state=s1", "s1")).text();
  assert.ok(html.includes("authorization:github:error:"));
});

test("injected HTML in the token response cannot break out of the script tag", async () => {
  mockGitHubToken({ error: "x", error_description: "</script><script>alert(1)</script>" });
  const html = await (await callCallback("code=abc&state=s1", "s1")).text();
  assert.ok(!html.includes("</script><script>alert(1)"));
});
