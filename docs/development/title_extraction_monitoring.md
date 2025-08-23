# Title Extraction Monitoring and Fine-tuning

This document outlines the monitoring and fine-tuning setup for the BERT-based title extraction system.

## Monitoring Setup

The monitoring system tracks the quality of title extractions in production and provides metrics for analysis.

### Key Features

- Logs all title extractions with confidence scores
- Tracks user feedback on extraction quality
- Provides metrics on extraction performance
- Identifies low-confidence extractions for review

### Usage

1. **Initialize the monitor**:
   ```python
   from app.monitoring.title_monitoring import title_monitor
   ```

2. **Log an extraction**:
   ```python
   title_monitor.log_extraction(
       document_id="doc123",
       extracted_title="TÜRK CEZA KANUNU",
       full_text="TÜRK CEZA KANUNU\nKanun Numarası: 5237...",
       confidence=0.95
   )
   ```

3. **Get metrics**:
   ```python
   metrics = title_monitor.get_metrics(days=7)
   print(metrics)
   ```

4. **Get low-confidence extractions**:
   ```python
   low_conf_titles = title_monitor.get_low_confidence_titles(threshold=0.7)
   ```

## Fine-tuning the BERT Model

To improve title extraction accuracy, you can fine-tune the BERT model on your legal document dataset.

### Prerequisites

- Python 3.7+
- PyTorch
- Transformers library
- A dataset of labeled legal document titles

### Dataset Format

Prepare your dataset in the following format:

```json
[
    {"text": "TÜRK CEZA KANUNU", "label": 1},
    {"text": "BİRİNCİ BÖLÜM Amaç, Kapsam, Tanımlar ve İlkeler", "label": 1},
    {"text": "Bu sıradan bir cümledir ve başlık değildir.", "label": 0}
]
```

### Training the Model

1. **Prepare your dataset**:
   - Create a directory for your dataset (default: `data/legal_titles/`)
   - Save your training data as `train.json` and validation data as `val.json`

2. **Run the training script**:
   ```bash
   python -m app.training.title_finetuner
   ```

3. **Configure training parameters** (optional):
   Edit the `config` dictionary in `title_finetuner.py` to adjust:
   - `model_name`: Pre-trained model to fine-tune
   - `max_length`: Maximum sequence length
   - `batch_size`: Training batch size
   - `learning_rate`: Learning rate
   - `epochs`: Number of training epochs
   - `data_dir`: Directory containing training data
   - `model_dir`: Directory to save the fine-tuned model

### Using the Fine-tuned Model

After training, the model will be saved to the specified `model_dir`. To use it:

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load the fine-tuned model
model_path = "models/bert_title_classifier"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Make predictions
def is_title(text, threshold=0.5):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    return probs[0][1].item() > threshold
```

## Monitoring Dashboard (Optional)

For a visual dashboard, you can use tools like:

1. **Grafana + Prometheus**: For real-time monitoring
2. **MLflow**: For experiment tracking
3. **Custom web dashboard**: Using Flask/Django with the monitoring data

## Best Practices

1. **Regularly monitor metrics**: Check the extraction quality weekly
2. **Collect user feedback**: Implement feedback mechanisms in your UI
3. **Retrain periodically**: Fine-tune the model with new data every few months
4. **A/B test changes**: Test new models on a small percentage of traffic before full rollout
5. **Monitor model drift**: Track how extraction quality changes over time
