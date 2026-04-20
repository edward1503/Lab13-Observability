# Alert Rules and Runbooks

## 1. High latency P95
- Severity: P2
- Trigger: `latency_p95_ms > 5000 for 30m`
- Impact: tail latency breaches SLO
- First checks:
  1. Open top slow traces in the last 1h
  2. Compare RAG span vs LLM span
  3. Check if incident toggle `rag_slow` is enabled
- Mitigation:
  - truncate long queries
  - fallback retrieval source
  - lower prompt size

## 2. High error rate
- Severity: P1
- Trigger: `error_rate_pct > 5 for 5m`
- Impact: users receive failed responses
- First checks:
  1. Group logs by `error_type`
  2. Inspect failed traces
  3. Determine whether failures are LLM, tool, or schema related
- Mitigation:
  - rollback latest change
  - disable failing tool
  - retry with fallback model

## 3. Cost budget spike
- Severity: P2
- Trigger: `hourly_cost_usd > 2x_baseline for 15m`
- Impact: burn rate exceeds budget
- First checks:
  1. Split traces by feature and model
  2. Compare tokens_in/tokens_out
  3. Check if `cost_spike` incident was enabled
- Mitigation:
  - shorten prompts
  - route easy requests to cheaper model
  - apply prompt cache

## 4. Low quality score
- Severity: P2
- Trigger: `quality_score_avg < 0.6 for 10m`
- Impact: AI Agent responses are inaccurate or unhelpful
- First checks:
  1. Inspect traces in Langfuse with low scores
  2. Check if PII redaction is over-triggering (causing score drop)
  3. Verify if RAG retrieval is returning irrelevant documents
- Mitigation:
  - adjust retrieval top_k
  - refine system prompt instructions
  - disable specific features or models if they underperform

## 5. Extreme latency P99
- Severity: P1
- Trigger: `latency_p99 > 10000 for 5m`
- Impact: Service is becoming unresponsive for many users
- First checks:
  1. Check for infinite loops in LLM response generation
  2. Inspect system load (CPU/Memory) if applicable
  3. Verify if an upstream provider (OpenAI/Langfuse) is down
- Mitigation:
  - Implement circuit breakers
  - Rate limit incoming requests
  - Scale up resources

## 6. Token consumption warning
- Severity: P2
- Trigger: `tokens_out_total > 1000000`
- Impact: Risk of exceeding API quota and service interruption
- First checks:
  1. Identify users or sessions with abnormally high usage
  2. Check if a specific prompt is causing "verbose" output
  3. Verify if `cost_spike` incident is enabled
- Mitigation:
  - Apply stricter output token limits
  - Switch to a more compact prompting style
  - Block abusive users if necessary

## 7. High runtime error rate
- Severity: P1
- Trigger: `error_breakdown['RuntimeError'] > 10 for 5m`
- Impact: Users are experiencing frequent hard failures
- First checks:
  1. Group logs by error message to find common patterns
  2. Verify connections to mock dependencies (RAG/LLM)
  3. Check for recent code deployments or config changes
- Mitigation:
  - Rollback to previous stable version
  - Disable failing tools or features
  - Fix underlying code bugs and redeploy
