import { FormEvent, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Brain,
  Check,
  CircleHelp,
  Database,
  LoaderCircle,
  Play,
  RotateCcw,
  Shield,
  Sparkles,
  Workflow as WorkflowIcon,
  X,
} from 'lucide-react';
import type { ReactNode } from 'react';
import AgentActivityFeed from '../components/AgentActivityFeed';
import EvidenceCard from '../components/EvidenceCard';
import RiskBadge from '../components/RiskBadge';
import {
  DeploymentTarget,
  ApiRequestError,
  fetchHealth,
  runWorkflowApi,
  WorkflowContext,
  WorkflowEnvironment,
  WorkflowRequest,
  WorkflowType,
} from '../services/api';

interface WorkflowDraft {
  workflow_type: WorkflowType | '';
  task_description: string;
  service_name: string;
  version: string;
  repository: string;
  environment: WorkflowEnvironment | '';
  deployment_target: DeploymentTarget;
}

type WorkflowField = keyof WorkflowDraft;

const initialDraft: WorkflowDraft = {
  workflow_type: '',
  task_description: '',
  service_name: '',
  version: '',
  repository: 'payment-service-demo',
  environment: '',
  deployment_target: 'Kubernetes',
};

const examples: Array<{ label: string; draft: Partial<WorkflowDraft> }> = [
  {
    label: 'Deploy payment-service v2.5.0',
    draft: {
      workflow_type: 'Deployment',
      task_description: 'Deploy payment-service v2.5.0',
      service_name: 'payment-service',
      version: 'v2.5.0',
      environment: 'Production',
    },
  },
  {
    label: 'Update authentication middleware',
    draft: {
      workflow_type: 'Service Update',
      task_description: 'Update authentication middleware',
      service_name: 'authentication-service',
      version: 'v2.5.0',
      environment: 'Staging',
    },
  },
  {
    label: 'Migrate production database',
    draft: {
      workflow_type: 'Database Migration',
      task_description: 'Migrate the production database',
      service_name: 'payment-service',
      version: 'v2.5.0',
      environment: 'Production',
    },
  },
];

const workflowTypes: WorkflowType[] = [
  'Deployment',
  'Database Migration',
  'Configuration Change',
  'Service Update',
];
const environments: WorkflowEnvironment[] = ['Development', 'Staging', 'Production'];
const targets: DeploymentTarget[] = ['Kubernetes', 'Docker', 'Cloud VM', 'Other'];

function getWorkflowError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.kind === 'connection') return error.message;
    return `Workflow could not be started. ${error.message}`;
  }
  if (error instanceof Error) {
    return `Workflow could not be started. ${error.message}`;
  }
  return 'Workflow could not be started.';
}

function getStepStatus(workflow: WorkflowContext, agentName: string) {
  return workflow.steps.find((step) => step.agent_name === agentName)?.status;
}

function StepStatus({ status }: { status?: string }) {
  if (status === 'SUCCESS') {
    return <Check className="h-4 w-4 text-emerald-400" aria-label="Passed" />;
  }
  if (status === 'FAILED') {
    return <X className="h-4 w-4 text-red-400" aria-label="Failed" />;
  }
  if (status === 'WARNING') {
    return <AlertTriangle className="h-4 w-4 text-amber-400" aria-label="Warning" />;
  }
  if (status === 'SKIPPED') {
    return <ArrowRight className="h-4 w-4 text-gray-500" aria-label="Skipped" />;
  }
  return <CircleHelp className="h-4 w-4 text-gray-600" aria-label="No result returned" />;
}

