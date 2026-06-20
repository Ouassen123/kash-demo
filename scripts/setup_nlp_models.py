#!/usr/bin/env python3
"""
Setup script for NLP models and dependencies.

This script downloads and validates required NLP models
for the KASH Knowledge Module CV analysis engine.
"""

import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ is required")
        return False
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_package(package_name):
    """Install a Python package using pip."""
    try:
        logger.info(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package_name}: {e}")
        return False

def download_spacy_model():
    """Download spaCy English model."""
    try:
        import spacy
        logger.info("Downloading spaCy English model...")
        spacy.cli.download("en_core_web_sm")
        logger.info("Successfully downloaded spaCy model")
        
        # Verify model can be loaded
        nlp = spacy.load("en_core_web_sm")
        logger.info("spaCy model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to download/load spaCy model: {e}")
        return False

def setup_nltk_data():
    """Download required NLTK data."""
    try:
        import nltk
        
        # Download required NLTK data
        required_data = ['punkt', 'stopwords', 'wordnet']
        
        for data_name in required_data:
            try:
                nltk.data.find(f'corpora/{data_name}')
                logger.info(f"NLTK {data_name} already exists")
            except LookupError:
                logger.info(f"Downloading NLTK {data_name}...")
                nltk.download(data_name)
        
        logger.info("NLTK setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to setup NLTK: {e}")
        return False

def validate_installation():
    """Validate that all NLP components work correctly."""
    try:
        # Test spaCy
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("This is a test sentence.")
        assert len(doc) > 0
        logger.info("✓ spaCy validation passed")
        
        # Test NLTK
        import nltk
        tokens = nltk.word_tokenize("This is a test sentence.")
        assert len(tokens) > 0
        logger.info("✓ NLTK validation passed")
        
        # Test our modules
        from src.modules.knowledge.nlp.cv_analyzer import CVAnalyzer
        analyzer = CVAnalyzer()
        result = analyzer.analyze_cv("Test CV with Python skills and experience.")
        assert 'metadata' in result
        logger.info("✓ CV Analyzer validation passed")
        
        return True
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("Starting KASH NLP models setup...")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install required packages
    packages = ['spacy', 'nltk']
    for package in packages:
        if not install_package(package):
            logger.error(f"Setup failed due to missing package: {package}")
            sys.exit(1)
    
    # Setup NLP models
    if not download_spacy_model():
        logger.error("Setup failed due to spaCy model issues")
        sys.exit(1)
    
    if not setup_nltk_data():
        logger.error("Setup failed due to NLTK issues")
        sys.exit(1)
    
    # Validate installation
    if not validate_installation():
        logger.error("Setup failed validation")
        sys.exit(1)
    
    logger.info("🎉 NLP models setup completed successfully!")
    logger.info("You can now use the CV analysis engine.")

if __name__ == "__main__":
    main()
