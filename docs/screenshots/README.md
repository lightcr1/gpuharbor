# Screenshots

Images used by the README live here.

To add one from a Windows machine:

```powershell
scp "C:\path\to\Screenshot.png" media@10.10.40.100:/home/media/gpuharbor/docs/screenshots/dashboard.png
```

Then reference it in the READMEs, as an image line with the path
`docs/screenshots/dashboard.png`. Keep that path in a code block when writing
documentation so the link checker does not treat the example as a real file.

Keep screenshots free of API keys, tokens, IP addresses and account details. Crop
the browser chrome and hide anything private before committing.
