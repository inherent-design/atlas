---
title: Licensing/Legal
---

# Licensing and Legal Information

This document provides detailed information about Atlas licensing, contribution terms, and related legal information.

## Open Source License

Atlas is released under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). This is a permissive license that allows you to:

- Use Atlas for commercial purposes
- Modify Atlas and create derivative works
- Distribute Atlas and derivative works
- Sublicense Atlas to others
- Use Atlas privately without distributing your changes

The Apache License 2.0 requires you to:

- Include a copy of the license in any redistribution
- Provide attribution to the original authors
- State changes made to the original code
- Include the NOTICE file if present

## Dual Licensing Model

Atlas uses a dual licensing model:

1. **Open Source Core (Apache License 2.0)**
   - The core functionality of Atlas is available under the Apache License 2.0
   - This covers all components in the main repository
   - Community contributions are accepted under the Apache License 2.0

2. **Commercial License for Enterprise Features**
   - Certain enterprise features are available under a separate commercial license
   - These features are developed and maintained by inherent.design
   - The commercial license provides additional rights and services
   - Enterprise features are clearly marked in the documentation

## Contributor License Agreement (CLA)

Contributors to Atlas are required to agree to the following terms:

1. **Grant of Copyright License**: Contributors grant inherent.design a perpetual, worldwide, non-exclusive, royalty-free copyright license to reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute their contributions and derivative works.

2. **Grant of Patent License**: Contributors grant inherent.design a perpetual, worldwide, non-exclusive, royalty-free patent license for any patents they own that are necessarily infringed by their contribution.

3. **Original Creation**: Contributors confirm that they are the original author of the contribution or have the right to submit it.

4. **Responsibility**: Contributors understand they are legally responsible for ensuring they have the right to submit their contributions.

The CLA ensures that inherent.design has the necessary rights to distribute contributions under both the open source and commercial licenses.

## Third-Party Dependencies

Atlas uses various third-party open source libraries, each with its own license. The main dependencies include:

| Dependency    | License    | Purpose                                  |
| ------------- | ---------- | ---------------------------------------- |
| LangGraph     | MIT        | Graph-based workflow orchestration       |
| ChromaDB      | Apache 2.0 | Vector storage for knowledge retrieval   |
| Anthropic SDK | MIT        | Integration with Anthropic Claude models |
| OpenAI SDK    | MIT        | Integration with OpenAI models           |
| VitePress     | MIT        | Documentation system                     |

A complete list of dependencies and their licenses can be found in the project's `pyproject.toml` file.

## Trademark Policy

"Atlas" and related logos are trademarks of inherent.design. The following guidelines apply to the use of these trademarks:

1. **Permitted Use**:
   - Referring to Atlas software in documentation
   - Indicating compatibility with Atlas
   - Non-commercial community presentations about Atlas

2. **Restricted Use** (requiring permission):
   - Use in product names
   - Use in domain names
   - Use on merchandise
   - Use that might imply endorsement

For questions about trademark usage, please contact legal@inherent.design.

## Patent Rights

The Apache License 2.0 includes a patent license grant that provides protection against patent litigation for users of the software. This means:

1. Contributors grant a patent license for any patents they own that are necessarily infringed by their contributions.

2. If a user initiates patent litigation against any contributor over patents that are infringed by the software, the user's patent licenses from such contributor are terminated.

## Commercial Licensing Details

The Atlas Enterprise edition is available under a commercial license with the following general terms:

1. **Subscription Term**: Annual subscription with renewal options
2. **License Scope**: Per-developer or per-organization licensing
3. **Support Terms**: SLA-backed support with tiered response times
4. **Maintenance**: Regular updates and security patches
5. **Legal Protection**: Additional intellectual property indemnification

For specific commercial licensing terms and pricing, please contact sales@inherent.design.

## Privacy Policy

When using Atlas, please be aware of the following privacy considerations:

1. **Data Collection**: Atlas itself does not collect usage data automatically.
2. **API Keys**: When using model providers (OpenAI, Anthropic, etc.), you must comply with their respective terms of service and privacy policies.
3. **Knowledge Base**: Any documents you ingest into the knowledge base remain yours and are not accessible to inherent.design.
4. **Telemetry**: Optional telemetry features can be enabled for debugging, which are governed by a separate privacy policy.

## Compliance and Export Control

Users of Atlas are responsible for ensuring their use complies with applicable laws and regulations, including:

1. **Export Control**: Restrictions on exporting software to certain countries
2. **Data Protection**: Regulations such as GDPR or CCPA
3. **Industry-Specific Regulations**: Requirements for specific sectors (healthcare, finance, etc.)

inherent.design does not provide legal advice on compliance matters.

## Changes to Legal Terms

inherent.design reserves the right to change the license terms for future versions of Atlas. Any such changes will:

1. Be clearly communicated in release notes
2. Include a transition period for users
3. Not affect the license of already released versions
4. Be made in good faith to balance business and community needs

## Legal Contacts

For legal inquiries regarding Atlas:

- **Licensing Questions**: licensing@inherent.design
- **Trademark Issues**: trademarks@inherent.design
- **Patent Concerns**: patents@inherent.design
- **General Legal**: legal@inherent.design

## FOSS Compliance Resources

For organizations requiring assistance with open source compliance:

1. **License Texts**: Full license texts are included in the repository
2. **Dependency List**: A complete list can be generated with `uv pip list --format=json`
3. **SBOM**: A Software Bill of Materials is available upon request
4. **Notices**: All required notices are included in the NOTICE file

## Acknowledgements

Atlas is built on the work of numerous open source projects and their contributors. We gratefully acknowledge their contributions and the open source community as a whole.
