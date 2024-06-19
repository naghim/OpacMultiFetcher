# Opac Multi Fetcher

A Python script designed to **bulk download** items from an Opac online library efficiently. This script automates the process of fetching all PDFs from an Opac website, saving you time and effort while being **highy configurable**.

## Prerequisites

- An **active account to access the Opac online library**.
- Python 3.10+

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/naghim/OpacMultiFetcher.git
cd OpacMultiFetcher
```

2. **Install the required Python packages**:

```bash
pip install -r requirements.txt
```

## Usage

1. **Configure the script and add your credentials** (see Configuration section). Ensure you have filled out the `settings.json` file with the correct details.

2. **Run the script**:

```bash
python download.py
```

3. The script will log in using your credentials and start **downloading PDFs** based on your configuration.

### Configuration

Create a file named `settings.json` in the root folder with the following structure:

```json
{
  "url": "http://opac3.ms.sapientia.ro",
  "tenant": "marosvasarhely",
  "lastRecord": 116323,
  "cookies": {
    "access_token": "...",
    "JSESSIONID": "...."
  }
}
```

- `url`: The base URL of the Opac online library.
- `tenant`: The tenant identifier for the library.
- `lastRecord`: The last record number you want to fetch. Adjust this based on your requirements.
- `cookies`: Your authentication cookies for accessing the library. You need to include your `access_token` and `JSESSIONID` obtained from logging into the library. **Note:** Some websites _are public and work without cookies set_.
