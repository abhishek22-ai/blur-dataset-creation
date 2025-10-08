# Configuration Guide

This guide provides comprehensive information about configuring the Blur Suite SDK for various use cases, environments, and requirements.

## Configuration Overview

Blur Suite SDK supports multiple configuration methods:
- **JSON configuration files** for dataset creation and batch processing
- **YAML configuration files** for global and project settings
- **Environment variables** for runtime configuration
- **Programmatic configuration** via Python API
- **Command-line options** for one-off operations
- **NEW in v2.0.0:** Hierarchical configuration with inheritance
- **NEW in v2.0.0:** Schema-based configuration validation
- **NEW in v2.0.0:** Runtime configuration management

## Configuration File Formats

### JSON Configuration

JSON is the primary format for dataset creation configurations:

#### v2.0.0 Enhanced Configuration

v2.0.0 introduces advanced configuration features:

```json
{
  "metadata": {
    "created_by": "Blur Suite Configuration Tool v2.0.0",
    "creation_date": "2024-10-08T12:00:00Z",
    "version": "2.0.0",
    "description": "Production dataset with v2.0.0 features"
  },
  "global_settings": {
    "output_format": "png",
    "quality": 95,
    "parallel_processing": true,
    "max_workers": 8,
    "preserve_metadata": true,
    "organize_by_blur_type": false,
    "performance": {
      "enable_caching": true,
      "cache_size_mb": 200,
      "memory_limit_percent": 75,
      "enable_monitoring": true
    },
    "monitoring": {
      "enable_metrics": true,
      "enable_health_checks": true,
      "metrics_interval": 30,
      "health_check_interval": 300
    },
    "logging": {
      "enable_structured_logging": true,
      "log_level": "INFO",
      "correlation_id": "dataset_2024_10_08"
    }
  },
  "image_configurations": {
    "path/to/image1.jpg": {
      "blur_type": "gaussian",
      "parameters": {
        "kernel_size": 7,
        "sigma_x": 1.5,
        "sigma_y": 1.5
      },
      "enabled": true,
      "custom_effects": {
        "post_processing": [
          {"type": "sharpen", "intensity": 0.8},
          {"type": "enhance", "enhancement_type": "contrast", "intensity": 1.2}
        ]
      }
    }
  }
}
```

```json
{
  "metadata": {
    "created_by": "Blur Suite Configuration Tool v2.0.0",
    "creation_date": "2024-10-08T12:00:00Z",
    "version": "2.0.0",
    "description": "Production dataset configuration"
  },
  "global_settings": {
    "output_format": "png",
    "quality": 95,
    "parallel_processing": true,
    "max_workers": 8,
    "preserve_metadata": true,
    "organize_by_blur_type": false
  },
  "image_configurations": {
    "path/to/image1.jpg": {
      "blur_type": "gaussian",
      "parameters": {
        "kernel_size": 7,
        "sigma_x": 1.5,
        "sigma_y": 1.5
      },
      "enabled": true
    }
  }
}
```

### YAML Configuration

YAML is used for global settings and project configuration:

```yaml
# Global Blur Suite Settings
sdk:
  version: "1.0.0"
  debug: false

# Processing settings
processing:
  default_workers: 4
  max_workers: 16
  chunk_size: 20
  timeout_per_image: 300

# Output settings
output:
  default_format: "png"
  default_quality: 95
  preserve_metadata: true
  organize_by_blur_type: false

# Plugin settings
plugins:
  enabled: []
  disabled: []
  search_paths:
    - "~/.blur-suite/plugins"
    - "./plugins"

# Logging configuration
logging:
  level: "INFO"
  file: "~/.blur-suite/blur_suite.log"
  max_size_mb: 100
  backup_count: 5

# Performance settings
performance:
  use_gpu: "auto"
  memory_limit_gb: 8
  temp_directory: "/tmp/blur_suite"
```

## Configuration Sections

### Metadata Section

Provides information about the configuration:

