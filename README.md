# Oregon Court Case Alerter

This project checks tracked Oregon circuit court cases for new filings and sends a Slack alert when it finds changes.

## What it does

The scraper logs into the Oregon public access portal, searches each case listed in [tracked_cases.txt](tracked_cases.txt), and compares the current filing events against the saved history in [cases/](cases/) master files. If new events are found, it updates the matching master file and posts a message to Slack.

## Project Files

- [court_scraper.py](court_scraper.py): main scraper and alert workflow
- [tracked_cases.txt](tracked_cases.txt): list of case numbers to monitor, one per line
- [cases/](cases/): stored filing snapshots for each tracked case

## Requirements

- Python 3
- Internet access and login to the Oregon public access portal
- A valid Slack bot token with permission to post to the target channel

## Install Dependencies

Install the Python packages used by the script:

```bash
pip install requests beautifulsoup4 pytz slack-sdk
```

## Configuration

Before running, make sure:

- `SLACK_TOKEN` is set in your environment.
- `LOGIN_PASSWORD` and `LOGIN_USERNAME` are set in your enviroment to login to the Oregon court's website.
- Every case you want to monitor is listed in [tracked_cases.txt](tracked_cases.txt).

The scraper saves each case's current filing list to [cases/CASE_NUMBER_master.txt](cases/). If a file does not exist yet, it creates one on the first run.

## Usage

Run the script directly:

```bash
python court_scraper.py
```

On each run, the script:

1. Reads the tracked case numbers
2. Logs into the court portal
3. Pulls the current filing history for each case
4. Compares the results with the saved master file
5. Sends a Slack alert when new filings are detected

## Output Behavior

- If a case has new filings, its master file is overwritten with the updated filing list and a Slack message is sent.
- If no changes are found for any tracked case, the script sends a single no-update message to Slack.
- On the first run for a case, the script creates the corresponding master file instead of sending a filing change alert.

## Notes

- The script is tuned to Oregon's public access site structure, so site changes may require scraper updates.
- The current implementation includes timing delays between requests to reduce the chance of hammering the portal.
- This project is intended for a small tracked set of cases rather than large-scale scraping.