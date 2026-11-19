---
short_name: SIRI
full_name: Service Interface for Real-time Information
homepage_url: https://github.com/TransmodelEcosystem/SIRI
status: not_compliant
modes: [public_transport]
maintainers: [cen]
licences: []
first_release_year: 2006
adoption:
  lifecycle: active
  tier: early
principles:
  cost_restriction_free:
    verdict: not_compliant
    rationale: The normative specification (EN 15531 and CEN/TS 15531) must be purchased from national standardization bodies.
    evidence_url: https://www.austrian-standards.at/de/shop/onorm-en-15531-1-2022-10-01~p2637091
  publicly_documented:
    verdict: partially_compliant
    rationale: The XML schemas and examples are publicly available on GitHub, but the full normative documentation must be purchased.
    evidence_url: https://github.com/TransmodelEcosystem/SIRI
  independent_maintainer:
    verdict: compliant
    rationale: CEN is a non-profit association whose standards are approved through formal votes by national standardization bodies, so that no single company, funder, or commercial group controls their content. Working groups are held with industry experts and project teams funded by the European Commission, but final decisions rest with CEN process.
    evidence_url: https://www.cencenelec.eu/about-cen/structure-and-governance/cen-board-members
  structured_releases:
    verdict: compliant
    rationale: Versioned releases matching the CEN documentation are published on GitHub.
    evidence_url: https://github.com/TransmodelEcosystem/SIRI/releases
  open_governance:
    verdict: not_compliant
    rationale: SIRI is developed within CEN/TC 278/WG 3, where direct participation in meetings and decisions requires nomination through a national standardization body, which can involve membership fees. Working documents are not publicly accessible, and final approval is reserved to formal votes by national members.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---
# Description

Exchange of real-time public transport information, including vehicle positions, estimated timetables, stop monitoring, and service disruptions.