```json
{
  "metadata": {
    "created_by": "Blur Suite Dataset Creator",
    "creation_date": "2024-10-07T12:00:00Z",
    "version": "1.0.0",
    "description": "Document blur analysis dataset",
    "project": "Blur Analysis Project",
    "experiment": "Parameter Study",
    "author": "Research Team",
    "contact": "team@research.org",
    "license": "CC BY 4.0",
    "tags": ["blur", "analysis", "research", "documents"]
  }
}
```

**Fields:**
- `created_by`: Tool or person that created the configuration
- `creation_date`: ISO 8601 timestamp of creation
- `version`: Configuration format version
- `description`: Human-readable description
- `project`: Associated project name
- `experiment`: Experiment or study name
- `author`: Configuration author
- `contact`: Contact information
- `license`: License for the configuration/dataset
- `tags`: Keywords for categorization

### Global Settings Section

Defines default settings for the entire operation:

```json
{
  "global_settings": {
    "output_format": "png",
    "quality": 95,
    "parallel_processing": true,
    "max_workers": 8,
    "chunk_size": 20,
    "retry_attempts": 3,
    "timeout_per_image": 300,
    "preserve_metadata": true,
    "organize_by_blur_type": false,
    "continue_on_error": false,
    "dry_run": false,
    "verbose": false
  }
}
```

**Fields:**
- `output_format`: Image format (png, jpg, tiff, bmp)
- `quality`: Output quality (1-100, format-dependent)
- `parallel_processing`: Enable multi-worker processing
- `max_workers`: Maximum number of parallel workers
- `chunk_size`: Images per processing chunk
- `retry_attempts`: Number of retries for failed operations
- `timeout_per_image`: Timeout per image in seconds
- `preserve_metadata`: Preserve original image metadata
- `organize_by_blur_type`: Organize output by blur type
- `continue_on_error`: Continue processing if some images fail
- `dry_run`: Show what would be processed without doing it
- `verbose`: Enable verbose output

### Image Configurations Section

Defines blur settings for individual images or groups:

```json
{
  "image_configurations": {
    "documents/research_paper_001.jpg": {
      "blur_type": "gaussian",
      "parameters": {
        "kernel_size": 5,
        "sigma_x": 1.0,
        "sigma_y": 1.0
      },
      "enabled": true,
      "priority": 1,
      "tags": ["research", "paper"]
    },
    "documents/presentation_001.jpg": {
      "blur_type": "motion",
      "parameters": {
        "angle": 45.0,
        "length": 15
      },
      "enabled": true,
      "priority": 2,
      "tags": ["presentation", "slide"]
    }
  }
}
```

**Fields:**
- `blur_type`: Type of blur effect to apply
- `parameters`: Blur effect parameters (type-specific)
- `enabled`: Whether to process this image
- `priority`: Processing priority (higher = first)
- `tags`: Custom tags for organization

## Blur Type Parameters

### Gaussian Blur Parameters

```json
{
  "blur_type": "gaussian",
  "parameters": {
    "kernel_size": 7,
    "sigma_x": 1.5,
    "sigma_y": 1.5
  }
}
```

**Parameter Details:**
- `kernel_size`: 3-25 (odd numbers only)
- `sigma_x`: 0.1-10.0 (horizontal blur strength)
- `sigma_y`: 0.1-10.0 (vertical blur strength)

### Motion Blur Parameters

```json
{
  "blur_type": "motion",
  "parameters": {
    "angle": 45.0,
    "length": 15
  }
}
```

**Parameter Details:**
- `angle`: 0-360° (direction of motion)
- `length`: 1-100 pixels (motion distance)

### Defocus Blur Parameters

```json
{
  "blur_type": "defocus",
  "parameters": {
    "radius": 8,
    "strength": 1.2
  }
}
```

**Parameter Details:**
- `radius`: 1-50 pixels (blur radius)
- `strength`: 0.1-5.0 (blur intensity)

### Average Blur Parameters

```json
{
  "blur_type": "average",
  "parameters": {
    "kernel_size": 7
  }
}
```

**Parameter Details:**
- `kernel_size`: 3-25 (odd numbers only)

### Bilateral Blur Parameters

