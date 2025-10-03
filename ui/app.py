"""Streamlit UI for AI Pre-Deployment Assistant.

This module provides the main Streamlit interface for the assistant, featuring:
1. Chat interface for conversational requirement gathering
2. Recommendation display with all specification details
3. Editable specification component for user review/modification
4. Integration with FastAPI backend
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="AI Pre-Deployment Assistant",
    page_icon="docs/ai_assistant_favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-badge {
        background-color: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .warning-badge {
        background-color: #ffc107;
        color: black;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "recommendation" not in st.session_state:
    st.session_state.recommendation = None
if "editing_mode" not in st.session_state:
    st.session_state.editing_mode = False
if "deployment_id" not in st.session_state:
    st.session_state.deployment_id = None
if "deployment_files" not in st.session_state:
    st.session_state.deployment_files = None


def main():
    """Main application entry point."""

    # Header
    col1, col2 = st.columns([1, 20])
    with col1:
        st.image("docs/ai_assistant_icon_256.png", width=50)
    with col2:
        st.markdown('<div class="main-header">AI Pre-Deployment Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">From concept to production-ready LLM deployment</div>', unsafe_allow_html=True)

    # Sidebar
    render_sidebar()

    # Main content area - two columns
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("💬 Conversation")
        render_chat_interface()

        # Action buttons below chat
        if st.session_state.recommendation:
            st.markdown("---")
            st.markdown("### 🚀 Actions")

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button("📄 Generate Deployment YAML", use_container_width=True, type="primary"):
                    generate_deployment_yaml(st.session_state.recommendation)

            with action_col2:
                if st.session_state.deployment_files:
                    st.button("🚢 Deploy to Kubernetes", use_container_width=True, disabled=True,
                             help="Coming in Sprint 5/6")

    with col2:
        if st.session_state.recommendation:
            st.subheader("📊 Recommendation")
            render_recommendation()
        else:
            st.info("👈 Start a conversation to get deployment recommendations")


def render_sidebar():
    """Render sidebar with app information and quick actions."""
    with st.sidebar:
        col1, col2 = st.columns([1, 5])
        with col1:
            st.image("docs/ai_assistant_icon_256.png", width=30)
        with col2:
            st.markdown("### AI Pre-Deployment Assistant")

        st.markdown("---")
        st.markdown("### 🎯 Quick Start")
        st.markdown("""
        1. Describe your LLM use case
        2. Review the recommendation
        3. Edit specifications if needed
        4. Deploy to Kubernetes
        """)

        st.markdown("---")
        st.markdown("### 📚 Example Prompts")

        example_prompts = [
            "Customer service chatbot for 5000 users, low latency critical",
            "Code generation assistant for 500 developers, quality over speed",
            "Document summarization pipeline, high throughput, cost efficient"
        ]

        for i, prompt in enumerate(example_prompts, 1):
            if st.button(f"Example {i}", key=f"example_{i}", use_container_width=True):
                st.session_state.current_prompt = prompt

        st.markdown("---")

        # Reset conversation
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.recommendation = None
            st.session_state.editing_mode = False
            st.rerun()

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        This assistant helps you:
        - Define LLM deployment requirements
        - Get GPU recommendations
        - Review SLO targets
        - Deploy to Kubernetes
        """)


