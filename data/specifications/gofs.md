---
short_name: GOFS
full_name: General On-Demand Feed Specification (GOFS)
homepage_url: https://github.com/MobilityData/GOFS/blob/main/governance.md
status: compliant
modes: [microtransit_drt, taxi_ridehail]
maintainers: [mobilitydata]
licences:
- id: Apache-2.0
  scopes: [specification, documentation]
first_release_year: 2021
adoption:
  lifecycle: early_adoption
  tier: early
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Yes, Apache 2.0
    evidence_url: https://github.com/MobilityData/GOFS
  publicly_documented:
    verdict: compliant
    rationale: Yes Specification, JSON schema, and governance process are all published in full on GitHub
    evidence_url: https://github.com/MobilityData/GOFS/blob/main/reference.md
  independent_maintainer:
    verdict: compliant
    rationale: Yes MobilityData is an independent nonprofit; the Maintainer role facilitates but does not vote on changes.
    evidence_url: https://mobilitydata.org/history/
  structured_releases:
    verdict: compliant
    rationale: Yes Structured MAJOR/MINOR release cycle with changelog via GitHub releases.
    evidence_url: https://github.com/MobilityData/GOFS
  open_governance:
    verdict: compliant
    rationale: Anyone can propose changes and anyone can vote; requires unanimous consensus including at least one producer and one consumer vote — the same open governance model used by GBFS/GTFS.
    evidence_url: https://github.com/MobilityData/GOFS/blob/main/governance.md
---

# Description

A lightweight, open data format for purely on-demand transport services (no fixed routes/schedule) to describe their offering for consumption by transport applications
