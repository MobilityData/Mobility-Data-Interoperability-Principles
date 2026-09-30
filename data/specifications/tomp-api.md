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
    verdict: partially_compliant
    rationale: TOMP-WG operates under the Maas Alliance ecosystem - governance is industry-participant led rather than a fully independent standards body.
    evidence_url: https://mobility-alliance.org/about-us
  structured_releases:
    verdict: compliant
    rationale: Versioned GitHub releases.
    evidence_url: https://github.com/TOMP-WG/TOMP-API/wiki/Versioning-and-releases
  open_governance:
    verdict: compliant
    rationale: Open to public GitHub contributions, but formal working-group decision-making is limited to participating members/companies.
    evidence_url: https://github.com/TOMP-WG/TOMP-API/blob/master/CONTRIBUTING.md
---

# Description

The TOMP-API is an interoperable open standard for technical communication between transport operators and mobility as a service providers. Compatible with GBFS, NeTEx.
