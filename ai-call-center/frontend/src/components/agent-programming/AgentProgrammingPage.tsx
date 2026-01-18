/**
 * Agent Programming Page
 * 
 * Visual interface for configuring AI agent prompts and LLM settings.
 * Allows customization of Primary, Supervisor, and Escalation agents.
 */

import { useState, useEffect, useCallback } from 'react'
import styles from './AgentProgrammingPage.module.css'

// Types
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

export function AgentProgrammingPage() {
  const [agents, setAgents] = useState<AgentConfig[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [editedConfig, setEditedConfig] = useState<Partial<AgentConfig>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [testInput, setTestInput] = useState("Hello, I have a question about my recent bill. It seems higher than usual.")
  const [hasChanges, setHasChanges] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'prompts' | 'settings' | 'schema'>('prompts')

  // Fetch agents
  const fetchAgents = useCallback(async () => {
    setIsLoading(true)
    try {
      const response = await fetch(`${API_BASE}/api/agent-config`)
      if (response.ok) {
        const data = await response.json()
        setAgents(data)
        if (!selectedAgent && data.length > 0) {
          setSelectedAgent(data[0].agentId)
        }
      }
    } catch (e) {
      setError('Failed to load agent configurations')
    }
    setIsLoading(false)
  }, [selectedAgent])

  // Fetch single agent details
  const fetchAgentDetails = useCallback(async (agentId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/agent-config/${agentId}`)
      if (response.ok) {
        const data = await response.json()
        // Convert snake_case to camelCase
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
    } catch (e) {
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

  // Handle config changes
  const handleConfigChange = (field: keyof AgentConfig, value: unknown) => {
    setEditedConfig(prev => ({ ...prev, [field]: value }))
    setHasChanges(true)
  }

  // Save configuration
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
    } catch (e) {
      setError('Failed to save configuration')
    }
    
    setIsSaving(false)
  }

  // Reset to defaults
  const handleReset = async () => {
    if (!selectedAgent) return
    if (!confirm('Reset this agent to default configuration? This cannot be undone.')) return
    
    setIsSaving(true)
    try {
      const response = await fetch(`${API_BASE}/api/agent-config/${selectedAgent}/reset`, {
        method: 'POST',
      })
      
      if (response.ok) {
        await fetchAgentDetails(selectedAgent)
        setHasChanges(false)
      }
    } catch (e) {
      setError('Failed to reset configuration')
    }
    setIsSaving(false)
  }

  // Test prompt
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
    } catch (e) {
      setTestResult({
        success: false,
        latencyMs: 0,
        error: 'Failed to test prompt',
      })
    }
    
    setIsTesting(false)
  }

  const currentAgent = agents.find(a => a.agentId === selectedAgent)

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Agent Programming</h1>
          <p className={styles.subtitle}>
            Configure AI agent prompts, LLM settings, and behavior
          </p>
        </div>
        {hasChanges && (
          <div className={styles.headerActions}>
            <span className={styles.unsavedBadge}>Unsaved Changes</span>
            <button className={styles.discardButton} onClick={() => selectedAgent && fetchAgentDetails(selectedAgent)}>
              Discard
            </button>
            <button className={styles.saveButton} onClick={handleSave} disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        )}
      </header>

      {error && (
        <div className={styles.errorBanner}>
          <span>⚠️</span> {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className={styles.mainLayout}>
        {/* Agent Selector Sidebar */}
        <aside className={styles.sidebar}>
          <h2 className={styles.sidebarTitle}>Agents</h2>
          <nav className={styles.agentList}>
            {agents.map(agent => (
              <button
                key={agent.agentId}
                className={`${styles.agentCard} ${selectedAgent === agent.agentId ? styles.selected : ''}`}
                onClick={() => setSelectedAgent(agent.agentId)}
              >
                <div className={styles.agentIcon}>
                  {agent.agentType === 'primary' ? '🎯' : agent.agentType === 'supervisor' ? '👁️' : '🚀'}
                </div>
                <div className={styles.agentInfo}>
                  <span className={styles.agentName}>{agent.agentName}</span>
                  <span className={styles.agentType}>{agent.agentType}</span>
                </div>
                {agent.isCustom && <span className={styles.customBadge}>Custom</span>}
              </button>
            ))}
          </nav>

          {currentAgent && (
            <div className={styles.agentMeta}>
              <p><strong>Model:</strong> {currentAgent.model}</p>
              <p><strong>Version:</strong> {currentAgent.version}</p>
              <button className={styles.resetButton} onClick={handleReset}>
                Reset to Default
              </button>
            </div>
          )}
        </aside>

        {/* Main Editor */}
        <main className={styles.editor}>
          {isLoading ? (
            <div className={styles.loading}>Loading agent configuration...</div>
          ) : !selectedAgent ? (
            <div className={styles.empty}>Select an agent to configure</div>
          ) : (
            <>
              {/* Agent Header */}
              <div className={styles.agentHeader}>
                <h2>{editedConfig.agentName}</h2>
                <p>{editedConfig.description}</p>
              </div>

              {/* Tabs */}
              <div className={styles.tabs}>
                <button
                  className={`${styles.tab} ${activeTab === 'prompts' ? styles.activeTab : ''}`}
                  onClick={() => setActiveTab('prompts')}
                >
                  📝 Prompts
                </button>
                <button
                  className={`${styles.tab} ${activeTab === 'settings' ? styles.activeTab : ''}`}
                  onClick={() => setActiveTab('settings')}
                >
                  ⚙️ LLM Settings
                </button>
                <button
                  className={`${styles.tab} ${activeTab === 'schema' ? styles.activeTab : ''}`}
                  onClick={() => setActiveTab('schema')}
                >
                  📋 Output Schema
                </button>
              </div>

              {/* Tab Content */}
              <div className={styles.tabContent}>
                {activeTab === 'prompts' && (
                  <div className={styles.promptsTab}>
                    {/* System Prompt */}
                    <div className={styles.promptSection}>
                      <label className={styles.promptLabel}>
                        System Prompt
                        <span className={styles.promptHint}>
                          Instructions that define the agent's role and behavior
                        </span>
                      </label>
                      <textarea
                        className={styles.promptTextarea}
                        value={editedConfig.systemPrompt || ''}
                        onChange={(e) => handleConfigChange('systemPrompt', e.target.value)}
                        rows={15}
                        placeholder="Enter system prompt..."
                      />
                    </div>

                    {/* User Prompt Template */}
                    <div className={styles.promptSection}>
                      <label className={styles.promptLabel}>
                        User Prompt Template
                        <span className={styles.promptHint}>
                          Template for user messages. Use {'{customer_message}'}, {'{channel}'}, etc.
                        </span>
                      </label>
                      <textarea
                        className={styles.promptTextarea}
                        value={editedConfig.userPromptTemplate || ''}
                        onChange={(e) => handleConfigChange('userPromptTemplate', e.target.value)}
                        rows={12}
                        placeholder="Enter user prompt template..."
                      />
                    </div>

                    {/* Test Section */}
                    <div className={styles.testSection}>
                      <h3 className={styles.testTitle}>🧪 Test Prompt</h3>
                      <div className={styles.testInputGroup}>
                        <label>Sample Customer Message:</label>
                        <input
                          type="text"
                          className={styles.testInput}
                          value={testInput}
                          onChange={(e) => setTestInput(e.target.value)}
                          placeholder="Enter a test message..."
                        />
                        <button
                          className={styles.testButton}
                          onClick={handleTestPrompt}
                          disabled={isTesting}
                        >
                          {isTesting ? 'Testing...' : 'Run Test'}
                        </button>
                      </div>

                      {testResult && (
                        <div className={`${styles.testResult} ${testResult.success ? styles.testSuccess : styles.testError}`}>
                          <div className={styles.testResultHeader}>
                            <span>{testResult.success ? '✓ Success' : '✗ Failed'}</span>
                            <span>{testResult.latencyMs}ms</span>
                            {testResult.tokensUsed && <span>{testResult.tokensUsed} tokens</span>}
                          </div>
                          {testResult.error && (
                            <p className={styles.testErrorMessage}>{testResult.error}</p>
                          )}
                          {testResult.output && (
                            <pre className={styles.testOutput}>{testResult.output}</pre>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'settings' && (
                  <div className={styles.settingsTab}>
                    <div className={styles.settingsGrid}>
                      {/* Model */}
                      <div className={styles.settingItem}>
                        <label>Model</label>
                        <select
                          value={editedConfig.model || 'gpt-4o-mini'}
                          onChange={(e) => handleConfigChange('model', e.target.value)}
                        >
                          <option value="gpt-4o">GPT-4o (Most Capable)</option>
                          <option value="gpt-4o-mini">GPT-4o Mini (Fast & Cheap)</option>
                          <option value="gpt-4-turbo">GPT-4 Turbo</option>
                          <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Fastest)</option>
                        </select>
                      </div>

                      {/* Temperature */}
                      <div className={styles.settingItem}>
                        <label>
                          Temperature: {editedConfig.temperature?.toFixed(1) || '0.3'}
                          <span className={styles.settingHint}>Lower = more deterministic</span>
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="2"
                          step="0.1"
                          value={editedConfig.temperature || 0.3}
                          onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                        />
                      </div>

                      {/* Max Tokens */}
                      <div className={styles.settingItem}>
                        <label>Max Tokens: {editedConfig.maxTokens || 1024}</label>
                        <input
                          type="range"
                          min="100"
                          max="4096"
                          step="100"
                          value={editedConfig.maxTokens || 1024}
                          onChange={(e) => handleConfigChange('maxTokens', parseInt(e.target.value))}
                        />
                      </div>

                      {/* Top P */}
                      <div className={styles.settingItem}>
                        <label>Top P: {editedConfig.topP?.toFixed(1) || '1.0'}</label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={editedConfig.topP || 1.0}
                          onChange={(e) => handleConfigChange('topP', parseFloat(e.target.value))}
                        />
                      </div>

                      {/* Confidence Threshold */}
                      <div className={styles.settingItem}>
                        <label>
                          Confidence Threshold: {((editedConfig.confidenceThreshold || 0.7) * 100).toFixed(0)}%
                          <span className={styles.settingHint}>Minimum confidence for autonomous action</span>
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={editedConfig.confidenceThreshold || 0.7}
                          onChange={(e) => handleConfigChange('confidenceThreshold', parseFloat(e.target.value))}
                        />
                      </div>

                      {/* Fallback Enabled */}
                      <div className={styles.settingItem}>
                        <label>
                          Fallback Logic
                          <span className={styles.settingHint}>Use rule-based fallback if LLM fails</span>
                        </label>
                        <button
                          className={`${styles.toggleButton} ${editedConfig.fallbackEnabled ? styles.toggleOn : ''}`}
                          onClick={() => handleConfigChange('fallbackEnabled', !editedConfig.fallbackEnabled)}
                        >
                          {editedConfig.fallbackEnabled ? 'Enabled' : 'Disabled'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === 'schema' && (
                  <div className={styles.schemaTab}>
                    <div className={styles.schemaInfo}>
                      <h3>Output Schema</h3>
                      <p>This JSON schema defines the structure of the agent's output. The LLM will be instructed to return data matching this format.</p>
                    </div>
                    <pre className={styles.schemaCode}>
                      {JSON.stringify(editedConfig.outputSchema, null, 2)}
                    </pre>
                    <div className={styles.schemaNote}>
                      <span>ℹ️</span>
                      Output schemas are read-only in this version. Contact engineering to modify.
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default AgentProgrammingPage
