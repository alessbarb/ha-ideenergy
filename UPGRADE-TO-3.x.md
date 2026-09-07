# Upgrading from i-DE Energy Monitor 2.x to 3.x

The 3.x series changes how historical energy data is represented. It uses Home Assistant statistics instead of writing directly to recorder internals. Treat the upgrade as a migration, not as an in-place database rewrite.

## Before upgrading

1. Create a **full Home Assistant backup** and make sure it completes successfully.
2. Record which i-DE entities or statistics are currently selected in the Energy Dashboard.
3. If automations depend on the old instant-consumption entity, disable or update them before migrating. The current 3.x series does not expose a separate Instant Consumption entity.
4. Do **not** delete recorder statistics merely to prepare the upgrade. Keeping the old statistics is safer than trying to reconstruct them later.

## Supported migration path

### 1. Install the 3.x release

Upgrade the custom integration through HACS, or replace `custom_components/ideenergy` with the files from the desired 3.x release, then restart Home Assistant.

### 2. Recreate the config entry only if necessary

If the existing 2.x config entry cannot be loaded by 3.x:

1. Remove the **i-DE integration config entry** from **Settings → Devices & services**.
2. Restart Home Assistant.
3. Add **i-DE Energy Monitor** again through the UI.
4. Select the same contract/service point.

Removing the config entry is not the same as deleting recorder statistics. Do not manually edit `.storage/core.entity_registry`, `.storage/core.device_registry`, or other Home Assistant storage files as part of the normal migration.

### 3. Let 3.x create its current entities and statistics

The current 3.x series exposes:

- accumulated consumption from direct meter readings;
- historical consumption statistics;
- historical generation statistics, disabled by default.

It does not currently expose a separate instant-consumption entity.

### 4. Allow the normal historical window to populate

The coordinator requests a bounded recent history window automatically. Do not edit `HISTORICAL_PERIOD_LENGHT` in the integration source to force a larger backfill.

If older historical data is missing after migration, keep the existing 2.x statistics as an archive rather than increasing API traffic aggressively. i-DE can reject or temporarily block excessive requests.

### 5. Reconfigure the Energy Dashboard

After the new 3.x statistics are available:

1. Open **Settings → Dashboards → Energy**.
2. Select the new 3.x consumption statistic where appropriate.
3. Verify the first complete day before relying on totals or comparisons.
4. Keep the previous 2.x statistic until you are satisfied that the new series is correct.

## Historical continuity

There is currently no supported automatic migration that merges an arbitrary 2.x recorder statistic into the 3.x statistic identifier.

For most users, the safest choice is:

- keep the old 2.x statistic for historical reference;
- start the 3.x statistic from the migration date;
- avoid direct database manipulation.

If uninterrupted historical continuity is mandatory, treat it as a separate advanced database-maintenance operation. Work only from a verified backup, stop Home Assistant before modifying the database, and use procedures appropriate for the actual recorder backend. Direct SQL against `statistics_meta` is **not** part of the supported integration upgrade path.

## Do not do these during a normal upgrade

- Do not manually remove JSON blocks from Home Assistant `.storage` files.
- Do not run ad-hoc `UPDATE statistics_meta ...` statements against the live recorder database.
- Do not modify coordinator source constants to request a large historical gap.
- Do not repeatedly reload the integration to force i-DE requests.

These actions can corrupt Home Assistant state or increase the chance of i-DE temporarily blocking the account.

## After the upgrade

Confirm that:

- the integration loads without setup errors;
- the configured CUPS/service point is the expected one;
- accumulated consumption updates when a direct reading is successfully available;
- historical consumption appears in Home Assistant statistics;
- the Energy Dashboard uses the intended 3.x statistic;
- automations do not reference the removed 2.x instant-consumption entity.

The 3.x line remains alpha software. Keep a recent Home Assistant backup while evaluating upgrades between prereleases.
