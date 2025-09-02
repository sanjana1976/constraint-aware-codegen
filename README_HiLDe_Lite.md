# HiLDe-Lite: Human-in-the-Loop Decoding for AI Code Generation

A lightweight prototype of HiLDe optimized for Google Colab T4 GPU (16GB VRAM)

## 🎯 Overview

HiLDe-Lite brings the power of Human-in-the-Loop Decoding to resource-constrained environments. It provides token-level alternatives with semantic explanations, enabling developers to make informed decisions during AI code generation.

## 🏗️ Architecture

### Dual-LLM Design
- **Completion LLM**: Qwen2.5-Coder-7B (runs on Colab GPU)
- **Analysis LLM**: GPT-4 API (runs via HTTP requests)
- **API Gateway**: Flask server orchestrating both services

### Key Optimizations for T4 GPU
- **Half Precision**: Uses `torch.float16` for memory efficiency
- **Device Mapping**: Automatic GPU memory management
- **Memory Limits**: Caps GPU usage at 14GB (leaving 2GB buffer)
- **Context Truncation**: Limits input to 512 tokens

## 🚀 Quick Start

### 1. Google Colab Setup

```python
# Run this in a Colab cell
!git clone <your-repo-url>
!cd hilde-lite && python hilde_lite_colab_setup.py
```

### 2. Set OpenAI API Key

```python
import os
os.environ['OPENAI_API_KEY'] = 'your-openai-api-key-here'
```

### 3. Start the Server

```python
# Run the main gateway
python hilde_lite_api_gateway.py
```

### 4. Test the System

```python
import requests

# Test with a code prompt
response = requests.post('http://localhost:5000/hilde/completion', 
                        json={
                            'prompt': 'def hash_password(password):',
                            'max_tokens': 80,
                            'top_k': 5,
                            'enable_analysis': True
                        })

result = response.json()
print(f"Completion: {result['completion']}")
print(f"Highlighted positions: {result['highlighted_positions']}")
```

## 📊 API Reference

### Main Endpoint

**POST** `/hilde/completion`

```json
{
  "prompt": "def hash_password(password):",
  "max_tokens": 100,
  "top_k": 5,
  "enable_analysis": true
}
```

### Response Format

```json
{
  "completion": "return hashlib.sha256(password.encode()).hexdigest()",
  "token_alternatives": [
    [
      {
        "token": "return",
        "probability": 0.95,
        "analysis": {
          "explanation": "Standard return statement",
          "category": "Minor",
          "importance_score": 0.3
        }
      }
    ]
  ],
  "entropy_scores": [0.2, 0.8, 0.1],
  "highlighted_positions": [1],
  "metadata": {
    "model": "Qwen2.5-Coder-7B",
    "analysis_enabled": true,
    "timestamp": 1234567890,
    "memory_usage": {
      "gpu_memory_used": "8.5 GB"
    }
  }
}
```

### Other Endpoints

- **GET** `/health` - Health check
- **GET** `/demo` - Demo with sample completion
- **GET** `/memory` - Memory usage information
- **POST** `/clear_cache` - Clear GPU cache
- **POST** `/test` - Quick test endpoint

## 🔧 Configuration

### Environment Variables

```bash
# Required for GPT-4 analysis
OPENAI_API_KEY=your-api-key-here

# Optional performance settings
TOKENIZERS_PARALLELISM=false
TRANSFORMERS_CACHE=/content/cache
```

### Model Parameters

```python
# Completion engine settings
max_tokens = 100      # Maximum tokens to generate
top_k = 5            # Number of alternatives per token
temperature = 0.1    # Generation temperature

# Analysis settings
enable_analysis = True  # Use GPT-4 for explanations
```

## 🧪 Testing

### Basic Test

```python
from hilde_lite_api_gateway import test_completion

# Test with a single prompt
result = test_completion("def hash_password(password):")
```

### Multiple Prompts Test

```python
from hilde_lite_api_gateway import test_multiple_prompts

# Test with multiple prompts
test_multiple_prompts()
```

### Custom Test

```python
import requests

def custom_test(prompt):
    response = requests.post('http://localhost:5000/hilde/completion', 
                           json={
                               'prompt': prompt,
                               'max_tokens': 50,
                               'top_k': 3,
                               'enable_analysis': True
                           })
    return response.json()

# Test your own prompts
result = custom_test("def process_payment(amount, card_number):")
```

## 📈 Performance

### Memory Usage
- **Model Loading**: ~8-10GB VRAM
- **Generation**: ~1-2GB additional VRAM
- **Total**: ~10-12GB VRAM (fits in 16GB T4)

### Speed
- **Model Loading**: ~2-3 minutes
- **Completion**: ~2-5 seconds per request
- **GPT-4 Analysis**: ~1-2 seconds per request

### Optimization Tips
- Reduce `max_tokens` for faster generation
- Lower `top_k` to reduce analysis time
- Use `clear_cache()` to free memory
- Disable analysis for faster responses

## 🔍 Features

### Token Alternatives
- Shows top-k alternative tokens for each position
- Includes probabilities and log probabilities
- Highlights uncertain decisions (high entropy)

### Semantic Analysis
- GPT-4 explanations for each alternative
- Categorizes choices (Significant/Minor/Incorrect)
- Provides importance scores (0.0-1.0)

### Entropy Highlighting
- Calculates entropy for each token position
- Highlights positions with high uncertainty
- Helps identify critical decision points

## 🛠️ Troubleshooting

### Common Issues

**CUDA Out of Memory**
```python
# Clear cache and restart
from hilde_lite_api_gateway import gateway
gateway.completion_engine.clear_cache()
```

**GPT-4 Analysis Fails**
```python
# Check API key
import os
print(f"API Key set: {bool(os.getenv('OPENAI_API_KEY'))}")
```

**Slow Performance**
```python
# Reduce parameters
response = requests.post('http://localhost:5000/hilde/completion', 
                        json={
                            'prompt': prompt,
                            'max_tokens': 50,  # Reduce from 100
                            'top_k': 3,        # Reduce from 5
                            'enable_analysis': False  # Disable for speed
                        })
```

### Memory Management

```python
# Check memory usage
import torch
print(f"GPU memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

# Clear cache when needed
torch.cuda.empty_cache()
```

## 📚 Examples

### Security-Focused Prompts

```python
security_prompts = [
    "def hash_password(password):",
    "def validate_input(user_input):",
    "def process_payment(amount, card_number):",
    "def authenticate_user(username, password):",
    "def generate_api_key():"
]

for prompt in security_prompts:
    result = test_completion(prompt)
    # Look for security-related alternatives
```

### Code Quality Prompts

```python
quality_prompts = [
    "def calculate_total(items):",
    "def format_date(date_string):",
    "def parse_config(config_file):",
    "def send_email(recipient, subject, body):",
    "def log_error(error_message):"
]

for prompt in quality_prompts:
    result = test_completion(prompt)
    # Look for best practice alternatives
```

## 🔮 Future Enhancements

- **Multi-language Support**: Extend beyond Python
- **Custom Constraints**: User-defined coding rules
- **Batch Processing**: Multiple prompts at once
- **Model Switching**: Support for different completion models
- **VS Code Extension**: Direct IDE integration

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on Colab T4
5. Submit a pull request

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: This README

---

**Built with ❤️ for the AI coding community**

*HiLDe-Lite: Making AI code generation more intentional and transparent*