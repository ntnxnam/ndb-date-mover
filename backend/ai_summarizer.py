"""
AI Summarizer Module

Provides functionality to summarize text content in an executive-friendly format.
Uses Anthropic Claude API for actual LLM-based summarization.

Author: NDB Date Mover Team
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")

# Default AI prompt for summarization
DEFAULT_AI_PROMPT = "Make it succinct, exec ready and with as few lines as possible."


def load_ai_prompt(prompt_file: Optional[str] = None) -> str:
    """
    Load AI prompt from configuration file.
    
    Args:
        prompt_file: Optional path to prompt file. If None, uses default location.
        
    Returns:
        str: AI prompt text
    """
    if prompt_file is None:
        # Default location: config/ai_prompt.txt
        project_root = Path(__file__).parent.parent
        prompt_file = project_root / "config" / "ai_prompt.txt"
    
    prompt_path = Path(prompt_file)
    
    if prompt_path.exists() and prompt_path.is_file():
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
            if prompt:
                logger.info(f"Loaded AI prompt from {prompt_path}")
                return prompt
        except Exception as e:
            logger.warning(f"Error loading AI prompt from {prompt_path}: {str(e)}")
    
    # Return default prompt if file doesn't exist or is empty
    logger.info("Using default AI prompt")
    return DEFAULT_AI_PROMPT


def call_claude_api(text: str, prompt: str) -> Optional[str]:
    """
    Call Anthropic Claude API to summarize text using the provided prompt.
    
    Supports multiple API providers:
    1. Anthropic Claude API (if ANTHROPIC_API_KEY is set)
    2. OpenAI API (if OPENAI_API_KEY is set, as fallback)
    
    Args:
        text: The text to summarize
        prompt: The system prompt/instructions for summarization
        
    Returns:
        Optional[str]: The AI-generated summary, or None if API call fails
    """
    # Try Anthropic Claude API first
    if ANTHROPIC_AVAILABLE:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            try:
                client = Anthropic(api_key=api_key)
                
                # Call Claude API
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",  # Use latest Claude 3.5 Sonnet
                    max_tokens=500,
                    system=prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": text
                        }
                    ]
                )
                
                # Extract the summary from the response
                if message.content and len(message.content) > 0:
                    summary = message.content[0].text
                    logger.info(f"Claude API returned summary of {len(summary)} characters")
                    return summary
                else:
                    logger.warning("Claude API returned empty response")
            except Exception as e:
                logger.error(f"Error calling Claude API: {str(e)}", exc_info=True)
    
    # Try OpenAI API as fallback
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent summaries
            )
            
            if response.choices and len(response.choices) > 0:
                summary = response.choices[0].message.content
                logger.info(f"OpenAI API returned summary of {len(summary)} characters")
                return summary
        except ImportError:
            logger.debug("OpenAI SDK not installed")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
    
    # No API keys available
    logger.warning("No AI API keys found (ANTHROPIC_API_KEY or OPENAI_API_KEY). Falling back to rule-based summarization.")
    return None


def summarize_for_executives(
    text: str, 
    max_length: int = 200,
    prompt: Optional[str] = None
) -> str:
    """
    Summarize text content in an executive-friendly format.
    
    Uses the prompt to guide intelligent extraction of key information:
    - Current status
    - Blockers
    - Ownership
    - Timelines
    - Asks
    
    Args:
        text: The text to summarize
        max_length: Maximum length of the summary
        prompt: Optional AI prompt for summarization context
        
    Returns:
        str: Executive-friendly summary
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Load prompt if not provided
    if prompt is None:
        prompt = load_ai_prompt()
    
    # Log the prompt being used (for debugging)
    logger.debug(f"Using AI prompt: {prompt[:100]}...")
    
    # Clean the text
    text = " ".join(text.split())
    
    # If text is already short, return as-is
    if len(text) <= max_length:
        return text
    
    # Try to use Claude API first
    ai_summary = call_claude_api(text, prompt)
    if ai_summary:
        logger.info("Using Claude API summary")
        # Trim to max_length if needed
        if len(ai_summary) > max_length:
            ai_summary = ai_summary[:max_length - 3].rsplit(' ', 1)[0] + '...'
        return ai_summary.strip()
    
    # Fallback to rule-based extraction if API is not available
    logger.info("Falling back to rule-based summarization")
    
    # Extract key information based on prompt guidance
    # The prompt asks for: status, blockers, ownership, timelines, asks
    import re
    summary_parts = []
    
    # Status keywords to look for
    status_keywords = [
        'In progress', 'In Review', 'Yet to start', 'NA', 'Complete', 
        'Done', 'Blocked', 'Pending', 'Review', 'Testing'
    ]
    
    # Split by hash (#) to get sections
    sections = [s.strip() for s in text.split('#') if s.strip()]
    
    # Extract key information from each section
    important_sections = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Extract section name (text between asterisks, remove trailing colon if present)
        name_match = re.search(r'\*([^*]+)\*', section)
        section_name = name_match.group(1).strip() if name_match else ""
        # Remove trailing colon from section name
        section_name = section_name.rstrip(':').strip()
        
        # Check if section has status information
        has_status = any(kw.lower() in section.lower() for kw in status_keywords)
        
        # Extract ETA/timeline
        eta_match = re.search(r'ETA[:\s-]+(\d+/\w+)', section, re.IGNORECASE)
        eta = eta_match.group(1) if eta_match else None
        
        # Extract status value
        status_value = None
        for kw in status_keywords:
            if kw.lower() in section.lower():
                status_value = kw
                break
        
        # Build concise section summary (skip NA sections unless critical)
        if section_name and (has_status or eta):
            # Skip pure "NA" sections to keep summary focused
            if status_value and status_value.upper() == 'NA' and not eta:
                continue
                
            # Build formatted section summary
            if eta:
                if status_value and status_value.upper() != 'NA':
                    important_sections.append(f"{section_name}: {status_value} ETA: {eta}")
                else:
                    important_sections.append(f"{section_name} ETA: {eta}")
            elif status_value and status_value.upper() != 'NA':
                important_sections.append(f"{section_name}: {status_value}")
    
    # Extract blockers/concerns
    blockers = []
    concern_patterns = [
        r'[Cc]oncern[:\s*]+([^#\n]+)',
        r'[Bb]locker[:\s*]+([^#\n]+)',
        r'[Rr]isk[:\s*]+([^#\n]+)',
    ]
    for pattern in concern_patterns:
        matches = re.findall(pattern, text)
        blockers.extend([m.strip() for m in matches if m.strip()])
    
    # Build summary based on prompt: "one-glance, C-suite project snapshot"
    # Focus on: current status, blockers, timelines, asks
    
    # Priority 1: Most critical sections (limit to 3-4 most important)
    if important_sections:
        # Filter out "NA" sections unless they're the only info
        non_na_sections = [s for s in important_sections if 'NA' not in s.upper()]
        if non_na_sections:
            summary_parts.extend(non_na_sections[:4])
        else:
            summary_parts.extend(important_sections[:3])
    
    # Priority 2: Blockers/Concerns (critical for executives)
    if blockers:
        summary_parts.append(f"⚠️ {blockers[0][:60]}")
    
    # Combine into concise summary
    if summary_parts:
        summary = " | ".join(summary_parts)
        # Trim to max_length if needed
        if len(summary) > max_length:
            # Try to keep most important parts
            words = summary.split(' | ')
            summary = words[0]
            for word in words[1:]:
                if len(summary + ' | ' + word) <= max_length - 3:
                    summary += ' | ' + word
                else:
                    break
            if len(summary) < max_length - 10:  # If we have space, add ellipsis
                summary += '...'
        return summary
    
    # Fallback: intelligent truncation
    # Try to find the most important sentence
    sentences = text.split('. ')
    if sentences:
        # Find sentence with most keywords
        best_sentence = sentences[0]
        max_keywords = 0
        for sentence in sentences[:5]:  # Check first 5 sentences
            keyword_count = sum(1 for kw in status_keywords if kw.lower() in sentence.lower())
            if keyword_count > max_keywords:
                max_keywords = keyword_count
                best_sentence = sentence
        
        if len(best_sentence) <= max_length:
            return best_sentence.strip()
    
    # Final fallback: truncate at word boundary
    summary = text[:max_length - 3].rsplit(' ', 1)[0] + '...'
    return summary


def summarize_status_update(
    status_text: str,
    prompt: Optional[str] = None
) -> str:
    """
    Summarize a status update field in an executive-friendly format.
    
    Args:
        status_text: The status update text to summarize
        prompt: Optional AI prompt for summarization context
        
    Returns:
        str: Executive-friendly summary
    """
    if not status_text:
        return ""
    
    # Clean the text
    text = str(status_text).strip()
    
    # Remove common prefixes/suffixes that aren't useful
    prefixes_to_remove = [
        "Status:",
        "Update:",
        "Note:",
        "Comment:",
    ]
    
    for prefix in prefixes_to_remove:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    
    # Summarize to executive-friendly length (150-200 chars)
    return summarize_for_executives(text, max_length=200, prompt=prompt)

