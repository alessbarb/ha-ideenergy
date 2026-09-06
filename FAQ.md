# FAQ

## Why does a feature not work?

The 3.x line is alpha software and is also a rewrite of the 2.x integration. If a feature is not listed as supported in the README, do not assume that an older 2.x feature has already been ported.

In particular, 3.x currently exposes an **Accumulated Consumption** direct-reading sensor but does not expose a separate **Instant Consumption** entity.

## Why is the Accumulated Consumption sensor unknown or not changing?

The accumulated sensor reads the physical service point through i-DE. That endpoint is significantly less reliable than the historical endpoints and individual requests can fail or take a long time.

The integration deliberately avoids frequent retries. After a successful direct reading it waits six hours before another direct read is due. After a failed direct-reading attempt, the retry throttle is five minutes.

A missing update therefore does not necessarily mean that Home Assistant or the integration is broken. Check the integration logs for the underlying connection/authentication error and avoid repeatedly reloading the integration to force calls to i-DE.

## Can I make direct meter readings update more frequently?

This is intentionally conservative. i-DE can temporarily block users that query service-point endpoints too often, and direct reads are already unreliable.

The current 3.x implementation uses a six-hour success interval for direct readings. Historical datasets use a twelve-hour success interval. Failed dataset attempts are throttled for five minutes.

The old 2.x documentation describing a minute-50-to-59 hourly window and several retries per window does not apply to the current 3.x coordinator.

## Why can accumulated consumption appear unchanged?

The direct meter reading reports accumulated energy with limited precision. If the meter has not advanced enough to change the returned accumulated value, Home Assistant will continue to show the previous value until a later successful reading reflects the increase.

## Why do Historical Consumption or Historical Generation not show a normal current state?

These entities exist to feed past measurements into Home Assistant statistics rather than to represent a live meter value. Use the History/Energy views to inspect their data.

Historical information is not real-time; i-DE commonly publishes it with roughly a 24-to-48-hour delay.

The 3.x implementation uses `homeassistant-historical-sensor` and Home Assistant statistics. It no longer follows the old 2.x design that directly manipulated recorder database rows.

## What should I do if I have multiple contracts?

Each configured contract is a separate Home Assistant config entry. Historical data is the safest choice when several service points are configured because it does not require frequent direct meter access.

Be conservative about enabling direct accumulated readings for many contracts at the same time. Every enabled direct-reading entity can generate service-point requests when its own refresh window is due, and i-DE may temporarily block an account that generates excessive traffic.

## Does restarting Home Assistant reset the request throttle?

No. The coordinator stores the success/attempt timestamps used by its dataset throttles, so a Home Assistant restart does not intentionally reset the normal request interval.

## Is this an official i-DE integration?

No. It uses endpoints exposed by the i-DE customer service rather than a stable public API contract. i-DE can change authentication, payloads or availability without notice, so temporary breakage is always possible.
