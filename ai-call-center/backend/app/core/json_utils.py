"""
JSON parsing utilities for handling LLM outputs.

LLMs often return JSON wrapped in markdown code blocks or with
minor formatting issues. These utilities handle those edge cases.
"""

import json
import re
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_json_from_llm_response(content: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract JSON from LLM response.
    
    Handles:
    - Markdown code blocks (```json ... ```)
    - Leading/trailing whitespace
    - Single quotes instead of double quotes
    - Trailing commas
    - Incomplete/truncated JSON (attempts repair)
    
    Returns None if extraction fails.
    """
    if not content or not content.strip():
        return None
    
    clean_content = content.strip()
    
    # 1. Handle markdown code blocks
    if "```" in clean_content:
        # Try to extract JSON from code block
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
            r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        ]
        for pattern in patterns:
            match = re.search(pattern, clean_content)
            if match:
                clean_content = match.group(1).strip()
                break
    
    # 2. Try direct JSON parse first
    try:
        return json.loads(clean_content)
    except json.JSONDecodeError:
        pass
    
    # 3. Try to fix common issues
    fixed_content = clean_content
    
    # Replace single quotes with double quotes (careful with apostrophes)
    # Only replace if it looks like JSON structure
    if fixed_content.startswith("{") or fixed_content.startswith("["):
        # Use a more careful replacement
        fixed_content = _fix_json_quotes(fixed_content)
    
    try:
        return json.loads(fixed_content)
    except json.JSONDecodeError:
        pass
    
    # 4. Try removing trailing commas
    fixed_content = re.sub(r',(\s*[}\]])', r'\1', fixed_content)
    try:
        return json.loads(fixed_content)
    except json.JSONDecodeError:
        pass
    
    # 5. Try to extract any valid JSON object
    try:
        # Find the first { and last }
        start = fixed_content.find('{')
        end = fixed_content.rfind('}')
        if start != -1 and end > start:
            potential_json = fixed_content[start:end+1]
            return json.loads(potential_json)
    except json.JSONDecodeError:
        pass
    
    # 6. Attempt to repair truncated JSON
    repaired = _attempt_json_repair(fixed_content)
    if repaired:
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass
    
    logger.warning(f"Failed to parse JSON. Raw content (first 500 chars): {content[:500]}")
    return None


def _fix_json_quotes(content: str) -> str:
    """
    Attempt to fix single quotes to double quotes in JSON.
    
    This is tricky because we need to handle:
    - 'key': value -> "key": value
    - 'value' -> "value"
    - But not: don't, it's (apostrophes in text)
    """
    result = []
    in_string = False
    string_char = None
    i = 0
    
    while i < len(content):
        char = content[i]
        
        if not in_string:
            if char == '"':
                in_string = True
                string_char = '"'
                result.append(char)
            elif char == "'":
                # Check if this looks like a JSON string start
                # (after :, [, {, or at start)
                prev_non_space = ''
                for j in range(i-1, -1, -1):
                    if content[j] not in ' \t\n':
                        prev_non_space = content[j]
                        break
                
                if prev_non_space in ':,[{' or i == 0:
                    in_string = True
                    string_char = "'"
                    result.append('"')  # Replace with double quote
                else:
                    result.append(char)
            else:
                result.append(char)
        else:
            if char == string_char and (i == 0 or content[i-1] != '\\'):
                in_string = False
                if string_char == "'":
                    result.append('"')  # Replace closing single quote
                else:
                    result.append(char)
            elif char == '"' and string_char == "'":
                result.append('\\"')  # Escape double quotes inside single-quoted strings
            else:
                result.append(char)
        
        i += 1
    
    return ''.join(result)


def _attempt_json_repair(content: str) -> Optional[str]:
    """
    Attempt to repair truncated JSON by closing open brackets and braces.
    """
    if not content.strip():
        return None
    
    # Count open brackets/braces
    stack = []
    in_string = False
    escape_next = False
    
    for char in content:
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"':
            in_string = not in_string
            continue
        
        if in_string:
            continue
        
        if char in '{[':
            stack.append('}' if char == '{' else ']')
        elif char in '}]':
            if stack and stack[-1] == char:
                stack.pop()
    
    if stack:
        # Close unclosed brackets
        repaired = content.rstrip()
        
        # Check if we're in the middle of a string
        if in_string:
            repaired += '"'
        
        # Close remaining brackets
        while stack:
            repaired += stack.pop()
        
        return repaired
    
    return content
