"""
AI Content Quality Control and Safety Filter for Astrological Consultations.
Ensures generated content meets safety standards and quality requirements.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ContentSafetyLevel(Enum):
    """Content safety levels"""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


class ContentQualityLevel(Enum):
    """Content quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNACCEPTABLE = "unacceptable"


class AIContentFilter:
    """Content filter for AI-generated astrological consultations"""
    
    def __init__(self):
        # Blacklisted content patterns (safety)
        self.harmful_patterns = [
            r"смерть",
            r"самоубийство",
            r"самоубийц",
            r"убийство",
            r"убить",
            r"умрешь",
            r"умереть",
            r"покончить.*жизн",
            r"трагедия",
            r"катастрофа",
            r"неизлечим",
            r"безнадежн",
            r"обречен",
            r"конец.*света",
            r"апокалипсис",
            r"проклят",
            r"прокля́т",
            r"злой.*рок",
            r"кара.*небесн",
        ]
        
        # Medical advice patterns (to avoid)
        self.medical_patterns = [
            r"диагноз",
            r"лечение",
            r"лекарство",
            r"операция",
            r"болезнь",
            r"заболевание",
            r"принимай.*препарат",
            r"откажись.*от.*лечения",
            r"не.*иди.*к.*врачу",
            r"медицинск.*совет",
        ]
        
        # Financial advice patterns (to avoid giving specific advice)
        self.financial_risk_patterns = [
            r"инвестируй.*в",
            r"покупай.*акции",
            r"продавай.*все",
            r"берите.*кредит",
            r"не.*плати.*налог",
            r"скрывай.*доход",
            r"конкретн.*сумм.*вложен",
        ]
        
        # Quality indicators (positive)
        self.quality_indicators = [
            r"астрологическ",
            r"планет",
            r"звезд",
            r"знак.*зодиака",
            r"аспект",
            r"транзит",
            r"натальн.*карт",
            r"гороскоп",
            r"влиян.*планет",
            r"энерг",
            r"гармони",
            r"развитие",
            r"возможност",
            r"рекомендац",
            r"совет",
        ]
        
        # Required disclaimers
        self.disclaimer_phrases = [
            "Астрология предназначена для развлечения",
            "Это общие рекомендации",
            "Учитывайте собственную интуицию",
            "Астрология не заменяет профессиональные консультации",
            "Помните, что это развлекательный контент",
        ]
        
        logger.info("AI_CONTENT_FILTER_INITIALIZED: Filter ready for content validation")
    
    def validate_content(
        self, 
        content: str, 
        consultation_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Validate AI-generated content for safety and quality.
        
        Args:
            content: Generated content to validate
            consultation_type: Type of consultation (general, medical, financial, etc.)
            
        Returns:
            Validation result with safety level, quality score, and recommendations
        """
        logger.info(f"AI_CONTENT_FILTER_VALIDATE_START: type={consultation_type}, length={len(content)}")
        
        if not content or len(content.strip()) < 10:
            return {
                "safety_level": ContentSafetyLevel.BLOCKED,
                "quality_level": ContentQualityLevel.UNACCEPTABLE,
                "issues": ["Content too short or empty"],
                "filtered_content": None,
                "needs_disclaimer": True
            }
        
        # Check for harmful content
        safety_issues = []
        for pattern in self.harmful_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.UNICODE):
                safety_issues.append(f"Harmful content detected: {pattern}")
        
        # Check for medical advice (especially in health consultations)
        if consultation_type == "здоровье":
            for pattern in self.medical_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.UNICODE):
                    safety_issues.append(f"Medical advice detected: {pattern}")
        
        # Check for risky financial advice
        if consultation_type == "финансы":
            for pattern in self.financial_risk_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.UNICODE):
                    safety_issues.append(f"Risky financial advice detected: {pattern}")
        
        # Determine safety level
        safety_level = ContentSafetyLevel.SAFE
        if safety_issues:
            if any("Harmful content" in issue for issue in safety_issues):
                safety_level = ContentSafetyLevel.BLOCKED
            else:
                safety_level = ContentSafetyLevel.WARNING
        
        # Assess content quality
        quality_score = self._assess_quality(content, consultation_type)
        quality_level = self._get_quality_level(quality_score)
        
        # Filter and enhance content if needed
        filtered_content = self._filter_content(content, safety_issues) if safety_level != ContentSafetyLevel.BLOCKED else None
        
        # Check if disclaimer is needed
        needs_disclaimer = self._needs_disclaimer(content, consultation_type)
        
        result = {
            "safety_level": safety_level,
            "quality_level": quality_level,
            "quality_score": quality_score,
            "issues": safety_issues,
            "filtered_content": filtered_content,
            "needs_disclaimer": needs_disclaimer,
            "recommendation": self._get_content_recommendation(safety_level, quality_level),
            "length_check": self._check_length_limits(content)
        }
        
        logger.info(
            f"AI_CONTENT_FILTER_VALIDATE_COMPLETE: "
            f"safety={safety_level.value}, quality={quality_level.value}, "
            f"issues={len(safety_issues)}"
        )
        
        return result
    
    def _assess_quality(self, content: str, consultation_type: str) -> float:
        """Assess content quality based on astrological relevance and coherence"""
        
        score = 0.0
        
        # Base score for having content
        if len(content) > 50:
            score += 20.0
        
        # Check for astrological terminology
        astro_terms_found = 0
        for pattern in self.quality_indicators:
            if re.search(pattern, content, re.IGNORECASE | re.UNICODE):
                astro_terms_found += 1
        
        # Quality score based on astrological relevance
        score += min(astro_terms_found * 10, 40)  # Max 40 points
        
        # Length appropriateness (Alice voice interface)
        length = len(content)
        if consultation_type in ["карьера", "любовь", "здоровье", "финансы", "духовность"]:
            # Specialized consultations should be 400-500 chars
            if 400 <= length <= 500:
                score += 20
            elif 300 <= length <= 600:
                score += 15
            else:
                score += 5
        else:
            # General content should be 600-800 chars
            if 600 <= length <= 800:
                score += 20
            elif 500 <= length <= 900:
                score += 15
            else:
                score += 5
        
        # Coherence check (basic)
        sentences = content.split('.')
        if len(sentences) >= 3:  # At least 3 sentences
            score += 10
        
        # Practical advice check
        if re.search(r"рекомендуе|советуе|предлага|стоит|лучше|важно", content, re.IGNORECASE):
            score += 10
        
        return min(score, 100.0)  # Cap at 100
    
    def _get_quality_level(self, score: float) -> ContentQualityLevel:
        """Convert numerical quality score to quality level"""
        if score >= 80:
            return ContentQualityLevel.HIGH
        elif score >= 60:
            return ContentQualityLevel.MEDIUM
        elif score >= 40:
            return ContentQualityLevel.LOW
        else:
            return ContentQualityLevel.UNACCEPTABLE
    
    def _filter_content(self, content: str, issues: List[str]) -> str:
        """Filter and sanitize content based on detected issues"""
        filtered = content
        
        # Remove or replace harmful phrases
        for pattern in self.harmful_patterns:
            if re.search(pattern, filtered, re.IGNORECASE | re.UNICODE):
                # Replace with neutral alternatives
                replacements = {
                    r"смерть": "изменения",
                    r"трагедия": "сложный период",
                    r"катастрофа": "вызов",
                    r"безнадежн": "требует внимания",
                    r"обречен": "предстоит работа над",
                    r"проклят": "энергетически сложный"
                }
                
                for harmful, neutral in replacements.items():
                    filtered = re.sub(harmful, neutral, filtered, flags=re.IGNORECASE | re.UNICODE)
        
        # Soften overly specific medical or financial advice
        filtered = re.sub(
            r"принимай.*препарат", 
            "обратитесь к специалисту", 
            filtered, 
            flags=re.IGNORECASE
        )
        filtered = re.sub(
            r"инвестируй.*в.*", 
            "рассмотрите возможности", 
            filtered, 
            flags=re.IGNORECASE
        )
        
        return filtered
    
    def _needs_disclaimer(self, content: str, consultation_type: str) -> bool:
        """Determine if content needs a disclaimer"""
        
        # Always need disclaimer for medical/financial advice
        if consultation_type in ["здоровье", "финансы"]:
            return True
        
        # Check if content has any existing disclaimer
        content_lower = content.lower()
        for phrase in self.disclaimer_phrases:
            if phrase.lower() in content_lower:
                return False  # Already has disclaimer
        
        # Need disclaimer for specific advice
        if re.search(r"обязательно|точно|гарантирую|100%|наверняка", content, re.IGNORECASE):
            return True
        
        return True  # Default to adding disclaimer
    
    def _check_length_limits(self, content: str) -> Dict[str, Any]:
        """Check if content meets Alice voice interface length requirements"""
        length = len(content)
        
        return {
            "length": length,
            "within_limits": length <= 1024,  # Alice text limit
            "recommended_voice_length": 400 <= length <= 800,  # Good for voice
            "needs_truncation": length > 1024
        }
    
    def _get_content_recommendation(
        self, 
        safety_level: ContentSafetyLevel, 
        quality_level: ContentQualityLevel
    ) -> str:
        """Get recommendation for content usage"""
        
        if safety_level == ContentSafetyLevel.BLOCKED:
            return "REJECT: Content contains harmful elements and should not be used"
        
        if quality_level == ContentQualityLevel.UNACCEPTABLE:
            return "REJECT: Content quality too low, regenerate required"
        
        if safety_level == ContentSafetyLevel.WARNING:
            return "USE_WITH_CAUTION: Content has minor issues, consider review"
        
        if quality_level == ContentQualityLevel.HIGH:
            return "APPROVE: High quality content, safe to use"
        elif quality_level == ContentQualityLevel.MEDIUM:
            return "APPROVE: Good quality content, acceptable for use"
        else:  # LOW quality
            return "CONDITIONAL: Content usable but consider improvement"
    
    def add_appropriate_disclaimer(
        self, 
        content: str, 
        consultation_type: str
    ) -> str:
        """Add appropriate disclaimer to content based on consultation type"""
        
        disclaimers = {
            "здоровье": "\n\nПомните: астрология не заменяет медицинские консультации. При проблемах со здоровьем обращайтесь к врачу.",
            "финансы": "\n\nВажно: это общие астрологические рекомендации. Для финансовых решений консультируйтесь со специалистами.",
            "general": "\n\nАстрологические советы предназначены для размышления и вдохновения.",
        }
        
        disclaimer = disclaimers.get(consultation_type, disclaimers["general"])
        
        # Check if content already has a disclaimer
        if any(phrase in content.lower() for phrase in [d.lower() for d in self.disclaimer_phrases]):
            return content  # Already has disclaimer
        
        # Add disclaimer only if total length won't exceed limits
        if len(content + disclaimer) <= 1020:  # Leave room for Alice limits
            return content + disclaimer
        else:
            # Truncate content to make room for disclaimer
            max_content_length = 1020 - len(disclaimer)
            truncated_content = content[:max_content_length].rsplit(' ', 1)[0] + "..."
            return truncated_content + disclaimer
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """Get filter usage statistics"""
        return {
            "filter_version": "1.0.0",
            "total_patterns": {
                "harmful": len(self.harmful_patterns),
                "medical": len(self.medical_patterns),
                "financial_risk": len(self.financial_risk_patterns),
                "quality_indicators": len(self.quality_indicators)
            },
            "safety_levels": [level.value for level in ContentSafetyLevel],
            "quality_levels": [level.value for level in ContentQualityLevel],
            "supported_consultation_types": [
                "general", "карьера", "любовь", "здоровье", "финансы", "духовность"
            ]
        }


# Global filter instance
ai_content_filter = AIContentFilter()