def render_chat_interface():
    """Render the chat interface for conversational requirement gathering."""

    # Display chat messages
    chat_container = st.container(height=400)

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    prompt = st.chat_input("Describe your LLM deployment requirements...")

    # Check if we have a prompt from example button
    if "current_prompt" in st.session_state:
        prompt = st.session_state.current_prompt
        del st.session_state.current_prompt

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Show user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Get recommendation from API
        with st.spinner("Analyzing requirements and generating recommendation..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/recommend",
                    json={"message": prompt},
                    timeout=30
                )

                if response.status_code == 200:
                    recommendation = response.json()
                    st.session_state.recommendation = recommendation

                    # Add assistant response
                    assistant_message = format_recommendation_summary(recommendation)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})

                    st.rerun()
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend API. Make sure the FastAPI server is running on http://localhost:8000")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def format_recommendation_summary(rec: Dict[str, Any]) -> str:
    """Format recommendation as a chat message."""

    meets_slo = rec.get("meets_slo", False)
    slo_status = "✅ Meets SLO" if meets_slo else "⚠️ Does not meet SLO"

    summary = f"""
I've analyzed your requirements and generated a recommendation:

**{rec['model_name']}** on **{rec['gpu_config']['gpu_count']}x {rec['gpu_config']['gpu_type']}**

**Performance:**
- TTFT p90: {rec['predicted_ttft_p90_ms']}ms
- TPOT p90: {rec['predicted_tpot_p90_ms']}ms
- E2E p95: {rec['predicted_e2e_p95_ms']}ms
- Throughput: {rec['predicted_throughput_qps']:.1f} QPS

**Cost:** ${rec['cost_per_month_usd']:,.2f}/month

**Status:** {slo_status}

{rec['reasoning']}

👉 Review the full details in the right panel, or ask me to adjust the configuration!
"""
    return summary.strip()


def render_recommendation():
    """Render the recommendation display and specification editor."""

    rec = st.session_state.recommendation

    # Tabs for different views
    tabs = st.tabs(["📋 Overview", "⚙️ Specifications", "📊 Performance", "💰 Cost", "📡 Monitoring"])

    with tabs[0]:
        render_overview_tab(rec)

    with tabs[1]:
        render_specifications_tab(rec)

    with tabs[2]:
        render_performance_tab(rec)

    with tabs[3]:
        render_cost_tab(rec)

    with tabs[4]:
        render_monitoring_tab(rec)


def render_overview_tab(rec: Dict[str, Any]):
    """Render overview tab with key information."""

    # SLO Status Badge
    meets_slo = rec.get("meets_slo", False)
    if meets_slo:
        st.markdown('<span class="success-badge">✅ MEETS SLO</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="warning-badge">⚠️ DOES NOT MEET SLO</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Model and GPU
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Model")
        st.markdown(f"**{rec['model_name']}**")
        st.caption(f"ID: `{rec['model_id']}`")

    with col2:
        st.markdown("### 🖥️ GPU Configuration")
        gpu_config = rec['gpu_config']
        st.markdown(f"**{gpu_config['gpu_count']}x {gpu_config['gpu_type']}**")
        st.caption(f"Tensor Parallel: {gpu_config['tensor_parallel']}, Replicas: {gpu_config['replicas']}")

    st.markdown("---")

    # Key Metrics
    st.markdown("### 📈 Key Metrics")

    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)

    with metrics_col1:
        st.metric("TTFT p90", f"{rec['predicted_ttft_p90_ms']}ms")

    with metrics_col2:
        st.metric("TPOT p90", f"{rec['predicted_tpot_p90_ms']}ms")

    with metrics_col3:
        st.metric("E2E p95", f"{rec['predicted_e2e_p95_ms']}ms")

    with metrics_col4:
        st.metric("Throughput", f"{rec['predicted_throughput_qps']:.1f} QPS")

    st.markdown("---")

    # Reasoning
    st.markdown("### 💡 Reasoning")
    st.info(rec['reasoning'])


