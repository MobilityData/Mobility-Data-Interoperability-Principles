---
short_name: NeTEx
full_name: Network, Timetables and Fare Exchange, CEN TS 16614-1 to 3 (SG9)
homepage_url: https://transmodel-cen.eu/index.php/netex/
status: not_compliant
modes: [microtransit_drt, public_transport, taxi_ridehail]
maintainers: [cen]
licences:
- id: GPL-3.0
  scopes: [specification]
- id: Apache-2.0
first_release_year: 2009
adoption:
  lifecycle: active
  tier: early
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: GPL 3.0
    evidence_url: https://github.com/NeTEx-CEN/NeTEx/blob/v2.0/LICENSE
  publicly_documented:
    verdict: partially_compliant
    rationale: Unable to find full public documentation.
    evidence_url: https://transmodel-cen.eu/index.php/netex/
  independent_maintainer:
    verdict: not_compliant
    rationale: Governmental institution
    evidence_url: https://transmodel-cen.eu/index.php/legal-context/
  structured_releases:
    verdict: compliant
    rationale: Versioning
    evidence_url: http://github.com/NeTEx-CEN/NeTEx/releases
  open_governance:
    verdict: not_compliant
    rationale: One vote per EU and some neighbouring countries. - Working Group participation requirements are unclear, potentail for industry conflict.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Exchange of network, schedules, and complex fare data.
