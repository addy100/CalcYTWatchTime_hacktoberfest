# CalcYTWatchTime

This repository contains Python scripts that calculate your total watch time from a YouTube watch history JSON file exported from YouTube Takeout. The scripts leverage the YouTube Data API v3 to retrieve video durations and provide comprehensive time breakdowns and statistics.

## Features

- **Interactive Setup:** User-friendly guided setup with prompts for all configuration options
- **User Support:** No command-line knowledge required - just run the script and follow the prompts
- **Comprehensive Watch Time Analysis:** Get detailed breakdowns of your YouTube viewing habits in seconds, minutes, hours, days, months, and years
- **Smart Video Handling:** Gracefully handles deleted videos, private videos, and unavailable content
- **Flexible Date Filtering:** Set custom start and end dates to analyze specific time periods
- **Automatic File Detection:** Automatically finds YouTube history files in your directory
- **Duration Capping:** Configure maximum video duration limits to handle outliers (livestreams, very long videos)
- **Rate Limiting:** Built-in API rate limiting to respect YouTube's usage quotas
- **Progress Tracking:** Real-time progress bars during video processing
- **Robust Error Handling:** Comprehensive error handling for API requests, network issues, and malformed data
- **Multiple Output Formats:** Console output and optional JSON export for further analysis
- **Environment Variable Support:** Secure API key management through environment variables
- **Batch Processing:** Configurable batch sizes for optimal API usage
- **Command-Line Interface:** Full command-line support for advanced users
- **Detailed Statistics:** Track processed, deleted, and skipped video counts

## Requirements

### Python Dependencies
```bash
pip install requests tqdm
```

### API Setup
You'll need a YouTube Data API v3 key:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Create credentials (API key)
5. Copy your API key for use with the script

## Installation

1. Clone this repository:
```bash
git clone https://github.com/zxkeyy/CalcYTWatchTime.git
cd CalcYTWatchTime
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download your YouTube watch history:
   - Go to [Google Takeout](https://takeout.google.com/)
   - Select "YouTube and YouTube Music"
   - Click "Multiple formats" and set history format to **JSON**
   - Download and extract the `watch-history.json` file

## Usage

### Basic Usage
```bash
# Set API key as environment variable (recommended)
export YOUTUBE_API_KEY="your_api_key_here"
python CalcYTWatchTime.py

# Or provide API key directly
python CalcYTWatchTime.py -k "your_api_key_here"
```

### Advanced Usage
```bash
# Custom parameters
python CalcYTWatchTime.py \
  -k "your_api_key" \
  -f "path/to/watch-history.json" \
  -s "2020-01-01T00:00:00Z" \
  -d 7200 \
  -b 25 \
  -o results.json \
  -v
```

### Command Line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--api-key` | `-k` | YouTube Data API v3 key | Environment variable |
| `--history-file` | `-f` | Path to watch history JSON file | `watch-history.json` |
| `--start-date` | `-s` | Start date in ISO 8601 format | `2000-01-01T00:00:00Z` |
| `--max-duration` | `-d` | Maximum video duration in seconds | `5400` (1.5 hours) |
| `--batch-size` | `-b` | Videos per API request | `50` |
| `--output` | `-o` | Save results to JSON file | None |
| `--verbose` | `-v` | Enable detailed logging | False |

### Example Output

```
==================================================
YOUTUBE WATCH TIME STATISTICS
==================================================

Total Watch Time:
  Formatted: 45 days, 12:34:56
  Years:     0.12
  Months:    1.48
  Days:      45.52
  Hours:     1092.58
  Minutes:   65554.93
  Seconds:   3933296

Video Statistics:
  Total videos in history: 15847
  Deleted videos:          342
  Skipped videos:          128
  Processed videos:        15377

Results saved to: results.json
```

## File Structure

```
CalcYTWatchTime/
├── CalcYTWatchTime.py             # Main enhanced script
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── examples/
    └── sample_output.json         # Example output format
```

## Privacy & Security

- **API Key Security:** Use environment variables to store your API key securely
- **Data Processing:** All processing is done locally on your machine
- **No Data Storage:** The script doesn't store or transmit your watch history data anywhere
- **Rate Limiting:** Built-in rate limiting respects YouTube's API quotas

## Limitations & Considerations

- **API Quotas:** YouTube Data API has daily quota limits (10,000 units by default)
- **Deleted Videos:** Videos removed from YouTube cannot be processed and are counted separately
- **Private Videos:** Private or unlisted videos may not be accessible via the API
- **Historical Data:** The script only processes videos that are still available on YouTube
- **Rate Limits:** Large watch histories may take considerable time to process due to API rate limiting

## Troubleshooting

### Common Issues

**"API key is required" error:**
- Ensure your API key is set via environment variable or command line argument
- Verify your API key is valid and has YouTube Data API v3 enabled

**"History file not found" error:**
- Verify the path to your `watch-history.json` file
- Ensure you exported your data in JSON format from Google Takeout

**API quota exceeded:**
- Wait for your quota to reset (usually 24 hours)
- Consider processing smaller date ranges using the `--start-date` parameter

**Slow processing:**
- Adjust `--batch-size` parameter (lower values = slower but more reliable)
- Use `--verbose` flag to monitor progress and identify issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Disclaimer

This script relies on the YouTube Data API, which may have usage limits, costs, or change behavior in the future. Use responsibly and in accordance with YouTube's Terms of Service and API usage policies.