```json
{
  "blur_type": "bilateral",
  "parameters": {
    "diameter": 9,
    "sigma_color": 75.0,
    "sigma_space": 75.0
  }
}
```

**Parameter Details:**
- `diameter`: 5-25 (filter diameter)
- `sigma_color`: 10-150 (color space standard deviation)
- `sigma_space`: 10-150 (coordinate space standard deviation)

## Advanced Configuration

### Conditional Processing

Apply different settings based on image properties:

```json
{
  "image_configurations": {
    "path/to/image1.jpg": {
      "blur_type": "gaussian",
      "parameters": {
        "kernel_size": 5,
        "sigma_x": 1.0,
        "sigma_y": 1.0
      },
      "enabled": true,
      "conditions": {
        "min_width": 1000,
        "min_height": 800,
        "format": ["jpg", "png"]
      }
    }
  }
}
```

### Batch Configuration Templates

Create reusable configuration templates:

```json
{
  "templates": {
    "light_blur": {
      "blur_type": "gaussian",
      "parameters": {"kernel_size": 3, "sigma_x": 0.5, "sigma_y": 0.5}
    },
    "medium_blur": {
      "blur_type": "gaussian",
      "parameters": {"kernel_size": 7, "sigma_x": 1.5, "sigma_y": 1.5}
    },
    "strong_blur": {
      "blur_type": "gaussian",
      "parameters": {"kernel_size": 15, "sigma_x": 3.0, "sigma_y": 3.0}
    }
  },
  "image_configurations": {
    "group1/": {
      "template": "light_blur",
      "count": 100
    },
    "group2/": {
      "template": "medium_blur",
      "count": 100
    }
  }
}
```

### Environment-Based Configuration

Different settings for different environments:

```json
{
  "environments": {
    "development": {
      "global_settings": {
        "max_workers": 2,
        "verbose": true,
        "dry_run": false
      }
    },
    "production": {
      "global_settings": {
        "max_workers": 16,
        "verbose": false,
        "continue_on_error": true
      }
    }
  },
  "active_environment": "development"
}
```

## Configuration Validation

### Manual Validation

```python
from blur_suite.dataset import DatasetCreator

# Load and validate configuration
creator = DatasetCreator("./output")
issues = creator.validate_configuration("config.json")

if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  ❌ {issue}")
else:
    print("✅ Configuration is valid!")
```

### CLI Validation

```bash
# Validate configuration file
blur-suite config validate config.json

# Strict validation
blur-suite config validate config.json --strict

# Show fix suggestions
blur-suite config validate config.json --fix-suggestions
```

## Environment Variables

Configure runtime behavior with environment variables:

### Processing Control
```bash
export BLUR_SUITE_MAX_WORKERS=8
export BLUR_SUITE_CHUNK_SIZE=20
export BLUR_SUITE_TIMEOUT=300
export BLUR_SUITE_CONTINUE_ON_ERROR=1
```

### Performance Settings
```bash
export BLUR_SUITE_USE_GPU=1
export BLUR_SUITE_MEMORY_LIMIT=8
export BLUR_SUITE_TEMP_DIR=/tmp/blur_suite
```

### Debug and Logging
```bash
export BLUR_SUITE_DEBUG=1
export BLUR_SUITE_LOG_LEVEL=DEBUG
export BLUR_SUITE_LOG_FILE=/var/log/blur_suite.log
```

### Plugin Configuration
```bash
export BLUR_SUITE_PLUGIN_PATH=~/.blur-suite/plugins
export BLUR_SUITE_ENABLE_PLUGINS=plugin1,plugin2
export BLUR_SUITE_DISABLE_PLUGINS=plugin3
```

## Configuration Examples

### Research Dataset Configuration

```json
{
  "metadata": {
    "project": "Document Blur Analysis",
    "experiment": "Blur Effect Study",
    "researcher": "Dr. Jane Smith",
    "institution": "Research University",
    "funding": "NSF Grant #123456"
  },
  "global_settings": {
    "output_format": "png",
    "quality": 100,
    "parallel_processing": true,
    "max_workers": 12,
    "preserve_metadata": true,
    "organize_by_blur_type": true
  },
  "parameter_study": {
    "kernel_sizes": [3, 5, 7, 9, 11],
    "sigma_values": [0.5, 1.0, 1.5, 2.0, 2.5]
  }
}
```

