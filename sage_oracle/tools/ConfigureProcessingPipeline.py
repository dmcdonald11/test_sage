"""
Configure and customize the document processing pipeline.
"""

from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any, List, Union
import json
from datetime import datetime

class ConfigureProcessingPipeline(BaseTool):
    """
    Configure and customize the document processing pipeline, allowing dynamic 
    adjustment of processing parameters and settings.
    """
    
    pipeline_config: Dict[str, Any] = Field(
        default={},
        description="Pipeline configuration parameters"
    )
    
    stage_settings: Dict[str, Any] = Field(
        default={},
        description="Individual stage configuration"
    )
    
    concurrency_settings: Dict[str, Any] = Field(
        default={},
        description="Concurrency and resource settings"
    )
    
    output_settings: Dict[str, Any] = Field(
        default={},
        description="Output format and storage settings"
    )

    def run(self):
        """
        Configure the processing pipeline with provided settings.
        """
        try:
            # Step 1: Validate configuration
            validation_result = self._validate_configuration()
            if not validation_result["valid"]:
                return json.dumps({
                    "success": False,
                    "error": "Configuration validation failed",
                    "validation_errors": validation_result["errors"]
                }, indent=2)
            
            # Step 2: Apply configuration
            result = self._apply_configuration()
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }, indent=2)
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate the provided configuration"""
        errors = []
        
        # Validate pipeline config
        if self.pipeline_config:
            valid_pipeline_keys = [
                "enable_chunking", "enable_embeddings", "enable_image_annotation",
                "chunk_size", "chunk_overlap", "embedding_model", "image_model"
            ]
            for key in self.pipeline_config:
                if key not in valid_pipeline_keys:
                    errors.append(f"Invalid pipeline config key: {key}")
        
        # Validate stage settings
        if self.stage_settings:
            valid_stages = ["conversion", "chunking", "embedding", "storage"]
            for stage in self.stage_settings:
                if stage not in valid_stages:
                    errors.append(f"Invalid stage: {stage}")
        
        # Validate concurrency settings
        if self.concurrency_settings:
            if "max_concurrent" in self.concurrency_settings:
                max_concurrent = self.concurrency_settings["max_concurrent"]
                if not isinstance(max_concurrent, int) or not (1 <= max_concurrent <= 50):
                    errors.append("max_concurrent must be an integer between 1 and 50")
            
            if "max_workers" in self.concurrency_settings:
                max_workers = self.concurrency_settings["max_workers"]
                if not isinstance(max_workers, int) or not (1 <= max_workers <= 20):
                    errors.append("max_workers must be an integer between 1 and 20")
        
        # Validate output settings
        if self.output_settings:
            if "output_format" in self.output_settings:
                valid_formats = ["markdown", "json", "html", "pdf"]
                if self.output_settings["output_format"] not in valid_formats:
                    errors.append(f"Invalid output format. Must be one of: {valid_formats}")
            
            if "save_images_as_files" in self.output_settings:
                if not isinstance(self.output_settings["save_images_as_files"], bool):
                    errors.append("save_images_as_files must be a boolean")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _apply_configuration(self) -> Dict[str, Any]:
        """Apply the configuration settings"""
        
        # Default configuration
        current_config = {
            "pipeline": {
                "enable_chunking": True,
                "enable_embeddings": True,
                "enable_image_annotation": True,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "embedding_model": "text-embedding-3-small",
                "image_model": "gpt-4o-mini"
            },
            "stages": {
                "conversion": {
                    "enabled": True,
                    "timeout": 300,
                    "retry_attempts": 3
                },
                "chunking": {
                    "enabled": True,
                    "strategy": "hybrid",
                    "max_chunk_size": 1000
                },
                "embedding": {
                    "enabled": True,
                    "model": "text-embedding-3-small",
                    "batch_size": 100
                },
                "storage": {
                    "enabled": True,
                    "format": "markdown",
                    "include_metadata": True
                }
            },
            "concurrency": {
                "max_concurrent": 10,
                "max_workers": 4,
                "batch_size": 10,
                "queue_size": 100
            },
            "output": {
                "format": "markdown",
                "save_images_as_files": True,
                "images_scale": 2,
                "include_annotations": True
            }
        }
        
        # Apply pipeline config
        if self.pipeline_config:
            current_config["pipeline"].update(self.pipeline_config)
        
        # Apply stage settings
        if self.stage_settings:
            for stage, settings in self.stage_settings.items():
                if stage in current_config["stages"]:
                    current_config["stages"][stage].update(settings)
        
        # Apply concurrency settings
        if self.concurrency_settings:
            current_config["concurrency"].update(self.concurrency_settings)
        
        # Apply output settings
        if self.output_settings:
            current_config["output"].update(self.output_settings)
        
        # Test configuration with sample data
        test_result = self._test_configuration(current_config)
        
        return {
            "success": True,
            "configuration_applied": True,
            "current_configuration": current_config,
            "test_result": test_result,
            "timestamp": datetime.now().isoformat(),
            "message": "Pipeline configuration updated successfully"
        }
    
    def _test_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test the configuration with sample data"""
        
        test_results = {
            "pipeline_test": "passed",
            "stage_test": "passed",
            "concurrency_test": "passed",
            "output_test": "passed"
        }
        
        # Test pipeline configuration
        try:
            if config["pipeline"]["chunk_size"] <= 0:
                test_results["pipeline_test"] = "failed: chunk_size must be positive"
            if config["pipeline"]["chunk_overlap"] < 0:
                test_results["pipeline_test"] = "failed: chunk_overlap cannot be negative"
        except Exception as e:
            test_results["pipeline_test"] = f"failed: {str(e)}"
        
        # Test stage configuration
        try:
            for stage, settings in config["stages"].items():
                if "enabled" in settings and not isinstance(settings["enabled"], bool):
                    test_results["stage_test"] = f"failed: {stage}.enabled must be boolean"
                    break
        except Exception as e:
            test_results["stage_test"] = f"failed: {str(e)}"
        
        # Test concurrency configuration
        try:
            if config["concurrency"]["max_concurrent"] > 50:
                test_results["concurrency_test"] = "failed: max_concurrent too high"
            if config["concurrency"]["max_workers"] > 20:
                test_results["concurrency_test"] = "failed: max_workers too high"
        except Exception as e:
            test_results["concurrency_test"] = f"failed: {str(e)}"
        
        # Test output configuration
        try:
            valid_formats = ["markdown", "json", "html", "pdf"]
            if config["output"]["format"] not in valid_formats:
                test_results["output_test"] = f"failed: invalid output format"
        except Exception as e:
            test_results["output_test"] = f"failed: {str(e)}"
        
        # Overall test result
        all_passed = all(result == "passed" for result in test_results.values())
        test_results["overall"] = "passed" if all_passed else "failed"
        
        return test_results


if __name__ == "__main__":
    # Test the tool
    print("Testing ConfigureProcessingPipeline...")
    
    tool = ConfigureProcessingPipeline(
        pipeline_config={
            "enable_chunking": True,
            "chunk_size": 1500,
            "chunk_overlap": 300
        },
        concurrency_settings={
            "max_concurrent": 15,
            "max_workers": 6
        },
        output_settings={
            "format": "markdown",
            "save_images_as_files": False
        }
    )
    
    result = tool.run()
    print("Configuration Result:")
    print(result)
