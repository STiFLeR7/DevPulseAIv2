// ── Agent definitions (static config) ─────────────

export const AGENTS = [
  { id: 'repo-researcher', name: 'RepoResearcher', icon: 'Search', swarm: 'Research', description: 'Deep-dives into GitHub repos, analyzes structure & dependencies', color: '#63ffd1' },
  { id: 'paper-analyst', name: 'PaperAnalyst', icon: 'FileText', swarm: 'Research', description: 'Finds and summarizes arXiv papers relevant to your tech stack', color: '#a78bfa' },
  { id: 'project-explorer', name: 'ProjectExplorer', icon: 'FolderOpen', swarm: 'Research', description: 'Scans local codebases to build project context and dependency graphs', color: '#00b4d8' },
  { id: 'community-vibe', name: 'CommunityVibe', icon: 'Globe', swarm: 'Analysis', description: 'Gauges developer sentiment from HN, Reddit, and social signals', color: '#ffbe32' },
  { id: 'risk-analyst', name: 'RiskAnalyst', icon: 'Shield', swarm: 'Analysis', description: 'Assesses security risks, abandon-ware likelihood, and license issues', color: '#ff6b6b' },
  { id: 'dep-impact', name: 'DepImpact', icon: 'Package', swarm: 'Analysis', description: 'Evaluates how dependency updates affect your project', color: '#e0e6ed' },
  { id: 'orchestrator', name: 'Orchestrator', icon: 'Brain', swarm: 'Core', description: 'Routes tasks, manages concurrency, and coordinates multi-swarm execution', color: '#63ffd1' },
  { id: 'evaluator', name: 'Evaluator', icon: 'Scale', swarm: 'Intelligence', description: 'Scores and ranks processed intelligence by relevance and confidence', color: '#a78bfa' },
  { id: 'trend-detector', name: 'TrendDetector', icon: 'BarChart3', swarm: 'Intelligence', description: 'Identifies emerging patterns across signal sources over time', color: '#00b4d8' },
];
