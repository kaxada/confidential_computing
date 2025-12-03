# phi_scrubber.py
# Scrubs Protected Health Information (PHI) and Personally Identifiable Information (PII)

import re
import logging
import config

class PHIScrubber:
    """
    Scrubs PHI/PII from text to ensure compliance with HIPAA and privacy regulations.
    This is a critical component of the privacy guardrails.
    """
    
    def __init__(self):
        """Initialize PHI scrubber with regex patterns."""
        # Compile regex patterns for efficiency
        
        # Names (simple pattern - in production use NER models)
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')
        
        # Email addresses
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Phone numbers (various formats)
        self.phone_pattern = re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b')
        
        # Social Security Numbers
        self.ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        
        # Medical Record Numbers (MRN) - common formats
        self.mrn_pattern = re.compile(r'\b(MRN|mrn|Medical Record #?):?\s*\d{6,10}\b', re.IGNORECASE)
        
        # Dates (MM/DD/YYYY, MM-DD-YYYY, etc.)
        self.date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        
        # Addresses (simplified - catches street addresses)
        self.address_pattern = re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)\b', re.IGNORECASE)
        
        # ZIP codes
        self.zip_pattern = re.compile(r'\b\d{5}(?:-\d{4})?\b')
        
        # Ages over 89 (HIPAA requires scrubbing)
        self.age_pattern = re.compile(r'\b(?:age|aged|years old)\s*(?:of\s*)?(\d+)\b', re.IGNORECASE)
        
        self.replacement_token = config.PHI_REPLACEMENT_TOKEN
        logging.info("PHI Scrubber initialized")

    def scrub(self, text: str) -> str:
        """
        Scrubs PHI/PII from the input text.
        
        Args:
            text: Input text that may contain PHI/PII
            
        Returns:
            Scrubbed text with PHI/PII replaced with [REDACTED]
        """
        if not config.ENABLE_PHI_SCRUBBING:
            return text
        
        if not text:
            return text
        
        scrubbed = text
        
        # Scrub SSNs
        scrubbed = self.ssn_pattern.sub(self.replacement_token, scrubbed)
        
        # Scrub emails
        scrubbed = self.email_pattern.sub(self.replacement_token, scrubbed)
        
        # Scrub phone numbers
        scrubbed = self.phone_pattern.sub(self.replacement_token, scrubbed)
        
        # Scrub MRNs
        scrubbed = self.mrn_pattern.sub(f"MRN: {self.replacement_token}", scrubbed)
        
        # Scrub dates (be careful not to scrub relative dates like "2 days ago")
        scrubbed = self.date_pattern.sub(self.replacement_token, scrubbed)
        
        # Scrub addresses
        scrubbed = self.address_pattern.sub(self.replacement_token, scrubbed)
        
        # Scrub ZIP codes
        scrubbed = self.zip_pattern.sub(self.replacement_token, scrubbed)
        
        # Scrub ages over 89
        def replace_age(match):
            age = int(match.group(1))
            if age > 89:
                return match.group(0).replace(match.group(1), "89+")
            return match.group(0)
        
        scrubbed = self.age_pattern.sub(replace_age, scrubbed)
        
        # Scrub potential names (this is aggressive and may have false positives)
        # In production, use a proper NER model instead
        # scrubbed = self.name_pattern.sub(self.replacement_token, scrubbed)
        
        # Log if scrubbing occurred
        if scrubbed != text:
            logging.warning("PHI/PII scrubbed from text")
        
        return scrubbed

    def scrub_document(self, doc: dict) -> dict:
        """
        Scrubs PHI/PII from a document dictionary.
        
        Args:
            doc: Document dictionary with 'content' and potentially 'metadata'
            
        Returns:
            Scrubbed document dictionary
        """
        scrubbed_doc = doc.copy()
        
        # Scrub content
        if 'content' in scrubbed_doc:
            scrubbed_doc['content'] = self.scrub(scrubbed_doc['content'])
        
        # Scrub metadata fields that might contain PHI
        if 'metadata' in scrubbed_doc:
            metadata = scrubbed_doc['metadata']
            if isinstance(metadata, dict):
                # Don't scrub speaker field if it's generic like "Therapist" or "Patient"
                # but scrub if it looks like a name
                if 'patient_id' in metadata:
                    metadata['patient_id'] = self.replacement_token
                if 'therapist_id' in metadata:
                    metadata['therapist_id'] = self.replacement_token
        
        return scrubbed_doc

    def validate_output(self, text: str) -> tuple[bool, list[str]]:
        """
        Validates that output text doesn't contain PHI/PII.
        
        Args:
            text: Output text to validate
            
        Returns:
            Tuple of (is_clean, list_of_violations)
        """
        violations = []
        
        # Check for various PHI patterns
        if self.ssn_pattern.search(text):
            violations.append("SSN detected")
        if self.email_pattern.search(text):
            violations.append("Email detected")
        if self.phone_pattern.search(text):
            violations.append("Phone number detected")
        if self.mrn_pattern.search(text):
            violations.append("MRN detected")
        
        is_clean = len(violations) == 0
        
        if not is_clean:
            logging.error(f"PHI validation failed: {violations}")
        
        return is_clean, violations