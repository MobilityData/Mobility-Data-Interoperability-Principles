---
short_name: IMDF
full_name: Indoor Mapping Data Format
homepage_url: https://register.apple.com/resources/imdf/
status: partially_compliant
modes: [pedestrian_accessibility]
maintainers: [ogc, apple]
licences:
- id: Custom-Open
first_release_year: 2019
adoption:
  lifecycle: active
  tier: hundred_plus
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: 'Yes'
    evidence_url: https://docs.ogc.org/cs/20-094/index.html
  publicly_documented:
    verdict: compliant
    rationale: Yes, full schemas, relationship rules, feature definitions, and validator tools are publicly accessible online.
    evidence_url: https://docs.ogc.org/cs/20-094/index.html
  independent_maintainer:
    verdict: partially_compliant
    rationale: No, it was originally developed as a proprietary specification by Apple Inc. before being submitted to the independent OGC for community standardization.
    evidence_url: https://docs.ogc.org/cs/20-094/index.html
  structured_releases:
    verdict: compliant
    rationale: 'Yes'
    evidence_url: https://docs.ogc.org/cs/20-094/CHANGELOG/index.html
  open_governance:
    verdict: partially_compliant
    rationale: Yes, governance is managed under the member-driven OGC consensus process alongside Apple community feedback.
    evidence_url: https://github.com/OGC-tracker/OGC-Standards-Tracker/
---

# Description

Indoor mapping, primarily used to create accurate, geo-referenced digital maps of indoor spaces. It’s often adopted for use in buildings like airports, malls, hospitals, universities, and other complex indoor environments
