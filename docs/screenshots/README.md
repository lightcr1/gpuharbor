# Screenshots

Images used by the README and the docs live here.

| File | What it shows |
|---|---|
| `dashboard.png` | dashboard in English, cost lock active |
| `dashboard.de.png` | dashboard in German |
| `model-editor.de.png` | model editor with the Hugging Face lookup |
| `social-preview.png` | 1280x640 banner for the GitHub repository settings |

## Replacing one

Take a fresh screenshot with a window of about 1280x820 and a device scale factor
of 2, so the text stays sharp.

The committed images were captured with Playwright against a local instance:

```bash
npm install playwright
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME });
  const page = await browser.newPage({ viewport: { width: 1280, height: 820 }, deviceScaleFactor: 2 });
  await page.goto('http://127.0.0.1:8080/');
  await page.fill('#username', 'admin');
  await page.fill('#password', process.env.GPUHARBOR_ADMIN_PASSWORD);
  await page.click('#login-form button');
  await page.waitForSelector('#app:not(.hidden)');
  await page.selectOption('#lang-switch', 'en');
  await page.screenshot({ path: 'docs/screenshots/dashboard.png' });
  await browser.close();
})();
"
```

Keep screenshots free of API keys, tokens, IP addresses and account details, and
leave the cost lock in its default state so the badge shows "Cost lock active".

## Social preview

GitHub has no API for the repository social preview image, so it has to be set by
hand: **Settings → General → Social preview → Edit → Upload an image** and pick
`docs/screenshots/social-preview.png` (1280x640).
