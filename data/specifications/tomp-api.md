---
short_name: TOMP API
full_name: Transport Operator Mobility-as-a-service (TOMP)
homepage_url: https://github.com/TOMP-WG/TOMP-API
status: partially_compliant
modes: [microtransit_drt, taxi_ridehail]
maintainers: [tomp-wg]
licences:
- id: Apache-2.0
first_release_year: 2019
adoption:
  lifecycle: early_adoption
  tier: hundred_plus
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://github.com/TOMP-WG/TOMP-API?tab=Apache-2.0-1-ov-file
  publicly_documented:
    verdict: compliant
    rationale: Human-readable docs and the OpenAPI (machine-readable) specification are both published in full on GitHub (TOMP-WG/TOMP-API).
    evidence_url: https://app.swaggerhub.com/apis-docs/TOMP-API-WG/transport-operator_maas_provider_api/
  independent_maintainer:
    verdict: compliant
    rationale: The TOMP-API is maintained by the open community of the TOMP-WG, which is supported by the House of TOMP, a Belgian AISBL (non-for-profit) with the sole purpose to support and disseminate.
    evidence_url: https://www.linkedin.com/company/tomp-wg
  structured_releases:
    verdict: compliant
    rationale: Versioned GitHub releases.
    evidence_url: https://github.com/TOMP-WG/TOMP-API/wiki/Versioning-and-releases
  open_governance:
    verdict: compliant
    rationale: Open to public GitHub contributions, and formal working-group decision-making is limited to the participants of the monthly general meetings.
    evidence_url: https://github.com/TOMP-WG/TOMP-API/blob/master/CONTRIBUTING.md
---

# Description

The TOMP-API is an interoperable open standard for technical communication between transport operators and mobility as a service providers. Compatible and usable in combination with GBFS, CDS, GTFS, OCPI (charging), APDS (parking), and NeTEx.