export default function Dashboard() {
  const [draft, setDraft] = useState<WorkflowDraft>(initialDraft);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<WorkflowField, string>>>({});
  const [step, setStep] = useState<'form' | 'review'>('form');
  const [workflow, setWorkflow] = useState<WorkflowContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [error, setError] = useState('');
  const [replayState, setReplayState] = useState<'idle' | 'phase1' | 'phase2' | 'complete'>('idle');
  const [replayBaseline, setReplayBaseline] = useState<WorkflowContext | null>(null);
  const [replayMemoryRun, setReplayMemoryRun] = useState<WorkflowContext | null>(null);
  const formRef = useRef<HTMLElement>(null);
  const requestInFlight = useRef(false);

  useEffect(() => {
    fetchHealth()
      .then((result) => setHealth(result.status))
      .catch(() => setHealth(null))
      .finally(() => setHealthLoading(false));
  }, []);

  const updateField = (field: WorkflowField, value: string) => {
    setDraft((current) => ({ ...current, [field]: value }));
    setFieldErrors((current) => ({ ...current, [field]: undefined }));
  };

  const validateDraft = () => {
    const errors: Partial<Record<WorkflowField, string>> = {};
    if (!draft.workflow_type) errors.workflow_type = 'Choose a workflow type.';
    if (!draft.task_description.trim()) errors.task_description = 'Describe the task to run.';
    if (!draft.service_name.trim()) errors.service_name = 'Enter the service name.';
    if (!draft.version.trim()) errors.version = 'Enter the version.';
    if (!draft.environment) errors.environment = 'Choose an environment.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleReview = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    if (validateDraft()) setStep('review');
  };

  const asRequest = (): WorkflowRequest | null => {
    if (!draft.workflow_type || !draft.environment || !draft.task_description.trim() ||
      !draft.service_name.trim() || !draft.version.trim()) {
      setStep('form');
      validateDraft();
      return null;
    }
    return {
      workflow_type: draft.workflow_type,
      task_description: draft.task_description.trim(),
      service_name: draft.service_name.trim(),
      version: draft.version.trim(),
      repository: draft.repository.trim() || 'payment-service-demo',
      environment: draft.environment,
      deployment_target: draft.deployment_target,
    };
  };

  const submitWorkflow = async (request: WorkflowRequest) => {
    if (requestInFlight.current) return null;
    requestInFlight.current = true;
    setLoading(true);
    setError('');
    setWorkflow(null);
    setReplayBaseline(null);
    setReplayMemoryRun(null);
    setReplayState('idle');
    try {
      const result = await runWorkflowApi(request);
      setWorkflow(result);
      setStep('form');
      return result;
    } catch (caught) {
      setError(getWorkflowError(caught));
      return null;
    } finally {
      requestInFlight.current = false;
      setLoading(false);
    }
  };

  const handleStartWorkflow = () => {
    const request = asRequest();
    if (request) void submitWorkflow(request);
  };

  const handleReplayDemo = async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setLoading(true);
    setError('');
    setStep('form');
    setDraft((current) => ({
      ...current,
      workflow_type: 'Deployment',
      task_description: 'Deploy API v2 endpoint with legacy auth middleware',
      service_name: 'payment-auth',
      version: 'v2',
      environment: 'Staging',
      repository: 'payment-service-demo',
      deployment_target: 'Kubernetes',
    }));
    setReplayBaseline(null);
    setReplayMemoryRun(null);
    setReplayState('phase1');
    try {
      const demoRequest: WorkflowRequest = {
        workflow_type: 'Deployment',
        task_description: 'Deploy API v2 endpoint with legacy auth middleware',
        service_name: 'payment-auth',
        version: 'v2',
        repository: 'payment-service-demo',
        environment: 'Staging',
        deployment_target: 'Kubernetes',
      };
      const firstRun = await runWorkflowApi({
        ...demoRequest,
        enable_recall: false,
        force_failure: true,
      });
      setWorkflow(firstRun);
      setReplayBaseline(firstRun);
      setReplayState('phase2');
      await new Promise((resolve) => setTimeout(resolve, 3500));
      const secondRun = await runWorkflowApi({ ...demoRequest, enable_recall: true });
      setWorkflow(secondRun);
      setReplayMemoryRun(secondRun);
      setReplayState('complete');
    } catch (caught) {
      setError(getWorkflowError(caught));
      setReplayState('idle');
    } finally {
      requestInFlight.current = false;
      setLoading(false);
    }
  };

  const populateExample = (exampleDraft: Partial<WorkflowDraft>) => {
    setDraft((current) => ({ ...current, ...exampleDraft }));
    setFieldErrors({});
    setError('');
    setStep('form');
    formRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const matchedEvidence = workflow?.risk_evidence[0];
  const matchedExperience = matchedEvidence
    ? workflow?.recalled_experiences.find((experience) => experience.experience_id === matchedEvidence.experience_id)
    : workflow?.recalled_experiences[0];
  const currentFinding = workflow?.steps.find((agentStep) =>
    agentStep.status === 'FAILED' || agentStep.status === 'WARNING',
  );
  const statusLabel = workflow?.status === 'BLOCKED_BY_RISK' ? 'BLOCKED' : workflow?.status;
  const completedAgents = workflow?.steps.filter((agentStep) => agentStep.status !== 'SKIPPED').length ?? 0;
  const warnings = workflow?.steps.filter((agentStep) => agentStep.status === 'WARNING').length ?? 0;
  const failures = workflow?.steps.filter((agentStep) => agentStep.status === 'FAILED').length ?? 0;
  const memoryInfluenced = workflow?.steps.filter((agentStep) => agentStep.metadata?.memory_influenced).length ?? 0;
  const testerResultAvailable = Boolean(
    replayBaseline?.steps.some((agentStep) => agentStep.agent_name === 'tester') &&
    replayMemoryRun?.steps.some((agentStep) => agentStep.agent_name === 'tester'),
  );

  return (
    <div className="space-y-6">
      {error && (
        <div role="alert" className="flex items-start gap-3 rounded-lg border border-red-800/70 bg-red-950/40 p-4 text-sm text-red-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
          <p>{error}</p>
        </div>
      )}

      {replayState !== 'idle' && (
        <div className="flex items-start justify-between gap-4 rounded-xl border border-indigo-800/70 bg-indigo-950/40 p-4">
          <div className="flex items-start gap-3">
            <RotateCcw className={`mt-0.5 h-5 w-5 shrink-0 text-indigo-300 ${loading ? 'animate-spin' : ''}`} />
            <div>
              <h2 className="text-sm font-semibold text-indigo-100">Demo / Evaluation Mode</h2>
              <p className="mt-1 text-xs text-indigo-200/80">
                {replayState === 'phase1' && 'Run 1: Memory OFF — awaiting the backend workflow result.'}
                {replayState === 'phase2' && 'Run 1 returned. Run 2: Memory ON — awaiting the backend workflow result.'}
                {replayState === 'complete' && 'Both backend results are available for comparison.'}
              </p>
            </div>
          </div>
          {replayState === 'complete' && (
            <button onClick={() => setReplayState('idle')} className="text-xs text-indigo-200 hover:text-white">
              Dismiss
            </button>
          )}
        </div>
      )}

      <section ref={formRef} className="scroll-mt-24 rounded-xl border border-gray-800 bg-gray-900/60 p-5 md:p-6">
        <div className="mb-5 flex items-start gap-3 border-b border-gray-800 pb-4">
          <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-2 text-indigo-300">
            <WorkflowIcon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-indigo-300">Learn what happened. Improve what happens next.</p>
            <h1 className="mt-1 text-lg font-bold text-gray-100">
              {step === 'form' ? 'Create New Workflow' : 'Review Workflow'}
            </h1>
            <p className="mt-1 text-xs text-gray-400">
              {step === 'form'
                ? 'Add a little context so Sentinel can assess this workflow against relevant experience.'
                : 'Confirm the workflow details and Hindsight behavior before starting.'}
            </p>
          </div>
        </div>

        {step === 'form' ? (
          <form onSubmit={handleReview} noValidate>
            <div className="grid grid-cols-1 gap-x-5 gap-y-4 md:grid-cols-2">
              <FormField label="Workflow Type" required error={fieldErrors.workflow_type}>
                <select
                  value={draft.workflow_type}
                  onChange={(event) => updateField('workflow_type', event.target.value)}
                  className={inputClass(Boolean(fieldErrors.workflow_type))}
                >
                  <option value="">Select a workflow type</option>
                  {workflowTypes.map((type) => <option key={type} value={type}>{type}</option>)}
                </select>
              </FormField>

              <FormField label="Environment" required error={fieldErrors.environment}>
                <select
                  value={draft.environment}
                  onChange={(event) => updateField('environment', event.target.value)}
                  className={inputClass(Boolean(fieldErrors.environment))}
                >
                  <option value="">Select an environment</option>
                  {environments.map((environment) => <option key={environment} value={environment}>{environment}</option>)}
                </select>
              </FormField>

              <FormField label="Task Description" required error={fieldErrors.task_description}>
                <input
                  value={draft.task_description}
                  onChange={(event) => updateField('task_description', event.target.value)}
                  placeholder="Deploy the new payment service version"
                  className={inputClass(Boolean(fieldErrors.task_description))}
                />
              </FormField>

              <FormField label="Service Name" required error={fieldErrors.service_name}>
                <input
                  value={draft.service_name}
                  onChange={(event) => updateField('service_name', event.target.value)}
                  placeholder="payment-service"
                  className={inputClass(Boolean(fieldErrors.service_name))}
                />
              </FormField>

              <FormField label="Version" required error={fieldErrors.version}>
                <input
                  value={draft.version}
                  onChange={(event) => updateField('version', event.target.value)}
                  placeholder="v2.5.0"
                  className={inputClass(Boolean(fieldErrors.version))}
                />
              </FormField>

              <FormField label="Repository / Project">
                <input
                  value={draft.repository}
                  onChange={(event) => updateField('repository', event.target.value)}
                  placeholder="payment-service-demo"
                  className={inputClass(false)}
                />
                <p className="mt-1 text-[10px] text-gray-500">Demo default — edit if needed.</p>
              </FormField>

              <FormField label="Deployment Target">
                <select
                  value={draft.deployment_target}
                  onChange={(event) => updateField('deployment_target', event.target.value)}
                  className={inputClass(false)}
                >
                  {targets.map((target) => <option key={target} value={target}>{target}</option>)}
                </select>
                <p className="mt-1 text-[10px] text-gray-500">Demo default — edit if needed.</p>
              </FormField>
            </div>

            {Object.values(fieldErrors).some(Boolean) && (
              <p role="alert" className="mt-4 rounded-lg border border-amber-800/50 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
                More information is needed before we can create this workflow. Complete the highlighted fields.
              </p>
            )}

            <div className="mt-5 flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-indigo-500"
              >
                Review Workflow <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </form>
        ) : (
          <div>
            <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
              <ReviewField label="Workflow Type" value={draft.workflow_type} />
              <ReviewField label="Service" value={draft.service_name} />
              <ReviewField label="Version" value={draft.version} />
              <ReviewField label="Repository" value={draft.repository || 'payment-service-demo (demo default)'} />
              <ReviewField label="Environment" value={draft.environment} />
              <ReviewField label="Deployment Target" value={draft.deployment_target} />
              <div className="sm:col-span-2">
                <ReviewField label="Task Description" value={draft.task_description} />
              </div>
            </dl>

            <div className="mt-5 rounded-lg border border-indigo-700/50 bg-indigo-950/25 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-indigo-200">
                <Brain className="h-4 w-4" /> Hindsight Memory: ENABLED
              </div>
              <ol className="mt-2 grid gap-1 text-xs leading-5 text-gray-300 sm:grid-cols-2">
                <li>1. Analyze the workflow</li>
                <li>2. Recall relevant past experiences</li>
                <li>3. Run the agent workflow</li>
                <li>4. Assess current and historical risk</li>
                <li>5. Provide evidence and recommendations</li>
                <li>6. Store the resulting experience for future workflows</li>
              </ol>
            </div>

            <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
              <button
                onClick={() => setStep('form')}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-700 px-4 py-2.5 text-xs font-semibold text-gray-300 hover:border-gray-600 hover:text-white disabled:opacity-50"
              >
                <ArrowLeft className="h-4 w-4" /> Back &amp; Edit
              </button>
              <button
                onClick={handleStartWorkflow}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {loading ? 'Starting Workflow…' : 'Start Workflow'}
              </button>
            </div>
          </div>
        )}
      </section>

      {!workflow && (
        <section className="rounded-xl border border-gray-800 bg-gray-900/35 p-5">
          <h2 className="text-sm font-semibold text-gray-200">No workflow running</h2>
          <p className="mt-1 text-xs text-gray-400">
            Create a workflow to see agents, Hindsight memory, risk analysis, and recommendations.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {examples.map((example) => (
              <button
                key={example.label}
                onClick={() => populateExample(example.draft)}
                className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-left text-xs text-gray-300 transition hover:border-indigo-500/60 hover:text-indigo-200"
              >
                {example.label}
              </button>
            ))}
          </div>
        </section>
      )}

      {workflow && (
        <>
          <section className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-indigo-300">Current Workflow</p>
                <h2 className="mt-1 text-base font-semibold text-gray-100">{workflow.task_description}</h2>
                <p className="mt-1 text-xs text-gray-400">
                  {workflow.workflow_type.replace(/_/g, ' ')} · Version {workflow.version} · {workflow.repository || 'Not provided'}
                </p>
              </div>
              <span className={`w-fit rounded-md border px-2.5 py-1 text-[10px] font-bold tracking-wide ${statusClass(workflow.status)}`}>
                {statusLabel}
              </span>
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-gray-800 pt-4 text-xs sm:grid-cols-4">
              <SummaryField label="Service" value={workflow.service_name} />
              <SummaryField label="Environment" value={workflow.environment} />
              <SummaryField label="Target" value={workflow.deployment_target || 'Not provided'} />
              <SummaryField label="Current agent" value={workflow.status === 'IN_PROGRESS'
                ? workflow.steps[workflow.steps.length - 1]?.agent_name || 'Not reported'
                : 'Not active (result returned)'} />
              <SummaryField label="Completed agents" value={`${completedAgents} of ${workflow.steps.length}`} />
              <SummaryField label="Warnings" value={String(warnings)} />
              <SummaryField label="Failures" value={String(failures)} />
              <SummaryField label="Hindsight-influenced agents" value={String(memoryInfluenced)} />
            </dl>
          </section>

          <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
            <div className="flex flex-col justify-between gap-2 border-b border-gray-800 pb-3 sm:flex-row sm:items-center">
              <div>
                <h2 className="text-sm font-semibold text-gray-100">Gemini Agent Reasoning</h2>
                <p className="mt-1 text-xs text-gray-500">
                  Reasoning supplements the agents; risk remains assigned by the deterministic Risk Engine.
                </p>
              </div>
              <span className={`w-fit rounded border px-2 py-1 text-[10px] font-semibold ${
                workflow.llm.used
                  ? 'border-emerald-800/60 bg-emerald-950/40 text-emerald-300'
                  : 'border-gray-700 bg-gray-950/50 text-gray-400'
              }`}>
                {workflow.llm.provider} · {workflow.llm.model} · {workflow.llm.used ? 'used' : workflow.llm.status.replace(/_/g, ' ')}
              </span>
            </div>
            {workflow.gemini_reasoning.length > 0 ? (
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {workflow.gemini_reasoning.map((reasoning) => (
                  <article key={reasoning.agent_name} className="rounded-lg border border-indigo-900/50 bg-indigo-950/15 p-3">
                    <h3 className="text-[10px] font-bold uppercase tracking-wide text-indigo-300">
                      {reasoning.agent_name} perspective
                    </h3>
                    <p className="mt-1.5 text-xs leading-5 text-gray-200">{reasoning.summary}</p>
                    {reasoning.observations.length > 0 && (
                      <ReasoningList label="Observations" items={reasoning.observations} />
                    )}
                    {reasoning.historical_context.length > 0 && (
                      <ReasoningList label="Historical context" items={reasoning.historical_context} />
                    )}
                    {reasoning.concerns.length > 0 && (
                      <ReasoningList label="Concerns to review" items={reasoning.concerns} />
                    )}
                    {reasoning.recommended_action && (
                      <p className="mt-2 text-[11px] leading-5 text-gray-300">
                        <strong className="text-gray-100">Agent suggestion:</strong> {reasoning.recommended_action}
                      </p>
                    )}
                  </article>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-xs text-gray-400">
                Gemini did not provide reasoning for this workflow. The existing deterministic agent behavior and Risk Engine remain active.
              </p>
            )}
          </section>

          {workflow.risk_level !== 'NORMAL' && (
            <section className="rounded-xl border border-amber-800/50 bg-gray-900/70 p-5">
              <h2 className="text-sm font-bold text-gray-100">Why this risk?</h2>
              <div className="mt-3 grid gap-3 text-xs md:grid-cols-3">
                <EvidenceSummary
                  label="Current finding"
                  value={currentFinding
                    ? `${currentFinding.agent_name}: ${currentFinding.observation}`
                    : 'No separate current finding was returned by the backend.'}
                />
                <EvidenceSummary
                  label="Historical experience"
                  value={matchedExperience
                    ? `${matchedExperience.context} — ${matchedExperience.outcome}${matchedExperience.lesson ? `. Lesson: ${matchedExperience.lesson}` : ''}`
                    : matchedEvidence
                      ? `${matchedEvidence.experience_id} — ${matchedEvidence.context} (${matchedEvidence.outcome})`
                      : 'No recalled experience details were returned by the backend.'}
                />
                <EvidenceSummary
                  label="Connection"
                  value={matchedEvidence?.reason || 'The backend did not return a connection rationale.'}
                />
              </div>
              <div className="mt-4 flex flex-col gap-2 border-t border-gray-800 pt-3 sm:flex-row sm:items-start">
                <p className="shrink-0 text-xs text-gray-300">
                  Risk: <strong className={riskClass(workflow.risk_level)}>{workflow.risk_level}</strong>
                </p>
                {workflow.recommended_action && (
                  <p className="text-xs leading-5 text-gray-300">
                    <strong className="text-gray-100">Recommendation:</strong> {workflow.recommended_action}
                  </p>
                )}
              </div>
            </section>
          )}

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
              <div className="mb-4 border-b border-gray-800 pb-3">
                <h2 className="text-sm font-semibold text-gray-100">Agent Pipeline</h2>
                <p className="mt-1 text-xs text-gray-500">Showing the state returned by the workflow backend.</p>
              </div>
              <div className="mb-4 grid grid-cols-4 gap-2">
                {(['planner', 'coder', 'tester', 'security'] as const).map((agentName, index) => (
                  <div key={agentName} className="flex min-w-0 items-center gap-1.5 rounded-md border border-gray-800 bg-gray-950/50 px-2 py-2">
                    <StepStatus status={getStepStatus(workflow, agentName)} />
                    <span className="truncate text-[10px] font-medium capitalize text-gray-300">{agentName}</span>
                    {index < 3 && <ArrowRight className="hidden h-3 w-3 text-gray-600 xl:block" />}
                  </div>
                ))}
              </div>
              {workflow.status === 'IN_PROGRESS' && (
                <p className="mb-3 text-[11px] text-indigo-300">
                  Current agent: {workflow.steps[workflow.steps.length - 1]?.agent_name || 'Not reported by backend'}
                </p>
              )}
              <AgentActivityFeed steps={workflow.steps} isExecuting={workflow.status === 'IN_PROGRESS'} />
            </section>

            <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
              <div className="mb-4 flex items-start justify-between gap-3 border-b border-gray-800 pb-3">
                <div>
                  <h2 className="text-sm font-semibold text-gray-100">Hindsight · Relevant Experiences</h2>
                  <p className="mt-1 text-xs text-gray-500">Current situation + past experience = better decision.</p>
                </div>
                <span className="rounded border border-indigo-800/50 bg-indigo-950/50 px-2 py-1 text-[10px] font-semibold text-indigo-200">
                  {workflow.recalled_experiences.length} returned
                </span>
              </div>
              {workflow.hindsight_reflection && (
                <div className="mb-3 rounded-md border border-indigo-900/50 bg-indigo-950/20 p-3 text-[11px] leading-5 text-indigo-100">
                <strong className="mr-1 text-indigo-300">Reflection:</strong>{workflow.hindsight_reflection}
                </div>
              )}
              {workflow.hindsight_message && (
                <p className="mb-3 text-[11px] leading-5 text-amber-200">{workflow.hindsight_message}</p>
              )}
              <EvidenceCard
                evidence={workflow.risk_evidence}
                recalledExperiences={workflow.recalled_experiences}
                extractedExperience={workflow.extracted_experience || replayBaseline?.extracted_experience}
                retentionStatus={workflow.retention_status}
              />
            </section>
          </div>

          {testerResultAvailable && replayBaseline && replayMemoryRun && (
            <section className="rounded-xl border border-indigo-800/50 bg-indigo-950/20 p-5">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-300" />
                <h2 className="text-sm font-semibold text-gray-100">Behavior Change · Closed-Loop Replay</h2>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <ReplayColumn title="Without relevant experience" workflow={replayBaseline} />
                <ReplayColumn title="With Hindsight" workflow={replayMemoryRun} />
              </div>
              <p className="mt-3 text-[10px] text-gray-500">Comparison uses the actual outcomes and tester steps returned by both demo runs.</p>
            </section>
          )}

          {workflow.risk_level && (
            <RiskBadge
              riskLevel={workflow.risk_level}
              recommendedAction={workflow.recommended_action}
              evidenceCount={workflow.risk_evidence.length + workflow.current_evidence.length}
            />
          )}
        </>
      )}

      <section className="rounded-xl border border-gray-800 bg-gray-950/40 p-4">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xs font-semibold text-gray-200">Demo / Evaluation Mode</h2>
            <p className="mt-1 text-[11px] text-gray-500">Replay the closed-loop scenario: first without recall, then with Hindsight memory enabled.</p>
          </div>
          <button
            onClick={() => void handleReplayDemo()}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-indigo-700/60 bg-indigo-950/50 px-3 py-2 text-xs font-semibold text-indigo-200 transition hover:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Replay Closed-Loop Demo
          </button>
        </div>
      </section>

      <footer className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-lg border border-gray-800 bg-gray-900/30 px-4 py-3 text-[10px] text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className={`h-2 w-2 rounded-full ${health ? 'bg-emerald-400' : 'bg-amber-400'}`} />
          Backend API: <strong className={health ? 'text-emerald-300' : 'text-amber-300'}>
            {healthLoading ? 'Checking…' : health || 'Unavailable'}
          </strong>
        </span>
        <span className="flex items-center gap-1.5"><Database className="h-3 w-3" /> Vectorize Hindsight Experience Engine</span>
        <span className="ml-auto flex items-center gap-1.5 text-gray-400"><Shield className="h-3 w-3" /> Learn from what happened. Detect what matters. Act differently next time.</span>
      </footer>
    </div>
  );
}

function inputClass(hasError: boolean) {
  return `w-full rounded-lg border bg-gray-950 px-3 py-2.5 text-xs text-gray-100 placeholder-gray-600 outline-none transition focus:border-indigo-500 ${
    hasError ? 'border-red-600/80' : 'border-gray-700'
  }`;
}

function FormField({
  label,
  required,
  error,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-xs font-medium text-gray-300">
      <span className="mb-1.5 block">{label}{required && <span className="ml-1 text-indigo-300">*</span>}</span>
      {children}
      {error && <span className="mt-1 block text-[10px] font-normal text-red-300">{error}</span>}
    </label>
  );
}

function ReviewField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="mt-1 break-words text-xs text-gray-200">{value}</dd>
    </div>
  );
}

function SummaryField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] text-gray-500">{label}</dt>
      <dd className="mt-1 break-words text-xs font-medium text-gray-200">{value}</dd>
    </div>
  );
}

