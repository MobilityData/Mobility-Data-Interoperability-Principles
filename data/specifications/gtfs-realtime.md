---
short_name: GTFS Realtime
full_name: General Transit Feed Specification Realtime
homepage_url: https://gtfs.org/
status: compliant
modes: [public_transport]
maintainers: [mobilitydata]
licences:
- id: Apache-2.0
  scopes: [specification]
- id: CC-BY-3.0
  scopes: [documentation]
first_release_year: 2011
adoption:
  lifecycle: active
  tier: hundred_plus
  adopters_count: 666
  adopters_count_updated: '2026-11-10'
  adopters_registry_url: https://mobilitydatabase.org/feeds?gtfs_rt=true
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: GTFS is free to use. Apache 2.0 allows commercial use.
    evidence_url: https://www.apache.org/licenses/LICENSE-2.0.txt
  publicly_documented:
    verdict: compliant
    rationale: The full documentation is available publicly.
    evidence_url: https://gtfs.org/documentation/overview
  independent_maintainer:
    verdict: compliant
    rationale: 'Actively maintained by MobilityData, an international non-profit organization. The maintainer facilitates specification development between data producers and data consumers and does not unilaterally decide its content.'
    evidence_url: https://mobilitydata.org/governance
  structured_releases:
    verdict: compliant
    rationale: Change history available
    evidence_url: https://gtfs.org/documentation/realtime/change-history/revision-history/
  open_governance:
    verdict: compliant
    rationale: Anyone can become a Contributor by participating in discussions within the official GTFS repository, regardless of their technical skills or experience with GTFS. Everyone can vote with equal rights.
    evidence_url: https://gtfs.org/community/governance/gtfs-realtime-amendment-process/
---

# Description

Extends GTFS to support live updates.
