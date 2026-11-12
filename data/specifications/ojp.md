---
short_name: OJP
full_name: Open API for distributed Journey Planning
homepage_url: https://transmodel-cen.eu/index.php/ojp/
status: not_compliant
modes: [public_transport]
maintainers: [cen]
licences: []
first_release_year: 2017
adoption:
  lifecycle: active
  tier: pilot
principles:
  cost_restriction_free:
    verdict: not_compliant
    rationale: The normative specification (CEN/TS 17118) must be purchased from national standardization bodies.
    evidence_url: https://www.dinmedia.de/en/pre-standard/din-cen-ts-17118/375690154
  publicly_documented:
    verdict: partially_compliant
    rationale: The XML schemas, examples and generated documentation tables are publicly available on GitHub, but the full normative documentation must be purchased.
    evidence_url: https://vdvde.github.io/OJP/index.html
  independent_maintainer:
    verdict: compliant
    rationale: CEN is a non-profit association whose standards are approved through formal votes by national standardization bodies, so that no single company, funder, or commercial group controls their content. Working groups are held with industry experts and project teams funded by the European Commission, but final decisions rest with CEN process. The XML schema repository is hosted by VDV, the German association of transport companies.
    evidence_url: https://www.cencenelec.eu/about-cen/structure-and-governance/cen-board-members
  structured_releases:
    verdict: compliant
    rationale: Versioned releases (OJP 1.0, 1.0.1 and 2.0) matching the CEN documentation are published on GitHub.
    evidence_url: https://github.com/VDVde/OJP/releases
  open_governance:
    verdict: not_compliant
    rationale: OJP is developed within CEN/TC 278/WG 3, where direct participation in meetings and decisions requires nomination through a national standardization body, which can involve membership fees. Working documents are not publicly accessible, and final approval is reserved to formal votes by national members. Contributions to the XML schemas are possible on GitHub, but the process for adopting them is not documented.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Defines an open API standard for distributed journey planning. It allows different systems and agencies to collaborate and calculate cross-border or multi-modal trips without needing a central data repository.
