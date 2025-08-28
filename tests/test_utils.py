"""Tests for utility classes."""

import pytest
from ringer.core.utils import ScoreAnalyzerInfoUtil


class TestScoreAnalyzerInfoUtil:
    """Tests for ScoreAnalyzerInfoUtil class."""
    
    def test_get_analyzer_info_list(self):
        """Test getting analyzer information list."""
        analyzer_infos = ScoreAnalyzerInfoUtil.get_analyzer_info_list()
        
        # Should have at least 2 analyzers
        assert len(analyzer_infos) >= 2
        
        # Check analyzer names
        analyzer_names = [info.name for info in analyzer_infos]
        assert "KeywordScoreAnalyzer" in analyzer_names
        assert "DhLlmScoreAnalyzer" in analyzer_names
    
    def test_keyword_analyzer_info(self):
        """Test KeywordScoreAnalyzer information."""
        analyzer_infos = ScoreAnalyzerInfoUtil.get_analyzer_info_list()
        
        keyword_info = next(info for info in analyzer_infos if info.name == "KeywordScoreAnalyzer")
        
        # Check basic info
        assert keyword_info.name == "KeywordScoreAnalyzer"
        assert keyword_info.description is not None
        assert len(keyword_info.description) > 0
        
        # Check fields
        field_names = [field.name for field in keyword_info.spec_fields]
        assert "name" in field_names
        assert "composite_weight" in field_names
        assert "keywords" in field_names
        
        # Check keywords field details
        keywords_field = next(field for field in keyword_info.spec_fields if field.name == "keywords")
        assert "List[WeightedKeyword]" in keywords_field.type_str
        assert not keywords_field.required  # keywords is now optional with default=[]
        
        # Check regexes field details
        regexes_field = next(field for field in keyword_info.spec_fields if field.name == "regexes")
        assert "List[WeightedRegex]" in regexes_field.type_str
        assert not regexes_field.required  # regexes is now optional with default=[]
    
    def test_llm_analyzer_info(self):
        """Test DhLlmScoreAnalyzer information."""
        analyzer_infos = ScoreAnalyzerInfoUtil.get_analyzer_info_list()
        
        llm_info = next(info for info in analyzer_infos if info.name == "DhLlmScoreAnalyzer")
        
        # Check basic info
        assert llm_info.name == "DhLlmScoreAnalyzer"
        assert llm_info.description is not None
        assert len(llm_info.description) > 0
        
        # Check fields
        field_names = [field.name for field in llm_info.spec_fields]
        assert "name" in field_names
        assert "composite_weight" in field_names
        assert "prompt_input" in field_names
        
        # Check prompt_input field type
        prompt_input_field = next(field for field in llm_info.spec_fields if field.name == "prompt_input")
        assert "PromptInput" in prompt_input_field.type_str
        assert prompt_input_field.required
    
    def test_extract_class_description(self):
        """Test extracting class description from docstring."""
        from ringer.core.score_analyzers import KeywordScoreAnalyzer
        
        description = ScoreAnalyzerInfoUtil._extract_class_description(KeywordScoreAnalyzer)
        
        # Should extract first line of docstring
        assert description is not None
        assert len(description) > 0
        assert "Score analyzer that scores text based on keyword and regex matches." in description
    
    def test_get_field_type_string_union(self):
        """Test getting field type string for union types."""
        from ringer.core.models import PromptInput, TextInput
        from typing import Union
        
        union_type = Union[PromptInput, TextInput]
        type_str = ScoreAnalyzerInfoUtil._get_field_type_string(union_type)
        
        # Should show both types
        assert "PromptInput" in type_str
        assert "TextInput" in type_str
        assert "|" in type_str
    
    def test_get_field_type_string_list(self):
        """Test getting field type string for list types."""
        from ringer.core.models import WeightedKeyword
        from typing import List
        
        list_type = List[WeightedKeyword]
        type_str = ScoreAnalyzerInfoUtil._get_field_type_string(list_type)
        
        assert type_str == "List[WeightedKeyword]"
    
    def test_get_simple_type_name(self):
        """Test getting simple type names."""
        # Test basic types
        assert ScoreAnalyzerInfoUtil._get_simple_type_name(str) == "str"
        assert ScoreAnalyzerInfoUtil._get_simple_type_name(int) == "int"
        assert ScoreAnalyzerInfoUtil._get_simple_type_name(float) == "float"
        
        # Test custom class
        from ringer.core.models import WeightedKeyword
        assert ScoreAnalyzerInfoUtil._get_simple_type_name(WeightedKeyword) == "WeightedKeyword"
