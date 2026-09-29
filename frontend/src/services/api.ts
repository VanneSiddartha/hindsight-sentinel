const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/+$/, '')
  : '/api';

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly kind: 'connection' | 'http' | 'response',
  ) {
    super(message);
    this.name = 'ApiRequestError';
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    const detail = error instanceof Error ? ` (${error.message})` : '';
    throw new ApiRequestError(
      `The browser could not reach the backend API at ${API_BASE_URL}${path}${detail}. ` +
        'Check that FastAPI is running at http://localhost:8000 and that the browser request is not blocked by CORS or a proxy.',
      'connection',
    );
  }

  const responseText = await response.text();
  let result: unknown;
  if (responseText) {
    try {
      result = JSON.parse(responseText);
    } catch {
      throw new ApiRequestError(
        `The backend returned an invalid JSON response for ${path} (HTTP ${response.status}).`,
        'response',
      );
    }
  }

  if (!response.ok) {
    const body = result as { message?: string; detail?: string } | undefined;
    throw new ApiRequestError(
      body?.message || body?.detail || `Backend request failed with HTTP ${response.status}.`,
      'http',
    );
  }

  return result as T;
}

export type WorkflowType =
  | 'Deployment'
  | 'Database Migration'
  | 'Configuration Change'
  | 'Service Update';

export type WorkflowEnvironment = 'Development' | 'Staging' | 'Production';
export type DeploymentTarget = 'Kubernetes' | 'Docker' | 'Cloud VM' | 'Other';

export interface WorkflowRequest {
  workflow_type: WorkflowType;
  task_description: string;
  service_name: string;
  version: string;
  repository: string;
  environment: WorkflowEnvironment;
  deployment_target: DeploymentTarget;
}

export interface DemoWorkflowControls {
  force_failure?: boolean;
  enable_recall?: boolean;
}

export interface AgentStep {
  step_id: string;
  agent_name: 'planner' | 'coder' | 'tester' | 'security';
  timestamp: string;
  observation: string;
  decision: string;
  action_taken: string;
  status: 'SUCCESS' | 'FAILED' | 'WARNING' | 'SKIPPED';
  metadata: Record<string, any>;
}

export interface ExperienceModel {
  experience_id: string;
  context: string;
  service_name: string;
  agents_involved: string[];
  decision: string;
  action: string;
  validation: string;
  outcome: 'SUCCESS' | 'FAILURE';
  root_cause?: string;
  lesson: string;
  future_applicability: string;
  timestamp: string;
  tags: string[];
  source?: 'agent_run' | 'seed';
}

export interface WorkflowEvidence {
  source: 'current' | 'historical';
  description: string;
  severity: 'info' | 'caution' | 'high';
  experience_id?: string;
  context?: string;
  outcome?: string;
  score?: number;
  reason?: string;
  lesson?: string;
}

export interface RecalledExperience {
  experience_id: string;
  context: string;
  service_name?: string;
  outcome: string;
  lesson?: string;
  root_cause?: string;
  future_applicability?: string;
  score?: number;
  tags?: string[];
}

export interface GeminiAgentReasoning {
  agent_name: 'planner' | 'coder' | 'tester' | 'security';
  summary: string;
  observations: string[];
  historical_context: string[];
  concerns: string[];
  recommended_action?: string | null;
}

export interface LLMStatus {
  provider: 'gemini';
  model: string;
  used: boolean;
  status: 'not_configured' | 'ready' | 'used' | 'error' | 'invalid_response';
  agents_used: string[];
}

export interface WorkflowContext {
  workflow_id: string;
  workflow_type: string;
  task_description: string;
  service_name: string;
  version: string;
  repository?: string;
  environment: string;
  deployment_target?: string;
  created_at: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'PASSED' | 'FAILED' | 'BLOCKED_BY_RISK' | 'COMPLETED_WITH_WARNING';
  outcome?: string;
  risk_level: 'NORMAL' | 'CAUTION' | 'HIGH RISK';
  risk_evidence: WorkflowEvidence[];
  current_evidence: WorkflowEvidence[];
  recommended_action?: string;
  recalled_experiences: RecalledExperience[];
  hindsight_available: boolean;
  hindsight_message?: string;
  hindsight_reflection?: string;
  retention_status: 'not_attempted' | 'remote' | 'local_only';
  summary_lesson?: string;
  steps: AgentStep[];
  extracted_experience?: ExperienceModel;
  llm: LLMStatus;
  gemini_reasoning: GeminiAgentReasoning[];
}

export async function fetchHealth(): Promise<{ status: string }> {
  const result = await requestJson<unknown>('/health');
  if (!result || typeof result !== 'object' || !('status' in result) || typeof result.status !== 'string') {
    throw new ApiRequestError('The backend returned an unexpected /health response.', 'response');
  }
  return result as { status: string };
}

export async function runWorkflowApi(
  payload: WorkflowRequest & DemoWorkflowControls,
): Promise<WorkflowContext> {
  const { force_failure, enable_recall, ...workflowRequest } = payload;
  const query = new URLSearchParams();
  if (force_failure !== undefined) query.set('force_failure', String(force_failure));
  if (enable_recall !== undefined) query.set('enable_recall', String(enable_recall));
  const queryString = query.size ? `?${query.toString()}` : '';
  return requestJson<WorkflowContext>(`/workflows/run${queryString}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflowRequest),
  });
}

export async function fetchWorkflowById(id: string): Promise<WorkflowContext> {
  return requestJson<WorkflowContext>(`/workflows/${encodeURIComponent(id)}`);
}

export async function fetchExperiences(): Promise<ExperienceModel[]> {
  const result = await requestJson<unknown>('/experiences');
  if (!Array.isArray(result)) {
    throw new ApiRequestError('The backend returned an unexpected /experiences response; expected a JSON array.', 'response');
  }
  return result as ExperienceModel[];
}

export async function storeExperience(exp: Partial<ExperienceModel>): Promise<any> {
  return requestJson('/experiences', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(exp),
  });
}

export async function assessRiskApi(payload: {
  task_description: string;
  service_name?: string;
}): Promise<any> {
  return requestJson('/risk-assessment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
