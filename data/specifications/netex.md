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
    verdict: not_compliant
    rationale: The normative specification (CEN/TS 16614) must be purchased from national standardization bodies.
    evidence_url: https://www.sis.se/en/produkter/information-technology-office-machines/applications-of-information-technology/it-applications-in-transport/sis-cents-16614-12020/
  publicly_documented:
    verdict: partially_compliant
    rationale: The XML schemas are freely available under GPL 3.0, but the full normative documentation must be purchased.
    evidence_url: https://transmodel-cen.eu/index.php/netex
  independent_maintainer:
    verdict: compliant
    rationale: CEN is a non-profit association whose standards are approved through formal votes by national standardization bodies, so that no single company, funder, or commercial group controls their content. Working groups are held with industry experts and project teams funded by the European Commission, but final decisions rest with CEN process.
    evidence_url: https://www.cencenelec.eu/about-cen/structure-and-governance/cen-board-members
  structured_releases:
    verdict: compliant
    rationale: Versioning available
    evidence_url: http://github.com/NeTEx-CEN/NeTEx/releases
  open_governance:
    verdict: not_compliant
    rationale: NeTEx and SIRI are developed within CEN/TC 278/WG 3, where direct participation in meetings and decisions requires nomination through a national standardization body, which can involve membership fees. Working documents are not publicly accessible, and final approval is reserved to formal votes by national members.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Exchange of network, schedules, and complex fare data.
