[< Roadmap](../index.md)

# CV12 — Mobile & Field

**Status:** 🔵 Future
**Goal:** Planners, maintenance managers, and warehouse supervisors use SmartInv from a phone or tablet — for approvals, alerts, item lookup with barcode, and offline-friendly inventory views in the field.

---

## What This Is

CV12 extends SmartInv to a second client surface. It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that): the MVP is web-only, but the *contracts pattern* ([ADR-002](../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b)) keeps the door open.

The promise once activated:

> *"From a phone, a planner can review the daily exception queue, approve a transfer, scan a part with the camera, and look up critical-spare coverage even when the warehouse Wi-Fi is unreliable."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| CV12.E1 | Cross-Platform Design System | Move the design tokens from CSS variables to a shared package consumed by Tamagui (web + native) | 🔵 Future |
| CV12.E2 | React Native App (Expo) | Expo app that reuses `@smartinv/ui-contracts` and the new shared `ui-native` package | 🔵 Future |
| CV12.E3 | Offline & Sync | WatermelonDB (or equivalent) offline cache for inventory lookups + sync on reconnect | 🔵 Future |
| CV12.E4 | Push Notifications & Field Tools | Expo Notifications, barcode/QR via Expo Camera, biometric unlock | 🔵 Future |

---

## Done Condition

When CV12 activates:

- The shared design system renders identically on web and mobile for KpiCard, EvidenceStrip, ApprovalStep, and Badge.
- An Expo build targets iOS and Android with the four MVP screens that benefit from mobile (Overview, Approvals, Alerts, Inventory Health item detail).
- Inventory item lookup works offline for at least 24 hours of cached data.
- Push notifications fire for high-priority alerts and approval requests.

---

## Out of Scope

- Native desktop apps (macOS / Windows) — Future / Radar.
- Voice assistants — Future.
- AR / overlay features for warehouse navigation — Future.

---

**See also:** [Roadmap](../index.md) · [ADR-002 Option B](../../decisions.md#adr-002--web-only-mvp-but-shared-system-ready-option-b) · [CV1 Foundations](../cv1-foundations/index.md)
