import sys
import requests
import json
import datetime
import argparse
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from tqdm import tqdm
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TimeConstants:
    SECONDS_IN_YEAR = 31536000
    SECONDS_IN_MONTH = 2592000
    SECONDS_IN_DAY = 86400
    SECONDS_IN_HOUR = 3600
    SECONDS_IN_MINUTE = 60

@dataclass
class Config:
    api_key: str
    history_file: Path
    start_date: str = "2000-01-01T00:00:00Z"
    end_date: str = ""
    max_duration: int = 5400
    batch_size: int = 50
    api_url: str = "https://www.googleapis.com/youtube/v3/videos"
    rate_limit_delay: float = 0.1  # Delay between API calls

@dataclass
class WatchTimeStats:
    total_seconds: float
    total_videos: int
    deleted_videos: int
    skipped_videos: int

    def format_time(self) -> Dict[str, float]:
        return {
            "seconds": self.total_seconds,
            "minutes": self.total_seconds / TimeConstants.SECONDS_IN_MINUTE,
            "hours": self.total_seconds / TimeConstants.SECONDS_IN_HOUR,
            "days": self.total_seconds / TimeConstants.SECONDS_IN_DAY,
            "months": self.total_seconds / TimeConstants.SECONDS_IN_MONTH,
            "years": self.total_seconds / TimeConstants.SECONDS_IN_YEAR,
            "formatted": str(datetime.timedelta(seconds=int(self.total_seconds)))
        }

