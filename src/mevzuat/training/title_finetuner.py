"""
Fine-tune BERT model for Turkish legal document title extraction
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm import tqdm

logger = logging.getLogger(__name__)

class TitleDataset(Dataset):
    """Dataset for title classification"""
    
    def __init__(self, data: List[Dict], tokenizer, max_length: int = 128):
        """
        Initialize the dataset
        
        Args:
            data: List of dictionaries with 'text' and 'label' keys
            tokenizer: BERT tokenizer
            max_length: Maximum sequence length
        """
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        item = self.data[idx]
        encoding = self.tokenizer(
            item['text'],
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'label': torch.tensor(item['label'], dtype=torch.long)
        }


def load_legal_dataset(data_dir: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Load and prepare the legal document dataset
    
    Args:
        data_dir: Directory containing the dataset files
        
    Returns:
        Tuple of (train_data, val_data)
    """
    # TODO: Replace with actual dataset loading logic
    # This is a placeholder - you should load your legal document dataset here
    data = []
    
    # Example data format (replace with actual data loading)
    # [
    #     {"text": "TÜRK CEZA KANUNU", "label": 1},
    #     {"text": "BİRİNCİ BÖLÜM Amaç, Kapsam, Tanımlar ve İlkeler", "label": 1},
    #     {"text": "Bu sıradan bir cümledir ve başlık değildir.", "label": 0},
    #     ...
    # ]
    
    # Split into train and validation sets
    train_data, val_data = train_test_split(data, test_size=0.2, random_state=42)
    return train_data, val_data


def train_model(
    model,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    epochs: int = 3,
    learning_rate: float = 2e-5,
    model_dir: str = "models/bert_title_classifier"
) -> None:
    """
    Train the BERT model
    
    Args:
        model: BERT model
        train_loader: Training data loader
        val_loader: Validation data loader
        device: Device to train on (cuda or cpu)
        epochs: Number of training epochs
        learning_rate: Learning rate
        model_dir: Directory to save the trained model
    """
    # Create output directory
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Set up optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=learning_rate)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=total_steps
    )
    
    best_val_loss = float('inf')
    
    # Training loop
    for epoch in range(epochs):
        logger.info(f"Epoch {epoch + 1}/{epochs}")
        
        # Training
        model.train()
        total_train_loss = 0
        
        progress_bar = tqdm(train_loader, desc="Training")
        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)
            
            model.zero_grad()
            
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            
            loss = outputs.loss
            total_train_loss += loss.item()
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            
            optimizer.step()
            scheduler.step()
            
            progress_bar.set_postfix({'loss': loss.item()})
        
        avg_train_loss = total_train_loss / len(train_loader)
        logger.info(f"  Average training loss: {avg_train_loss:.4f}")
        
        # Validation
        model.eval()
        total_val_loss = 0
        total_correct = 0
        total_samples = 0
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)
                
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                total_val_loss += loss.item()
                
                # Calculate accuracy
                _, preds = torch.max(outputs.logits, dim=1)
                total_correct += (preds == labels).sum().item()
                total_samples += labels.size(0)
        
        avg_val_loss = total_val_loss / len(val_loader)
        val_accuracy = total_correct / total_samples
        
        logger.info(f"  Validation Loss: {avg_val_loss:.4f}")
        logger.info(f"  Validation Accuracy: {val_accuracy:.4f}")
        
        # Save the best model
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            model.save_pretrained(model_path)
            logger.info(f"  New best model saved to {model_path}")


