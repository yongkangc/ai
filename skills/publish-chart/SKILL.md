---
name: publish-chart
description: Publish an HTML chart/visualization to www.ksgabrieltan.com/charts. Use when you've generated an HTML visualization during analysis and want to share it via the charts index page. Handles copying the file, registering metadata, and regenerating the index.
---

# Publish Chart

Publish an HTML visualization to the charts page at `www.ksgabrieltan.com/charts`.

## Arguments

The skill is invoked as:
```
/publish-chart <file> --name "<title>" [--desc "<description>"] [--issue "<url>"]
```

- `<file>` — path to the HTML chart file (required)
- `--name` — display name for the chart (required)
- `--desc` — short description of what the chart shows (optional)
- `--issue` — GitHub issue URL the chart is associated with (optional)

## Steps

### 1. Copy the chart file into the charts directory

```bash
cp "<file>" ~/ksgabrieltan-site/charts/
```

If the file is already in `~/ksgabrieltan-site/charts/`, skip this step.

### 2. Register the chart and regenerate the index

```bash
python3 ~/ksgabrieltan-site/charts/generate-index.py \
  --add "<filename>" \
  --name "<title>" \
  --desc "<description>" \
  --issue "<issue_url>"
```

`<filename>` is the basename only (e.g. `my-chart.html`), not the full path.

Omit `--issue` if no issue URL was provided.

### 3. Verify

```bash
curl -sI http://localhost:8100/charts/<filename>
```

Confirm it returns HTTP 200.

### 4. Report

Print the public URL:
```
Published: https://www.ksgabrieltan.com/charts/<filename>
```

## Notes

- The charts directory is `/home/ubuntu/ksgabrieltan-site/charts/`
- `manifest.json` tracks all chart metadata — don't edit it by hand
- `index.html` is auto-generated — don't edit it by hand
- The site is served by `ksgabrieltan-site.service` on port 8100 via a Cloudflare tunnel
