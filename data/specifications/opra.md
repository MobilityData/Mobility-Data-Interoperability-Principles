---
short_name: OpRa
full_name: Operating Raw Data and Statistics Exchange
homepage_url: https://www.opra-cen.eu/
status: not_compliant
modes: [public_transport]
maintainers: [cen]
licences:
- id: GPL-3.0
  scopes: [specification]
first_release_year: 2026
adoption:
  lifecycle: pre_adoption
  tier: none
  confirmed_by_maintainer: false
principles:
  cost_restriction_free:
    verdict: not_compliant
    rationale: The XML schemas are available under GPL 3.0, but the normative specification (CEN/TS 17370) must be purchased.
    evidence_url: https://genorma.com/en/standards/cen-ts-17370-2026
  publicly_documented:
    verdict: partially_compliant
    rationale: The XML schemas are freely available under GPL 3.0, but the full normative documentation must be purchased.
    evidence_url: https://github.com/OpRa-CEN/OpRa
  independent_maintainer:
    verdict: compliant
    rationale: CEN is a non-profit association whose standards are approved through formal votes by national standardization bodies, so that no single company, funder, or commercial group controls their content. Working groups are held with industry experts and project teams funded by the European Commission, but final decisions rest with CEN process.
    evidence_url: https://www.cencenelec.eu/about-cen/structure-and-governance/cen-board-members
  structured_releases:
    verdict: compliant
    rationale: Version 1.0 of the XML schemas, matching CEN/TS 17370:2026, is published on GitHub.
    evidence_url: https://github.com/OpRa-CEN/OpRa
  open_governance:
    verdict: not_compliant
    rationale: OpRa is developed within CEN/TC 278/WG 3, where direct participation in meetings and decisions requires nomination through a national standardization body, which can involve membership fees. Working documents are not publicly accessible, and final approval is reserved to formal votes by national members.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Exchange of historical public transport operations data, such as observed run times, delays, cancellations and passenger loads, for planning and service analysis.
