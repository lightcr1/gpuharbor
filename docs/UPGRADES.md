# Safe upgrades and model-catalog ownership

GPUHarbor deliberately separates shipped data from owner data.

## Files

| Path | Owner | Upgrade behavior |
|---|---|---|
| `/app/registry/models.json` | GPUHarbor image | replaced when the controller image updates |
| `/data/user-models.json` | installation owner | persistent; never replaced by the image |
| `/data/user-models.json.bak` | GPUHarbor | previous user-catalog generation |
| `/data/models.json.migrated` | legacy migration | preserved copy of the old mutable catalog |
| `/data/state.json` | controller | persistent managed-pod state |

The user catalog has an explicit `schema_version`. GPUHarbor refuses to write a
newer unknown schema instead of attempting a destructive downgrade.

## Merge rules

- New unmodified built-ins appear automatically after an image update.
- Custom models remain unchanged.
- Editing a built-in creates a full user override; later built-in changes do not
  overwrite it.
- Resetting an override returns to the currently shipped built-in.
- If an updated image removes a built-in that has an override, the override is
  retained as `orphaned-override` rather than deleted.
- Custom IDs may not collide with built-in IDs.
- Writes use a temporary file plus atomic rename and retain the previous catalog
  as `.bak`.

## Legacy migration

If `/data/models.json` exists and no versioned user catalog exists, first startup
splits it into custom models and built-in overrides, writes
`/data/user-models.json`, and renames the original to
`/data/models.json.migrated`. Migration never deletes the source file.

## Running pods and changed profiles

The controller records an operational profile fingerprint when creating a pod.
If an update or catalog edit changes model/runtime settings, GPUHarbor refuses to
silently restart that existing pod. Review the new start plan, then explicitly
delete/recreate the pod. Cosmetic metadata such as description, license and
verification status does not change the operational fingerprint.

## Backup and transfer

Use **Export own profiles** in the dashboard before upgrades. Import merges by
default; it does not remove unmentioned custom entries. A replace mode exists in
the API but is intentionally not exposed as the normal UI action.

Back up the controller's named Docker volume before major upgrades. Never copy
`.env` credentials into model-export files.
