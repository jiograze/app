# Turkish BERT Integration

This document describes the integration of the Turkish BERT model (`dbmdz/bert-base-turkish-cased`) into the LegalTextAnalyzer for advanced Turkish text analysis.

## Features

1. **Text Embeddings**: Generate contextual embeddings for Turkish legal texts
2. **Semantic Similarity**: Calculate semantic similarity between Turkish texts
3. **Keyword Enhancement**: Improve keyword extraction using BERT embeddings
4. **Sentiment Analysis**: Basic sentiment analysis for Turkish legal texts

## Requirements

- Python 3.8+
- PyTorch
- Transformers library
- spaCy with Turkish model (optional, falls back to English)

## Installation

1. Install the required packages:

```bash
pip install torch transformers
```

2. (Optional) Install the Turkish spaCy model:

```bash
python -m spacy download tr_core_news_sm
```

## Usage

### Basic Usage

```python
from app.core.turkish_bert import TurkishBERTAnalyzer

# Initialize the analyzer
analyzer = TurkishBERTAnalyzer(device='cpu')  # 'cuda' for GPU

# Get embeddings for a text
embeddings = analyzer.get_embeddings("Bu bir örnek metindir.")

# Calculate similarity between two texts
similarity = analyzer.get_similarity("Bu bir örnek metindir.", "Bu başka bir örnek metindir.")

# Get sentiment (positive/negative/neutral)
sentiment = analyzer.get_sentiment("Bu olumlu bir örnek cümledir.")
```

### Integration with LegalTextAnalyzer

```python
from app.core.legal_analyzer import LegalTextAnalyzer

# Initialize with BERT enabled
analyzer = LegalTextAnalyzer(language='tr', use_bert=True)

# Analyze text with BERT enhancements
result = analyzer.analyze_text("Tapu kaydı örneği...")

# Access BERT-enhanced features
print("BERT Embedding:", result.additional_analysis.get('bert_embedding'))
print("Sentiment:", result.additional_analysis.get('sentiment'))
print("Enhanced Keywords:", result.additional_analysis.get('bert_keyword_scores', {}))
```

## Configuration

The following environment variables can be set to configure the BERT integration:

- `BERT_MODEL_NAME`: Name of the BERT model (default: `dbmdz/bert-base-turkish-cased`)
- `BERT_DEVICE`: Device to run the model on (`cpu` or `cuda`)
- `BATCH_SIZE`: Batch size for processing multiple texts (default: 8)

## Error Handling

The system is designed to be resilient to missing dependencies:

1. If BERT dependencies are missing, the system will fall back to non-BERT analysis
2. If the Turkish spaCy model is not available, it will fall back to the English model
3. All BERT operations are wrapped in try-except blocks to prevent crashes

## Performance Considerations

- Running BERT on CPU is significantly slower than on GPU
- For production use, consider using a GPU for better performance
- The model uses approximately 1.5GB of RAM when loaded

## Troubleshooting

### Common Issues

1. **Model not found**: Ensure you have internet access to download the model
2. **CUDA out of memory**: Reduce batch size or use CPU
3. **Missing dependencies**: Install required packages with `pip install -r requirements.txt`

### Logging

Check the `legal_analyzer.log` file for detailed error messages and warnings.

## License

This integration is provided under the same license as the main project. The BERT model is licensed under the MIT License.