### Production Configuration

```json
{
  "metadata": {
    "environment": "production",
    "quality_standard": "high",
    "sla_requirements": "99.9% uptime"
  },
  "global_settings": {
    "output_format": "jpg",
    "quality": 90,
    "parallel_processing": true,
    "max_workers": 32,
    "retry_attempts": 5,
    "timeout_per_image": 600,
    "continue_on_error": true,
    "monitoring_enabled": true
  },
  "monitoring": {
    "metrics_enabled": true,
    "alerting_enabled": true,
    "log_level": "WARNING"
  }
}
```

### Development Configuration

```json
{
  "metadata": {
    "environment": "development",
    "debug_mode": true,
    "profiling_enabled": true
  },
  "global_settings": {
    "output_format": "png",
    "quality": 95,
    "parallel_processing": false,
    "max_workers": 2,
    "verbose": true,
    "dry_run": false,
    "debug_output": true
  },
  "development": {
    "save_intermediate_results": true,
    "detailed_error_messages": true,
    "performance_profiling": true
  }
}
```

## Configuration Management

### Configuration Inheritance

Create base configurations and extend them:

```json
{
  "base_config": {
    "global_settings": {
      "output_format": "png",
      "quality": 95,
      "parallel_processing": true
    }
  },
  "configurations": {
    "experiment_1": {
      "extends": "base_config",
      "global_settings": {
        "max_workers": 8
      },
      "image_configurations": { ... }
    },
    "experiment_2": {
      "extends": "base_config",
      "global_settings": {
        "max_workers": 16
      },
      "image_configurations": { ... }
    }
  }
}
```

### Configuration Profiles

Different profiles for different use cases:

```json
{
  "profiles": {
    "fast": {
      "global_settings": {
        "max_workers": 16,
        "chunk_size": 50,
        "output_format": "jpg",
        "quality": 80
      }
    },
    "quality": {
      "global_settings": {
        "max_workers": 4,
        "chunk_size": 10,
        "output_format": "png",
        "quality": 100
      }
    },
    "memory_efficient": {
      "global_settings": {
        "max_workers": 2,
        "chunk_size": 5,
        "memory_limit_gb": 4
      }
    }
  },
  "active_profile": "quality"
}
```

## Best Practices

### Configuration Organization

1. **Use descriptive names** for configuration files
2. **Include comprehensive metadata** for reproducibility
3. **Version control** configuration files
4. **Document parameter choices** and rationale
5. **Use consistent naming conventions**

### Performance Optimization

1. **Match worker count** to CPU cores (2-4 workers per core)
2. **Use appropriate chunk sizes** based on memory
3. **Enable parallel processing** for large datasets
4. **Choose optimal output formats** for your use case

### Quality Assurance

1. **Validate configurations** before large processing runs
2. **Test configurations** with small datasets first
3. **Document expected outcomes** for each configuration
4. **Archive working configurations** for future use

### Maintenance

1. **Keep configurations up to date** with SDK versions
2. **Review and optimize** configurations regularly
3. **Document changes** and their rationale
4. **Share successful configurations** with team members

## Troubleshooting Configuration Issues

### Common Issues

#### Invalid Parameter Values
```bash
# Check parameter ranges
blur-suite config validate config.json --show-issues

# Fix suggestions
blur-suite config validate config.json --fix-suggestions
```

#### Missing Required Fields
```json
{
  "metadata": {
    "created_by": "Tool Name",
    "creation_date": "2024-10-07T12:00:00Z",
    "version": "1.0.0"
  },
  "global_settings": {
    "output_format": "png",
    "parallel_processing": true
  },
  "image_configurations": {
    // At least one image configuration required
  }
}
```

#### File Path Issues
```json
{
  "image_configurations": {
    "./data/documents/doc1.jpg": {  // Use relative paths
      "blur_type": "gaussian",
      "parameters": {"kernel_size": 5}
    }
  }
}
```

