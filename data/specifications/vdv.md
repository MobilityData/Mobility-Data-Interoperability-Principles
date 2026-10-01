---
short_name: VDV
full_name: Verband Deutscher Verkehrsunternehmen - Kernapplikation (VDV-KA)
homepage_url: http://eticket-deutschland.de
status: not_compliant
modes: [public_transport]
maintainers: [vdv-ets]
licences:
- id: Proprietary
  scopes: [documentation, specification]
first_release_year: 2002
adoption:
  lifecycle: active
  tier: hundred_plus
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: not_compliant
    rationale: No. Specifications require paid manufacturer subscriptions (((etiKIT) ranging from €359 to €1,790/month for commercial use, alongside mandatory participation/framework agreements.
    evidence_url: https://www.eticket-deutschland.de/en/about-us/
  publicly_documented:
    verdict: not_compliant
    rationale: No. High-level overviews and glossaries are public, but complete technical specifications, test tools, and XML schemas are restricted behind login walls (ASM Tool).
    evidence_url: https://www.eticket-deutschland.de/en/eticket/vdv-ka-and-eticore/
  independent_maintainer:
    verdict: not_compliant
    rationale: Industry Consortium / Sector Subsidiary. Maintained by VDV ETS, an entity owned and controlled by German transport associations and public transport operators under the umbrella of the VDV.
    evidence_url: https://www.eticket-deutschland.de/en/eticket/vdv-ka-and-eticore/
  structured_releases:
    verdict: compliant
    rationale: Yes. Maintained across active releases (VDV-KA Release 1.12.1 currently live; (((etiCORE / KA 3.0.0-rc in active transition).
    evidence_url: https://www.eticket-deutschland.de/en/eticket/vdv-ka-and-eticore/
  open_governance:
    verdict: not_compliant
    rationale: Restricted. Governance is tied to German transport association participation and paid manufacturer tiers. Access to development groups and voting influence requires formal membership and contractual accession.
    evidence_url: https://www.eticket-deutschland.de/en/eticket/vdv-ka-and-eticore/
---

# Description

Nationwide open data and interface standard for electronic ticketing and electronic fare management (EFM) in public transport across smart cards, 2D barcodes, mobile NFC ticketing, and background processing systems.
