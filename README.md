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

## More contributions enhanced

Technical Documentation: CalcYTWatchTime - A YouTube Watch Time Analysis Tool
The CalcYTWatchTime repository presents a Python-based utility engineered to perform comprehensive quantitative analysis of user watch time derived from a YouTube watch history JSON file, which is typically obtained via Google Takeout. This application leverages the YouTube Data API v3 to dynamically retrieve video duration metadata, enabling the calculation of total consumption time and subsequent statistical reporting.

Key Functional Specifications
The system is designed for robust and flexible execution, featuring both an interactive and a full Command-Line Interface (CLI) mode.

Data Acquisition and Processing: The core function involves parsing the user's local watch-history.json file. It utilizes the YouTube Data API v3 to fetch the true duration for each video entry. Batch processing is implemented, configurable via the --batch-size argument (default: 50 videos), to optimize API usage.

Time Calculation and Reporting: The output provides a comprehensive watch time analysis, presenting the total consumption time across multiple granularities: seconds, minutes, hours, days, months, and years. Example output formatting includes a precise breakdown (e.g., 45 days, 12:34:56).

Statistical Robustness: The tool intelligently handles various data integrity challenges:

Deleted and Unavailable Content: Videos that are no longer accessible (deleted, private, or restricted) are gracefully handled and tallied under specific metrics (Deleted videos, Skipped videos).

Outlier Management: A configurable duration capping mechanism (--max-duration, default: 5400 seconds or 1.5 hours) is provided to filter out excessively long videos, such as livestreams, which could skew results.

Configuration and Security: The application supports flexible configuration via both interactive prompts for novice users and CLI arguments for advanced operation. For secure handling of the mandatory YouTube Data API v3 key, environment variable support (YOUTUBE_API_KEY) is the recommended method.

Operational Resilience: It includes built-in rate limiting to respect YouTube's API quotas and features robust error handling to manage malformed data, network interruptions, and API request failures. Real-time progress tracking is displayed during the video processing phase.
