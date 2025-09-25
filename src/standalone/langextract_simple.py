"""
Simple LangExtract integration for document processing.

Minimal working example with Ollama that focuses on getting basic extraction working.
"""

import time
import os
from typing import Optional, Dict, Any, List

try:
    import langextract as lx
    from langextract import ExampleData
except ImportError:
    lx = None
    ExampleData = None

def test_langextract_simple():
    """Simple test without complex examples first."""
    print("Testing LangExtract with Ollama (Simple Version)...")
    
    if lx is None:
        print("❌ LangExtract not installed. Run: pip install langextract")
        return False
    
    try:
        # Very simple test without examples first
        print("\n1. Testing connection to Ollama...")
        
        # Simple extraction without examples to test connection
        result = lx.extract(
            text_or_documents="Wärtsilä engine power 12.6 MW, speed 514 rpm",
            prompt_description="Extract the power and speed values",
            model_id="gpt-oss:20b",
            model_url="http://localhost:11434"
        )
        
        print(f"✓ Connection successful!")
        print(f"Extracted: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_examples():
    """Test with proper LangExtract examples."""
    print("\n2. Testing with examples...")
    
    try:
        # Create proper examples using ExampleData
        examples = [
            ExampleData(
                text="The Wärtsilä 46F engine delivers 12.6 MW power at 514 rpm",
                extractions=[
                    {"power": "12.6 MW", "speed": "514 rpm", "model": "Wärtsilä 46F"}
                ]
            ),
            ExampleData(
                text="Project deadline March 2025, budget $2.5M, contact john@example.com",
                extractions=[
                    {"deadline": "March 2025", "budget": "$2.5M", "contact": "john@example.com"}
                ]
            )
        ]
        
        # Test extraction with examples
        result = lx.extract(
            text_or_documents="""
            Wärtsilä 46F Project Guide
            
            This technical document provides specifications for the Wärtsilä 46F engine.
            Key specifications include:
            - Power output: 12.6 MW
            - Fuel consumption: 190 g/kWh
            - Operating speed: 514 rpm
            - Installation requirements: Minimum clearance 2.5m
            
            The project timeline is 18 months with delivery scheduled for Q2 2025.
            Contact: engineering@wartsila.com for technical support.
            """,
            prompt_description="Extract technical specifications, timeline, and contact information",
            examples=examples,
            model_id="gpt-oss:20b",
            model_url="http://localhost:11434"
        )
        
        print(f"✓ Extraction with examples successful!")
        print(f"Extracted data: {result}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error with examples: {e}")
        return None

def simple_document_processor(text: str, extraction_type: str = "general") -> Dict[str, Any]:
    """Simple document processor using LangExtract."""
    
    prompts = {
        "general": "Extract key information including important facts, entities, and concepts",
        "technical": "Extract technical specifications, measurements, requirements, and procedures",
        "contact": "Extract contact information, names, emails, phone numbers, and addresses",
        "timeline": "Extract dates, deadlines, timelines, and scheduling information"
    }
    
    # Simple examples for each type
    examples_map = {
        "general": [
            ExampleData(
                text="The project involves installing new equipment worth $1M by December 2024",
                extractions=[{"equipment": "new equipment", "cost": "$1M", "deadline": "December 2024"}]
            )
        ],
        "technical": [
            ExampleData(
                text="Engine power 12.6 MW, speed 514 rpm, fuel consumption 190 g/kWh",
                extractions=[{"power": "12.6 MW", "speed": "514 rpm", "fuel_consumption": "190 g/kWh"}]
            )
        ],
        "contact": [
            ExampleData(
                text="Contact John Smith at john.smith@company.com or call +1-555-0123",
                extractions=[{"name": "John Smith", "email": "john.smith@company.com", "phone": "+1-555-0123"}]
            )
        ],
        "timeline": [
            ExampleData(
                text="Phase 1 starts January 2025, Phase 2 in March 2025, completion by June 2025",
                extractions=[{"phase_1": "January 2025", "phase_2": "March 2025", "completion": "June 2025"}]
            )
        ]
    }
    
    start_time = time.time()
    
    try:
        prompt = prompts.get(extraction_type, prompts["general"])
        examples = examples_map.get(extraction_type, examples_map["general"])
        
        result = lx.extract(
            text_or_documents=text,
            prompt_description=prompt,
            examples=examples,
            model_id="gpt-oss:20b",
            model_url="http://localhost:11434"
        )
        
        processing_time = time.time() - start_time
        
        return {
            "extracted_data": result,
            "extraction_type": extraction_type,
            "processing_time_seconds": processing_time,
            "success": True,
            "text_length": len(text)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "extraction_type": extraction_type,
            "processing_time_seconds": time.time() - start_time,
            "success": False,
            "text_length": len(text)
        }

def main():
    """Main test function."""
    print("LangExtract Simple Integration Test")
    print("=" * 50)
    
    # Test basic connection
    if not test_langextract_simple():
        print("\n❌ Basic connection failed. Check if Ollama is running.")
        return
    
    # Test with examples
    result = test_with_examples()
    if not result:
        print("\n❌ Examples test failed.")
        return
    
    print("\n3. Testing document processor function...")
    
    test_text = """
    Wärtsilä 46F Technical Specifications
    
    Engine Details:
    - Model: Wärtsilä 46F
    - Power Output: 12.6 MW
    - Operating Speed: 514 rpm
    - Fuel Consumption: 190 g/kWh
    - Clearance Required: 2.5m minimum
    
    Project Information:
    - Timeline: 18 months
    - Delivery: Q2 2025
    - Budget: $5.2M allocated
    - Project Manager: Sarah Johnson
    - Technical Contact: engineering@wartsila.com
    - Phone: +358-10-709-0000
    
    Installation Requirements:
    - Foundation depth: 3.5m
    - Vibration isolation required
    - Ambient temperature: -20°C to +45°C
    - Humidity: Max 95% RH
    """
    
    # Test different extraction types
    extraction_types = ["technical", "contact", "timeline", "general"]
    
    for ext_type in extraction_types:
        print(f"\n--- {ext_type.upper()} EXTRACTION ---")
        result = simple_document_processor(test_text, ext_type)
        
        if result["success"]:
            print(f"✓ Time: {result['processing_time_seconds']:.2f}s")
            print(f"✓ Extracted: {result['extracted_data']}")
        else:
            print(f"❌ Failed: {result['error']}")
    
    print("\n" + "=" * 50)
    print("✓ LangExtract integration test completed!")
    print("\nNext steps:")
    print("1. Add this to your main document processor")
    print("2. Use different extraction types based on document content")
    print("3. Combine with fast PDF extraction for complete pipeline")

if __name__ == "__main__":
    main()

