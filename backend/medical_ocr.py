"""
Medical OCR processing module for extracting text from uploaded images.
Supports lab reports, X-rays, prescriptions, and other medical documents.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from typing import Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalOCR:
    """Medical document OCR processor with preprocessing for better accuracy."""
    
    def __init__(self):
        # Configure tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # OCR configurations for different document types
        self.configs = {
            'lab_report': '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-+/()[]%<>= ',
            'prescription': '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-+/()[]mg ',
            'xray': '--psm 6',
            'blood_test': '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:-+/()[]%<>=μ ',
            'default': '--psm 6'
        }
    
    def preprocess_image(self, image_path: str, doc_type: str = 'default') -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image_path: Path to the image file
            doc_type: Type of medical document for specific preprocessing
            
        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply document-specific preprocessing
            if doc_type in ['lab_report', 'blood_test']:
                # For lab reports: enhance contrast and denoise
                gray = cv2.bilateralFilter(gray, 9, 75, 75)
                gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            elif doc_type == 'prescription':
                # For prescriptions: heavy denoising and contrast enhancement
                gray = cv2.medianBlur(gray, 3)
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            elif doc_type == 'xray':
                # For X-rays: edge enhancement and contrast adjustment
                gray = cv2.equalizeHist(gray)
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                gray = cv2.filter2D(gray, -1, kernel)
            
            else:
                # Default preprocessing
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Additional noise removal
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            return gray
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            # Return original grayscale if preprocessing fails
            image = cv2.imread(image_path)
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image is not None else None
    
    def extract_text(self, image_path: str, doc_type: str = 'default') -> Dict[str, any]:
        """
        Extract text from medical document image.
        
        Args:
            image_path: Path to the image file
            doc_type: Type of medical document
            
        Returns:
            Dictionary with extracted text, confidence, and metadata
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path, doc_type)
            if processed_image is None:
                return {
                    'text': '',
                    'confidence': 0.0,
                    'success': False,
                    'error': 'Image preprocessing failed'
                }
            
            # Get OCR configuration for document type
            config = self.configs.get(doc_type, self.configs['default'])
            
            # Extract text with confidence
            text = pytesseract.image_to_string(processed_image, config=config)
            
            # Get confidence data
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT, config=config)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Clean extracted text
            cleaned_text = self.clean_medical_text(text, doc_type)
            
            return {
                'text': cleaned_text,
                'raw_text': text,
                'confidence': avg_confidence,
                'success': True,
                'word_count': len(cleaned_text.split()),
                'doc_type': doc_type
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def clean_medical_text(self, text: str, doc_type: str) -> str:
        """
        Clean and standardize extracted medical text.
        
        Args:
            text: Raw OCR text
            doc_type: Type of medical document
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Basic cleaning
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip very short lines (likely OCR artifacts)
            if len(line) < 2:
                continue
            
            # Document-specific cleaning
            if doc_type in ['lab_report', 'blood_test']:
                # Keep lines with medical values/units
                if any(unit in line.lower() for unit in ['mg/dl', 'mmol/l', 'g/dl', 'μg/ml', 'ng/ml', '%', 'bpm']):
                    cleaned_lines.append(line)
                elif any(term in line.lower() for term in ['glucose', 'cholesterol', 'hemoglobin', 'creatinine', 'sodium', 'potassium']):
                    cleaned_lines.append(line)
                elif len(line) > 10:  # Keep longer descriptive lines
                    cleaned_lines.append(line)
            
            elif doc_type == 'prescription':
                # Keep medication-related lines
                if any(term in line.lower() for term in ['mg', 'tablet', 'capsule', 'daily', 'twice', 'three times']):
                    cleaned_lines.append(line)
                elif len(line) > 5:
                    cleaned_lines.append(line)
            
            else:
                # Default: keep lines longer than 3 characters
                if len(line) > 3:
                    cleaned_lines.append(line)
        
        # Join and final cleanup
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive whitespace
        import re
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        
        return cleaned_text.strip()
    
    def detect_document_type(self, text: str) -> str:
        """
        Detect the type of medical document based on extracted text.
        
        Args:
            text: Extracted text
            
        Returns:
            Detected document type
        """
        text_lower = text.lower()
        
        # Lab report indicators
        if any(term in text_lower for term in ['glucose', 'cholesterol', 'hemoglobin', 'creatinine', 'lab', 'laboratory']):
            return 'lab_report'
        
        # Blood test indicators
        elif any(term in text_lower for term in ['blood', 'plasma', 'serum', 'hematocrit', 'platelet']):
            return 'blood_test'
        
        # Prescription indicators
        elif any(term in text_lower for term in ['prescription', 'rx', 'tablet', 'capsule', 'mg', 'dosage']):
            return 'prescription'
        
        # X-ray indicators
        elif any(term in text_lower for term in ['x-ray', 'radiograph', 'chest', 'fracture', 'radiology']):
            return 'xray'
        
        return 'default'