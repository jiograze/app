"""
Turkish BERT model integration for legal text analysis.
Uses dbmdz/bert-base-turkish-cased model from Hugging Face.
"""
import logging
from typing import List, Dict, Any, Optional, Union
import torch
from transformers import AutoTokenizer, AutoModel, pipeline

# Configure logging
logger = logging.getLogger(__name__)

class TurkishBERTAnalyzer:
    """
    A wrapper around the Turkish BERT model for text analysis tasks.
    """
    
    def __init__(self, model_name: str = "dbmdz/bert-base-turkish-cased", 
                 device: Optional[str] = None):
        """
        Initialize the Turkish BERT analyzer.
        
        Args:
            model_name: Name or path of the BERT model (default: dbmdz/bert-base-turkish-cased)
            device: Device to run the model on ('cuda', 'mps', 'cpu'). Auto-detects if None.
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.tokenizer = None
        self.model = None
        self.nlp = None
        
        self._load_model()
    
    def _get_device(self, device: Optional[str] = None) -> str:
        """Determine the best available device if not specified."""
        if device is None:
            if torch.cuda.is_available():
                return 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'
            else:
                return 'cpu'
        return device
    
    def _load_model(self):
        """Load the BERT model and tokenizer."""
        try:
            logger.info(f"Loading Turkish BERT model: {self.model_name}")
            logger.info(f"Using device: {self.device}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            
            # Put model in evaluation mode
            self.model.eval()
            
            logger.info("Turkish BERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading Turkish BERT model: {str(e)}")
            raise
    
    def get_embeddings(self, texts: Union[str, List[str]], 
                      max_length: int = 512) -> torch.Tensor:
        """
        Get BERT embeddings for the input text(s).
        
        Args:
            texts: Single text or list of texts to get embeddings for
            max_length: Maximum sequence length (truncate or pad to this length)
            
        Returns:
            For a single text: 1D tensor of shape (hidden_size,)
            For multiple texts: 2D tensor of shape (num_texts, hidden_size)
        """
        if not self.tokenizer or not self.model:
            raise RuntimeError("Model or tokenizer not loaded. Call _load_model() first.")
        
        try:
            # Convert single text to list for batch processing
            is_single = isinstance(texts, str)
            if is_single:
                texts = [texts]
            
            # Tokenize the input texts
            encoded_input = self.tokenizer(
                texts,
                padding='max_length',
                truncation=True,
                max_length=max_length,
                return_tensors='pt'
            )
            
            # Move tensors to the appropriate device
            input_ids = encoded_input['input_ids'].to(self.device)
            attention_mask = encoded_input['attention_mask'].to(self.device)
            
            # Get model outputs
            with torch.no_grad():
                model_outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    return_dict=True
                )
            
            # Get the [CLS] token embeddings (first token of each sequence)
            # Shape: (batch_size, hidden_size)
            cls_embeddings = model_outputs.last_hidden_state[:, 0, :]
            
            # For single input, return as 1D tensor
            if is_single:
                return cls_embeddings[0].cpu()
                
            return cls_embeddings.cpu()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
            raise
    
    def get_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate the cosine similarity between two texts using BERT embeddings.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Get embeddings for both texts
            emb1 = self.get_embeddings(text1)
            emb2 = self.get_embeddings(text2)
            
            # Calculate cosine similarity
            cos = torch.nn.CosineSimilarity(dim=0)
            similarity = cos(emb1, emb2).item()
            
            # Normalize to [0, 1] range
            return (similarity + 1) / 2
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            raise
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Perform sentiment analysis on the input text (positive/negative/neutral).
        
        Note: This is a simple implementation using the [CLS] token embedding
        and may not be as accurate as a fine-tuned sentiment analysis model.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        try:
            # Get the [CLS] token embedding
            embedding = self.get_embeddings(text)
            
            # Simple heuristic: use the first dimension as a sentiment indicator
            # This is a very basic approach - in practice, you'd want to fine-tune
            # a classifier on top of BERT for better results
            score = embedding[0].item()  # Using first dimension as a simple heuristic
            
            # Convert to probabilities (this is a simplification)
            positive = (score + 1) / 2
            negative = 1 - positive
            
            return {
                'positive': float(positive),
                'negative': float(negative),
                'score': float(score)  # Raw score between -1 and 1
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            raise

# Singleton instance
_bert_analyzer = None

def get_bert_analyzer() -> TurkishBERTAnalyzer:
    """Get or create a singleton instance of the Turkish BERT analyzer."""
    global _bert_analyzer
    if _bert_analyzer is None:
        _bert_analyzer = TurkishBERTAnalyzer()
    return _bert_analyzer
