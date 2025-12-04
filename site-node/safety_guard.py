# safety_guard.py
# Safety guard for general healthcare RAG system
# Detects harmful requests, medical misinformation attempts, and privacy violations

import re
import config
import logging

class SafetyGuard:
    """
    Safety guard for general healthcare chatbot.
    Prevents medical advice that could cause harm, protects privacy, and detects attacks.
    """
    def __init__(self, debug_mode: bool = False):
        """
        Initializes the safety guard with pre-compiled regex patterns.
        
        Args:
            debug_mode: If True, prints detailed debug information
        """
        self.debug_mode = debug_mode
        
        # Medical emergency keywords - should direct to emergency services
        self.emergency_regex = re.compile(
            r'\b(chest pain|heart attack|stroke|can\'?t breathe|difficulty breathing|'
            r'severe bleeding|head injury|poisoning|overdose|allergic reaction|'
            r'unconscious|seizing|seizure)\b', 
            re.IGNORECASE
        )
        
        # Self-harm/suicide keywords - still relevant in healthcare
        self.self_harm_regex = re.compile(
            r'\b(harm myself|suicide|kill myself|end my life|end it all|hurt myself)\b', 
            re.IGNORECASE
        )
        
        # Requests for medical diagnosis or treatment plans
        self.diagnosis_request_regex = re.compile(
            r'\b(diagnose me|what do i have|do i have (cancer|diabetes|disease)|'
            r'prescribe|what medication should i take|how much should i take|'
            r'can i take|should i stop taking)\b',
            re.IGNORECASE
        )
        
        # Drug/medication dosage requests (potentially dangerous)
        self.dosage_regex = re.compile(
            r'\b(how (much|many)|what dose|dosage of|mg of|ml of) .{0,30}(take|give|administer)\b',
            re.IGNORECASE
        )
        
        # Requests to bypass medical advice
        self.bypass_medical_regex = re.compile(
            r'\b(ignore|skip|avoid) (doctor|physician|medical advice|prescription|treatment)\b',
            re.IGNORECASE
        )
        
        # Alternative medicine that could be dangerous
        self.dangerous_alternative_regex = re.compile(
            r'\b(instead of|replace|substitute) .{0,30}(medication|prescription|treatment|surgery) with '
            r'.{0,30}(herb|natural|homeopathic|essential oil)\b',
            re.IGNORECASE
        )
        
        # Attempts to bypass rules
        self.rule_bypass_regex = re.compile(
            r'\b(ignore your rules|forget the rules|disregard the instructions|'
            r'ignore instructions|bypass|pretend you\'?re|act as if)\b', 
            re.IGNORECASE
        )
        
        # URLs and data exfiltration
        self.url_regex = re.compile(r'https?:\/\/[^\s/$.?#].[^\s]*', re.IGNORECASE)
        self.send_data_regex = re.compile(
            r'\b(send|email|post|forward|transmit|export) (?:this|the|my) '
            r'(?:to|log|data|information|records|results)\b', 
            re.IGNORECASE
        )
        
        # Medical record number or identifier requests
        self.record_request_regex = re.compile(
            r'\b(medical record|MRN|patient id|chart number|account number) '
            r'(for|of|number)\b',
            re.IGNORECASE
        )
        
        logging.info(f"SafetyGuard initialized for general healthcare (debug_mode={debug_mode})")

    def check_prompt(self, prompt: str, history: list) -> tuple:
        """
        Checks a prompt against healthcare-specific safety rules.

        Args:
            prompt: The user's input string.
            history: The recent conversation history.

        Returns:
            A tuple containing:
            - A boolean indicating if the prompt is safe (True) or not (False).
            - A string with a pre-canned response if unsafe, otherwise None.
        """
        if self.debug_mode:
            print(f"\n--- SafetyGuard Check for Prompt: '{prompt}' ---")
        
        # --- Check 1: Medical Emergency ---
        emergency_match = self.emergency_regex.search(prompt)
        if emergency_match:
            if self.debug_mode:
                print(f"DEBUG: Medical emergency detected: {emergency_match.group(0)}")
            logging.warning(f"Medical emergency keywords detected: '{emergency_match.group(0)}'")
            return (False, 
                "This sounds like a medical emergency. Please call 911 (US), 999 (UK), or your "
                "local emergency number immediately. If someone is unconscious, not breathing, or in "
                "severe distress, do not wait - get emergency help now.")
        
        # --- Check 2: Self-Harm (still relevant in healthcare) ---
        self_harm_match = self.self_harm_regex.search(prompt)
        if self_harm_match:
            if self.debug_mode:
                print(f"DEBUG: Self-harm language detected: {self_harm_match.group(0)}")
            logging.warning(f"Self-harm language detected: '{self_harm_match.group(0)}'")
            return (False,
                "I'm concerned about what you're sharing. Please reach out for immediate support: "
                "Call 988 (Suicide & Crisis Lifeline in US/Canada), text 'HELLO' to 741741 (Crisis Text Line), "
                "or call 111 (UK). You can also go to your nearest emergency room. You don't have to face this alone.")
        
        # --- Check 3: Request for Diagnosis ---
        diagnosis_match = self.diagnosis_request_regex.search(prompt)
        if diagnosis_match:
            if self.debug_mode:
                print(f"DEBUG: Diagnosis request detected: {diagnosis_match.group(0)}")
            logging.info("User requested medical diagnosis - providing disclaimer")
            return (False,
                "I cannot provide medical diagnoses or tell you what condition you have. Only a qualified "
                "healthcare provider can diagnose medical conditions after proper examination and testing. "
                "I can provide general health information, but please consult with your doctor or healthcare "
                "provider for personalized medical advice.")
        
        # --- Check 4: Medication Dosage Requests ---
        dosage_match = self.dosage_regex.search(prompt)
        if dosage_match:
            if self.debug_mode:
                print(f"DEBUG: Medication dosage request detected: {dosage_match.group(0)}")
            logging.warning("User requested medication dosage information")
            return (False,
                "I cannot provide specific medication dosages as this requires personalized medical evaluation. "
                "Incorrect dosing can be dangerous. Please consult your doctor, pharmacist, or the medication's "
                "prescribing information. If you're having concerns about your current medication, contact your "
                "healthcare provider.")
        
        # --- Check 5: Bypassing Medical Advice ---
        bypass_medical_match = self.bypass_medical_regex.search(prompt)
        if bypass_medical_match:
            if self.debug_mode:
                print(f"DEBUG: Attempt to bypass medical advice: {bypass_medical_match.group(0)}")
            logging.warning("User attempting to bypass medical advice")
            return (False,
                "I strongly encourage you to follow your healthcare provider's advice. They have access to your "
                "full medical history and can provide personalized recommendations. If you have concerns about "
                "their advice, I recommend discussing those concerns with them or seeking a second opinion from "
                "another qualified healthcare professional.")
        
        # --- Check 6: Dangerous Alternative Medicine Substitution ---
        dangerous_alt_match = self.dangerous_alternative_regex.search(prompt)
        if dangerous_alt_match:
            if self.debug_mode:
                print(f"DEBUG: Dangerous alternative medicine substitution: {dangerous_alt_match.group(0)}")
            logging.warning("User considering dangerous alternative medicine substitution")
            return (False,
                "⚠️ Please do not replace prescribed medications or treatments with alternative remedies without "
                "consulting your healthcare provider. Some combinations can be dangerous, and stopping prescribed "
                "treatments can have serious health consequences. If you're interested in complementary approaches, "
                "discuss them with your doctor so they can be safely integrated into your care plan.")
        
        # --- Check 7: Rule Bypass Attempts ---
        rule_bypass_match = self.rule_bypass_regex.search(prompt)
        if rule_bypass_match:
            if self.debug_mode:
                print(f"DEBUG: Rule bypass attempt: {rule_bypass_match.group(0)}")
            logging.warning("Attempt to bypass safety rules detected")
            return (False,
                "I'm designed to provide helpful health information within safe boundaries. I cannot ignore my "
                "safety guidelines as they're in place to protect you. I'm happy to answer questions about general "
                "health topics, but I cannot provide medical advice, diagnoses, or treatment recommendations.")
        
        # --- Check 8: Data Exfiltration / Privacy Violation ---
        url_match = self.url_regex.search(prompt)
        send_data_match = self.send_data_regex.search(prompt)
        record_match = self.record_request_regex.search(prompt)
        
        if self.debug_mode:
            print(f"URL match: {bool(url_match)}")
            print(f"Send data match: {bool(send_data_match)}")
            print(f"Record request match: {bool(record_match)}")

        if url_match or send_data_match or record_match:
            if self.debug_mode:
                print("DEBUG: Data exfiltration/privacy violation detected.")
            logging.warning("Privacy violation or data exfiltration attempt detected")
            return (False, 
                "For your privacy and security, I cannot interact with external websites, send information "
                "outside this chat, or access medical records. All our conversations remain private and secure. "
                "If you need to access your medical records, please contact your healthcare provider directly.")
        
        # --- Check 9: Pattern of Concerning Health Queries ---
        # Check if user is asking increasingly serious questions without seeking real medical help
        concerning_keywords = ['getting worse', 'not getting better', 'severe', 'spreading', 
                              'unbearable', 'weeks', 'months', 'won\'t go away']
        concern_count = 0
        for message in history[-4:]:  # Check last 4 turns
            user_msg = message.get('user', '').lower()
            if any(keyword in user_msg for keyword in concerning_keywords):
                concern_count += 1
        
        if self.debug_mode:
            print(f"Concerning pattern count in history: {concern_count}")
        
        # If showing pattern of worsening condition without seeking help
        if concern_count >= 2 and any(word in prompt.lower() for word in ['should i wait', 'will it go away', 'need to see']):
            if self.debug_mode:
                print("DEBUG: Pattern of escalating health concern detected.")
            logging.warning("Escalating health concern pattern detected")
            return (False,
                "I'm concerned about the symptoms you're describing. When health issues persist, worsen, or cause "
                "significant discomfort, it's important to see a healthcare provider. They can properly evaluate "
                "your condition and provide appropriate treatment. Please don't delay seeking medical attention - "
                "early intervention often leads to better outcomes.")

        if self.debug_mode:
            print("DEBUG: Prompt deemed safe.")
        
        # If no safety issues detected, the prompt is safe
        return (True, None)
    
    def get_emergency_info(self, region: str = "US") -> str:
        """
        Returns emergency contact information for a specific region.
        
        Args:
            region: Region code (US, UK, etc.)
            
        Returns:
            Formatted emergency contact information
        """
        emergency_numbers = {
            "US": "911",
            "UK": "999",
            "EU": "112",
            "AU": "000",
            "CA": "911",
            "default": "911 (US/Canada), 999 (UK), 112 (EU)"
        }
        
        crisis_hotlines = {
            "US": "988 (Suicide & Crisis Lifeline)",
            "UK": "111 (NHS) or 999 (emergency)",
            "default": "988 (US/Canada) or 111 (UK)"
        }
        
        emergency = emergency_numbers.get(region, emergency_numbers["default"])
        crisis = crisis_hotlines.get(region, crisis_hotlines["default"])
        
        return f"Emergency: {emergency} | Crisis Support: {crisis}"