### Configuration Debugging

```python
import json
from blur_suite.dataset import DatasetCreator

# Load and inspect configuration
with open("config.json", "r") as f:
    config = json.load(f)

print("Configuration structure:")
print(json.dumps(config, indent=2))

# Validate with detailed output
creator = DatasetCreator("./output")
issues = creator.validate_configuration("config.json", verbose=True)

for issue in issues:
    print(f"Issue: {issue['type']} - {issue['message']}")
    if 'suggestion' in issue:
        print(f"Suggestion: {issue['suggestion']}")
```

## Integration with Other Tools

### Export from Interactive Tool

```python
# Export configuration from interactive tool
from blur_suite.interactive import BlurSuiteApp

app = BlurSuiteApp()
app.load_image("sample.jpg")
app.set_blur_type("gaussian")
app.set_parameters(kernel_size=7, sigma_x=1.5)

# Export configuration
app.export_configuration("interactive_config.json")
```

### Import to Dataset Creation

```python
# Use exported configuration
from blur_suite.dataset import DatasetCreator

creator = DatasetCreator("./dataset")
success = creator.create_from_config("interactive_config.json")
```

### Version Control Integration

```bash
#!/bin/bash
# config_version_control.sh

CONFIG_DIR="./configs"
GIT_REPO="./config_repo"

# Initialize configuration repository
cd "$CONFIG_DIR"
git init "$GIT_REPO"
cd "$GIT_REPO"

# Copy current configurations
cp ../*.json .

# Commit configurations
git add .
git commit -m "Initial configuration commit"

# Create branch for experiment
git checkout -b experiment/blur_study

# Update configuration for experiment
# ... modify config files ...

# Commit changes
git add .
git commit -m "Updated configuration for blur study"
```

## Configuration Templates

### Template Categories

#### Research Templates
- **Parameter Study**: Systematic parameter variation
- **Quality Analysis**: High-quality reference datasets
- **Performance Benchmark**: Speed and efficiency testing

#### Production Templates
- **Batch Processing**: High-throughput configurations
- **Quality Assurance**: Consistent quality standards
- **Monitoring**: Comprehensive logging and metrics

#### Development Templates
- **Debug**: Detailed logging and error reporting
- **Testing**: Small-scale test configurations
- **Profiling**: Performance analysis configurations

### Creating Custom Templates

```python
import json

def create_parameter_study_template(
    base_config,
    parameter_name,
    parameter_values,
    output_dir="./templates"
):
    """Create configuration templates for parameter studies"""

    templates = {}

    for value in parameter_values:
        template_name = f"{parameter_name}_{value}"

        # Create configuration variant
        config = base_config.copy()
        config["metadata"]["description"] = f"Parameter study: {parameter_name}={value}"

        # Update parameter in all image configurations
        for img_config in config["image_configurations"].values():
            if "parameters" in img_config:
                img_config["parameters"][parameter_name] = value

        templates[template_name] = config

        # Save individual template
        with open(f"{output_dir}/{template_name}.json", "w") as f:
            json.dump(config, f, indent=2)

    return templates
```

## API Reference

For programmatic configuration management:

```python
from blur_suite.dataset import DatasetCreator
import json

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

# Modify configuration programmatically
config["global_settings"]["max_workers"] = 8
config["metadata"]["modified_date"] = "2024-10-07T12:00:00Z"

# Validate modified configuration
creator = DatasetCreator("./output")
issues = creator.validate_config_dict(config)

if not issues:
    # Use modified configuration
    success = creator.create_from_config_dict(config)
else:
    print("Configuration issues:", issues)
```

## Support and Resources

- 📖 **[API Reference: Configuration](api_reference/)** - Complete API documentation
- 💡 **[Examples: Configuration](examples/)** - Working configuration examples
- 🛠️ **[Troubleshooting Guide](../troubleshooting.md)** - Common configuration issues
- 💬 **[FAQ](../faq.md)** - Frequently asked configuration questions

---

*Need help?* Check the [Troubleshooting Guide](../troubleshooting.md) or explore the [Examples](../examples/) for more configuration patterns.