def render_specifications_tab(rec: Dict[str, Any]):
    """Render specifications tab with editable fields."""

    st.markdown("### 🔧 Deployment Specifications")
    st.caption("Review and modify the specifications before deployment")

    # Intent
    st.markdown("#### Use Case & Requirements")
    intent = rec['intent']

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Use Case", value=intent['use_case'], disabled=True)
        st.number_input("Users", value=intent['user_count'], disabled=True)

    with col2:
        st.text_input("Latency Requirement", value=intent['latency_requirement'], disabled=True)
        st.text_input("Budget Constraint", value=intent['budget_constraint'], disabled=True)

    # Traffic Profile
    st.markdown("#### Traffic Profile")
    traffic = rec['traffic_profile']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Expected QPS", value=traffic['expected_qps'], format="%.2f", disabled=not st.session_state.editing_mode)

    with col2:
        st.number_input("Avg Prompt Tokens", value=traffic['prompt_tokens_mean'], disabled=not st.session_state.editing_mode)

    with col3:
        st.number_input("Avg Generation Tokens", value=traffic['generation_tokens_mean'], disabled=not st.session_state.editing_mode)

    # SLO Targets
    st.markdown("#### SLO Targets")
    slo = rec['slo_targets']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("TTFT p90 (ms)", value=slo['ttft_p90_target_ms'], disabled=not st.session_state.editing_mode)

    with col2:
        st.number_input("TPOT p90 (ms)", value=slo['tpot_p90_target_ms'], disabled=not st.session_state.editing_mode)

    with col3:
        st.number_input("E2E p95 (ms)", value=slo['e2e_p95_target_ms'], disabled=not st.session_state.editing_mode)

    # Edit mode toggle
    st.markdown("---")
    if not st.session_state.editing_mode:
        if st.button("✏️ Enable Editing", use_container_width=True):
            st.session_state.editing_mode = True
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", use_container_width=True):
                st.success("Changes saved! (Note: Re-recommendation not yet implemented)")
                st.session_state.editing_mode = False
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.editing_mode = False
                st.rerun()


def render_performance_tab(rec: Dict[str, Any]):
    """Render performance tab with detailed metrics."""

    st.markdown("### 📊 Predicted Performance")

    slo = rec['slo_targets']

    # TTFT
    st.markdown("#### Time to First Token (TTFT)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted p90", f"{rec['predicted_ttft_p90_ms']}ms")
    with col2:
        delta_ms = rec['predicted_ttft_p90_ms'] - slo['ttft_p90_target_ms']
        st.metric("Target p90", f"{slo['ttft_p90_target_ms']}ms",
                 delta=f"{delta_ms}ms", delta_color="inverse")

    # TPOT
    st.markdown("#### Time Per Output Token (TPOT)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted p90", f"{rec['predicted_tpot_p90_ms']}ms")
    with col2:
        delta_ms = rec['predicted_tpot_p90_ms'] - slo['tpot_p90_target_ms']
        st.metric("Target p90", f"{slo['tpot_p90_target_ms']}ms",
                 delta=f"{delta_ms}ms", delta_color="inverse")

    # E2E Latency
    st.markdown("#### End-to-End Latency")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted p95", f"{rec['predicted_e2e_p95_ms']}ms")
    with col2:
        delta_ms = rec['predicted_e2e_p95_ms'] - slo['e2e_p95_target_ms']
        st.metric("Target p95", f"{slo['e2e_p95_target_ms']}ms",
                 delta=f"{delta_ms}ms", delta_color="inverse")

    # Throughput
    st.markdown("#### Throughput")
    st.metric("Requests/sec", f"{rec['predicted_throughput_qps']:.1f} QPS")