def main():
    """Main function for fine-tuning the BERT model"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    config = {
        'model_name': 'dbmdz/bert-base-turkish-cased',
        'max_length': 128,
        'batch_size': 16,
        'learning_rate': 2e-5,
        'epochs': 3,
        'data_dir': 'data/legal_titles',
        'model_dir': 'models/bert_title_classifier'
    }
    
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(config['model_name'])
    model = AutoModelForSequenceClassification.from_pretrained(
        config['model_name'],
        num_labels=2  # Binary classification: title or not
    )
    model = model.to(device)
    
    # Load and prepare dataset
    logger.info("Loading dataset...")
    train_data, val_data = load_legal_dataset(config['data_dir'])
    
    if not train_data or not val_data:
        logger.error("No training data found. Please prepare your dataset first.")
        return
    
    logger.info(f"Training samples: {len(train_data)}")
    logger.info(f"Validation samples: {len(val_data)}")
    
    # Create data loaders
    train_dataset = TitleDataset(train_data, tokenizer, config['max_length'])
    val_dataset = TitleDataset(val_data, tokenizer, config['max_length'])
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['batch_size'],
        shuffle=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['batch_size']
    )
    
    # Train the model
    logger.info("Starting training...")
    train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        device=device,
        epochs=config['epochs'],
        learning_rate=config['learning_rate'],
        model_dir=config['model_dir']
    )
    
    logger.info("Training completed!")




class TitleFinetuner:
    """A class for fine-tuning BERT models for title extraction."""
    
    def __init__(self, model_name: str = "dbmdz/bert-base-turkish-cased", device: str = None):
        """
        Initialize the title finetuner.
        
        Args:
            model_name: Name or path of the pre-trained BERT model
            device: Device to use for training ('cuda' or 'cpu')
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, 
            num_labels=2,  # Binary classification: title or not
            output_attentions=False,
            output_hidden_states=False,
        ).to(self.device)
    
    def train(
        self,
        train_data: List[Dict],
        val_data: List[Dict],
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        output_dir: str = "models/bert_title_classifier"
    ) -> Dict:
        """
        Fine-tune the BERT model for title extraction.
        
        Args:
            train_data: Training data as a list of dictionaries with 'text' and 'label' keys
            val_data: Validation data with the same format as train_data
            epochs: Number of training epochs
            batch_size: Batch size for training
            learning_rate: Learning rate for the optimizer
            output_dir: Directory to save the trained model
            
        Returns:
            Dictionary containing training metrics
        """
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create data loaders
        train_dataset = TitleDataset(train_data, self.tokenizer)
        val_dataset = TitleDataset(val_data, self.tokenizer)
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4
        )
        
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=4
        )
        
        # Set up optimizer and scheduler
        optimizer = AdamW(self.model.parameters(), lr=learning_rate)
        total_steps = len(train_loader) * epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=0,
            num_training_steps=total_steps
        )
        
        # Training loop
        training_stats = []
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            total_train_loss = 0
            
            for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{epochs}"):
                # Move batch to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                loss = outputs.loss
                
                # Backward pass and optimization
                loss.backward()
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                
                total_train_loss += loss.item()
            
            # Calculate average training loss
            avg_train_loss = total_train_loss / len(train_loader)
            
            # Validation
            avg_val_loss, val_accuracy = self.evaluate(val_loader)
            
            # Save the best model
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                self.save_model(output_dir)
            
            # Record statistics
            training_stats.append({
                'epoch': epoch + 1,
                'training_loss': avg_train_loss,
                'validation_loss': avg_val_loss,
                'validation_accuracy': val_accuracy
            })
            
            logger.info(f"Epoch {epoch + 1}/{epochs}")
            logger.info(f"  Training loss: {avg_train_loss:.4f}")
            logger.info(f"  Validation loss: {avg_val_loss:.4f}")
            logger.info(f"  Validation accuracy: {val_accuracy:.4f}")
        
        return {
            'training_stats': training_stats,
            'best_validation_loss': best_val_loss
        }
    
    def evaluate(self, data_loader: DataLoader) -> Tuple[float, float]:
        """
        Evaluate the model on the given data loader.
        
        Args:
            data_loader: DataLoader for evaluation data
            
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.eval()
        total_eval_loss = 0
        total_eval_accuracy = 0
        
        with torch.no_grad():
            for batch in data_loader:
                # Move batch to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                # Calculate loss
                loss = outputs.loss
                total_eval_loss += loss.item()
                
                # Calculate accuracy
                logits = outputs.logits
                predictions = torch.argmax(logits, dim=1)
                total_eval_accuracy += torch.sum(predictions == labels).item()
        
        # Calculate average loss and accuracy
        avg_val_loss = total_eval_loss / len(data_loader)
        avg_val_accuracy = total_eval_accuracy / len(data_loader.dataset)
        
        return avg_val_loss, avg_val_accuracy
    
    def save_model(self, output_dir: Union[str, Path]) -> None:
        """
        Save the model and tokenizer to the specified directory.
        
        Args:
            output_dir: Directory to save the model
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the model and tokenizer
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        logger.info(f"Model saved to {output_dir}")
    
    def predict(self, texts: Union[str, List[str]], batch_size: int = 32) -> List[Dict]:
        """
        Predict whether each input text is a title.
        
        Args:
            texts: Single text or list of texts to classify
            batch_size: Batch size for inference
            
        Returns:
            List of dictionaries containing predictions
        """
        if isinstance(texts, str):
            texts = [texts]
        
        self.model.eval()
        predictions = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get predictions
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(probs, dim=1)
            
            # Convert to list of dicts
            for j in range(len(batch_texts)):
                predictions.append({
                    'text': batch_texts[j],
                    'is_title': bool(preds[j].item()),
                    'confidence': probs[j][preds[j]].item(),
                    'probabilities': {
                        'not_title': probs[j][0].item(),
                        'is_title': probs[j][1].item()
                    }
                })
        
        return predictions


if __name__ == "__main__":
    main()
