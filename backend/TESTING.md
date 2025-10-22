# Sprint 2 Testing Guide

## Overview

Sprint 2 implements the core recommendation logic:
- Intent extraction from natural language
- Traffic profile and SLO target generation
- Model recommendation
- GPU capacity planning
- End-to-end orchestration workflow

## Testing the Workflow

### 1. End-to-End Test with Demo Scenarios

Run the test script with all 3 demo scenarios:

```bash
cd backend
source venv/bin/activate
cd ..
python tests/test_sprint2.py
```

This will test:
- Customer service chatbot (5000 users, strict latency)
- Code generation assistant (500 devs, quality focus)
- Document summarization (2000 users/day, cost-sensitive)

### 2. Manual Testing - Individual Components

#### Test Intent Extraction

```bash
cd backend
source venv/bin/activate

python -c "
from src.context_intent.extractor import IntentExtractor

extractor = IntentExtractor()
intent = extractor.extract_intent(
    'I need a customer service chatbot for 5000 users with low latency'
)

print('Extracted Intent:')
print(f'  Use Case: {intent.use_case}')
print(f'  Users: {intent.user_count}')
print(f'  Latency: {intent.latency_requirement}')
print(f'  Budget: {intent.budget_constraint}')
"
```

#### Test Traffic Profile Generation

```bash
python -c "
from src.context_intent.schema import DeploymentIntent
from src.recommendation.traffic_profile import TrafficProfileGenerator

intent = DeploymentIntent(
    use_case='chatbot',
    user_count=1000,
    latency_requirement='high'
)

generator = TrafficProfileGenerator()
profile = generator.generate_profile(intent)
slo = generator.generate_slo_targets(intent)

print('Traffic Profile:')
print(f'  Expected QPS: {profile.expected_qps}')
print(f'  Avg Prompt: {profile.prompt_tokens_mean} tokens')
print(f'  Avg Gen: {profile.generation_tokens_mean} tokens')
print()
print('SLO Targets:')
print(f'  TTFT p90: {slo.ttft_p90_target_ms}ms')
print(f'  TPOT p90: {slo.tpot_p90_target_ms}ms')
print(f'  E2E p90: {slo.e2e_p90_target_ms}ms')
"
```

#### Test Model Recommendation

```bash
python -c "
from src.context_intent.schema import DeploymentIntent
from src.recommendation.model_recommender import ModelRecommender

intent = DeploymentIntent(
    use_case='code_generation',
    user_count=500,
    latency_requirement='medium',
    domain_specialization=['code']
)

recommender = ModelRecommender()
models = recommender.recommend_models(intent, top_k=3)

print('Top Model Recommendations:')
for i, (model, score) in enumerate(models, 1):
    print(f'{i}. {model.name} (score: {score:.1f})')
    print(f'   Size: {model.size_parameters}')
    print(f'   Domains: {model.domain_specialization}')
    print()
"
```

#### Test Full Workflow

```bash
python -c "
from src.orchestration.workflow import RecommendationWorkflow

workflow = RecommendationWorkflow()

recommendation = workflow.generate_recommendation(
    'I need a chatbot for 1000 users. Low latency is important.'
)

print('Recommendation:')
print(f'Model: {recommendation.model_name}')
print(f'GPU: {recommendation.gpu_config.gpu_count}x {recommendation.gpu_config.gpu_type}')
print(f'Cost: \${recommendation.cost_per_month_usd:.2f}/month')
print(f'TTFT: {recommendation.predicted_ttft_p90_ms}ms')
print(f'TPOT: {recommendation.predicted_tpot_p90_ms}ms')
print(f'Meets SLO: {recommendation.meets_slo}')
"
```

### 3. Test FastAPI Backend

Start the API server:

```bash
cd backend
source venv/bin/activate
python -m src.api.routes
```

In another terminal, test the API:

```bash
# Health check
curl http://localhost:8000/health

# Quick test endpoint
curl -X POST http://localhost:8000/api/v1/test

# Full recommendation
curl -X POST http://localhost:8000/api/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "I need a customer service chatbot for 5000 users with strict latency requirements"
  }'

# List available models
curl http://localhost:8000/api/v1/models

# List GPU types
curl http://localhost:8000/api/v1/gpu-types

# List use cases
curl http://localhost:8000/api/v1/use-cases
```

### 4. Test Knowledge Base Queries

```bash
python -c "
from src.knowledge_base.benchmarks import BenchmarkRepository
from src.knowledge_base.model_catalog import ModelCatalog
from src.knowledge_base.slo_templates import SLOTemplateRepository

# Test benchmarks
bench_repo = BenchmarkRepository()
bench = bench_repo.get_benchmark('meta-llama/Llama-3.1-8B-Instruct', 'NVIDIA-L4', 1)
print(f'Llama 3.1 8B on L4: TTFT={bench.ttft_p90_ms}ms, TPOT={bench.tpot_p90_ms}ms')

# Test model catalog
catalog = ModelCatalog()
models = catalog.find_models_for_use_case('chatbot')
print(f'\nModels for chatbot: {len(models)}')
for m in models[:3]:
    print(f'  - {m.name}')

# Test SLO templates
slo_repo = SLOTemplateRepository()
template = slo_repo.get_template('customer_service')
print(f'\nCustomer Service SLO:')
print(f'  TTFT: {template.ttft_p90_target_ms}ms')
print(f'  TPOT: {template.tpot_p90_target_ms}ms')
"
```

## Expected Results

### Demo Scenario 1: Customer Service Chatbot
- **Model**: Llama 3.1 8B or similar
- **GPU**: 2x NVIDIA-A100-80GB (or similar high-end GPU)
- **Cost**: ~$6,000-7,000/month
- **Meets SLO**: ✅ Yes

### Demo Scenario 2: Code Generation
- **Model**: Llama 3.1 70B or Mixtral 8x7B
- **GPU**: 4x NVIDIA-A100-80GB with tensor parallelism
- **Cost**: ~$12,000-15,000/month
- **Meets SLO**: ✅ Yes

### Demo Scenario 3: Document Summarization
- **Model**: Mistral 7B or Llama 3.1 8B
- **GPU**: 2-3x NVIDIA-A10G or L4
- **Cost**: ~$1,500-2,500/month
- **Meets SLO**: ✅ Yes

## Troubleshooting

### Ollama Not Available
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# If not running
ollama serve
```

### ModuleNotFoundError
```bash
# Make sure you're in the backend directory and venv is activated
cd backend
source venv/bin/activate
which python  # Should show backend/venv/bin/python
```

### LLM Returns Invalid JSON
- This is expected with smaller models like llama3.2:3b
- The code has cleanup logic to handle common mistakes
- For better extraction, try `llama3.1:8b` or `mistral:7b`

### No Viable Configurations Found
- Check that benchmark data exists for the selected models
- Verify SLO targets aren't impossibly strict
- Look at logs to see which models were considered

## Next Steps

Sprint 2 is complete! Ready for Sprint 3:
- Streamlit UI implementation
- Chat interface
- Spec editor
- Visualization of recommendations
