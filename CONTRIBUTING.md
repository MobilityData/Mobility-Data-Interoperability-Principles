# Contributing

## Specifications

The [specification registry](https://www.interoperablemobility.org/specifications/) is open. Anyone can propose a new specification, or a change to an existing one, verdicts included. A few simple rules keep it fair.

### Who does what

| Who | What they can do |
| --- | --- |
| Anyone | Propose a new specification, or a change to any entry |
| Specification maintainers | The same, including changes to their own specification |
| Reviewers (someone from another organization, or from the MDIP Coalition) | Approve a change proposed by someone else |
| MDIP Manager (MobilityData) | Ask for clarification, and merge approved changes |
| MDIP Coalition | Have the final say on the hardest cases |

### Rules

1. **Back it with a public source.** Every change needs a link to a public document that supports it. Link as close to the evidence as you can: the exact page or section, not a home page.
2. **Discuss in the open.** All discussion happens here on GitHub, in the pull request or issue.
3. **No self-approval.** A change is merged only after someone from another organization, or from the MDIP Coalition, approves it. Nobody approves their own change, maintainers and Coalition members included.

### When it is not clear

If the sources, a verdict, or the relevance of a proposed specification are in doubt, the MDIP Manager will comment on the pull request to ask for clarification. For the hardest cases, the MDIP Coalition has the final say: the decision goes on the agenda of its next meeting.

### How to propose a change

Use "Suggest a change" on a specification's page, or "Propose a specification" on the registry page. Both open the file in GitHub's editor and lead to a pull request. See [`data/README.md`](data/README.md) for the file format.

## Optimizing Images for the Website

When adding or updating images such as logos on the website, they should be optimized _before_ they are committed_; meaning they should be stripped of metadata and other information reducing the file size allowing them to load faster for users. There are two tools that can be used for this,

- [Squoosh](https://squoosh.app/) - a web browser based image optimizer; use the OxiPNG option for PNGs
- [ImageOptim](https://imageoptim.com/mac) - a macOS application that will take care of choosing the best algorithm
