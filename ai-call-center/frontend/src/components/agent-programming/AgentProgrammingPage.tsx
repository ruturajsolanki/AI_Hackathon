/**
 * Agent Programming Page
 * 
 * Visual interface for configuring AI agent prompts and LLM settings.
 * Allows customization of Primary, Supervisor, and Escalation agents.
 */

import { useState, useEffect, useCallback } from 'react'
import styles from './AgentProgrammingPage.module.css'

interface AgentConfig {
  agentId: string
  agentName: string
  agentType: 'primary' | 'supervisor' | 'escalation'
  description: string
  systemPrompt: string
  userPromptTemplate: string
  outputSchema: Record<string, unknown>
  model: string
  temperature: number
  maxTokens: number
  topP: number
  confidenceThreshold: number
  fallbackEnabled: boolean
  isCustom: boolean
  version: number
  updatedAt: string
}

interface TestResult {
  success: boolean
  output?: string
  parsedOutput?: Record<string, unknown>
  latencyMs: number
  tokensUsed?: number
  error?: string
}

const API_BASE = import.meta.env.VITE_API_URL || ''

// Model options per provider
const OPENAI_MODELS = [
  { value: 'gpt-4o', label: 'GPT-4o (Most Capable)' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (Fast)' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
]

const GEMINI_MODELS = [
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash (Recommended)' },
  { value: 'gemini-1.5-flash-latest', label: 'Gemini 1.5 Flash' },
  { value: 'gemini-1.5-pro-latest', label: 'Gemini 1.5 Pro (Most Capable)' },
  { value: 'gemini-pro', label: 'Gemini Pro (Legacy)' },
]

export function AgentProgrammingPage() {
  const [agents, setAgents] = useState<AgentConfig[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [editedConfig, setEditedConfig] = useState<Partial<AgentConfig>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [testInput, setTestInput] = useState("Hello, I have a question about my recent bill.")
  const [hasChanges, setHasChanges] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentProvider, setCurrentProvider] = useState<'openai' | 'gemini'>('openai')

  // Fetch current LLM provider
  useEffect(() => {
    const fetchProvider = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/config/llm/status`)
        if (response.ok) {
          const data = await response.json()
          if (data.provider === 'gemini') {
            setCurrentProvider('gemini')
          } else {
            setCurrentProvider('openai')
          }
        }
      } catch {
        // Default to OpenAI
      }
    }
    fetchProvider()
  }, [])

  // Get models based on current provider
  const availableModels = currentProvider === 'gemini' ? GEMINI_MODELS : OPENAI_MODELS
  const defaultModel = currentProvider === 'gemini' ? 'gemini-2.0-flash' : 'gpt-4o-mini'

  const fetchAgents = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/agent-config`)
      if (response.ok) {
        const data = await response.json()
        const transformedAgents: AgentConfig[] = data.map((agent: Record<string, unknown>) => ({
          agentId: agent.agent_id as string,
          agentName: agent.agent_name as string,
          agentType: agent.agent_type as 'primary' | 'supervisor' | 'escalation',
          description: agent.description as string,
          model: agent.model as string,
          temperature: agent.temperature as number,
          confidenceThreshold: agent.confidence_threshold as number,
          isCustom: agent.is_custom as boolean,
          version: agent.version as number,
          updatedAt: agent.updated_at as string,
          systemPrompt: '',
          userPromptTemplate: '',
          outputSchema: {},
          maxTokens: 1024,
          topP: 1.0,
          fallbackEnabled: true,
        }))
        setAgents(transformedAgents)
        if (!selectedAgent && transformedAgents.length > 0) {
          setSelectedAgent(transformedAgents[0].agentId)
        }
      }
    } catch {
      setError('Failed to load agent configurations')
    }
    setIsLoading(false)
  }, [selectedAgent])

  const fetchAgentDetails = useCallback(async (agentId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/agent-config/${agentId}`)
      if (response.ok) {
        const data = await response.json()
        const config: AgentConfig = {
          agentId: data.agent_id,
          agentName: data.agent_name,
          agentType: data.agent_type,
          description: data.description,
          systemPrompt: data.system_prompt,
          userPromptTemplate: data.user_prompt_template,
          outputSchema: data.output_schema,
          model: data.model,
          temperature: data.temperature,
          maxTokens: data.max_tokens,
          topP: data.top_p,
          confidenceThreshold: data.confidence_threshold,
          fallbackEnabled: data.fallback_enabled,
          isCustom: data.is_custom,
          version: data.version,
          updatedAt: data.updated_at,
        }
        setEditedConfig(config)
        setHasChanges(false)
        setTestResult(null)
      }
    } catch {
      setError('Failed to load agent details')
    }
  }, [])

  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  useEffect(() => {
    if (selectedAgent) {
      fetchAgentDetails(selectedAgent)
    }
  }, [selectedAgent, fetchAgentDetails])

  const handleConfigChange = (field: keyof AgentConfig, value: unknown) => {
    setEditedConfig(prev => ({ ...prev, [field]: value }))
    setHasChanges(true)
  }

  const handleSave = async () => {
    if (!selectedAgent) return
    setIsSaving(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE}/api/agent-config/${selectedAgent}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system_prompt: editedConfig.systemPrompt,
          user_prompt_template: editedConfig.userPromptTemplate,
          model: editedConfig.model,
          temperature: editedConfig.temperature,
          max_tokens: editedConfig.maxTokens,
          top_p: editedConfig.topP,
          confidence_threshold: editedConfig.confidenceThreshold,
          fallback_enabled: editedConfig.fallbackEnabled,
        }),
      })
      
      if (response.ok) {
        setHasChanges(false)
        await fetchAgents()
        await fetchAgentDetails(selectedAgent)
      } else {
        const err = await response.json()
        setError(err.detail || 'Failed to save configuration')
      }
    } catch {
      setError('Failed to save configuration')
    }
    setIsSaving(false)
  }

  const handleReset = async () => {
    if (!selectedAgent) return
    if (!confirm('Reset this agent to default configuration?')) return
    
    setIsSaving(true)
    try {
      const response = await fetch(`${API_BASE}/api/agent-config/${selectedAgent}/reset`, {
        method: 'POST',
      })
      if (response.ok) {
        await fetchAgentDetails(selectedAgent)
        setHasChanges(false)
      }
    } catch {
      setError('Failed to reset configuration')
    }
    setIsSaving(false)
  }

  const handleTestPrompt = async () => {
    if (!editedConfig.systemPrompt || !editedConfig.userPromptTemplate) return
    setIsTesting(true)
    setTestResult(null)
    
    try {
      const response = await fetch(`${API_BASE}/api/agent-config/${selectedAgent}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system_prompt: editedConfig.systemPrompt,
          user_prompt: editedConfig.userPromptTemplate.replace('{customer_message}', testInput),
          model: editedConfig.model,
          temperature: editedConfig.temperature,
          test_input: testInput,
        }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setTestResult({
          success: data.success,
          output: data.output,
          parsedOutput: data.parsed_output,
          latencyMs: data.latency_ms,
          tokensUsed: data.tokens_used,
          error: data.error,
        })
      }
    } catch {
      setTestResult({ success: false, latencyMs: 0, error: 'Failed to test prompt' })
    }
    setIsTesting(false)
  }

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'primary': return '🤖'
      case 'supervisor': return '👁️'
      case 'escalation': return '⚡'
      default: return '⚙️'
    }
  }

  const getAgentColor = (type: string) => {
    switch (type) {
      case 'primary': return '#3b82f6'
      case 'supervisor': return '#8b5cf6'
      case 'escalation': return '#f59e0b'
      default: return '#6b7280'
    }
  }

  // Loading State
  if (isLoading && agents.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <span>Loading agents...</span>
        </div>
      </div>
    )
  }

  // Error State
  if (error && agents.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠️</span>
          <h2>Failed to load agents</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <h1>Agent Studio</h1>
        <p>Configure AI agent prompts and behavior settings</p>
      </header>

      {/* Layout */}
      <div className={styles.layout}>
        {/* Agent Selector */}
        <aside className={styles.agentSelector}>
          <div className={styles.selectorTitle}>Select Agent</div>
          <div className={styles.agentList}>
            {agents.map(agent => (
              <div
                key={agent.agentId}
                className={`${styles.agentItem} ${selectedAgent === agent.agentId ? styles.selected : ''}`}
                onClick={() => setSelectedAgent(agent.agentId)}
              >
                <div 
                  className={styles.agentIcon}
                  style={{ backgroundColor: `${getAgentColor(agent.agentType)}20` }}
                >
                  {getAgentIcon(agent.agentType)}
                </div>
                <div className={styles.agentInfo}>
                  <h4>{agent.agentName}</h4>
                  <span>{agent.agentType}</span>
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Editor */}
        <div className={styles.editor}>
          {!selectedAgent ? (
            <div className={styles.selectPrompt}>
              <span style={{ fontSize: '2.5rem' }}>📝</span>
              <p>Select an agent to configure its prompts and settings</p>
            </div>
          ) : (
            <>
              {/* System Prompt Section */}
              <div className={styles.section}>
                <div className={styles.sectionHeader}>
                  <div className={styles.sectionTitle}>
                    <span className={styles.sectionIcon}>💬</span>
                    <h3>System Prompt</h3>
                  </div>
                  <span className={styles.sectionBadge}>{editedConfig.agentType}</span>
                </div>
                <div className={styles.sectionBody}>
                  <textarea
                    className={styles.textarea}
                    value={editedConfig.systemPrompt || ''}
                    onChange={(e) => handleConfigChange('systemPrompt', e.target.value)}
                    placeholder="Enter the system prompt that defines the agent's role and behavior..."
                    rows={10}
                  />
                </div>
              </div>

              {/* User Prompt Template */}
              <div className={styles.section}>
                <div className={styles.sectionHeader}>
                  <div className={styles.sectionTitle}>
                    <span className={styles.sectionIcon}>📝</span>
                    <h3>User Prompt Template</h3>
                  </div>
                </div>
                <div className={styles.sectionBody}>
                  <textarea
                    className={styles.textarea}
                    value={editedConfig.userPromptTemplate || ''}
                    onChange={(e) => handleConfigChange('userPromptTemplate', e.target.value)}
                    placeholder="Use {customer_message}, {channel}, {context} placeholders..."
                    rows={8}
                  />

                  {/* Test Area */}
                  <div className={styles.testArea}>
                    <div className={styles.testTitle}>Test Prompt</div>
                    <div className={styles.testRow}>
                      <input
                        type="text"
                        className={styles.testInput}
                        value={testInput}
                        onChange={(e) => setTestInput(e.target.value)}
                        placeholder="Enter test message..."
                      />
                      <button
                        className={styles.testBtn}
                        onClick={handleTestPrompt}
                        disabled={isTesting}
                      >
                        {isTesting ? 'Testing...' : 'Run Test'}
                      </button>
                    </div>
                    {testResult && (
                      <div className={styles.testResult}>
                        <div className={styles.testResultLabel}>
                          {testResult.success ? '✓ Success' : '✗ Error'} • {testResult.latencyMs}ms
                        </div>
                        <div className={styles.testResultContent}>
                          {testResult.error || testResult.output || 'No output'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* LLM Settings */}
              <div className={styles.section}>
                <div className={styles.sectionHeader}>
                  <div className={styles.sectionTitle}>
                    <span className={styles.sectionIcon}>⚙️</span>
                    <h3>LLM Settings</h3>
                  </div>
                </div>
                <div className={styles.sectionBody}>
                  <div className={styles.formGrid}>
                    <div className={styles.formField}>
                      <label>Model ({currentProvider === 'gemini' ? 'Google Gemini' : 'OpenAI'})</label>
                      <select
                        value={editedConfig.model || defaultModel}
                        onChange={(e) => handleConfigChange('model', e.target.value)}
                      >
                        {availableModels.map(m => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                    </div>

                    <div className={styles.formField}>
                      <label>Max Tokens</label>
                      <input
                        type="number"
                        value={editedConfig.maxTokens || 1024}
                        onChange={(e) => handleConfigChange('maxTokens', parseInt(e.target.value))}
                        min={100}
                        max={4096}
                      />
                    </div>

                    <div className={`${styles.formField} ${styles.sliderField}`}>
                      <label>Temperature: {(editedConfig.temperature || 0.3).toFixed(1)}</label>
                      <div className={styles.sliderContainer}>
                        <input
                          type="range"
                          className={styles.slider}
                          min={0}
                          max={2}
                          step={0.1}
                          value={editedConfig.temperature || 0.3}
                          onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                        />
                        <span className={styles.sliderValue}>{(editedConfig.temperature || 0.3).toFixed(1)}</span>
                      </div>
                    </div>

                    <div className={`${styles.formField} ${styles.sliderField}`}>
                      <label>Confidence Threshold: {((editedConfig.confidenceThreshold || 0.7) * 100).toFixed(0)}%</label>
                      <div className={styles.sliderContainer}>
                        <input
                          type="range"
                          className={styles.slider}
                          min={0}
                          max={1}
                          step={0.05}
                          value={editedConfig.confidenceThreshold || 0.7}
                          onChange={(e) => handleConfigChange('confidenceThreshold', parseFloat(e.target.value))}
                        />
                        <span className={styles.sliderValue}>{((editedConfig.confidenceThreshold || 0.7) * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Bar */}
                <div className={styles.actionBar}>
                  {hasChanges && <span className={styles.savedIndicator}>⚡ Unsaved changes</span>}
                  <button className={styles.resetBtn} onClick={handleReset}>
                    Reset to Default
                  </button>
                  <button 
                    className={styles.saveBtn} 
                    onClick={handleSave}
                    disabled={isSaving || !hasChanges}
                  >
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AgentProgrammingPage
