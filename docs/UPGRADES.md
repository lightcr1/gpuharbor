# Upgrades

GPUHarbor keeps shipped data and your data separate, so updating the controller
image does not wipe your setup.

## How to upgrade a running install

Your profiles live in the Docker volume, not in the code, and `.env` is never
overwritten. A normal update is two commands:

```bash
git pull
./scripts/install        # keeps .env, rebuilds and restarts
```

If you run a released image instead of building from source:

```bash
docker compose pull
docker compose up -d
```

Afterwards open the dashboard again. New shipped profiles appear by themselves;
your own profiles and overrides stay untouched (rules below).

To go back to an older version, check out the previous tag or git commit and run
`./scripts/install` again. Your data is not affected either way.

## Update check (opt-in)

The dashboard never talks to the internet on its own. Open **Settings** in the
header and turn on **Show update notifications**. Then the controller asks the
public GitHub releases API at most once a day and shows an "update available"
link. Only that request leaves the machine; no token and no configuration is
sent. The choice is stored in the data volume.

For a scripted install you can seed the default with `GPUHARBOR_UPDATE_CHECK=true`
in `.env`. The toggle in the web interface wins afterwards.

## Merge rules

- New shipped profiles appear automatically.
- Your own profiles are never touched.
- Editing a shipped profile creates an override. Later image updates do not
  overwrite it.
- "Reset" on an override returns to whatever the image currently ships.
- If an update removes a shipped profile you had edited, the override stays as
  `orphaned-override`. Nothing is deleted silently.
- Custom IDs may not collide with shipped IDs.
- Writes go to a temp file and are renamed into place. The previous version stays
  as `user-models.json.bak`.
- The file has a `schema_version`. A newer, unknown version is refused instead of
  being downgraded.

## Coming from an older layout

If `/data/models.json` exists and there is no versioned file yet, the first start
splits it into custom profiles and overrides, writes `/data/user-models.json`,
and renames the old file to `/data/models.json.migrated`. The original is kept.

## Running pods

The controller stores a fingerprint of the operational profile when it creates a
pod. If the profile changes afterwards, starting that pod again is refused with a
clear message. Review the new plan and delete/recreate the pod. Cosmetic fields
like description, license or verification do not change the fingerprint.

## Back up before upgrading

Use **Export** in the dashboard for your profiles, and back up the controller
volume. Never put credentials into an exported profile file.
