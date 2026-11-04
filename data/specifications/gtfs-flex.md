---
short_name: GTFS' Flex features
full_name: GTFS-Flex (flexible / demand-responsive service extensions to core GTFS).
homepage_url: https://gtfs.org/
status: compliant
modes: [microtransit_drt]
maintainers: [mobilitydata]
licences:
- id: Apache-2.0
  scopes: [specification]
- id: CC-BY-3.0
  scopes: [documentation]
first_release_year: 2020
adoption:
  lifecycle: early_adoption
  tier: early
  adopters_count: 150
  adopters_count_updated: '2026-11-04'
  adopters_registry_url: https://mobilitydatabase.org/feeds?features=Booking+Rules%2CContinuous+Stops%2CFixed-Stops+Demand+Responsive+Transit%2CPredefined+Routes+with+Deviation%2CZone-Based+Demand+Responsive+Services
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://github.com/google/transit?tab=Apache-2.0-1-ov-file
  publicly_documented:
    verdict: compliant
    rationale: Apache 2.0
    evidence_url: https://creativecommons.org/licenses/by/3.0/
  independent_maintainer:
    verdict: compliant
    rationale: International non profit organization
      Official Maintainer: MobilityData.

      (GitHub repo still held by Google. Google delegated admin rights to MobilityData.)
    evidence_url: https://gtfs.org/community/governance/gtfs-schedule-governance/roles/
  structured_releases:
    verdict: compliant
    rationale: Changelog
    evidence_url: https://gtfs.org/documentation/schedule/change-history/revision-history/
  open_governance:
    verdict: compliant
    rationale: Anyone can vote with equal rights.
    evidence_url: https://gtfs.org/community/governance/gtfs-schedule-governance/roles/
---

# Description

Extends core GTFS Schedule to describe flexible and demand-responsive service: booking rules, flexible service zones/areas, and continuous stops/pickup-dropoff windows
