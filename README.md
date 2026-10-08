# Fare Watch

Tracks the cheapest business-class fares for routes in `watchlist.json`.
GitHub Actions checks prices every 8 hours and saves them to `data/prices.json`;
`index.html` (GitHub Pages) charts them. Everything runs on free tiers.

## Setup (about 5 minutes)
1. Create a new **public** GitHub repo and upload all these files (keep the folder structure, including `.github/`).
2. **Settings → Pages**: Source = "Deploy from a branch", branch `main`, folder `/ (root)`.
3. **Actions tab → Check fares → Run workflow** to fetch the first prices (takes a few minutes).
4. Open `https://<your-username>.github.io/<repo-name>/`.

## Add a route
Use the "Add a route" form on the page: it copies a JSON entry and opens GitHub's editor for
`watchlist.json`. Paste it into the list, commit, then run the workflow once.
Set `"airline_codes": []` and `"airline_names": []` to track any airline.

## Price alerts (optional, free)
Install the ntfy app, subscribe to a hard-to-guess topic name, then add that name as a repo secret
called `NTFY_TOPIC` (Settings → Secrets and variables → Actions). Set `alert_below` on a route.

## Things to check
- Currency: prices are shown as returned by Google Flights. Compare one fare against google.com/flights
  and change `currency_label` if it doesn't match.
- Data comes from an unofficial library and may break or return nothing for some dates. If a route
  shows no fares, check the Actions log, and confirm Virgin sells business on that route.
- Fares are indicative; the airline sets the final price.
