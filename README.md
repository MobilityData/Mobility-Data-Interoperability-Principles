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
