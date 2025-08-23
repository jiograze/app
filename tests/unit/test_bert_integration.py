"""
Test script for Turkish BERT model integration with LegalTextAnalyzer.
"""
import sys
import os
import logging
from pathlib import Path
from app.core.legal_analyzer import BERT_AVAILABLE

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bert_integration_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_bert_analyzer_initialization():
    """Test that the BERT analyzer initializes correctly."""
    try:
        from app.core.turkish_bert import TurkishBERTAnalyzer
        
        # Test with default parameters
        analyzer = TurkishBERTAnalyzer()
        assert analyzer is not None, "Failed to initialize TurkishBERTAnalyzer"
        logger.info("✓ TurkishBERTAnalyzer initialized successfully")
        
        # Test with explicit device
        analyzer = TurkishBERTAnalyzer(device='cpu')
        assert analyzer is not None, "Failed to initialize with explicit device"
        logger.info("✓ Initialized with explicit device")
        
        return True
    except ImportError:
        logger.warning("Skipping BERT analyzer test - required dependencies not installed")
        return False
    except Exception as e:
        logger.error(f"❌ BERT analyzer initialization failed: {str(e)}")
        return False

def test_bert_embeddings():
    """Test that BERT embeddings are generated correctly."""
    try:
        from app.core.turkish_bert import TurkishBERTAnalyzer
        import torch
        
        analyzer = TurkishBERTAnalyzer()
        test_text = "Bu bir test cümlesidir."
        
        # Test single text
        embedding = analyzer.get_embeddings(test_text)
        assert isinstance(embedding, torch.Tensor), "Embedding should be a PyTorch tensor"
        assert embedding.dim() == 1, f"Single text embedding should be 1D, got {embedding.dim()}D"
        assert embedding.size(0) > 0, "Embedding should have positive dimension"
        
        # Test batch processing
        texts = ["İlk cümle.", "İkinci cümle.", "Üçüncü cümle."]
        embeddings = analyzer.get_embeddings(texts)
        assert isinstance(embeddings, torch.Tensor), "Batch embeddings should be a PyTorch tensor"
        assert embeddings.dim() == 2, f"Batch embeddings should be 2D, got {embeddings.dim()}D"
        assert embeddings.size(0) == len(texts), f"Batch size {embeddings.size(0)} should match input size {len(texts)}"
        
        logger.info("✓ BERT embeddings generated successfully")
        return True
    except ImportError:
        logger.warning("Skipping BERT embeddings test - required dependencies not installed")
        return False
    except Exception as e:
        logger.error(f"❌ BERT embedding generation failed: {str(e)}", exc_info=True)
        return False

def test_bert_similarity():
    """Test that BERT similarity calculation works correctly."""
    try:
        from app.core.turkish_bert import TurkishBERTAnalyzer
        
        analyzer = TurkishBERTAnalyzer()
        
        # Test with identical sentences
        text1 = "Bu bir test cümlesidir."
        text2 = "Bu bir test cümlesidir."
        similarity = analyzer.get_similarity(text1, text2)
        
        # Identical sentences should have similarity close to 1.0
        assert 0.9 <= similarity <= 1.1, f"Identical sentences should have similarity ~1.0, got {similarity}"
        logger.info(f"✓ Similarity score for identical sentences: {similarity:.4f}")
        
        # Test with similar but not identical sentences
        text3 = "Bu başka bir test cümlesidir."
        similarity_similar = analyzer.get_similarity(text1, text3)
        
        # Test with different sentences
        text4 = "Python programlama dili yapay zeka uygulamalarında yaygın olarak kullanılır."
        similarity_diff = analyzer.get_similarity(text1, text4)
        
        logger.info(f"✓ Similarity score for similar sentences: {similarity_similar:.4f}")
        logger.info(f"✓ Similarity score for different sentences: {similarity_diff:.4f}")
        
        # Similarity between identical sentences should be higher than different ones
        assert similarity_similar > similarity_diff, "Similar sentences should have higher similarity"
        
        return True
    except ImportError:
        logger.warning("Skipping BERT similarity test - required dependencies not installed")
        return False
    except Exception as e:
        logger.error(f"❌ BERT similarity calculation failed: {str(e)}", exc_info=True)
        return False

def test_bert_integration_with_legal_analyzer():
    """Test integration of BERT with LegalTextAnalyzer."""
    try:
        import spacy
        from app.core.legal_analyzer import LegalTextAnalyzer
        
        # Skip if BERT is not available
        if not BERT_AVAILABLE:
            logger.warning("Skipping BERT integration test - BERT not available")
            return False
            
        # Check if Turkish model is available
        try:
            spacy.load("tr_core_news_md")
        except OSError:
            logger.warning("Skipping BERT integration test - Turkish spaCy model not found")
            return False
            
        # Initialize with BERT enabled
        analyzer = LegalTextAnalyzer(language='tr', use_bert=True)
        
        # Test text (a simple legal text in Turkish)
        test_text = """
        Tapu kaydında 1234 ada 56 parsel sayılı taşınmaz üzerinde Ahmet Yılmaz adına kayıtlıdır. 
        Söz konusu taşınmaz üzerinde 12.05.2020 tarihli 1234 sayılı ipotek kaydı bulunmaktadır.
        """
        
        # Analyze the text
        result = analyzer.analyze_text(test_text)
        
        # Check if BERT analysis was performed
        bert_used = result.additional_analysis.get('bert_used', False)
        if not bert_used:
            logger.warning("BERT analysis was not performed, but was expected")
            return False
            
        # Check if we have embeddings
        has_embeddings = 'bert_embedding' in result.additional_analysis
        has_sentiment = 'sentiment' in result.additional_analysis
        
        logger.info(f"✓ BERT analysis performed - Embeddings: {has_embeddings}, Sentiment: {has_sentiment}")
        
        # Check if keywords were enhanced with BERT
        if 'bert_keyword_scores' in result.additional_analysis:
            logger.info("✓ BERT keyword enhancement results (top 5):")
            keywords = result.additional_analysis['bert_keyword_scores']
            for kw, score in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]:
                logger.info(f"  - {kw}: {score:.4f}")
        
        logger.info("✓ BERT integration with LegalTextAnalyzer completed")
        return has_embeddings and has_sentiment
        
    except ImportError as e:
        logger.warning(f"Skipping BERT integration test - required modules not found: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ BERT integration test failed: {str(e)}", exc_info=True)
        return False

def run_all_tests():
    """Run all BERT integration tests."""
    logger.info("=" * 50)
    logger.info("Starting BERT Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("BERT Analyzer Initialization", test_bert_analyzer_initialization),
        ("BERT Embeddings Generation", test_bert_embeddings),
        ("BERT Similarity Calculation", test_bert_similarity),
        ("BERT + LegalTextAnalyzer Integration", test_bert_integration_with_legal_analyzer)
    ]
    
    results = {}
    for name, test_func in tests:
        logger.info(f"\n{' TEST: ' + name + ' ':=^80}")
        results[name] = test_func()
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    all_passed = True
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED SUCCESSFULLY!")
    else:
        logger.error("❌ SOME TESTS FAILED. Please check the logs for details.")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
