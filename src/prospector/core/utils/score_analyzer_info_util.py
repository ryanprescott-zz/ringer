"""Utility for gathering information about available score analyzers."""

import inspect
from typing import List, Dict, Any, get_origin, get_args
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from ..score_analyzers import KeywordScoreAnalyzer, LLMServiceScoreAnalyzer
from ..models import KeywordScoringSpec, LLMScoringSpec, PromptInput, TopicListInput


class FieldDescriptor:
    """Descriptor for a field in an analyzer spec."""
    
    def __init__(self, name: str, type_str: str, description: str, required: bool, default: str = None):
        self.name = name
        self.type_str = type_str
        self.description = description
        self.required = required
        self.default = default


class AnalyzerInfo:
    """Information about a score analyzer."""
    
    def __init__(self, name: str, description: str, spec_fields: List[FieldDescriptor]):
        self.name = name
        self.description = description
        self.spec_fields = spec_fields


class ScoreAnalyzerInfoUtil:
    """Utility class for gathering information about available score analyzers."""
    
    # Hardcoded list of known analyzers and their spec classes
    KNOWN_ANALYZERS = {
        "KeywordScoreAnalyzer": {
            "class": KeywordScoreAnalyzer,
            "spec_class": KeywordScoringSpec
        },
        "LLMServiceScoreAnalyzer": {
            "class": LLMServiceScoreAnalyzer,
            "spec_class": LLMScoringSpec
        }
    }
    
    @classmethod
    def get_analyzer_info_list(cls) -> List[AnalyzerInfo]:
        """
        Get information about all available score analyzers.
        
        Returns:
            List of AnalyzerInfo objects containing analyzer details
        """
        analyzer_infos = []
        
        for analyzer_name, analyzer_config in cls.KNOWN_ANALYZERS.items():
            analyzer_class = analyzer_config["class"]
            spec_class = analyzer_config["spec_class"]
            
            # Extract description from class docstring
            description = cls._extract_class_description(analyzer_class)
            
            # Get field descriptors from the spec class
            spec_fields = cls._get_spec_field_descriptors(spec_class)
            
            analyzer_info = AnalyzerInfo(
                name=analyzer_name,
                description=description,
                spec_fields=spec_fields
            )
            analyzer_infos.append(analyzer_info)
        
        return analyzer_infos
    
    @classmethod
    def _extract_class_description(cls, analyzer_class) -> str:
        """
        Extract description from class docstring.
        
        Args:
            analyzer_class: The analyzer class to extract description from
            
        Returns:
            Description string from the class docstring
        """
        docstring = inspect.getdoc(analyzer_class)
        if docstring:
            # Take the first line of the docstring as the description
            return docstring.split('\n')[0].strip()
        return f"Score analyzer: {analyzer_class.__name__}"
    
    @classmethod
    def _get_spec_field_descriptors(cls, spec_class: BaseModel) -> List[FieldDescriptor]:
        """
        Get field descriptors for a Pydantic model class.
        
        Args:
            spec_class: Pydantic model class to analyze
            
        Returns:
            List of FieldDescriptor objects
        """
        field_descriptors = []
        
        # Get model fields from Pydantic model
        model_fields = spec_class.model_fields
        
        for field_name, field_info in model_fields.items():
            # Get field type as string
            type_str = cls._get_field_type_string(field_info.annotation)
            
            # Get field description
            description = field_info.description or f"Field: {field_name}"
            
            # Check if field is required
            required = field_info.is_required()
            
            # Get default value as string
            default_str = None
            if not required and field_info.default is not None:
                default_str = str(field_info.default)
            
            field_descriptor = FieldDescriptor(
                name=field_name,
                type_str=type_str,
                description=description,
                required=required,
                default=default_str
            )
            field_descriptors.append(field_descriptor)
        
        return field_descriptors
    
    @classmethod
    def _get_field_type_string(cls, field_type) -> str:
        """
        Convert a field type annotation to a string representation.
        
        Args:
            field_type: Type annotation from Pydantic field
            
        Returns:
            String representation of the type
        """
        # Handle Union types (e.g., PromptInput | TopicListInput)
        origin = get_origin(field_type)
        if origin is not None:
            args = get_args(field_type)
            
            # Handle Union types
            if hasattr(field_type, '__origin__') and str(field_type).startswith('typing.Union'):
                type_names = [cls._get_simple_type_name(arg) for arg in args if arg != type(None)]
                return " | ".join(type_names)
            
            # Handle other generic types like List, Dict, etc.
            if origin == list:
                if args:
                    inner_type = cls._get_simple_type_name(args[0])
                    return f"List[{inner_type}]"
                return "List"
            
            if origin == dict:
                if len(args) >= 2:
                    key_type = cls._get_simple_type_name(args[0])
                    value_type = cls._get_simple_type_name(args[1])
                    return f"Dict[{key_type}, {value_type}]"
                return "Dict"
        
        # Handle simple types and custom classes
        return cls._get_simple_type_name(field_type)
    
    @classmethod
    def _get_simple_type_name(cls, type_obj) -> str:
        """
        Get a simple string name for a type.
        
        Args:
            type_obj: Type object
            
        Returns:
            Simple string name for the type
        """
        if hasattr(type_obj, '__name__'):
            return type_obj.__name__
        
        # Handle string representations
        type_str = str(type_obj)
        
        # Clean up common type string patterns
        if 'typing.' in type_str:
            type_str = type_str.replace('typing.', '')
        
        # Extract class name from module paths
        if '.' in type_str and not type_str.startswith('typing'):
            parts = type_str.split('.')
            return parts[-1]
        
        return type_str
