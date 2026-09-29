import os
from app.models.experience import WorkflowContext, AgentStep
from app.llm.gemini_client import analyze_workflow_agent

def run_planner_agent(context: WorkflowContext) -> AgentStep:
    """
    Planner Agent: Analyzes the task description AND retrieved Hindsight memories.
    CRITICAL: Retrieved experiences DIRECTLY INFLUENCE agent decision-making.
    """
    task = context.task_description
    recalled = context.recalled_experiences
    
    observation = (
        f"Workflow analysis request: type='{context.workflow_type}', task='{task}', "
        f"service='{context.service_name}', version='{context.version}', "
        f"repository/project='{context.repository or 'not provided'}', "
        f"environment='{context.environment}', target='{context.deployment_target or 'not provided'}'."
    )
    
    # Check if Hindsight retrieved relevant prior experiences
    memory_influence = None
    if recalled:
        matched = recalled[0]
        exp_id = matched.get("experience_id", "past-memory")
        lesson = matched.get("lesson", "")
        outcome = matched.get("outcome", "FAILURE")
        
        observation += f" Hindsight Memory Retrieved: Matched past experience [{exp_id}] (Outcome: {outcome}). Lesson: '{lesson}'."
        memory_influence = (
            f"[MEMORY INFLUENCE - Hindsight Precedent {exp_id}]:\n"
            f"Previous incident shows that executing '{task}' without fallback handling resulted in {outcome}. "
            f"Lesson Learned: '{lesson}'.\n"
            f"Planner Decision Modification: Incorporating proactive risk mitigation into plan roadmap."
        )

    groq_api_key = os.getenv("GROQ_API_KEY")
    plan_steps = []
    
    if groq_api_key and groq_api_key != "mock_groq_key":
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            
            prompt_context = (
                f"Workflow type: '{context.workflow_type}'. Task: '{task}'. "
                f"Service: '{context.service_name}'. Version: '{context.version}'. "
                f"Repository/project label: '{context.repository or 'not provided'}'. "
                f"Environment: '{context.environment}'. Deployment target: "
                f"'{context.deployment_target or 'not provided'}'."
            )
            if memory_influence:
                prompt_context += f" Hindsight Memory Lesson: '{lesson}'. Modify plan to avoid repeating past failure."
                
            prompt = (
                "Create a concise controlled workflow-analysis plan from the supplied facts. "
                "Do not claim to inspect repository contents, run real tests, or deploy software. "
                "Do not invent files or repository details. "
                f"{prompt_context}"
            )
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                max_tokens=200
            )
            raw_text = response.choices[0].message.content or ""
            plan_steps = [s.strip() for s in raw_text.split("\n") if s.strip()][:3]
        except Exception as e:
            plan_steps = []
            
    if not plan_steps:
        # Structured deterministic agent planning logic
        if "legacy auth" in task.lower() or "auth middleware" in task.lower():
            if recalled:
                plan_steps = [
                    f"1. Preserving X-Legacy-Auth header fallback in API v2 routes as instructed by Hindsight [{recalled[0].get('experience_id')}].",
                    "2. Apply dual-authentication middleware patch supporting both v2 bearer tokens & legacy headers.",
                    "3. Validate backward compatibility against legacy web client suite."
                ]
            else:
                # Baseline plan without memory (Strips legacy headers -> leads to test failure)
                plan_steps = [
                    "1. Update API v2 route definitions to require new bearer token format.",
                    "2. Remove legacy authorization header middleware.",
                    "3. Execute standard v2 route integration tests."
                ]
        elif "flaky test" in task.lower() or "async" in task.lower():
            if recalled:
                plan_steps = [
                    f"1. Enforce 300ms exponential retry policy on async worker database pools as learned from [{recalled[0].get('experience_id')}].",
                    "2. Isolate worker queue connection listener.",
                    "3. Run 100x iteration load test suite."
                ]
            else:
                plan_steps = [
                    "1. Run async worker test harness.",
                    "2. Log connection pool errors.",
                    "3. Execute test suite."
                ]
        elif "env" in task.lower() or "misconfig" in task.lower():
            if recalled:
                plan_steps = [
                    f"1. Inject DB_POOL_SIZE default fallback directly in container init script per Hindsight [{recalled[0].get('experience_id')}].",
                    "2. Audit k8s ConfigMap definitions.",
                    "3. Deploy container update."
                ]
            else:
                plan_steps = [
                    "1. Update deployment manifest.",
                    "2. Deploy pod update.",
                    "3. Verify pod status."
                ]
        else:
            plan_steps = [
                f"1. Confirm the requested {context.workflow_type.replace('_', ' ')} for {context.service_name} {context.version}.",
                f"2. Review workflow considerations for {context.environment} on {context.deployment_target or 'the selected target'}.",
                "3. Identify validation and security checks; report limitations where repository execution is unavailable.",
                "4. Consider relevant recalled experience and determine a risk-informed recommendation.",
            ]

    decision_parts = []
    if memory_influence:
        decision_parts.append(memory_influence)
    decision_parts.append("Execution Plan:\n" + "\n".join(plan_steps))
    
    decision = "\n\n".join(decision_parts)
    action_taken = (
        "Generated a memory-informed simulated workflow-analysis roadmap."
        if recalled
        else "Generated a baseline simulated workflow-analysis roadmap."
    )
    
    step = AgentStep(
        agent_name="planner",
        observation=observation,
        decision=decision,
        action_taken=action_taken,
        status="SUCCESS",
        metadata={"plan_steps": plan_steps, "memory_influenced": bool(recalled)}
    )
    analysis = analyze_workflow_agent(
        context,
        "planner",
        "Interpret the complete workflow request and assess whether this deterministic plan addresses the supplied context and recalled lessons. Do not create new repository facts.",
        {"deterministic_plan": plan_steps},
    )
    if analysis:
        context.gemini_reasoning.append(analysis)
        step.metadata["gemini_reasoning"] = analysis.model_dump()
    context.steps.append(step)
    return step
