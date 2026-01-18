/**
 * Settings Page
 * 
 * Configuration interface for the AI Call Center.
 * Includes secure API key management for LLM providers.
 */

import { useState, useEffect, useCallback } from 'react'
import { setLlmApiKey, getLlmStatus, validateLlmKey, clearLlmKey } from '../../services/apiClient'
import styles from './SettingsPage.module.css'

interface SettingsState {
  // Application
  appName: string
  environment: string
  // AI Transparency
  showConfidenceScores: boolean
  showAgentDecisions: boolean
  showEscalationReasons: boolean
  aiDisclosureEnabled: boolean
  // Escalation
  autoEscalateThreshold: number
  maxRetryAttempts: number
  humanHandoffEnabled: boolean
  // Voice
  voiceEnabled: boolean
  speechRate: number
  voiceGender: 'male' | 'female' | 'neutral'
  language: string
}

interface LlmStatus {
  configured: boolean
  provider: string
  validated: boolean | null
  message: string
  configuredAt: string | null
}

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>({
    appName: 'AI Call Center',
    environment: 'demo',
    showConfidenceScores: true,
    showAgentDecisions: true,
    showEscalationReasons: true,
    aiDisclosureEnabled: true,
    autoEscalateThreshold: 40,
    maxRetryAttempts: 2,
    humanHandoffEnabled: true,
    voiceEnabled: true,
    speechRate: 1.0,
    voiceGender: 'neutral',
    language: 'en-US',
  })

  const [hasChanges, setHasChanges] = useState(false)

  // LLM Configuration State
  const [llmStatus, setLlmStatus] = useState<LlmStatus>({
    configured: false,
    provider: 'openai',
    validated: null,
    message: 'Loading...',
    configuredAt: null,
  })
  const [apiKeyInput, setApiKeyInput] = useState('')
  const [selectedProvider, setSelectedProvider] = useState<'openai' | 'gemini'>('openai')
  const [isSettingKey, setIsSettingKey] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [keyError, setKeyError] = useState<string | null>(null)

  // Fetch LLM status on mount
  const fetchLlmStatus = useCallback(async () => {
    const result = await getLlmStatus()
    if (result.success && result.data) {
      setLlmStatus({
        configured: result.data.configured,
        provider: result.data.provider,
        validated: result.data.validated,
        message: result.data.message,
        configuredAt: result.data.configuredAt,
      })
    }
  }, [])

  useEffect(() => {
    fetchLlmStatus()
  }, [fetchLlmStatus])

  const handleSetApiKey = async () => {
    if (!apiKeyInput.trim()) {
      setKeyError('Please enter an API key')
      return
    }
    if (apiKeyInput.length < 10) {
      setKeyError('API key is too short')
      return
    }

    setIsSettingKey(true)
    setKeyError(null)

    const result = await setLlmApiKey(apiKeyInput.trim(), selectedProvider)
    
    if (result.success) {
      setApiKeyInput('')
      await fetchLlmStatus()
      // Auto-validate after setting
      handleValidateKey()
    } else {
      setKeyError(result.error?.message || 'Failed to set API key')
    }

    setIsSettingKey(false)
  }

  const handleValidateKey = async () => {
    setIsValidating(true)
    setKeyError(null)

    const result = await validateLlmKey()
    
    if (result.success && result.data) {
      if (!result.data.valid) {
        setKeyError(result.data.message)
      }
    } else {
      setKeyError(result.error?.message || 'Validation failed')
    }

    await fetchLlmStatus()
    setIsValidating(false)
  }

  const handleClearKey = async () => {
    if (!confirm('Are you sure you want to clear the API key? AI features will use fallback logic.')) {
      return
    }

    const result = await clearLlmKey()
    if (result.success) {
      await fetchLlmStatus()
    }
  }

  const handleChange = <K extends keyof SettingsState>(
    key: K,
    value: SettingsState[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const handleSave = () => {
    // Demo only - no backend mutation for display settings
    setHasChanges(false)
    alert('Settings saved! (Demo mode - display settings are not persisted)')
  }

  const handleReset = () => {
    setSettings({
      appName: 'AI Call Center',
      environment: 'demo',
      showConfidenceScores: true,
      showAgentDecisions: true,
      showEscalationReasons: true,
      aiDisclosureEnabled: true,
      autoEscalateThreshold: 40,
      maxRetryAttempts: 2,
      humanHandoffEnabled: true,
      voiceEnabled: true,
      speechRate: 1.0,
      voiceGender: 'neutral',
      language: 'en-US',
    })
    setHasChanges(false)
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Settings</h1>
          <p className={styles.subtitle}>
            Configure your AI Call Center preferences
          </p>
        </div>
        <div className={styles.headerActions}>
          {hasChanges && (
            <span className={styles.unsavedBadge}>Unsaved changes</span>
          )}
          <button
            className={styles.resetButton}
            onClick={handleReset}
            disabled={!hasChanges}
          >
            Reset
          </button>
          <button
            className={styles.saveButton}
            onClick={handleSave}
            disabled={!hasChanges}
          >
            Save Changes
          </button>
        </div>
      </header>

      <div className={styles.sectionsGrid}>
        {/* AI Configuration - Most Important */}
        <section className={`${styles.section} ${styles.aiConfigSection}`}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionIcon}>🤖</span>
            <div>
              <h2 className={styles.sectionTitle}>AI Configuration</h2>
              <p className={styles.sectionDescription}>
                Configure your LLM provider API key for AI-powered features
              </p>
            </div>
          </div>

          {/* Status Banner */}
          <div className={`${styles.statusBanner} ${
            llmStatus.configured && llmStatus.validated 
              ? styles.statusSuccess 
              : llmStatus.configured 
                ? styles.statusWarning 
                : styles.statusError
          }`}>
            <span className={styles.statusIcon}>
              {llmStatus.configured && llmStatus.validated ? '✓' : llmStatus.configured ? '⚠' : '○'}
            </span>
            <span className={styles.statusMessage}>{llmStatus.message}</span>
          </div>

          <div className={styles.settingsGroup}>
            {/* Provider Selection */}
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>LLM Provider</label>
                <span className={styles.settingHint}>
                  Select your AI provider - OpenAI (GPT) or Google (Gemini)
                </span>
              </div>
              <select
                className={styles.select}
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value as 'openai' | 'gemini')}
                disabled={isSettingKey}
              >
                <option value="openai">OpenAI (GPT-4, GPT-4o)</option>
                <option value="gemini">Google Gemini (Gemini Pro, Flash)</option>
              </select>
            </div>

            {/* API Key Input */}
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>
                  {selectedProvider === 'gemini' ? 'Gemini API Key' : 'OpenAI API Key'}
                </label>
                <span className={styles.settingHint}>
                  Your API key is stored securely in-memory (never persisted to disk)
                </span>
              </div>
              <div className={styles.apiKeyInputGroup}>
                <input
                  type="password"
                  className={`${styles.input} ${styles.apiKeyInput}`}
                  placeholder={llmStatus.configured ? '••••••••••••••••' : selectedProvider === 'gemini' ? 'AIza...' : 'sk-...'}
                  value={apiKeyInput}
                  onChange={(e) => {
                    setApiKeyInput(e.target.value)
                    setKeyError(null)
                  }}
                  disabled={isSettingKey}
                />
                <button
                  className={styles.setKeyButton}
                  onClick={handleSetApiKey}
                  disabled={isSettingKey || !apiKeyInput.trim()}
                >
                  {isSettingKey ? 'Setting...' : llmStatus.configured ? 'Update' : 'Set Key'}
                </button>
              </div>
            </div>

            {keyError && (
              <div className={styles.errorMessage}>
                <span>⚠️</span> {keyError}
              </div>
            )}

            {/* Current Status */}
            {llmStatus.configured && (
              <>
                <div className={styles.settingRow}>
                  <div className={styles.settingInfo}>
                    <label className={styles.settingLabel}>Status</label>
                    <span className={styles.settingHint}>
                      Connection status to {llmStatus.provider === 'gemini' ? 'Google Gemini' : 'OpenAI'} API
                    </span>
                  </div>
                  <div className={styles.statusValue}>
                    <span className={`${styles.statusDot} ${
                      llmStatus.validated === true 
                        ? styles.statusDotSuccess 
                        : llmStatus.validated === false 
                          ? styles.statusDotError 
                          : styles.statusDotPending
                    }`} />
                    <span>
                      {llmStatus.validated === true 
                        ? 'Connected' 
                        : llmStatus.validated === false 
                          ? 'Invalid' 
                          : 'Not Validated'}
                    </span>
                    <button
                      className={styles.validateButton}
                      onClick={handleValidateKey}
                      disabled={isValidating}
                    >
                      {isValidating ? 'Validating...' : 'Test Connection'}
                    </button>
                  </div>
                </div>

                <div className={styles.settingRow}>
                  <div className={styles.settingInfo}>
                    <label className={styles.settingLabel}>Provider</label>
                    <span className={styles.settingHint}>
                      LLM provider in use
                    </span>
                  </div>
                  <span className={styles.readOnlyValue}>
                    {llmStatus.provider === 'gemini' ? 'Google Gemini' : 'OpenAI (GPT-4)'}
                  </span>
                </div>

                <div className={styles.settingRow}>
                  <div className={styles.settingInfo}>
                    <label className={styles.settingLabel}>Clear Key</label>
                    <span className={styles.settingHint}>
                      Remove the API key (AI will use fallback logic)
                    </span>
                  </div>
                  <button
                    className={styles.dangerButton}
                    onClick={handleClearKey}
                  >
                    Clear API Key
                  </button>
                </div>
              </>
            )}
          </div>

          <div className={styles.infoBox}>
            <span className={styles.infoIcon}>🔒</span>
            <p>
              <strong>Security Note:</strong> Your API key is stored in server memory only and is never 
              logged, persisted to disk, or returned in API responses. For production deployments, 
              use environment variables or a secrets manager.
            </p>
          </div>
        </section>

        {/* Application Info */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionIcon}>⚙️</span>
            <div>
              <h2 className={styles.sectionTitle}>Application Info</h2>
              <p className={styles.sectionDescription}>
                Basic application configuration and environment settings
              </p>
            </div>
          </div>

          <div className={styles.settingsGroup}>
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Application Name</label>
                <span className={styles.settingHint}>
                  Display name shown in the interface
                </span>
              </div>
              <input
                type="text"
                className={styles.input}
                value={settings.appName}
                onChange={(e) => handleChange('appName', e.target.value)}
              />
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Environment</label>
                <span className={styles.settingHint}>
                  Current deployment environment
                </span>
              </div>
              <select
                className={styles.select}
                value={settings.environment}
                onChange={(e) => handleChange('environment', e.target.value)}
              >
                <option value="demo">Demo</option>
                <option value="development">Development</option>
                <option value="staging">Staging</option>
                <option value="production" disabled>Production (Locked)</option>
              </select>
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Version</label>
                <span className={styles.settingHint}>
                  Current application version
                </span>
              </div>
              <span className={styles.readOnlyValue}>v1.0.0</span>
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>API Endpoint</label>
                <span className={styles.settingHint}>
                  Backend service URL
                </span>
              </div>
              <code className={styles.codeValue}>http://localhost:8000</code>
            </div>
          </div>
        </section>

        {/* AI Transparency */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionIcon}>🔍</span>
            <div>
              <h2 className={styles.sectionTitle}>AI Transparency</h2>
              <p className={styles.sectionDescription}>
                Control how AI decisions and confidence are displayed
              </p>
            </div>
          </div>

          <div className={styles.settingsGroup}>
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Show Confidence Scores</label>
                <span className={styles.settingHint}>
                  Display AI confidence levels in the interface
                </span>
              </div>
              <Toggle
                checked={settings.showConfidenceScores}
                onChange={(v) => handleChange('showConfidenceScores', v)}
              />
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Show Agent Decisions</label>
                <span className={styles.settingHint}>
                  Display the decision-making process of AI agents
                </span>
              </div>
              <Toggle
                checked={settings.showAgentDecisions}
                onChange={(v) => handleChange('showAgentDecisions', v)}
              />
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Show Escalation Reasons</label>
                <span className={styles.settingHint}>
                  Explain why calls are escalated to humans
                </span>
              </div>
              <Toggle
                checked={settings.showEscalationReasons}
                onChange={(v) => handleChange('showEscalationReasons', v)}
              />
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>AI Disclosure</label>
                <span className={styles.settingHint}>
                  Inform customers they are speaking with AI
                </span>
              </div>
              <Toggle
                checked={settings.aiDisclosureEnabled}
                onChange={(v) => handleChange('aiDisclosureEnabled', v)}
                locked
              />
            </div>
          </div>

          <div className={styles.infoBox}>
            <span className={styles.infoIcon}>ℹ️</span>
            <p>
              AI Disclosure is required by policy and cannot be disabled. 
              Customers are always informed when interacting with AI agents.
            </p>
          </div>
        </section>

        {/* Escalation Settings */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionIcon}>⬆️</span>
            <div>
              <h2 className={styles.sectionTitle}>Escalation Settings</h2>
              <p className={styles.sectionDescription}>
                Configure when and how calls are escalated to human agents
              </p>
            </div>
          </div>

          <div className={styles.lockedBanner}>
            <span className={styles.lockIcon}>🔒</span>
            <span>These settings are managed by administrators</span>
          </div>

          <div className={styles.settingsGroup}>
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Auto-Escalate Threshold</label>
                <span className={styles.settingHint}>
                  Escalate when confidence drops below this level
                </span>
              </div>
              <div className={styles.sliderContainer}>
                <input
                  type="range"
                  className={styles.slider}
                  min={0}
                  max={100}
                  value={settings.autoEscalateThreshold}
                  onChange={(e) => handleChange('autoEscalateThreshold', Number(e.target.value))}
                  disabled
                />
                <span className={styles.sliderValue}>{settings.autoEscalateThreshold}%</span>
              </div>
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Max Retry Attempts</label>
                <span className={styles.settingHint}>
                  Number of times AI will retry before escalating
                </span>
              </div>
              <select
                className={styles.select}
                value={settings.maxRetryAttempts}
                disabled
              >
                <option value={1}>1 attempt</option>
                <option value={2}>2 attempts</option>
                <option value={3}>3 attempts</option>
              </select>
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Human Handoff</label>
                <span className={styles.settingHint}>
                  Allow customers to request human agents
                </span>
              </div>
              <Toggle
                checked={settings.humanHandoffEnabled}
                onChange={() => {}}
                locked
              />
            </div>
          </div>

          <div className={styles.warningBox}>
            <span className={styles.warningIcon}>⚠️</span>
            <p>
              Escalation settings affect customer experience and support costs.
              Contact your administrator to request changes.
            </p>
          </div>
        </section>

        {/* Voice Configuration */}
        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <span className={styles.sectionIcon}>🎙️</span>
            <div>
              <h2 className={styles.sectionTitle}>Voice Configuration</h2>
              <p className={styles.sectionDescription}>
                Configure text-to-speech and voice interaction settings
              </p>
            </div>
          </div>

          <div className={styles.settingsGroup}>
            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Voice Responses</label>
                <span className={styles.settingHint}>
                  Enable text-to-speech for AI responses
                </span>
              </div>
              <Toggle
                checked={settings.voiceEnabled}
                onChange={(v) => handleChange('voiceEnabled', v)}
              />
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Speech Rate</label>
                <span className={styles.settingHint}>
                  Speed of voice responses (0.5x - 2.0x)
                </span>
              </div>
              <div className={styles.sliderContainer}>
                <input
                  type="range"
                  className={styles.slider}
                  min={0.5}
                  max={2}
                  step={0.1}
                  value={settings.speechRate}
                  onChange={(e) => handleChange('speechRate', Number(e.target.value))}
                  disabled={!settings.voiceEnabled}
                />
                <span className={styles.sliderValue}>{settings.speechRate}x</span>
              </div>
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Voice Type</label>
                <span className={styles.settingHint}>
                  Preferred voice gender for TTS
                </span>
              </div>
              <select
                className={styles.select}
                value={settings.voiceGender}
                onChange={(e) => handleChange('voiceGender', e.target.value as any)}
                disabled={!settings.voiceEnabled}
              >
                <option value="neutral">Neutral</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
              </select>
            </div>

            <div className={styles.settingRow}>
              <div className={styles.settingInfo}>
                <label className={styles.settingLabel}>Language</label>
                <span className={styles.settingHint}>
                  Language for voice recognition and synthesis
                </span>
              </div>
              <select
                className={styles.select}
                value={settings.language}
                onChange={(e) => handleChange('language', e.target.value)}
                disabled={!settings.voiceEnabled}
              >
                <option value="en-US">English (US)</option>
                <option value="en-GB">English (UK)</option>
                <option value="es-ES">Spanish</option>
                <option value="fr-FR">French</option>
                <option value="de-DE">German</option>
              </select>
            </div>
          </div>

          {settings.voiceEnabled && (
            <button className={styles.testButton}>
              🔊 Test Voice Settings
            </button>
          )}
        </section>
      </div>

      {/* Footer */}
      <footer className={styles.footer}>
        <p className={styles.footerNote}>
          <span className={styles.demoLabel}>Demo Mode</span>
          Settings changes are not persisted in demo mode.
          In production, changes would be saved to the backend.
        </p>
      </footer>
    </div>
  )
}

// Toggle Component
function Toggle({ 
  checked, 
  onChange, 
  locked = false 
}: { 
  checked: boolean
  onChange: (value: boolean) => void
  locked?: boolean
}) {
  return (
    <button
      className={`${styles.toggle} ${checked ? styles.toggleOn : ''} ${locked ? styles.toggleLocked : ''}`}
      onClick={() => !locked && onChange(!checked)}
      disabled={locked}
      aria-pressed={checked}
      type="button"
    >
      <span className={styles.toggleTrack}>
        <span className={styles.toggleThumb} />
      </span>
      {locked && <span className={styles.toggleLockIcon}>🔒</span>}
    </button>
  )
}
