import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import io
import streamlit as st
from translations import TRANSLATIONS

def get_text(key: str, language: str = None) -> str:
    '''Get translated text for the given key.'''
    if language is None:
        language = st.session_state.get('language', 'en')
    
    # Split the key into sections (e.g., 'navigation.dashboard')
    sections = key.split('.')
    current = TRANSLATIONS[language]
    
    try:
        for section in sections:
            current = current[section]
        return current
    except (KeyError, TypeError):
        # Fallback to English if translation not found
        current = TRANSLATIONS['en']
        for section in sections:
            current = current[section]
        return current

[Previous helper functions remain unchanged...]
