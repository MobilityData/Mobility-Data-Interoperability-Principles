---
short_name: OJP
full_name: Open Journey Planner
homepage_url: https://transmodel-cen.eu/index.php/ojp/
status: not_compliant
modes: [public_transport]
maintainers: [cen]
licences:
- id: Proprietary
- id: Apache-2.0
  scopes: [specification]
first_release_year: 2017
adoption:
  lifecycle: active
  tier: pilot
principles:
  cost_restriction_free:
    verdict: unknown
    rationale: No licence specified
    evidence_url: https://transmodel-cen.eu/index.php/ojp/
  publicly_documented:
    verdict: partially_compliant
    rationale: Only the technical XML schema and API endpoints are published.
    evidence_url: https://github.com/VDVde/OJP
  independent_maintainer:
    verdict: not_compliant
    rationale: Governmental institution
    evidence_url: https://www.itsstandards.eu/
  structured_releases:
    verdict: compliant
    rationale: Yes, major releases (OJP 1.0, 2.0) are published via CEN and GitHub.
    evidence_url: https://github.com/VDVde/OJP/blob/develop/CHANGELOG.md
  open_governance:
    verdict: not_compliant
    rationale: Unclear, no information on adoped changes after a pull request.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Defines an open API standard for distributed journey planning. It allows different systems and agencies to collaborate and calculate cross-border or multi-modal trips without needing a central data repository.