function EvidenceSummary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-800 bg-gray-950/50 p-3">
      <p className="mb-1 text-[10px] font-bold uppercase tracking-wide text-amber-300">{label}</p>
      <p className="leading-5 text-gray-300">{value}</p>
    </div>
  );
}

function ReasoningList({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="mt-2">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-500">{label}</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] leading-5 text-gray-300">
        {items.map((item, index) => <li key={`${label}-${index}`}>{item}</li>)}
      </ul>
    </div>
  );
}

function ReplayColumn({ title, workflow }: { title: string; workflow: WorkflowContext }) {
  const testStep = workflow.steps.find((agentStep) => agentStep.agent_name === 'tester');
  return (
    <div className="rounded-lg border border-gray-800 bg-gray-950/50 p-4">
      <h3 className="text-xs font-semibold text-gray-200">{title}</h3>
      <p className="mt-2 text-[10px] uppercase tracking-wide text-gray-500">Returned outcome</p>
      <p className={`mt-1 text-sm font-bold ${statusTextClass(workflow.status)}`}>{workflow.status}</p>
      {testStep && (
        <div className="mt-3 flex items-start gap-2 border-t border-gray-800 pt-3">
          <StepStatus status={testStep.status} />
          <div>
            <p className="text-[10px] font-semibold uppercase text-gray-500">Tester result</p>
            <p className="mt-1 text-xs text-gray-300">{testStep.observation}</p>
            <ArrowDown className="my-1 h-3.5 w-3.5 text-indigo-400" />
            <p className="text-[11px] text-gray-400">{testStep.action_taken}</p>
          </div>
        </div>
      )}
      {workflow.recommended_action && (
        <p className="mt-3 border-t border-gray-800 pt-3 text-[11px] leading-5 text-gray-400">
          Recommendation: {workflow.recommended_action}
        </p>
      )}
    </div>
  );
}

function statusClass(status: WorkflowContext['status']) {
  if (status === 'PASSED') return 'border-emerald-700/60 bg-emerald-950/40 text-emerald-300';
  if (status === 'FAILED') return 'border-red-700/60 bg-red-950/40 text-red-300';
  if (status === 'BLOCKED_BY_RISK') return 'border-amber-700/60 bg-amber-950/40 text-amber-300';
  if (status === 'COMPLETED_WITH_WARNING') return 'border-amber-700/60 bg-amber-950/40 text-amber-300';
  return 'border-indigo-700/60 bg-indigo-950/40 text-indigo-300';
}

function statusTextClass(status: WorkflowContext['status']) {
  if (status === 'PASSED') return 'text-emerald-300';
  if (status === 'FAILED') return 'text-red-300';
  if (status === 'BLOCKED_BY_RISK') return 'text-amber-300';
  if (status === 'COMPLETED_WITH_WARNING') return 'text-amber-300';
  return 'text-gray-300';
}

function riskClass(level: WorkflowContext['risk_level']) {
  if (level === 'HIGH RISK') return 'text-red-300';
  if (level === 'CAUTION') return 'text-amber-300';
  return 'text-emerald-300';
}
