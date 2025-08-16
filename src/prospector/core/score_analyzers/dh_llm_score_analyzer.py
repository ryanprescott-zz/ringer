"""DhLlmScoreAnalyzer - A score analyzer that uses the DH LLM service for content scoring."""

import json
import logging
import requests

from prospector.core.models import (
    DhLlmScoringSpec,
    PromptInput,
    TopicListInput,
    DhLlmGenerationInput,
    FieldMap,
    DhLlmGenerationRequest
)
from prospector.core.settings import DhLlmScoreAnalyzerSettings
from .score_analyzer import ScoreAnalyzer

logger = logging.getLogger(__name__)


class DhLlmScoreAnalyzer(ScoreAnalyzer):
    """Score analyzer that uses the DH LLM service for content scoring."""
    
    def __init__(self, spec: DhLlmScoringSpec):
        """
        Initialize the score analyzer.
        
        Args:
            spec: DhLlmScoringSpec containing LLM inputs (prompt or topics)
            
        Raises:
            ValueError: If keywords list is empty
        """
        self.settings = DhLlmScoreAnalyzerSettings()
        # Create a requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        # Get a prompt string based on the scoring input
        scoring_input = spec.scoring_input
        prompt_str = (
            scoring_input.prompt if isinstance(scoring_input, PromptInput)
            else self._build_default_prompt(scoring_input.topics) if isinstance(scoring_input, TopicListInput)
            else None
        )

        logger.info(f"Scoring prompt: {prompt_str}")

        # Create the generation input for the DH LLM service
        self._generation_input = DhLlmGenerationInput(
            prompt=prompt_str,
            output_format=FieldMap(name_to_type=self.settings.output_format)
        )
    
    def _build_default_prompt(self, topics: list[str]) -> str:
        """
        Build a default prompt string based on the provided topics.
        
        Args:
            topics: List of topics to include in the prompt
            
        Returns:
            str: Formatted prompt string
        """
        
        topics_str = ', '.join(topics)
        return f"{self.settings.default_prompt_template} {topics_str}"

    def score(self, content: str) -> float:
        """
        Score content using the DH LLM service.
        
        Makes an HTTP POST request to the configured service with the text
        content and prompt. Returns the score provided by the service.
        
        Args:
            content (str): Content to score
            
        Returns:
            float: Score between 0 and 1 from the service
            
        Raises:
            TypeError: If content is not DhLlmScoreServiceInput
        """
        if not isinstance(content, str):
            raise TypeError("Content must be a string")
            
        try:
            # Create the request payload
            request_data = DhLlmGenerationRequest(
                generation_input=self._generation_input,
                text_inputs=[content],  # Wrap text in a list for processing
            )
            
            # Make the HTTP POST request
            response = self.session.post(
                self.settings.service_url,
                json=request_data.model_dump(),
                timeout=self.settings.request_timeout,
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            response_data = response.json()
            
            # Extract score from response
            if 'score' not in response_data:
                logger.error(f"LLM service response missing 'score' field: {response_data}")
                return 0.0
            
            try:
                score = float(response_data['score'])
                
                # Validate score is in range 0-1
                if not (0.0 <= score <= 1.0):
                    logger.error(f"LLM service returned score outside 0-1 range: {score}")
                    return 0.0
                
                return score
                
            except (ValueError, TypeError) as e:
                logger.error(f"Could not parse score value '{response_data['score']}': {e}")
                return 0.0
        
        except requests.exceptions.Timeout as e:
            logger.error(f"LLM service request timeout: {e}")
            return 0.0
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM service request failed: {e}")
            return 0.0
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM service: {e}")
            return 0.0
        
        except Exception as e:
            logger.error(f"Unexpected error calling LLM service: {e}")
            return 0.0
    
    def __del__(self):
        """Cleanup the requests session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()
