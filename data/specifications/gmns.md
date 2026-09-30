---
short_name: GMNS
full_name: General Modeling Network Specification
homepage_url: https://github.com/zephyr-data-specs/GMNS
status: not_compliant
modes: [bicycle, pedestrian_accessibility, public_transport]
maintainers: [zephyr]
licences:
- id: Apache-2.0
  scopes: [specification]
- id: MIT
  scopes: [documentation]
first_release_year: 2018
adoption:
  lifecycle: early_adoption
  tier: early
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://rosap.ntl.bts.gov/view/dot/44136
  publicly_documented:
    verdict: compliant
    rationale: Everything is available on GitHub and GitHub Pages.
    evidence_url: https://github.com/zephyr-data-specs/GMNS
  independent_maintainer:
    verdict: partially_compliant
    rationale: |-
      Board does include a minority of seats for industry.
      But not maintained by an independant organization.
    evidence_url: https://zephyrtransport.org/
  structured_releases:
    verdict: compliant
    rationale: Yes, formal version tagging is maintained on GitHub.
    evidence_url: https://github.com/zephyr-data-specs/GMNS/releases
  open_governance:
    verdict: not_compliant
    rationale: Operates with an open-source, community-driven governance model via the Zephyr Foundation. However, voting is only possible as a member.
    evidence_url: https://zephyrtransport.org/
---

# Description

Provides a common machine- and human-readable format for sharing routable road and multi-modal network files. Used primarily for static and dynamic transportation planning and operations modeling.
