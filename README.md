# Mobility Data Interoperability Principles

Public Transit, and the mobility services which support it, is a critical backbone to our environmental, economic, and societal well-being.  Modern, easily-accessible and well-operated public transit depends on a complex system of operations and customer-oriented technology components which work together.  

Interoperable transit technology systems enable transit providers to plan service which is responsive to rider needs, improve service quality and efficiency, and adapt to continuing changes. Interoperability also encourages innovation among transportation technology companies while helping them to contain costs.

Released in October 2021 after a collaborative public process, [Mobility Data Interoperability Principles](http:interoperablemobility.org) create an industry-agreed upon vision, definition and direction for achieving interoperability with clear roles and responsibilities. The Principles were collaboratively developed and refined over Summer and Fall of 2021 by dozens of public and private organizations and researchers through a public review process.  

Over 60 public and private signatories have committed to implementing the Principles. Organizations who are interested in publicly committing to the Principles and their faithful implementation can submit the form found at: [Mobility Data Interoperability Principles](http://interoperablemobility.org).  

## Attribution

- [California Association of Coordinated Transportation (CALACT)](https://www.calact.org)
- [California Integrated Travel Project (Cal-ITP)](http://calitp.org)
- [Denver Regional Transportation District (RTD)](https://www.rtd-denver.com/)
- [ENTUR](https://entur.no/)
- [Los Angeles County Metropolitan Transportation Authority](https://www.metro.net/)
- [Massachusetts Bay Transportation Authority (MBTA)](https://www.mbta.com/)
- [MetroTransit](https://www.metrotransit.org/)
- [Metropolitan Transportation Commission (MTC)](http://bayareametro.org)
- [Minnesota Department of Transportation](https://www.dot.state.mn.us/)
- [MobilityData](http://mobilitydata.org)
- [North Carolina Department of Transportation](https://www.ncdot.gov/)
- [Oregon Department of Transportation](https://www.oregon.gov/odot/Pages/index.aspx)
- [Shared Use Mobility Center (SUMC)](https://sharedusemobilitycenter.org/)
- [Taskar Center for Accessible Technology](https://tcat.cs.washington.edu/)
- [Tri-Met](https://trimet.org/)
- [Vermont Agency of Transportation](https://vtrans.vermont.gov/)
- [VIA Metropolitan Transit San Antonio](https://www.viainfo.net/)
- [Washington State Department of Transportation (WSDOT) Public Transportation Division](https://wsdot.wa.gov/)

## Specification registry (`/specifications`)

The `/specifications` page, one page per specification under
`/specifications/<id>/`, and a read-only JSON API under `/api/` are generated
at build time from the files in [`data/`](data/README.md). GitHub is the
source of truth and the place to contribute: each specification and each
organization is one Markdown file with YAML front matter, and "Suggest a
change" on a specification's page opens that file in GitHub's editor.

The section is unlisted for now: it is not in the nav bar, the site search or
the sitemap, and its pages carry `<meta name="robots" content="noindex">`.

| Path | What it is |
| --- | --- |
| `data/specifications/<id>.md` | One specification: fields in front matter, then `# Description`. |
| `data/organizations/<id>.md` | One organization, its role and a link to its logo. |
| `data/principles.csv` | The criteria and what earns each verdict. |
| `data/licences.csv` | The licence ids specifications may use. |
| `data/README.md` | Every field and allowed value, the ranking, and the API. |
| `scripts/spec_data.py` | Loads, validates and joins the files. |
| `scripts/spec_api.py` | Builds the `/api/` files: catalogue, full records, export CSV, the OpenAPI description, and its Swagger UI page at `/api/docs/`. |
| `scripts/check_specs.py` | `make specs-check`: validation, also run on every pull request. |
| `hooks/specifications.py` | MkDocs hook that renders the pages and publishes the API. |

```bash
make specs-check    # validate the data; fails on any unknown value or key
make specs-export   # write the API files to generated/api/
make serve          # check the result
```

`make serve` caches the hook module, so restart the server after editing
`hooks/` or `scripts/`: it rebuilds, but with the previous code.

## Building the site locally

1. In Terminal, change the directory to one where you wish to build the site.
1. Ensure you have an up-to-date version of pip: 
   - Linux: `pip install pip` or `pip install --upgrade pip`
   - macOS: `pip3 install pip` or `pip3 install --upgrade pip`
1. Clone this repository:
   - `git clone https://github.com/MobilityData/Mobility-Data-Interoperability-Principles`
1. Change the directory to the cloned repository, and create & enable a Python virtual environment:
   - `python3 -m venv venv`
   - `source venv/bin/activate`
1. Have [`requirements.txt`](requirements.txt) installed:
   - Linux: `pip install --force-reinstall -r requirements.txt`
   - macOS: `pip3 install --force-reinstall -r requirements.txt`
1. Have [Material for MkDocs Insiders](https://squidfunk.github.io/mkdocs-material/insiders/`) installed. Substitute `${GH_TOKEN}` with MobilityData's access token:
   - Linux: `pip install git+https://${GH_TOKEN}@github.com/squidfunk/mkdocs-material-insiders.git`
   - macOS: `pip3 install git+https://${GH_TOKEN}@github.com/squidfunk/mkdocs-material-insiders.git`
1. To run the site locally (command defined in `MakeFile`):
   - `make serve`
   - Then each language will have it's own address:
     - English: `http://127.0.0.1:8000/`
1. To build the site locally only (command defined in `MakeFile`):
   - `make build`
1. Deactivate the Python virtual environment when done:
   - `deactivate`

## License

This code in this repository is licensed under [Apache 2.0](./LICENSE).

The content in this repository is licensed under [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/)
