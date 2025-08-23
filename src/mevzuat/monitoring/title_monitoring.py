"""
Title extraction monitoring and quality metrics
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import os
from pathlib import Path
import pandas as pd
from mevzuat.core.bert_title_analyzer import BERTTitleAnalyzer

logger = logging.getLogger(__name__)

class TitleExtractionMonitor:
    """Monitors and tracks the quality of title extractions"""
    
    def __init__(self, log_dir: str = "logs/title_extraction"):
        """
        Initialize the title extraction monitor
        
        Args:
            log_dir: Directory to store monitoring logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = BERTTitleAnalyzer()
        
    def log_extraction(
        self, 
        document_id: str,
        extracted_title: str,
        full_text: str,
        confidence: float,
        user_feedback: Optional[bool] = None
    ) -> None:
        """
        Log a title extraction event with metadata
        
        Args:
            document_id: Unique identifier for the document
            extracted_title: The title that was extracted
            full_text: The full text of the document
            confidence: Confidence score of the extraction (0-1)
            user_feedback: Optional user feedback (True if correct, False if incorrect)
        """
        try:
            # Create log entry
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": document_id,
                "extracted_title": extracted_title,
                "title_length": len(extracted_title),
                "confidence": confidence,
                "user_feedback": user_feedback,
                "has_feedback": user_feedback is not None,
                "text_preview": full_text[:500]  # Store first 500 chars for analysis
            }
            
            # Save to daily log file
            today = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"extractions_{today}.jsonl"
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to log title extraction: {str(e)}")
    
    def get_metrics(self, days: int = 7) -> Dict:
        """
        Calculate metrics for title extractions
        
        Args:
            days: Number of days to include in metrics
            
        Returns:
            Dictionary containing metrics
        """
        try:
            # Load recent log files
            dfs = []
            for i in range(days):
                date = (datetime.utcnow() - pd.Timedelta(days=i)).strftime("%Y-%m-%d")
                log_file = self.log_dir / f"extractions_{date}.jsonl"
                
                if log_file.exists():
                    try:
                        df = pd.read_json(log_file, lines=True)
                        dfs.append(df)
                    except Exception as e:
                        logger.warning(f"Error reading log file {log_file}: {str(e)}")
            
            if not dfs:
                return {"total_extractions": 0, "error": "No data available"}
                
            df = pd.concat(dfs, ignore_index=True)
            
            # Calculate metrics
            metrics = {
                "total_extractions": len(df),
                "avg_confidence": df["confidence"].mean(),
                "feedback_ratio": df["has_feedback"].mean() if "has_feedback" in df.columns else 0,
                "avg_title_length": df["title_length"].mean(),
                "confidence_distribution": {
                    "0-0.5": ((df["confidence"] <= 0.5).sum() / len(df)) * 100,
                    "0.5-0.7": ((df["confidence"] > 0.5) & (df["confidence"] <= 0.7)).sum() / len(df) * 100,
                    "0.7-0.9": ((df["confidence"] > 0.7) & (df["confidence"] <= 0.9)).sum() / len(df) * 100,
                    "0.9-1.0": (df["confidence"] > 0.9).sum() / len(df) * 100,
                }
            }
            
            # Add accuracy if we have feedback
            if "user_feedback" in df.columns and df["has_feedback"].sum() > 0:
                feedback_df = df[df["has_feedback"]]
                metrics["accuracy"] = feedback_df["user_feedback"].mean() * 100
                metrics["total_feedback"] = int(feedback_df["has_feedback"].sum())
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {"error": str(e)}
    
    def get_low_confidence_titles(self, threshold: float = 0.7, limit: int = 100) -> List[Dict]:
        """
        Get titles with low confidence scores for analysis
        
        Args:
            threshold: Confidence threshold below which to return titles
            limit: Maximum number of titles to return
            
        Returns:
            List of dictionaries containing title information
        """
        try:
            # Load recent log files (last 7 days)
            dfs = []
            for i in range(7):
                date = (datetime.utcnow() - pd.Timedelta(days=i)).strftime("%Y-%m-%d")
                log_file = self.log_dir / f"extractions_{date}.jsonl"
                
                if log_file.exists():
                    try:
                        df = pd.read_json(log_file, lines=True)
                        dfs.append(df)
                    except Exception as e:
                        logger.warning(f"Error reading log file {log_file}: {str(e)}")
            
            if not dfs:
                return []
                
            df = pd.concat(dfs, ignore_index=True)
            
            # Filter low confidence extractions
            low_conf = df[df["confidence"] < threshold].sort_values("confidence")
            
            # Convert to list of dicts
            return low_conf.head(limit).to_dict("records")
            
        except Exception as e:
            logger.error(f"Error getting low confidence titles: {str(e)}")
            return []

# Singleton instance
title_monitor = TitleExtractionMonitor()

# Backward compatibility
TitleMonitoring = TitleExtractionMonitor
