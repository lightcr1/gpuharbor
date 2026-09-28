# Upgrades

GPUHarbor keeps shipped data and your data separate, so updating the controller
image does not wipe your setup.

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
