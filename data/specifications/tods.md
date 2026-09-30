---
short_name: TODS
full_name: Transit Operational Data Standard
homepage_url: http://tods-transit.org/
status: compliant
modes: [public_transport]
maintainers: [tods-board, mobilitydata]
licences:
- id: Apache-2.0
  scopes: [specification]
- id: CC-BY-4.0
  scopes: [documentation]
first_release_year: 2022
adoption:
  lifecycle: early_adoption
  tier: early
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://github.com/MobilityData/transit-operational-data-standard/blob/main/LICENSE-APACHE-2.0
  publicly_documented:
    verdict: compliant
    rationale: CC-BY-4.0
    evidence_url: https://github.com/MobilityData/transit-operational-data-standard/blob/main/LICENSE-CC-BY-4.0
  independent_maintainer:
    verdict: compliant
    rationale: Board does include a minority of seats for industry.
    evidence_url: https://tods-transit.org/governance/governance/
  structured_releases:
    verdict: compliant
    rationale: Versioning, Revision History
    evidence_url: https://tods-transit.org/spec/revision-history/
  open_governance:
    verdict: compliant
    rationale: Anyone can become a contributor and vote.
    evidence_url: https://tods-transit.org/governance/governance/
---

# Description

Extends GTFS for personnel and non-revenue service information used in scheduled transit operations.