def render_cost_tab(rec: Dict[str, Any]):
    """Render cost tab with pricing details."""

    st.markdown("### 💰 Cost Breakdown")

    # Main cost metrics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### Hourly Cost")
        st.markdown(f"## ${rec['cost_per_hour_usd']:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### Monthly Cost")
        st.markdown(f"## ${rec['cost_per_month_usd']:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # GPU details
    gpu_config = rec['gpu_config']
    st.markdown("#### GPU Configuration")
    st.markdown(f"""
    - **GPU Type:** {gpu_config['gpu_type']}
    - **Total GPUs:** {gpu_config['gpu_count']}
    - **Tensor Parallel:** {gpu_config['tensor_parallel']}
    - **Replicas:** {gpu_config['replicas']}
    """)

    st.markdown("---")

    # Cost assumptions
    st.info("""
    **💡 Cost Assumptions:**
    - Pricing based on typical cloud GPU rates
    - 730 hours/month (24/7 operation)
    - Does not include networking, storage, or egress costs
    - Actual costs may vary by cloud provider
    """)


def generate_deployment_yaml(rec: Dict[str, Any]):
    """Generate deployment YAML files via API."""
    try:
        with st.spinner("Generating deployment YAML files..."):
            response = requests.post(
                f"{API_BASE_URL}/api/deploy",
                json={"recommendation": rec, "namespace": "default"},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.deployment_id = result["deployment_id"]
                st.session_state.deployment_files = result["files"]

                st.success(f"✅ Deployment files generated successfully!")
                st.info(f"**Deployment ID:** `{result['deployment_id']}`")

                # Show file paths
                st.markdown("**Generated Files:**")
                for config_type, file_path in result["files"].items():
                    st.code(file_path, language="text")

                st.markdown("---")
                st.markdown("**Next:** Go to the **Monitoring** tab to see simulated observability metrics!")

            else:
                st.error(f"Failed to generate YAML: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API. Make sure the FastAPI server is running.")
    except Exception as e:
        st.error(f"❌ Error generating deployment: {str(e)}")


def render_monitoring_tab(rec: Dict[str, Any]):
    """Render mock monitoring dashboard."""

    st.markdown("### 📡 Deployment Monitoring")

    if not st.session_state.deployment_id:
        st.info("""
        👈 **No deployment yet!**

        Generate deployment YAML files from the **Cost** tab, and monitoring data will appear here.

        This dashboard demonstrates Component 9 (Inference Observability & SLO Monitoring) from the architecture,
        showing what real-time metrics would look like after deployment.
        """)
        return

    # Fetch mock monitoring data
    try:
        with st.spinner("Loading deployment metrics..."):
            response = requests.get(
                f"{API_BASE_URL}/api/deployments/{st.session_state.deployment_id}/status",
                timeout=10
            )

            if response.status_code == 200:
                status = response.json()
                render_monitoring_dashboard(status, rec)
            else:
                st.error(f"Failed to fetch monitoring data: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend API.")
    except Exception as e:
        st.error(f"❌ Error fetching monitoring data: {str(e)}")


def render_monitoring_dashboard(status: Dict[str, Any], rec: Dict[str, Any]):
    """Render the actual monitoring dashboard with metrics."""

    deployment_id = status["deployment_id"]

    st.markdown(f"**Deployment ID:** `{deployment_id}`")
    st.markdown(f"**Status:** 🟢 {status['status'].upper()}")

    st.markdown("---")

    # SLO Compliance
    st.markdown("### ✅ SLO Compliance (Last 7 Days)")

    slo = status["slo_compliance"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ttft_delta = slo["ttft_p90_ms"] - slo["ttft_target_ms"]
        st.metric(
            "TTFT p90",
            f"{slo['ttft_p90_ms']}ms",
            delta=f"{ttft_delta}ms vs target",
            delta_color="inverse"
        )
        st.caption(f"Target: {slo['ttft_target_ms']}ms {'✓' if slo['ttft_compliant'] else '⚠️'}")

    with col2:
        tpot_delta = slo["tpot_p90_ms"] - slo["tpot_target_ms"]
        st.metric(
            "TPOT p90",
            f"{slo['tpot_p90_ms']}ms",
            delta=f"{tpot_delta}ms vs target",
            delta_color="inverse"
        )
        st.caption(f"Target: {slo['tpot_target_ms']}ms {'✓' if slo['tpot_compliant'] else '⚠️'}")

    with col3:
        e2e_delta = slo["e2e_p95_ms"] - slo["e2e_target_ms"]
        st.metric(
            "E2E p95",
            f"{slo['e2e_p95_ms']}ms",
            delta=f"{e2e_delta}ms vs target",
            delta_color="inverse"
        )
        st.caption(f"Target: {slo['e2e_target_ms']}ms {'✓' if slo['e2e_compliant'] else '⚠️'}")

    with col4:
        qps_delta = slo["throughput_qps"] - slo["throughput_target_qps"]
        st.metric(
            "Throughput",
            f"{slo['throughput_qps']} QPS",
            delta=f"{qps_delta:+.0f} vs target"
        )
        st.caption(f"Target: {slo['throughput_target_qps']} QPS {'✓' if slo['throughput_compliant'] else '⚠️'}")

    # Uptime
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        uptime_delta = slo["uptime_pct"] - slo["uptime_target_pct"]
        st.metric(
            "Uptime",
            f"{slo['uptime_pct']:.2f}%",
            delta=f"{uptime_delta:+.2f}% vs target"
        )
        st.caption(f"Target: {slo['uptime_target_pct']}% {'✓' if slo['uptime_compliant'] else '⚠️'}")

    # Resource Utilization
    st.markdown("---")
    st.markdown("### 🖥️ Resource Utilization")

    util = status["resource_utilization"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("GPU Utilization", f"{util['gpu_utilization_pct']}%")
        st.caption("Target: >80% for cost efficiency")
        if util['gpu_utilization_pct'] < 80:
            st.warning("⚠️ Below efficiency target")

    with col2:
        st.metric(
            "GPU Memory",
            f"{util['gpu_memory_used_gb']:.1f} GB",
            delta=f"of {util['gpu_memory_total_gb']} GB"
        )

    with col3:
        st.metric("Avg Batch Size", util['avg_batch_size'])
        st.caption(f"Queue depth: {util['queue_depth']}")

    # Cost Analysis
    st.markdown("---")
    st.markdown("### 💰 Cost Analysis")

    cost = status["cost_analysis"]

    col1, col2 = st.columns(2)

    with col1:
        cost_diff_month = cost["actual_cost_per_month_usd"] - cost["predicted_cost_per_month_usd"]
        st.metric(
            "Monthly Cost",
            f"${cost['actual_cost_per_month_usd']:.0f}",
            delta=f"${cost_diff_month:+.0f} vs predicted"
        )
        st.caption(f"Predicted: ${cost['predicted_cost_per_month_usd']:.0f}")

    with col2:
        st.metric(
            "Cost per 1k Tokens",
            f"${cost['cost_per_1k_tokens_usd']:.3f}"
        )
        st.caption(f"Predicted: ${cost['predicted_cost_per_1k_tokens_usd']:.3f}")

    # Traffic Patterns
    st.markdown("---")
    st.markdown("### 📊 Traffic Patterns")

    traffic = status["traffic_patterns"]

    col1, col2, col3 = st.columns(3)

    with col1:
        prompt_diff = traffic["avg_prompt_tokens"] - traffic["predicted_prompt_tokens"]
        st.metric(
            "Avg Prompt Tokens",
            traffic["avg_prompt_tokens"],
            delta=f"{prompt_diff:+d} vs predicted"
        )
        st.caption(f"Predicted: {traffic['predicted_prompt_tokens']}")

    with col2:
        gen_diff = traffic["avg_generation_tokens"] - traffic["predicted_generation_tokens"]
        st.metric(
            "Avg Generation Tokens",
            traffic["avg_generation_tokens"],
            delta=f"{gen_diff:+d} vs predicted"
        )
        st.caption(f"Predicted: {traffic['predicted_generation_tokens']}")

    with col3:
        qps_diff = traffic["peak_qps"] - traffic["predicted_peak_qps"]
        st.metric(
            "Peak QPS",
            traffic["peak_qps"],
            delta=f"{qps_diff:+d} vs predicted"
        )
        st.caption(f"Predicted: {traffic['predicted_peak_qps']}")

    # Request volume
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Requests (Last Hour)", f"{traffic['requests_last_hour']:,}")
    with col2:
        st.metric("Requests (Last 24h)", f"{traffic['requests_last_24h']:,}")

    # Recommendations
    st.markdown("---")
    st.markdown("### 💡 Optimization Recommendations")

    for recommendation in status.get("recommendations", []):
        st.info(recommendation)

    st.markdown("---")
    st.caption("**Note:** This is simulated monitoring data for POC purposes. In production, this would connect to Prometheus/Grafana.")


if __name__ == "__main__":
    main()
