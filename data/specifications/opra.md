---
short_name: OpRa
full_name: Operational Raw Data
homepage_url: http://transmodel-cen.eu/opra
status: not_compliant
modes: [public_transport]
maintainers: [cen]
licences:
- id: GPL-3.0
  scopes: [specification]
first_release_year: 2018
adoption:
  lifecycle: pre_adoption
  tier: none
  confirmed_by_maintainer: false
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: GPL 3.0
    evidence_url: https://github.com/OpRa-CEN/OpRa/blob/1.0rc/LICENSE
  publicly_documented:
    verdict: not_compliant
    rationale: Unable to find full public documentation.
  independent_maintainer:
    verdict: partially_compliant
    rationale: |-
      CEN

      Working Group participation requirements are unclear, potentail for industry conflict.
  structured_releases:
    verdict: compliant
    rationale: Versioning is planned.
    evidence_url: https://github.com/OpRa-CEN/OpRa/releases
  open_governance:
    verdict: not_compliant
    rationale: One vote per EU and some neighbouring countries.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Archive of observed data about transit operations for future planning
