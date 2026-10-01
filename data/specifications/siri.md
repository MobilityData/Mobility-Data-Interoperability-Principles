---
short_name: SIRI
full_name: Service Interface for Real Time Information
homepage_url: https://transmodel-cen.eu/index.php/siri/
status: not_compliant
modes: [public_transport]
maintainers: [cen]
licences:
- id: Crown-Copyright
  scopes: [specification]
first_release_year: 2006
adoption:
  lifecycle: active
  tier: hundred_plus
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: unknown
    rationale: No licence specified
    evidence_url: https://github.com/TransmodelEcosystem/SIRI
  publicly_documented:
    verdict: not_compliant
    rationale: Schemas available, no full and clear documentation available.
    evidence_url: https://transmodel-cen.eu/index.php/uml-documents/
  independent_maintainer:
    verdict: partially_compliant
    rationale: |-
      CEN - Working Group participation requirements are unclear

      Governmental entity (EU)
  structured_releases:
    verdict: compliant
    rationale: Versioning
    evidence_url: https://github.com/SIRI-CEN/SIRI/releases
  open_governance:
    verdict: not_compliant
    rationale: Unclear, no information on adoped changes after a pull request.
    evidence_url: https://www.cencenelec.eu/european-standardization/cen-and-cenelec/
---

# Description

Exchange of realtime information about schedules, vehicles, transfers, and additional informational messages about operational status
