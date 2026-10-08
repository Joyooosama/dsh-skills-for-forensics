# User-Level Skills Functional Index

Physical layout remains flat under `C:\Users\27516\.agents\skills` so Codex and Copilot can still discover each skill. This file is the functional tree used for routing.

## Routing Priority

1. Exact named skill or tool-specific local skill.
2. Existing CTF/reverse/forensics router skills for CTF and challenge work.
3. `cybersecurity-skill-router` for broad cybersecurity requests.
4. Anthropic cybersecurity task skill by group and subdomain.

## Tree Overview

```text
C:\Users\27516\.agents\skills
|- local-existing-and-index-skills
|  |- Agent Workflow and Engineering Process (13)
|  |- Skill Management and Routing (4)
|  |- CTF and Challenge Solving (18)
|  |- Reverse Engineering and Binary Analysis (12)
|  |- Forensics and Traffic Analysis (7)
|  |- Infrastructure Security and Pentest (2)
|  |- Frontend, Design and Visual Artifacts (8)
|  |- Documents, Spreadsheets and Communications (8)
|  |- Developer Tools, APIs and Databases (6)
|  |- General Utilities and Writing Help (3)
`- anthropic-cybersecurity-skills
   |- Security Operations, Detection and Incident Response (151)
   |  |- incident-response (26)
   |  |- purple-team (1)
   |  |- security-operations (28)
   |  |- soc-operations (33)
   |  |- threat-detection (7)
   |  |- threat-hunting (56)
   |- Threat Intelligence, Phishing, Ransomware and Deception (82)
   |  |- deception-technology (3)
   |  |- phishing-defense (15)
   |  |- ransomware-defense (13)
   |  |- social-engineering-defense (1)
   |  |- threat-intelligence (50)
   |- Forensics, Malware, Endpoint, Mobile and Firmware (108)
   |  |- digital-forensics (37)
   |  |- endpoint-security (17)
   |  |- firmware-analysis (1)
   |  |- firmware-security (1)
   |  |- malware-analysis (39)
   |  |- mobile-security (13)
   |- Offensive Testing, Web, API and Wireless (120)
   |  |- api-security (28)
   |  |- offensive-security (2)
   |  |- penetration-testing (20)
   |  |- red-team (2)
   |  |- red-teaming (24)
   |  |- web-application-security (42)
   |  |- wireless-security (2)
   |- Cloud, Container, DevSecOps, Application and Supply Chain (118)
   |  |- ai-security (2)
   |  |- application-security (4)
   |  |- cloud-security (63)
   |  |- container-security (29)
   |  |- devsecops (17)
   |  |- supply-chain-security (3)
   |- Network and OT/ICS (72)
   |  |- network-security (43)
   |  |- ot-ics-security (28)
   |  |- ot-security (1)
   |- Identity, Zero Trust, Privacy and Data (57)
   |  |- data-protection (1)
   |  |- identity-access-management (33)
   |  |- identity-and-access-management (2)
   |  |- identity-security (1)
   |  |- privacy-compliance (2)
   |  |- zero-trust (1)
   |  |- zero-trust-architecture (17)
   |- Governance, Vulnerability, Compliance and Risk (30)
   |  |- compliance-governance (4)
   |  |- governance-risk-compliance (1)
   |  |- vulnerability-management (25)
   |- Cryptography, Blockchain and AI Security (16)
   |  |- blockchain-security (1)
   |  |- cryptography (15)
```

## Files

- `anthropic-cybersecurity-skills-by-subdomain.md`: complete list of the 754 new cybersecurity skills.
- `existing-local-skills.md`: local skills that were already present plus this router skill, grouped by function.
- `all-skills-index.json`: machine-readable index with source, group, subdomain, path, and description.
