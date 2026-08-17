# Architecture v2.1

## Perception order

1. UIAutomator resource-id/accessibility/text/hierarchy
2. WebView DOM/role/aria-label/text/bounds with stale-DOM protection
3. Computer vision template matching in a bounded ROI
4. OCR (`eng`, `vie`) on a cropped ROI
5. Safe failure with screenshot, UI XML and evidence artifacts

Resolvers return candidates with method, bounds, confidence and evidence. Candidate fusion may increase confidence only when independent sources agree.

## Device core

ADB is the transport boundary. Each serial has an isolated context and lock. Commands have timeouts, captured stdout/stderr and structured errors. No global device state.
