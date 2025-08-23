#!/usr/bin/env python3
"""
Analyze the quality of title extractions and generate a report.
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TitleQualityAnalyzer:
    """Analyze the quality of title extractions."""
    
    def __init__(self, log_dir: str = "logs/title_extraction"):
        """
        Initialize the analyzer with the log directory.
        
        Args:
            log_dir: Directory containing the title extraction logs
        """
        self.log_dir = Path(log_dir)
        self.df = None
        
    def load_data(self, days: int = 7) -> None:
        """
        Load title extraction data from log files.
        
        Args:
            days: Number of days of data to load
        """
        data = []
        
        # Load data from each log file
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.log_dir / f"extractions_{date}.jsonl"
            
            if not log_file.exists():
                logger.warning(f"Log file not found: {log_file}")
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning(f"Error parsing JSON in {log_file}: {e}")
            except Exception as e:
                logger.error(f"Error reading {log_file}: {e}")
        
        if not data:
            logger.error("No data found in log files")
            return
            
        self.df = pd.DataFrame(data)
        logger.info(f"Loaded {len(self.df)} title extractions")
    
    def generate_report(self, output_dir: str = "reports") -> None:
        """
        Generate a quality report with visualizations.
        
        Args:
            output_dir: Directory to save the report
        """
        if self.df is None or self.df.empty:
            logger.error("No data available for report generation")
            return
            
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Basic statistics
        total_extractions = len(self.df)
        avg_confidence = self.df['confidence'].mean()
        has_feedback = self.df['has_feedback'].sum() if 'has_feedback' in self.df.columns else 0
        
        # Create report
        report = {
            'summary': {
                'total_extractions': total_extractions,
                'avg_confidence': round(avg_confidence, 4),
                'has_feedback': int(has_feedback),
                'feedback_ratio': round(has_feedback / total_extractions, 4) if total_extractions > 0 else 0,
                'start_date': self.df['timestamp'].min(),
                'end_date': self.df['timestamp'].max()
            },
            'confidence_distribution': self._get_confidence_distribution(),
            'common_patterns': self._analyze_common_patterns(),
            'common_errors': self._identify_common_errors()
        }
        
        # Save report as JSON
        report_path = output_dir / f"title_quality_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate visualizations
        self._generate_visualizations(output_dir)
        
        logger.info(f"Report generated: {report_path}")
        return report
    
    def _get_confidence_distribution(self) -> dict:
        """Calculate confidence score distribution."""
        if 'confidence' not in self.df.columns:
            return {}
            
        bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
        labels = ['0-0.3', '0.3-0.5', '0.5-0.7', '0.7-0.9', '0.9-1.0']
        
        if self.df.empty:
            return {label: 0 for label in labels}
            
        distribution = self.df['confidence'].value_counts(
            bins=bins,
            sort=False
        ).to_dict()
        
        # Convert to percentage
        total = len(self.df)
        return {
            label: round((count / total) * 100, 2)
            for label, count in zip(labels, distribution.values())
        }
    
    def _analyze_common_patterns(self, top_n: int = 10) -> list:
        """Analyze common patterns in extracted titles."""
        if 'extracted_title' not in self.df.columns:
            return []
            
        # Get most common starting words/phrases
        start_phrases = defaultdict(int)
        
        for title in self.df['extracted_title'].dropna():
            # Get first 1-3 words
            words = str(title).strip().split()
            for i in range(1, min(4, len(words) + 1)):
                phrase = ' '.join(words[:i])
                start_phrases[phrase] += 1
        
        return sorted(start_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def _identify_common_errors(self) -> list:
        """Identify common error patterns in low-confidence extractions."""
        if 'extracted_title' not in self.df.columns or 'confidence' not in self.df.columns:
            return []
            
        # Get low-confidence extractions
        low_conf = self.df[self.df['confidence'] < 0.5]
        
        if low_conf.empty:
            return []
        
        # Common issues to check for
        issues = {
            'too_short': lambda x: len(str(x)) < 5,
            'too_long': lambda x: len(str(x)) > 200,
            'no_uppercase': lambda x: str(x).strip() == str(x).lower(),
            'contains_digits': lambda x: bool(re.search(r'\d', str(x))),
            'contains_special_chars': lambda x: bool(re.search(r'[^\w\s]', str(x)))
        }
        
        error_counts = {}
        for issue_name, check in issues.items():
            count = low_conf['extracted_title'].apply(check).sum()
            if count > 0:
                error_counts[issue_name] = count
        
        return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
    
    def _generate_visualizations(self, output_dir: Path) -> None:
        """Generate visualizations for the report."""
        if self.df is None or self.df.empty:
            return
            
        try:
            # Confidence distribution plot
            plt.figure(figsize=(10, 6))
            self.df['confidence'].plot.hist(bins=20, alpha=0.7)
            plt.title('Title Extraction Confidence Distribution')
            plt.xlabel('Confidence Score')
            plt.ylabel('Count')
            plt.savefig(output_dir / 'confidence_distribution.png')
            plt.close()
            
            # Title length distribution
            if 'extracted_title' in self.df.columns:
                plt.figure(figsize=(10, 6))
                self.df['extracted_title'].str.len().plot.hist(bins=30, alpha=0.7)
                plt.title('Title Length Distribution')
                plt.xlabel('Title Length (characters)')
                plt.ylabel('Count')
                plt.savefig(output_dir / 'title_length_distribution.png')
                plt.close()
                
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")


def main():
    """Main function to run the analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze title extraction quality')
    parser.add_argument('--days', type=int, default=7, help='Number of days of data to analyze')
    parser.add_argument('--log-dir', type=str, default='logs/title_extraction', 
                       help='Directory containing title extraction logs')
    parser.add_argument('--output-dir', type=str, default='reports',
                       help='Directory to save the report')
    
    args = parser.parse_args()
    
    analyzer = TitleQualityAnalyzer(log_dir=args.log_dir)
    analyzer.load_data(days=args.days)
    report = analyzer.generate_report(output_dir=args.output_dir)
    
    if report:
        print("\n=== Title Extraction Quality Report ===")
        print(f"Total extractions: {report['summary']['total_extractions']}")
        print(f"Average confidence: {report['summary']['avg_confidence']:.2f}")
        print(f"Feedback provided: {report['summary']['has_feedback']} "
              f"({report['summary']['feedback_ratio']*100:.1f}%)")
        
        print("\nConfidence Distribution:")
        for range_, pct in report['confidence_distribution'].items():
            print(f"  {range_}: {pct:.1f}%")
            
        if report['common_errors']:
            print("\nCommon Issues in Low-Confidence Extractions:")
            for issue, count in report['common_errors']:
                print(f"  {issue}: {count} occurrences")


if __name__ == "__main__":
    main()
