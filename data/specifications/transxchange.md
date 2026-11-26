---
short_name: TransXChange
full_name: TransXChange (TXC)
homepage_url: http://gov.uk/government/collections/transxchange
status: not_compliant
modes: [public_transport]
maintainers: [uk-dft]
licences:
- id: OGL-3.0
  scopes: [specification, documentation]
first_release_year: 2001
adoption:
  lifecycle: active
  tier: hundred_plus
  confirmed_by_maintainer: true
  adopters_count: 943
  adopters_count_updated: '2026-11-24'
  adopters_registry_url: https://data.bus-data.dft.gov.uk/timetable/?area=&organisation=&status=live&start=&published_at=&submitform=submit&ordering=-modified
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Yes. 100% free to use, integrate, and redistribute commercially without restrictions under the Open Government Licence.
    evidence_url: https://assets.publishing.service.gov.uk/media/5a7482f3ed915d0e8bf18e16/1-1_Overview.pdf
  publicly_documented:
    verdict: compliant
    rationale: Yes. Complete XML schemas, technical documentation, implementation guides (UML), and sample files are publicly accessible on GOV.UK without registration.
    evidence_url: https://www.gov.uk/government/publications/national-public-transport-access-node-schema
  independent_maintainer:
    verdict: partially_compliant
    rationale: Maintained by the UK Government. While it has no business interest in the specification's content itself, the standard relies on a single organization.
    evidence_url: https://www.gov.uk/government/collections/transxchange
  structured_releases:
    verdict: compliant
    rationale: Yes. Major public releases. No release since 2014
    evidence_url: https://assets.publishing.service.gov.uk/media/5a74a3ce40f0b61df4777456/transxchange-publisher-guidance.pdf
  open_governance:
    verdict: not_compliant
    rationale: No public governance document - last updated in 2016
    evidence_url: https://assets.publishing.service.gov.uk/media/5a74a3ce40f0b61df4777456/transxchange-publisher-guidance.pdf
---

# Description

UK national XML-based standard for modeling and exchanging bus routes, stops, and timetables, used for passenger information systems and regulatory registration (Electronic Bus Service Registration / EBSR).
