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
    rationale: Apache 2.0
    evidence_url: https://github.com/google/transit?tab=Apache-2.0-1-ov-file
  publicly_documented:
    verdict: compliant
    rationale: CC-BY-3.0
    evidence_url: https://creativecommons.org/licenses/by/3.0/
  independent_maintainer:
    verdict: compliant
    rationale: 'Actively maintained by MobilityData, an international non-profit organization. The maintainer facilitates specification development between data producers and data consumers and does not unilaterally decide its content.'
    evidence_url: https://mobilitydata.org/governance
  structured_releases:
    verdict: compliant
    rationale: Changelog
    evidence_url: https://gtfs.org/documentation/realtime/change-history/revision-history/
  open_governance:
    verdict: compliant
    rationale: |-
      Anyone can vote with equal rights.

      Note: Interface between governance and actual protobuf file implementation
    evidence_url: https://gtfs.org/community/governance/gtfs-realtime-amendment-process/
---

# Description

Extends GTFS to support live updates.
