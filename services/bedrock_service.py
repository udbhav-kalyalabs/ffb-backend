"""
AWS Bedrock service for interacting with Claude 3.5 Sonnet
"""
import json
import boto3
from typing import Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class BedrockService:
    """Service for AWS Bedrock model inference"""
    
    def __init__(self):
        """Initialize Bedrock client"""
        # Determine region based on inference profile or default
        region = settings.AWS_REGION
        if settings.BEDROCK_USE_INFERENCE_PROFILE and settings.BEDROCK_INFERENCE_PROFILE_ARN:
            # Extract region from ARN: arn:aws:bedrock:REGION:...
            arn_parts = settings.BEDROCK_INFERENCE_PROFILE_ARN.split(":")
            if len(arn_parts) >= 4:
                region = arn_parts[3]
                logger.info(f"Using region {region} from inference profile ARN")
        
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        # Use inference profile ARN if available, otherwise use model ID
        if settings.BEDROCK_USE_INFERENCE_PROFILE and settings.BEDROCK_INFERENCE_PROFILE_ARN:
            self.model_id = settings.BEDROCK_INFERENCE_PROFILE_ARN
            logger.info(f"Using inference profile: {self.model_id}")
        else:
            self.model_id = settings.BEDROCK_MODEL_ID
            logger.info(f"Using model ID: {self.model_id}")
        
    def invoke_model_with_image(
        self,
        prompt: str,
        image_base64: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model with image and text prompt (Claude format)
        
        Args:
            prompt: Text prompt for analysis
            image_base64: Base64 encoded image
            system_prompt: Optional system prompt
            temperature: Sampling temperature (default from settings)
            max_tokens: Maximum tokens to generate (default from settings)
        
        Returns:
            Model response as dictionary
        """
        try:
            # Claude 3.5 Sonnet message format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # Prepare request body for Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "messages": messages,
                "max_tokens": max_tokens or settings.BEDROCK_MAX_TOKENS,
                "temperature": temperature if temperature is not None else settings.BEDROCK_TEMPERATURE,
                "top_p": settings.BEDROCK_TOP_P,
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_body["system"] = system_prompt
            
            logger.info(f"Invoking Bedrock model: {self.model_id}")
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            logger.info("Successfully received model response")
            
            return response_body
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {str(e)}")
            raise
    
    def parse_model_response(self, response: Dict[str, Any]) -> str:
        """
        Parse model response to extract generated text (Claude format)
        
        Args:
            response: Raw response from Bedrock
        
        Returns:
            Generated text content
        """
        try:
            # Claude response format: {"content": [{"type": "text", "text": "..."}]}
            if "content" in response:
                for content_block in response["content"]:
                    if content_block.get("type") == "text":
                        return content_block.get("text", "")
            
            # Fallback for other formats
            if "generation" in response:
                return response["generation"]
            elif "output" in response:
                return response["output"]
            
            # Last resort: return entire response as string
            logger.warning("Unexpected response format, returning as string")
            return json.dumps(response)
            
        except Exception as e:
            logger.error(f"Error parsing model response: {str(e)}")
            raise
    
    def analyze_image(
        self,
        prompt: str,
        image_base64: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        High-level method to analyze an image
        
        Args:
            prompt: Analysis prompt
            image_base64: Base64 encoded image
            system_prompt: Optional system prompt
        
        Returns:
            Model's text response
        """
        response = self.invoke_model_with_image(
            prompt=prompt,
            image_base64=image_base64,
            system_prompt=system_prompt
        )
        
        return self.parse_model_response(response)

# Global instance
bedrock_service = BedrockService()
