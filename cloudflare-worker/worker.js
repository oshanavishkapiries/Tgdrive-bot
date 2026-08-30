// Tgdrive-bot OAuth redirect catcher.
//
// This Worker is the Google OAuth "redirect_uri" for the bot. Google sends the
// user's browser here after they approve access, with an authorization `code`
// in the query string. This page just displays that code so the user can copy
// it and paste it back into the Telegram bot chat, where the bot exchanges it
// for real credentials using GDRIVE_CLIENT_SECRET (which never touches this
// Worker or the browser).
//
// Deploy: paste this whole file into a new Worker in the Cloudflare dashboard
// (Workers & Pages -> Create -> Create Worker -> edit code), then hit Deploy.
// The Worker's URL (https://<name>.<subdomain>.workers.dev) is what goes into
// this project's .env as GDRIVE_REDIRECT_URI, and into Google Cloud Console's
// OAuth client "Authorized redirect URIs" (exact match, including no
// trailing slash unless you keep one consistently in both places).

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const code = url.searchParams.get("code");
    const error = url.searchParams.get("error");

    let bodyHtml;
    if (error) {
      bodyHtml = `
        <h1>Authorization failed</h1>
        <p>Google reported: <code>${escapeHtml(error)}</code></p>
        <p>Go back to the Telegram bot and send /auth to try again.</p>
      `;
    } else if (code) {
      bodyHtml = `
        <h1>Authorization successful</h1>
        <p>Copy the code below and paste it back into the Telegram bot chat:</p>
        <textarea readonly rows="4" style="width:100%;font-size:1rem;padding:0.5rem;">${escapeHtml(code)}</textarea>
        <p>You can close this tab afterwards.</p>
      `;
    } else {
      bodyHtml = `<h1>Nothing to show</h1><p>This page only works when Google redirects here after you approve access.</p>`;
    }

    return new Response(
      `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Tgdrive-bot Authorization</title>
      <style>body{font-family:system-ui,sans-serif;max-width:640px;margin:3rem auto;padding:0 1rem;line-height:1.5;}</style>
      </head><body>${bodyHtml}</body></html>`,
      { headers: { "content-type": "text/html; charset=UTF-8" } }
    );
  },
};

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
