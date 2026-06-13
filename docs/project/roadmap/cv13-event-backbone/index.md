[< Roadmap](../index.md)

# CV13 — Event Backbone

**Status:** 🔵 Future
**Goal:** Move SmartInv from batch ingestion to event-driven intelligence — ERP/EAM events trigger agent reactions, alerts surface in near real-time, and the Alert Center becomes a first-class product surface.

---

## What This Is

CV13 is the architectural shift from *batch* to *event-driven*. It is **explicitly deferred** from the MVP per [AGENTS.md MVP scope](../../../../AGENTS.md#mvp-scope--build-this-defer-that): "Streaming / event-driven / Kafka" is on the deferred list — *batch is enough* at MVP.

The promise once activated:

> *"When a corrective work order opens, when a PO ships late, when stock breaches a threshold, when a price changes — SmartInv knows within seconds and the right agent reacts. Alerts arrive prioritized by business impact, not chronological order."*

---

## Epics

| Code | Epic | User-visible outcome | Status |
|------|------|----------------------|--------|
| [CV13.E1](cv13-e1-event-broker/index.md) | Event Broker (Kafka or NATS) | Schema-registered topics for source events, internal events, agent triggers, and audit | 🔵 Future |
| [CV13.E2](cv13-e2-cdc-source-systems/index.md) | CDC from Source Systems | Debezium for SAP/Oracle databases; Maximo MIF webhooks for events | 🔵 Future |
| [CV13.E3](cv13-e3-event-driven-agent-triggers/index.md) | Event-Driven Agent Triggers | Specific events activate specific agents under defined rules | 🔵 Future |
| [CV13.E4](cv13-e4-alert-center-ui/index.md) | Alert Center UI | Prioritized alert center page with severity, business impact, source event lineage | 🔵 Future |

---

## Done Condition

When CV13 activates:

- Source-system events land on the broker within seconds of the source change.
- At least 5 event types trigger specific agent reactions with eval coverage.
- The Alert Center page renders prioritized alerts; users can drill from alert to source event to recommendation.
- Audit topic captures every event the system reacted to, with retention long enough for compliance.

---

## Out of Scope

- Marketplace / partner connector ecosystem — Radar.
- Backfill / historical replay tooling beyond what Kafka offers natively — Future.
- Geo-distributed multi-region event bus — Future.

---

**See also:** [Roadmap](../index.md) · [CV11 Multi-Agent Orchestration](../cv11-multi-agent-orchestration/index.md) · [CV2 Inventory Health](../cv2-inventory-health/index.md)
