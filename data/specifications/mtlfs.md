---
short_name: MTLFS
full_name: Managed and Tolled Lanes Feed Specification
homepage_url: https://github.com/vta/Managed-and-Tolled-Lanes-Feed-Specification
status: not_compliant
maintainers: [vta]
licences:
- id: MIT
first_release_year: 2016
adoption:
  lifecycle: inactive
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Yes for the specification text/code itself -- released under the MIT License, which permits free use, modification, and redistribution.
    evidence_url: https://github.com/vta/Managed-and-Tolled-Lanes-Feed-Specification?tab=MIT-1-ov-file
  publicly_documented:
    verdict: partially_compliant
    rationale: 'Documented only as an unfinished draft/proposal: the spec (mtlfs.md) and supporting materials (including a 2018 conference poster) are publicly posted on GitHub, but it was never finalized into a ratified standard.'
    evidence_url: https://github.com/vta/Managed-and-Tolled-Lanes-Feed-Specification/blob/master/README.md
  independent_maintainer:
    verdict: not_compliant
    rationale: No -- authored and hosted by a single public transit/toll agency (VTA)
    evidence_url: https://github.com/vta
  structured_releases:
    verdict: partially_compliant
    rationale: No -- the repository has no formal release tags or versioned releases.
    evidence_url: https://github.com/vta/Managed-and-Tolled-Lanes-Feed-Specification
  open_governance:
    verdict: not_compliant
    rationale: No formal governance process identified -- this is a single-agency proposal open only for public GitHub issue comments (17 open, unresolved issues)
    evidence_url: https://github.com/vta/Managed-and-Tolled-Lanes-Feed-Specification
---

# Description

A proposed open data-feed format for managed/tolled highway lanes: defines agency, toll-program, facility, gantry-location, and real-time toll-pricing data so that third-party applications (trip planners, payment tools, smartphone apps) can consume live tolling information.
