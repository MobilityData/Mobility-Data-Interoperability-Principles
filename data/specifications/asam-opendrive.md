---
short_name: ASAM OpenDRIVE
full_name: Association for Standardization of Automation and Measuring Systems
homepage_url: https://www.asam.net/standards/detail/opendrive
status: partially_compliant
modes: [taxi_ridehail, microtransit_drt]
maintainers: [asam]
licences:
- id: Members-Only
first_release_year: 2005
adoption:
  lifecycle: active
  tier: hundred_plus
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: partially_compliant
    rationale: Free to download and use/redistribute under ASAM's own license terms, but access requires either ASAM membership (annual dues scaled to company size) or providing registration details as a non-member; it is not licensed under a conventional open-source license (e.g., MIT/CC)."
    evidence_url: https://www.asam.net/standards/detail/opendrive/#:~:text=(The%20download%20of%20the%20standard%20ASAM%20OpenDRIVE,as%20features%20along%20the%20roads%2C%20like%20signals.
  publicly_documented:
    verdict: compliant
    rationale: Yes -- the full specification text is published and downloadable (registration required for non-members) at ASAM's publications site; there is no separate paywalled 'full version'.
    evidence_url: https://publications.pages.asam.net/standards/ASAM_OpenDRIVE/ASAM_OpenDRIVE_Specification/v1.9.0/specification/00_preface/00_introduction.html
  independent_maintainer:
    verdict: partially_compliant
    rationale: No in the neutral/public-interest sense -- ASAM e.V. is an industry-membership association (~400 member companies, predominantly automotive OEMs, Tier-1 suppliers, and tool vendors) that funds and governs the standard through paid membership.
    evidence_url: https://www.asam.net/about-asam/organization/
  structured_releases:
    verdict: compliant
    rationale: Yes -- versioned releases with documented changes
    evidence_url: https://www.asam.net/standards/detail/opendrive/older/
  open_governance:
    verdict: partially_compliant
    rationale: Partially -- non-members can read/download the standard, but proposing changes and voting on standard development is generally reserved for dues-paying ASAM members
    evidence_url: https://code.asam.net/simulation/openx/-/blob/main/README.md?ref_type=heads
---

# Description

XML-based open format specification (file extension .xodr) for describing the static logic of road networks -- roads, lanes, junctions, signals, and roadside objects -- so that road descriptions can be exchanged between different driving simulators for ADAS/automated-driving development and validation. However the ASAM is the unique owner of the standard itself.
