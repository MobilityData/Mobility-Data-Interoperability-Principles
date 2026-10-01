---
short_name: MQTT
full_name: Message Queuing Telemetry Transport
homepage_url: https://mqtt.org/
status: not_compliant
maintainers: [oasis]
first_release_year: 1999
adoption:
  lifecycle: active
  tier: hundred_plus
  confirmed_by_maintainer: true
principles:
  cost_restriction_free:
    verdict: compliant
    rationale: Yes, however, the OASIS name is under copyright.
    evidence_url: https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901001
  publicly_documented:
    verdict: compliant
    rationale: 'Yes'
    evidence_url: https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
  independent_maintainer:
    verdict: compliant
    rationale: 'Yes'
    evidence_url: https://www.oasis-open.org/org/
  structured_releases:
    verdict: compliant
    rationale: 'Yes'
    evidence_url: https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
  open_governance:
    verdict: not_compliant
    rationale: No, only payed members can contribute
    evidence_url: https://www.oasis-open.org/join-a-tc/
---

# Description

MQTT for Sensor Networks is aimed at embedded devices on non-TCP/IP networks, such as Zigbee. MQTT-SN is a publish/subscribe messaging protocol for wireless sensor networks (WSN), with the aim of extending the MQTT protocol beyond the reach of TCP/IP infrastructure for Sensor and Actuator solutions.
