"""
LangExtract Processor for structured information extraction from documents.

This processor uses LangExtract with Ollama for local LLM-based extraction
of structured information from documents.
"""

import time
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import langextract as lx
except ImportError:
    lx = None

try:
    from llama_stack_client import RAGDocument
except ImportError:
    class RAGDocument:
        def __init__(self, document_id: str, content: Any, mime_type: str, metadata: Optional[Dict] = None):
            self.document_id = document_id
            self.content = content
            self.mime_type = mime_type
            self.metadata = metadata or {}


class LangExtractProcessor:
    """
    LangExtract processor for structured information extraction using Ollama.
    
    This processor extracts structured information from documents using
    LangExtract with local Ollama models.
    """
    
    def __init__(self, 
                 model_id: str = "gemma3:4b",
                 model_url: str = "http://localhost:11434",
                 extraction_prompts: Optional[Dict[str, str]] = None):
        """
        Initialize LangExtract processor.
        
        Args:
            model_id: Ollama model to use (e.g., "gpt-oss:20b", "gemma2:2b", "llama3:8b")
            model_url: Ollama endpoint URL
            extraction_prompts: Dictionary of extraction prompts for different types
        """
        if lx is None:
            raise ImportError("LangExtract not installed. Run: pip install langextract")
            
        self.model_id = model_id
        self.model_url = model_url
        self.extraction_prompts = extraction_prompts or self._default_prompts()
        self.examples = self._create_examples()
        
        # Test Ollama connection
        self._test_connection()
    
    def _default_prompts(self) -> Dict[str, str]:
        """Default extraction prompts for common document types."""
        return {
            "general": "Extract key information including main topics, important entities, and key facts from this document.",
            "technical": "Extract technical specifications, requirements, procedures, and important technical details.",
            "legal": "Extract key legal terms, obligations, dates, parties involved, and important clauses.",
            "medical": "Extract medical conditions, treatments, medications, dosages, and important medical information.",
            "financial": "Extract financial data, amounts, dates, transactions, and key financial metrics."
        }
    
    def _create_examples(self) -> List[Dict]:
        """Create example data for LangExtract few-shot learning."""
        return [
            {
                "input": "The Wärtsilä 46F engine delivers 12.6 MW power at 514 rpm with fuel consumption of 190 g/kWh. Installation requires minimum 2.5m clearance.",
                "output": {
                    "power_output": "12.6 MW",
                    "operating_speed": "514 rpm", 
                    "fuel_consumption": "190 g/kWh",
                    "clearance_requirement": "2.5m minimum",
                    "product": "Wärtsilä 46F engine"
                }
            },
            {
                "input": "Project deadline is March 2025. Contact John Smith at john@example.com for technical support. Budget allocated: $2.5M.",
                "output": {
                    "deadline": "March 2025",
                    "contact_person": "John Smith",
                    "contact_email": "john@example.com",
                    "budget": "$2.5M",
                    "purpose": "technical support"
                }
            }
        ]
    
    def _test_connection(self):
        """Test connection to Ollama."""
        try:
            # Simple test extraction with examples
            test_result = lx.extract(
                text_or_documents="Test document with power rating 100 MW.",
                prompt_description="Extract any key information",
                examples=self.examples,
                model_id=self.model_id,
                model_url=self.model_url,
                fence_output=False,
                use_schema_constraints=False
            )
            print(f"✓ LangExtract connected to Ollama model: {self.model_id}")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to Ollama ({e})")
            print(f"Make sure Ollama is running and model '{self.model_id}' is available")
    
    def extract_from_text(self, 
                         text: str, 
                         extraction_type: str = "general",
                         custom_prompt: Optional[str] = None,
                         examples: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Extract structured information from text.
        
        Args:
            text: Input text to extract from
            extraction_type: Type of extraction ("general", "technical", etc.)
            custom_prompt: Custom extraction prompt (overrides extraction_type)
            examples: Examples for few-shot learning
            
        Returns:
            Dictionary with extracted information and metadata
        """
        start_time = time.time()
        
        try:
            prompt = custom_prompt or self.extraction_prompts.get(extraction_type, self.extraction_prompts["general"])
            
            result = lx.extract(
                text_or_documents=text,
                prompt_description=prompt,
                examples=examples or self.examples,
                model_id=self.model_id,
                model_url=self.model_url,
                fence_output=False,
                use_schema_constraints=False
            )
            
            processing_time = time.time() - start_time
            
            return {
                "extracted_data": result,
                "extraction_type": extraction_type,
                "prompt_used": prompt,
                "processing_time_seconds": processing_time,
                "model_id": self.model_id,
                "text_length": len(text),
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "extraction_type": extraction_type,
                "processing_time_seconds": time.time() - start_time,
                "model_id": self.model_id,
                "text_length": len(text),
                "success": False
            }
    
    def process_document_with_extraction(self, 
                                       document_text: str,
                                       document_id: str,
                                       extraction_type: str = "general",
                                       custom_prompt: Optional[str] = None) -> RAGDocument:
        """
        Process document and extract structured information.
        
        Args:
            document_text: Text content of the document
            document_id: Document identifier
            extraction_type: Type of extraction to perform
            custom_prompt: Custom extraction prompt
            
        Returns:
            RAGDocument with original text and extracted structured data
        """
        extraction_result = self.extract_from_text(
            text=document_text,
            extraction_type=extraction_type,
            custom_prompt=custom_prompt
        )
        
        # Create enriched content with both original and extracted data
        enriched_content = {
            "original_text": document_text,
            "extracted_information": extraction_result.get("extracted_data", {}),
            "extraction_metadata": {
                "type": extraction_type,
                "model": self.model_id,
                "processing_time": extraction_result.get("processing_time_seconds", 0),
                "success": extraction_result.get("success", False)
            }
        }
        
        metadata = {
            "document_id": document_id,
            "processing_method": "langextract",
            "extraction_type": extraction_type,
            "model_id": self.model_id,
            "processing_time_seconds": extraction_result.get("processing_time_seconds", 0),
            "text_length": len(document_text),
            "extraction_success": extraction_result.get("success", False),
            "langextract_version": "1.0.9"
        }
        
        return RAGDocument(
            document_id=document_id,
            content=enriched_content,
            mime_type="application/json",
            metadata=metadata
        )
    
    def extract_key_entities(self, text: str) -> Dict[str, Any]:
        """Extract key entities like names, dates, locations, etc."""
        prompt = """Extract key entities from this text including:
        - People names
        - Organizations
        - Locations
        - Dates
        - Numbers/quantities
        - Key concepts or topics
        """
        
        return self.extract_from_text(text, custom_prompt=prompt)
    
    def summarize_and_extract(self, text: str) -> Dict[str, Any]:
        """Create a summary and extract key points."""
        prompt = """Provide a concise summary of this document and extract:
        - Main topics/themes
        - Key facts or findings
        - Important recommendations or conclusions
        - Critical dates or deadlines
        """
        
        return self.extract_from_text(text, custom_prompt=prompt)
    
    def extract_action_items(self, text: str) -> Dict[str, Any]:
        """Extract action items, tasks, and requirements."""
        prompt = """Extract action items and tasks from this document including:
        - Required actions or tasks
        - Responsibilities and assignments
        - Deadlines or timeframes
        - Requirements or specifications
        - Next steps or follow-ups
        """
        
        return self.extract_from_text(text, custom_prompt=prompt)
    
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models (requires requests)."""
        try:
            import requests
            response = requests.get(f"{self.model_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except Exception as e:
            print(f"Could not fetch available models: {e}")
        
        return ["gemma2:2b", "llama3:8b", "mistral:7b"]  # Common models
    
    def benchmark_extraction(self, text: str) -> Dict[str, Any]:
        """Benchmark extraction performance."""
        results = {}
        
        extraction_types = ["general", "technical", "entities", "summary"]
        
        for ext_type in extraction_types:
            if ext_type == "entities":
                result = self.extract_key_entities(text)
            elif ext_type == "summary":
                result = self.summarize_and_extract(text)
            else:
                result = self.extract_from_text(text, extraction_type=ext_type)
            
            results[ext_type] = {
                "processing_time": result.get("processing_time_seconds", 0),
                "success": result.get("success", False),
                "data_length": len(str(result.get("extracted_data", "")))
            }
        
        return results


def test_langextract_basic():
    """Basic test of LangExtract functionality."""
    print("Testing LangExtract with Ollama...")
    
    try:
        processor = LangExtractProcessor()
        
        test_text = """
        Wärtsilä 46F Project Guide
        
        This technical document provides specifications for the Wärtsilä 46F engine.
        Key specifications include:
        - Power output: 12.6 MW
        - Fuel consumption: 190 g/kWh
        - Operating speed: 514 rpm
        - Installation requirements: Minimum clearance 2.5m
        
        The project timeline is 18 months with delivery scheduled for Q2 2025.
        Contact: engineering@wartsila.com for technical support.
        """
        
        # Test different extraction types
        print("\n1. General extraction:")
        result = processor.extract_from_text(test_text, "general")
        print(f"Time: {result.get('processing_time_seconds', 0):.2f}s")
        print(f"Success: {result.get('success', False)}")
        if result.get("extracted_data"):
            print(f"Extracted: {result['extracted_data']}")
        
        print("\n2. Technical extraction:")
        result = processor.extract_from_text(test_text, "technical")
        print(f"Time: {result.get('processing_time_seconds', 0):.2f}s")
        print(f"Extracted: {result.get('extracted_data', 'N/A')}")
        
        print("\n3. Key entities:")
        result = processor.extract_key_entities(test_text)
        print(f"Time: {result.get('processing_time_seconds', 0):.2f}s")
        print(f"Entities: {result.get('extracted_data', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    test_langextract_basic()
