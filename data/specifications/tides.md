---
short_name: TIDES
full_name: Transit Integrated Data Exchange Specification
homepage_url: https://tides-transit.org/main/
status: compliant
modes: [public_transport]
maintainers: [tides-board, mobilitydata]
licences:
- id: Apache-2.0
  scopes: [specification]
- id: CC-BY-4.0
  scopes: [documentation]
first_release_year: 2024
adoption:
  lifecycle: pilot_adoption
  tier: pilot
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://github.com/TIDES-transit/TIDES
  publicly_documented:
    verdict: compliant
    rationale: CC-BY-4.0
    evidence_url: http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1
  independent_maintainer:
    verdict: compliant
    rationale: Board does include a minority of seats for industry.
    evidence_url: https://tides-transit.org/main/governance/
  structured_releases:
    verdict: compliant
    rationale: Versioning, Revision History
    evidence_url: https://github.com/TIDES-transit/TIDES/releases
  open_governance:
    verdict: compliant
    rationale: Anyone can become a contributor and vote.
    evidence_url: https://tides-transit.org/main/governance/
---

# Description

Standard format for archiving transit operational data (AFC, AVL, APC).
