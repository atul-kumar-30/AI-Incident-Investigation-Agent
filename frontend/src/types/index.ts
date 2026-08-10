export type IncidentStatus = 'OPEN' | 'INVESTIGATING' | 'RESOLVED' | 'FAILED';
export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentSource = 'MANUAL' | 'API';

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  source: IncidentSource;
  created_at: string;
  updated_at: string;
}

export interface IncidentCreate {
  title: string;
  description: string;
  severity?: IncidentSeverity;
}

export interface IncidentUpdate {
  title?: string;
  description?: string;
  status?: IncidentStatus;
  severity?: IncidentSeverity;
}

export type InvestigationRunStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export const InvestigationRunStatus = {
  PENDING: 'PENDING',
  RUNNING: 'RUNNING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
} as const;

export type StepType = 'PLANNING' | 'TOOL_CALL' | 'TOOL_RESULT' | 'SYSTEM';

export const StepType = {
  PLANNING: 'PLANNING',
  TOOL_CALL: 'TOOL_CALL',
  TOOL_RESULT: 'TOOL_RESULT',
  SYSTEM: 'SYSTEM',
} as const;

export type StepStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export const StepStatus = {
  PENDING: 'PENDING',
  RUNNING: 'RUNNING',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
} as const;

export type EvidenceSourceType = 'INCIDENT' | 'TOOL' | 'LOG' | 'CODE' | 'GIT_CHANGE' | 'DOCUMENT';

export const EvidenceSourceType = {
  INCIDENT: 'INCIDENT',
  TOOL: 'TOOL',
  LOG: 'LOG',
  CODE: 'CODE',
  GIT_CHANGE: 'GIT_CHANGE',
  DOCUMENT: 'DOCUMENT'
} as const;

export interface InvestigationRun {
  id: string;
  incident_id: string;
  status: InvestigationRunStatus;
  current_step?: string;
  summary?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface InvestigationStep {
  id: string;
  investigation_run_id: string;
  step_number: number;
  node_name: string;
  step_type: StepType;
  status: StepStatus;
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface Evidence {
  id: string;
  investigation_run_id: string;
  source_type: EvidenceSourceType;
  source_name: string;
  content: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface LogEntry {
  id: string;
  incident_id?: string;
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
  service: string;
  environment?: string;
  message: string;
  trace_id?: string;
  request_id?: string;
  endpoint?: string;
  http_status?: number;
  metadata_?: Record<string, any>;
  created_at: string;
}

export type RepositorySourceType = 'LOCAL' | 'GIT';

export type IngestionStatus = 'PENDING' | 'INDEXING' | 'READY' | 'FAILED';

export interface Repository {
  id: string;
  name: string;
  source_type: RepositorySourceType;
  source_location: string;
  default_branch?: string;
  current_commit?: string;
  ingestion_status: IngestionStatus;
  created_at: string;
  updated_at: string;
}

export interface RepositoryCreate {
  name: string;
  source_type: RepositorySourceType;
  source_location: string;
  default_branch?: string;
}

export type DocumentType = 'RUNBOOK' | 'ARCHITECTURE' | 'SERVICE_DOC' | 'TROUBLESHOOTING' | 'POSTMORTEM' | 'GENERAL';

export interface Document {
  id: string;
  title: string;
  type: DocumentType;
  status: IngestionStatus;
  created_at: string;
}

export type HypothesisStatus = 'PROPOSED' | 'UNDER_REVIEW' | 'SUPPORTED' | 'WEAKENED' | 'INCONCLUSIVE';

export type HypothesisCategory = 'APPLICATION' | 'DATABASE' | 'INFRASTRUCTURE' | 'CONFIGURATION' | 'DEPLOYMENT' | 'DEPENDENCY' | 'TRAFFIC' | 'AUTHENTICATION' | 'UNKNOWN';

export type EvidenceRelationshipType = 'SUPPORTS' | 'CONTRADICTS' | 'NEUTRAL' | 'CONTEXT';

export type EvidenceStrength = 'LOW' | 'MEDIUM' | 'HIGH';

export interface HypothesisEvidenceMapping {
  id: string;
  hypothesis_id: string;
  evidence_id: string;
  relationship: EvidenceRelationshipType;
  strength: EvidenceStrength;
  reason?: string;
  origin?: 'INITIAL' | 'VERIFICATION';
  created_at: string;
  evidence?: Evidence;
}

export type HypothesisVerificationStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';

export type VerificationStepType = 'PLANNING' | 'TOOL_CALL' | 'TOOL_RESULT' | 'EVIDENCE_EVALUATION' | 'SYSTEM';

export interface VerificationStep {
  id: string;
  verification_id: string;
  step_number: number;
  step_type: VerificationStepType;
  status: string;
  tool_name?: string;
  objective?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface HypothesisVerification {
  id: string;
  hypothesis_id: string;
  investigation_run_id: string;
  status: HypothesisVerificationStatus;
  verification_objective?: string;
  initial_score?: number;
  final_score?: number;
  support_delta: number;
  contradiction_delta: number;
  summary?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Hypothesis {
  id: string;
  investigation_run_id: string;
  title: string;
  description: string;
  category: HypothesisCategory;
  status: HypothesisStatus;
  rank?: number;
  score?: number;
  preliminary_score?: number; // legacy frontend might use this
  generation_source?: string;
  reasoning_summary?: string;
  missing_evidence?: Array<{description: string, preferred_source?: string}>;
  verification_requirements?: string[];
  created_at: string;
  updated_at: string;
  evidence_mappings?: HypothesisEvidenceMapping[];
  verifications?: HypothesisVerification[];
}