class YouTubeWatchTimeCalculator:
    def __init__(self, config: Config):
        self.config = config
        self._validate_config()
        self.last_api_call = 0

    def _validate_config(self) -> None:
        """Validate the configuration parameters."""
        if not self.config.api_key or self.config.api_key == "YOUR_API_KEY":
            raise ValueError("Valid YouTube API key is required")
        
        if not self.config.history_file.exists():
            raise FileNotFoundError(f"History file not found: {self.config.history_file}")
        
        try:
            datetime.datetime.fromisoformat(self.config.start_date.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid start date format. Use ISO 8601 format (e.g., '2000-01-01T00:00:00Z')")

    @staticmethod
    def parse_iso_duration(duration: str) -> int:
        """
        Convert ISO 8601 duration to seconds.
        Example: PT1H2M10S -> 3730 seconds (1 hour + 2 minutes + 10 seconds)
        """
        if not duration or not duration.startswith('P'):
            logger.warning(f"Invalid duration format: {duration}")
            return 0

        # Initialize duration components
        hours = 0
        minutes = 0
        seconds = 0

        # Remove 'P' prefix and split by 'T'
        time_part = duration.split('T')[-1] if 'T' in duration else ''

        # Parse time components
        current_number = ''
        for char in time_part:
            if char.isdigit():
                current_number += char
            elif char == 'H':
                hours = int(current_number) if current_number else 0
                current_number = ''
            elif char == 'M':
                minutes = int(current_number) if current_number else 0
                current_number = ''
            elif char == 'S':
                seconds = int(current_number) if current_number else 0
                current_number = ''

        # Calculate total seconds
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        return total_seconds

    def _rate_limit(self) -> None:
        """Simple rate limiting to avoid hitting API limits."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        if time_since_last_call < self.config.rate_limit_delay:
            time.sleep(self.config.rate_limit_delay - time_since_last_call)
        self.last_api_call = time.time()

    def _fetch_video_durations(self, video_ids: List[str]) -> List[int]:
        """Fetch video durations from YouTube API with rate limiting."""
        self._rate_limit()
        
        params = {
            "part": "contentDetails",
            "id": ",".join(video_ids),
            "key": self.config.api_key
        }

        try:
            response = requests.get(self.config.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"API Error: {data['error']['message']}")
                return []

            durations = []
            for video in data.get('items', []):
                try:
                    duration = self.parse_iso_duration(video['contentDetails']['duration'])
                    durations.append(min(duration, self.config.max_duration))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Could not parse duration for video: {e}")
                    durations.append(0)
            
            return durations

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return []

    def _extract_video_ids(self, watch_history: List[Dict]) -> tuple[List[str], int, int]:
        """Extract valid video IDs from watch history."""
        video_ids = []
        deleted_count = 0
        skipped_count = 0

        for entry in watch_history:
            if 'titleUrl' not in entry:
                deleted_count += 1
                continue
            
            entry_time = entry.get("time", "")
            
            # Check start date
            if entry_time < self.config.start_date:
                skipped_count += 1
                continue
            
            # Check end date if specified
            if self.config.end_date and entry_time > self.config.end_date:
                skipped_count += 1
                continue

            try:
                video_url = entry['titleUrl']
                video_id = video_url.split('=')[-1]
                if video_id and len(video_id) == 11:  # YouTube video IDs are 11 characters
                    video_ids.append(video_id)
                else:
                    logger.warning(f"Invalid video ID extracted: {video_id}")
            except (KeyError, IndexError):
                logger.warning(f"Could not extract video ID from entry: {entry}")
                continue

        return video_ids, deleted_count, skipped_count

    def calculate_watch_time(self) -> WatchTimeStats:
        """Calculate total watch time from YouTube history."""
        try:
            with open(self.config.history_file, 'r', encoding='utf-8') as file:
                watch_history = json.load(file)
            logger.info(f"Loaded {len(watch_history)} entries from history file")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in watch history file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading history file: {e}")
            raise

        video_ids, deleted_count, skipped_count = self._extract_video_ids(watch_history)
        logger.info(f"Extracted {len(video_ids)} valid video IDs")
        logger.info(f"Deleted videos: {deleted_count}, Skipped videos: {skipped_count}")

        if not video_ids:
            logger.warning("No valid video IDs found")
            return WatchTimeStats(0, len(watch_history), deleted_count, skipped_count)

        total_duration = 0
        processed_videos = 0
        
        for i in tqdm(range(0, len(video_ids), self.config.batch_size), 
                     desc="Processing videos", unit="batch"):
            batch = video_ids[i:i + self.config.batch_size]
            durations = self._fetch_video_durations(batch)
            total_duration += sum(durations)
            processed_videos += len(durations)

        logger.info(f"Processed {processed_videos} videos successfully")
        return WatchTimeStats(
            total_seconds=total_duration,
            total_videos=len(watch_history),
            deleted_videos=deleted_count,
            skipped_videos=skipped_count
        )

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Calculate total watch time from YouTube watch history",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "-k", "--api-key", 
        type=str, 
        default=os.getenv('YOUTUBE_API_KEY', ''),
        help="YouTube Data API V3 key (or set YOUTUBE_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "-f", "--history-file", 
        type=str, 
        default="",
        help="Path to the watch history JSON file"
    )
    
    parser.add_argument(
        "-s", "--start-date", 
        type=str, 
        default="",
        help="Start date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)"
    )
    
    parser.add_argument(
        "-e", "--end-date", 
        type=str, 
        default="",
        help="End date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ) - optional"
    )
    
    parser.add_argument(
        "-d", "--max-duration", 
        type=int, 
        default=0,
        help="Maximum duration of a video in seconds (caps long videos)"
    )
    
    parser.add_argument(
        "-b", "--batch-size", 
        type=int, 
        default=0,
        help="Number of videos to process per API request"
    )
    
    parser.add_argument(
        "-o", "--output", 
        type=str,
        default="",
        help="Save results to JSON file (optional)"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--no-interactive", 
        action="store_true",
        help="Disable interactive prompts (use defaults for missing arguments)"
    )
    
    return parser

def find_history_files() -> List[str]:
    """Find potential YouTube history files in current directory."""
    possible_files = []
    common_names = [
        'watch-history.json',
        'watch_history.json', 
        'youtube-history.json',
        'youtube_history.json',
        'takeout-history.json',
        'my-watch-history.json'
    ]
    
    # Check for exact matches first
    for name in common_names:
        if Path(name).exists():
            possible_files.append(name)
    
    # Look for any JSON files that might be history files
    for file_path in Path('.').glob('*.json'):
        filename = file_path.name.lower()
        if 'history' in filename and filename not in possible_files:
            possible_files.append(str(file_path))
    
    return possible_files

def validate_date_format(date_string: str) -> bool:
    """Validate date string format."""
    if not date_string:
        return True  # Empty string is valid (will use default)
    
    try:
        # Try parsing as YYYY-MM-DD first
        if len(date_string) == 10 and date_string.count('-') == 2:
            datetime.datetime.strptime(date_string, '%Y-%m-%d')
            return True
        
        # Try parsing as ISO format
        datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def format_date_for_api(date_string: str) -> str:
    """Convert user-friendly date to API format."""
    if not date_string:
        return ""
    
    # If it's already in ISO format, return as-is
    if 'T' in date_string:
        return date_string
    
    # Convert YYYY-MM-DD to ISO format
    if len(date_string) == 10:
        return f"{date_string}T00:00:00Z"
    
    return date_string

def interactive_setup(args) -> dict:
    """Interactively prompt user for missing configuration."""
    print("CalcYTWatchTime - YouTube Watch Time Calculator")
    print("=" * 40)
    print("Let's set up your analysis parameters!\n")
    
    config = {}
    
    # API Key
    if not args.api_key:
        print("First, you'll need a YouTube Data API v3 key.")
        print("   Get one at: https://console.cloud.google.com/")
        print("   (Enable YouTube Data API v3 and create an API key)")
        api_key = input("\nPlease enter your YouTube Data API v3 key: ").strip()
        if not api_key:
            print("API key is required to proceed.")
            sys.exit(1)
        config['api_key'] = api_key
    else:
        config['api_key'] = args.api_key
    
    # History File
    if not args.history_file:
        print("\nNow please provide the path to your YouTube watch history file.")
        print("   (Download from Google Takeout → YouTube → watch-history.json)")
        
        found_files = find_history_files()
        
        if found_files:
            print(f"\n   Found {len(found_files)} potential history file(s) in the current directory:")
            for i, file in enumerate(found_files, 1):
                print(f"   {i}. {file}")
            
            print(f"   {len(found_files) + 1}. Enter custom path")
            
            while True:
                try:
                    choice = input(f"\nChoose an option (1-{len(found_files) + 1}): ").strip()
                    if not choice:
                        continue
                    
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(found_files):
                        config['history_file'] = found_files[choice_num - 1]
                        break
                    elif choice_num == len(found_files) + 1:
                        custom_path = input("Enter path to your history file: ").strip()
                        if custom_path and Path(custom_path).exists():
                            config['history_file'] = custom_path
                            break
                        else:
                            print("File not found. Please try again.")
                    else:
                        print(f"Please enter a number between 1 and {len(found_files) + 1}")
                except ValueError:
                    print("Please enter a valid number")
        else:
            history_file = input("Enter path to your watch-history.json file: ").strip()
            if not history_file or not Path(history_file).exists():
                print("History file not found.")
                sys.exit(1)
            config['history_file'] = history_file
    else:
        config['history_file'] = args.history_file
    
    # Start Date
    if not args.start_date:
        print("\nAdd a date range for counting your watch time?")
        start_date = input("Enter start date (YYYY-MM-DD) or press Enter to start from the beginning: ").strip()

        if start_date:
            if not validate_date_format(start_date):
                print("Invalid date format. Using default (all time).")
                start_date = "2000-01-01T00:00:00Z"
            else:
                start_date = format_date_for_api(start_date)
        else:
            start_date = "2000-01-01T00:00:00Z"
        
        config['start_date'] = start_date
    else:
        config['start_date'] = args.start_date
    
    # End Date
    if not args.end_date:
        end_date = input("Enter end date (YYYY-MM-DD) or press Enter to use today's date: ").strip()

        if end_date:
            if not validate_date_format(end_date):
                print("Invalid date format. Skipping end date filter.")
                end_date = ""
            else:
                end_date = format_date_for_api(end_date)
        
        config['end_date'] = end_date
    else:
        config['end_date'] = args.end_date
    
    # Max Duration
    if args.max_duration == 0:
        print("\nSetting a maximum video duration helps focus on shorter content and prevents livestreams from skewing results.")
        while True:
            max_dur_input = input("Enter maximum video duration in seconds or press Enter for default (default: 5400 = 1.5 hours): ").strip()

            if not max_dur_input:
                config['max_duration'] = 5400
                break
            
            try:
                max_duration = int(max_dur_input)
                if max_duration < 0:
                    print("Duration must be positive. Try again.")
                    continue
                config['max_duration'] = max_duration if max_duration > 0 else 999999
                break
            except ValueError:
                print("Please enter a valid number.")
    else:
        config['max_duration'] = args.max_duration
    
    # Batch Size
    if args.batch_size == 0:
        print("\nAPI batch size affects processing speed vs reliability.")
        print("   Larger = faster but more likely to hit rate limits")
        while True:
            batch_input = input("Enter batch size or press Enter for default (default: 50, range: 1-50): ").strip()
            
            if not batch_input:
                config['batch_size'] = 50
                break
            
            try:
                batch_size = int(batch_input)
                if 1 <= batch_size <= 50:
                    config['batch_size'] = batch_size
                    break
                else:
                    print("Batch size must be between 1 and 50.")
            except ValueError:
                print("Please enter a valid number.")
    else:
        config['batch_size'] = args.batch_size
    
    # Output File
    if not args.output:
        print("\nWould you like to save the results to a file?")
        save_choice = input("Enter filename (e.g., 'my_results.json') or press Enter to skip: ").strip()
        config['output'] = save_choice if save_choice else None
    else:
        config['output'] = args.output if args.output else None
    
    print("\nConfiguration complete! Starting analysis...\n")
    return config

# The print_results function was incorrectly indented, making it inaccessible.
# It should be a top-level function like the others.
def print_results(stats: WatchTimeStats) -> None:
    """Print formatted results to console."""
    time_stats = stats.format_time()
    
    print("\n" + "="*50)
    print("YOUTUBE WATCH TIME STATISTICS")
    print("="*50)
    
    print(f"\nTotal Watch Time:")
    print(f"   Formatted: {time_stats['formatted']}")
    print(f"   Years:     {time_stats['years']:.2f}")
    print(f"   Months:    {time_stats['months']:.2f}")
    print(f"   Days:      {time_stats['days']:.2f}")
    print(f"   Hours:     {time_stats['hours']:.2f}")
    print(f"   Minutes:   {time_stats['minutes']:.2f}")
    print(f"   Seconds:   {time_stats['seconds']:.0f}")
    
    print(f"\nVideo Statistics:")
    print(f"   Total videos in history: {stats.total_videos}")
    print(f"   Deleted videos:          {stats.deleted_videos}")
    print(f"   Skipped videos:          {stats.skipped_videos}")
    print(f"   Processed videos:        {stats.total_videos - stats.deleted_videos - stats.skipped_videos}")

def save_results(stats: WatchTimeStats, config: Config, output_file: str) -> None:
    """Save results to JSON file."""
    time_stats = stats.format_time()
    
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "time_stats": time_stats,
        "video_stats": {
            "total_videos": stats.total_videos,
            "deleted_videos": stats.deleted_videos,
            "skipped_videos": stats.skipped_videos,
            "processed_videos": stats.total_videos - stats.deleted_videos - stats.skipped_videos
        },
        "parameters": {
            "start_date": config.start_date,
            "end_date": config.end_date,
            "max_duration": config.max_duration,
            "batch_size": config.batch_size,
            "history_file": str(config.history_file)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")

def main():
    """Main function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Interactive setup if not in no-interactive mode
    if not args.no_interactive:
        config_dict = interactive_setup(args)
    else:
        # Use provided arguments or defaults
        api_key = args.api_key
        if not api_key:
            print("Error: YouTube API key is required!")
            print("Either:")
            print("   1. Use -k/--api-key argument")
            print("   2. Set YOUTUBE_API_KEY environment variable")
            print("   3. Run without --no-interactive for guided setup")
            print("   4. Get a key from: https://console.developers.google.com/")
            sys.exit(1)
        
        config_dict = {
            'api_key': api_key,
            'history_file': args.history_file or "watch-history.json",
            'start_date': format_date_for_api(args.start_date or "2000-01-01T00:00:00Z"), # Apply formatting to ensure consistency
            'end_date': format_date_for_api(args.end_date or ""), # An empty string if no end date
            'max_duration': args.max_duration or 5400,
            'batch_size': args.batch_size or 50,
            'output': args.output
        }
    
    try:
        # Create configuration
        config = Config(
            api_key=config_dict['api_key'],
            history_file=Path(config_dict['history_file']),
            start_date=config_dict['start_date'],
            end_date=config_dict['end_date'],
            max_duration=config_dict['max_duration'],
            batch_size=config_dict['batch_size']
        )
        
        # Calculate watch time
        if not args.no_interactive:
            print(f"Processing YouTube watch history...")
        else:
            print(f"Processing YouTube watch history from: {config.history_file}")
            print(f"Start date: {config.start_date}")
            if config.end_date:
                print(f"End date: {config.end_date}")
            print(f"Max video duration: {config.max_duration} seconds")
        
        calculator = YouTubeWatchTimeCalculator(config)
        stats = calculator.calculate_watch_time()
        
        # Display results
        print_results(stats)  # This call will now work
        
        # Save results if requested
        output_file = config_dict.get('output')
        if output_file:
            save_results(stats, config, output_file)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if not args.no_interactive:
            print(f"\nError: {str(e)}")
            print("💡 Try running with --verbose for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()