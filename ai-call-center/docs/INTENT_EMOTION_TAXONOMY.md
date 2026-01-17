# Intent & Emotion Classification Taxonomy

## AI-Powered Digital Call Center Using Autonomous AI Agents

**Document Version:** 1.0  
**Date:** January 17, 2026  
**Phase:** 3 — AI & Data Design  
**Audience:** Product, Compliance, Operations, Quality Assurance  

---

## Purpose

This document defines the **classification categories** the AI system uses to understand customer interactions. These categories determine how the AI:

- Understands what the customer needs (Intent)
- Recognizes how the customer feels (Emotion)
- Decides how to respond appropriately
- Determines when to escalate to a human

These classifications are designed to be **fair, transparent, and operationally useful**.

---

## 1. Customer Intent Categories

### 1.1 Intent Category Overview

The AI recognizes **12 primary intent categories** that represent the core reasons customers contact support.

| # | Category | Description | Typical Resolution Path |
|---|----------|-------------|------------------------|
| 1 | **Status Inquiry** | Customer wants to know the current state of something | Information retrieval |
| 2 | **Transaction Request** | Customer wants to complete an action | Workflow execution |
| 3 | **Problem Report** | Customer is experiencing an issue | Troubleshooting |
| 4 | **Information Request** | Customer has a question about products, services, or policies | Knowledge retrieval |
| 5 | **Complaint** | Customer is expressing dissatisfaction | Service recovery |
| 6 | **Change Request** | Customer wants to modify existing arrangements | Account update |
| 7 | **Cancellation Request** | Customer wants to terminate something | Retention/processing |
| 8 | **Billing Inquiry** | Customer has questions about charges or payments | Account review |
| 9 | **Technical Support** | Customer needs help with functionality | Guided troubleshooting |
| 10 | **Account Access** | Customer has issues accessing their account | Authentication support |
| 11 | **Feedback/Suggestion** | Customer wants to share input | Documentation |
| 12 | **Human Request** | Customer wants to speak with a person | Immediate escalation |

---

### 1.2 Detailed Intent Definitions

#### Intent 1: Status Inquiry

**Definition:** Customer wants to know the current state of an order, request, application, or process.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Get accurate, current information about something in progress |
| **Typical Triggers** | "Where is my...," "What's the status of...," "Has my... been processed" |
| **Required Information** | Identifier (order number, case ID, account number) |
| **Resolution** | Retrieve and communicate current status |
| **Escalation Triggers** | Status shows problem; customer disputes information |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Order Status | "Where is my package?" |
| Application Status | "Has my credit application been approved?" |
| Request Status | "Did you receive my documents?" |
| Appointment Status | "Is my appointment still confirmed?" |

---

#### Intent 2: Transaction Request

**Definition:** Customer wants to complete a specific action or purchase.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Successfully execute a transaction |
| **Typical Triggers** | "I want to...," "Can I...," "I'd like to order/book/schedule" |
| **Required Information** | Transaction details; authentication |
| **Resolution** | Complete the requested transaction |
| **Escalation Triggers** | Transaction fails; exceeds AI authority; requires exception |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| New Purchase | "I want to order the premium plan" |
| Booking | "I need to schedule an appointment" |
| Payment | "I want to pay my bill" |
| Enrollment | "Sign me up for automatic payments" |

---

#### Intent 3: Problem Report

**Definition:** Customer is experiencing something that isn't working as expected.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Get the problem fixed |
| **Typical Triggers** | "It's not working," "I received the wrong...," "There's an issue with..." |
| **Required Information** | Problem description; relevant identifiers; timeline |
| **Resolution** | Diagnose and resolve, or escalate with context |
| **Escalation Triggers** | Problem cannot be resolved remotely; safety concern; repeated issue |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Product Defect | "The item arrived broken" |
| Service Disruption | "My internet has been down since yesterday" |
| Incorrect Delivery | "I received the wrong item" |
| Feature Malfunction | "The app keeps crashing" |

---

#### Intent 4: Information Request

**Definition:** Customer has a question and needs an answer.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Obtain accurate information |
| **Typical Triggers** | "What is...," "How does...," "Can you explain...," "Tell me about..." |
| **Required Information** | Topic of inquiry |
| **Resolution** | Provide accurate, relevant information |
| **Escalation Triggers** | Question outside knowledge base; requires expert opinion |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Product Information | "What's included in the premium package?" |
| Policy Inquiry | "What's your return policy?" |
| Pricing Question | "How much does shipping cost?" |
| Process Inquiry | "How do I submit a claim?" |

---

#### Intent 5: Complaint

**Definition:** Customer is expressing dissatisfaction with a product, service, or experience.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Be heard; receive resolution or compensation |
| **Typical Triggers** | "I'm unhappy with...," "This is unacceptable," "I want to complain about..." |
| **Required Information** | Nature of complaint; desired outcome |
| **Resolution** | Acknowledge; investigate; offer appropriate resolution |
| **Escalation Triggers** | Complaint about AI; request for manager; legal mentions |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Service Complaint | "Your customer service has been terrible" |
| Product Complaint | "This product doesn't work as advertised" |
| Experience Complaint | "I've been on hold for an hour" |
| Employee Complaint | "The representative was rude to me" |

---

#### Intent 6: Change Request

**Definition:** Customer wants to modify existing information, services, or arrangements.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Successfully update their situation |
| **Typical Triggers** | "I need to change...," "Can you update...," "I want to switch..." |
| **Required Information** | What to change; new information; authentication |
| **Resolution** | Process the modification |
| **Escalation Triggers** | Change affects billing significantly; complex changes |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Contact Update | "I need to change my phone number" |
| Service Modification | "I want to upgrade my plan" |
| Appointment Change | "I need to reschedule my appointment" |
| Preference Update | "Change my notification settings" |

---

#### Intent 7: Cancellation Request

**Definition:** Customer wants to terminate a service, order, subscription, or appointment.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Successfully cancel without obstacles |
| **Typical Triggers** | "I want to cancel...," "Stop my subscription," "I don't want this anymore" |
| **Required Information** | What to cancel; authentication |
| **Resolution** | Process cancellation; explain any implications |
| **Escalation Triggers** | Retention offer needed; complex cancellation; contractual implications |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Order Cancellation | "Cancel my order before it ships" |
| Subscription Cancellation | "I want to cancel my monthly membership" |
| Appointment Cancellation | "I need to cancel my appointment" |
| Account Closure | "I want to close my account entirely" |

---

#### Intent 8: Billing Inquiry

**Definition:** Customer has questions or concerns about charges, payments, or their account balance.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Understand or resolve billing matters |
| **Typical Triggers** | "I have a question about my bill," "Why was I charged...," "I need to pay..." |
| **Required Information** | Account identifier; specific charges in question |
| **Resolution** | Explain charges; process payments; resolve disputes |
| **Escalation Triggers** | Disputed charges above threshold; suspected fraud; payment failures |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Charge Inquiry | "What is this $29.99 charge?" |
| Payment Request | "I need to make a payment" |
| Billing Dispute | "I was charged twice for the same thing" |
| Statement Request | "Can you send me a copy of my invoice?" |

---

#### Intent 9: Technical Support

**Definition:** Customer needs help with functionality, setup, or usage of a product or service.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Get something working correctly |
| **Typical Triggers** | "How do I...," "I can't figure out how to...," "It's not connecting..." |
| **Required Information** | Product/service; specific issue; steps already tried |
| **Resolution** | Guide through troubleshooting; resolve issue |
| **Escalation Triggers** | Requires advanced technical intervention; physical service needed |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Setup Help | "How do I set up my new device?" |
| Usage Guidance | "How do I use this feature?" |
| Connectivity Issue | "I can't connect to the service" |
| Error Resolution | "I'm getting an error message" |

---

#### Intent 10: Account Access

**Definition:** Customer is having trouble accessing their account.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Regain access to their account |
| **Typical Triggers** | "I forgot my password," "I can't log in," "My account is locked" |
| **Required Information** | Account identifier; verification information |
| **Resolution** | Verify identity; restore access |
| **Escalation Triggers** | Failed verification; suspected compromise; security concern |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Password Reset | "I need to reset my password" |
| Account Lockout | "My account is locked after too many attempts" |
| Access Recovery | "I lost access to my email and can't verify" |
| Security Concern | "I think someone else is using my account" |

---

#### Intent 11: Feedback/Suggestion

**Definition:** Customer wants to share positive or constructive input about products or services.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Have their input acknowledged and recorded |
| **Typical Triggers** | "I wanted to suggest...," "I think you should...," "I have feedback about..." |
| **Required Information** | Nature of feedback |
| **Resolution** | Acknowledge; document; thank customer |
| **Escalation Triggers** | Feedback about serious issue; request for response |

**Sub-Categories:**

| Sub-Category | Example |
|--------------|---------|
| Positive Feedback | "I wanted to compliment your delivery service" |
| Improvement Suggestion | "It would be great if you offered..." |
| Feature Request | "You should add this capability" |

---

#### Intent 12: Human Request

**Definition:** Customer explicitly wants to speak with a human agent.

| Aspect | Details |
|--------|---------|
| **Customer Goal** | Connect with a real person |
| **Typical Triggers** | "Human," "Agent," "Representative," "Real person," "Let me talk to someone" |
| **Required Information** | None — request is self-explanatory |
| **Resolution** | Immediate transfer to human agent |
| **Escalation Triggers** | This IS the escalation trigger |

**Response:** Comply immediately. Do not attempt to retain, convince, or delay.

---

### 1.3 Intent Hierarchy for Ambiguous Cases

When customer input could match multiple intents:

| Priority | Rule |
|----------|------|
| 1 | **Human Request** always takes precedence |
| 2 | **Complaint** signals take priority over transactional intents |
| 3 | **Problem Report** takes priority over status inquiry |
| 4 | Most specific intent wins over general intent |
| 5 | When truly ambiguous, ask clarifying question |

---

## 2. Emotional State Categories

### 2.1 Emotional State Overview

The AI recognizes **7 primary emotional states** that influence how it responds to customers.

| # | State | Description | AI Response Approach |
|---|-------|-------------|---------------------|
| 1 | **Positive** | Happy, grateful, satisfied | Match warmth; efficient service |
| 2 | **Neutral** | Calm, businesslike, matter-of-fact | Professional; focused on task |
| 3 | **Impatient** | In a hurry, wants quick resolution | Prioritize efficiency; minimize steps |
| 4 | **Frustrated** | Annoyed, disappointed, exasperated | Acknowledge; empathize; solve |
| 5 | **Anxious** | Worried, stressed, concerned | Reassure; explain clearly; be patient |
| 6 | **Angry** | Hostile, demanding, aggressive | De-escalate; offer human; don't argue |
| 7 | **Distressed** | Upset, overwhelmed, in crisis | Prioritize; show care; escalate if needed |

---

### 2.2 Detailed Emotional State Definitions

#### State 1: Positive

**Definition:** Customer is in a good mood, expressing satisfaction or gratitude.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | "Thank you so much," expressions of satisfaction, compliments |
| **Customer Experience** | Feeling good about the interaction |
| **AI Response Style** | Warm, friendly, efficient |
| **Caution** | Don't assume positive throughout; monitor for changes |

**Example Indicators:**
- "You've been really helpful!"
- "I appreciate your quick response"
- "This is exactly what I needed"

---

#### State 2: Neutral

**Definition:** Customer is calm and businesslike, focused on completing their task.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | Direct questions, no emotional language, factual statements |
| **Customer Experience** | Transactional, expectation of competent service |
| **AI Response Style** | Professional, clear, efficient |
| **Caution** | Neutral can shift quickly if things go wrong |

**Example Indicators:**
- "I need to check my account balance"
- "What time are you open until?"
- "Can you transfer me to billing?"

---

#### State 3: Impatient

**Definition:** Customer is in a hurry and wants quick resolution.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | Short responses, "just," "quickly," time pressure mentions |
| **Customer Experience** | Feeling time-pressured; values efficiency |
| **AI Response Style** | Concise; skip unnecessary pleasantries; get to the point |
| **Caution** | Impatience can escalate to frustration if not handled efficiently |

**Example Indicators:**
- "I'm in a hurry"
- "Can we speed this up?"
- "Just tell me the answer"
- "I don't have time for this"

---

#### State 4: Frustrated

**Definition:** Customer is annoyed or disappointed about a situation.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | Expressions of annoyance, repeated issue mentions, mild complaints |
| **Customer Experience** | Something hasn't met expectations; patience wearing thin |
| **AI Response Style** | Acknowledge frustration first; then move to solution |
| **Caution** | Frustration can escalate to anger if not addressed |

**Example Indicators:**
- "This is frustrating"
- "I've already tried that"
- "Why is this so complicated?"
- "I shouldn't have to call about this"

**Response Pattern:**
1. Acknowledge: "I understand this is frustrating"
2. Own it: "I'm sorry you're dealing with this"
3. Solve: Move directly to resolution

---

#### State 5: Anxious

**Definition:** Customer is worried, stressed, or concerned about a situation.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | Worry expressions, urgency, concern about outcomes |
| **Customer Experience** | Uncertainty causing stress; needs reassurance |
| **AI Response Style** | Calm, reassuring, clear explanations, patient |
| **Caution** | Rushing may increase anxiety; take time to explain |

**Example Indicators:**
- "I'm worried about..."
- "Will this affect my...?"
- "I'm concerned that..."
- "What happens if...?"

**Response Pattern:**
1. Reassure: "Let me help you with this"
2. Explain: Provide clear information
3. Confirm: "Does that address your concern?"

---

#### State 6: Angry

**Definition:** Customer is hostile, demanding, or aggressive.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | Hostile language, demands, raised voice indicators, ultimatums |
| **Customer Experience** | Feeling wronged; wants acknowledgment and action |
| **AI Response Style** | Calm, non-defensive, acknowledge, offer human option |
| **Caution** | Do not argue, defend, or escalate the tension |

**Example Indicators:**
- "This is completely unacceptable"
- "I demand to speak to a manager"
- Profanity or harsh language
- Threats to leave, sue, or publicize

**Response Pattern:**
1. Don't argue or defend
2. Acknowledge their right to be upset
3. Offer human agent proactively
4. If continuing, focus only on resolution

---

#### State 7: Distressed

**Definition:** Customer is upset, overwhelmed, or potentially in a vulnerable state.

| Aspect | Details |
|--------|---------|
| **Observable Signals** | Expressions of overwhelm, desperation, crisis language |
| **Customer Experience** | Genuinely struggling; may extend beyond the immediate issue |
| **AI Response Style** | Compassionate, patient, prioritize their wellbeing |
| **Caution** | May need specialized support; escalate if concerning |

**Example Indicators:**
- "I don't know what to do"
- "Everything is going wrong"
- Signs of extreme stress or desperation
- Mentions of personal hardship

**Response Pattern:**
1. Express genuine care
2. Slow down; don't rush
3. Solve what you can
4. Escalate if wellbeing concern

---

### 2.3 Emotional State Transitions

Emotion is dynamic. The AI monitors for transitions during the conversation.

| From | To | Trigger | AI Response |
|------|-----|---------|-------------|
| Neutral | Frustrated | Issue not resolved quickly | Acknowledge; accelerate resolution |
| Frustrated | Angry | Continued failure to resolve | De-escalate; offer human |
| Frustrated | Neutral/Positive | Issue resolved | Express satisfaction; confirm resolution |
| Anxious | Neutral | Concerns addressed | Confirm understanding; summarize |
| Angry | Frustrated | AI response calms situation | Continue with empathy; solve issue |
| Any | Distressed | Crisis language appears | Prioritize; show care; consider escalation |

---

## 3. Intent and Emotion Interaction

### 3.1 Interaction Matrix

How emotion modifies the response to intent:

| Intent | Positive/Neutral | Impatient | Frustrated | Anxious | Angry | Distressed |
|--------|------------------|-----------|------------|---------|-------|------------|
| **Status Inquiry** | Provide info | Provide quickly | Provide + acknowledge | Provide + reassure | Provide + offer human | Provide + support |
| **Problem Report** | Troubleshoot | Troubleshoot fast | Acknowledge + troubleshoot | Reassure + troubleshoot | Empathize + offer human | Support + prioritize |
| **Complaint** | Document + respond | Document quickly | Acknowledge + resolve | Address concerns | De-escalate + escalate | Support + escalate |
| **Cancellation** | Process | Process quickly | Acknowledge + process | Clarify implications calmly | Don't retain + process | Process with care |
| **Billing Inquiry** | Explain | Explain concisely | Acknowledge + explain | Reassure + explain | Empathize + escalate | Support + explain |

### 3.2 Response Modification Rules

| Emotional Overlay | Response Modification |
|-------------------|----------------------|
| **Positive** | Match warmth; proceed efficiently |
| **Neutral** | Focus on task completion |
| **Impatient** | Reduce pleasantries; be concise; skip optional steps |
| **Frustrated** | Add acknowledgment before solution |
| **Anxious** | Add reassurance; explain more; confirm understanding |
| **Angry** | Lead with empathy; offer human; don't defend |
| **Distressed** | Prioritize wellbeing; slow down; show genuine care |

### 3.3 The "Emotion Before Transaction" Rule

When negative emotion is detected, address the emotion before proceeding with the transaction:

```
┌─────────────────────────────────────────────────────────────────┐
│              EMOTION BEFORE TRANSACTION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STANDARD (Neutral/Positive):                                    │
│  └── Customer asks → AI resolves                                │
│                                                                  │
│  NEGATIVE EMOTION DETECTED:                                      │
│  └── Customer asks (with frustration)                           │
│      └── AI acknowledges emotion                                │
│      └── AI expresses empathy                                   │
│      └── AI resolves                                            │
│                                                                  │
│  WRONG:                                                          │
│  ✗ "Sure, I can help with that. Your order shipped yesterday."  │
│                                                                  │
│  RIGHT:                                                          │
│  ✓ "I understand that's frustrating, and I'm sorry you've been │
│    waiting. Let me check on your order right now."              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Edge Cases: Clear Intent, Escalation Emotion

### 4.1 Definition

There are situations where the AI clearly understands what the customer wants, but the emotional state requires human involvement regardless of the AI's ability to complete the task.

> **"I can solve your problem, but you need a human."**

### 4.2 Edge Case Scenarios

#### Scenario A: Simple Request + Extreme Anger

| Element | Details |
|---------|---------|
| **Customer Request** | "I WANT TO KNOW WHERE MY DAMN ORDER IS" |
| **Intent** | Status Inquiry (simple, AI can handle) |
| **Emotion** | Angry (signals include: capitals, profanity, aggressive tone) |
| **AI Action** | Offer human agent; if customer declines, proceed with empathy |
| **Reasoning** | Customer's emotional state suggests they may not accept AI resolution even if correct |

#### Scenario B: Routine Transaction + Distress Signals

| Element | Details |
|---------|---------|
| **Customer Request** | "I need to cancel my subscription. Everything is falling apart right now." |
| **Intent** | Cancellation Request (simple, AI can handle) |
| **Emotion** | Distressed (signals include: "everything is falling apart") |
| **AI Action** | Express care; process request if customer wants; don't probe personal issues |
| **Reasoning** | Customer may be going through difficulty; treat with extra care |

#### Scenario C: Information Request + Persistent Frustration

| Element | Details |
|---------|---------|
| **Customer Request** | "Just tell me what time you close. This is the THIRD time I've asked." |
| **Intent** | Information Request (simple, AI can handle) |
| **Emotion** | Frustrated, escalating to angry |
| **AI Action** | Answer immediately; acknowledge failure; offer human if customer remains unhappy |
| **Reasoning** | Repeated failure has eroded trust; customer may prefer human confirmation |

#### Scenario D: Complaint + Any Strong Negative Emotion

| Element | Details |
|---------|---------|
| **Customer Request** | "I want to file a formal complaint about my experience" |
| **Intent** | Complaint |
| **Emotion** | Frustrated or Angry |
| **AI Action** | Acknowledge; offer immediate human escalation |
| **Reasoning** | Complaints with strong emotion typically require human judgment for resolution |

#### Scenario E: Account Access + Security Anxiety

| Element | Details |
|---------|---------|
| **Customer Request** | "Someone might be in my account. I'm really scared right now." |
| **Intent** | Account Access / Security Concern |
| **Emotion** | Anxious, approaching distressed |
| **AI Action** | Immediate security steps; reassure; offer human for additional support |
| **Reasoning** | Security concerns with fear require both technical and emotional support |

### 4.3 Edge Case Decision Framework

```
┌─────────────────────────────────────────────────────────────────┐
│         EDGE CASE DECISION: INTENT vs. EMOTION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Can AI technically complete this request?                       │
│         │                                                        │
│         YES                                                      │
│         │                                                        │
│         ▼                                                        │
│  Is emotional state elevated?                                    │
│         │                                                        │
│    ┌────┴────┐                                                  │
│    NO        YES                                                │
│    │         │                                                  │
│    ▼         ▼                                                  │
│  Proceed   Does emotion suggest customer                        │
│  normally   would reject AI resolution?                         │
│                │                                                │
│           ┌────┴────┐                                           │
│           NO        YES                                         │
│           │         │                                           │
│           ▼         ▼                                           │
│      Proceed    Offer human                                     │
│      with       proactively                                     │
│      empathy                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Signals That Trigger Escalation Despite Clear Intent

| Signal | Interpretation | Action |
|--------|---------------|--------|
| Repeated demand for human | Customer has decided AI isn't acceptable | Comply immediately |
| Profanity directed at AI | Customer is angry at the channel, not just the issue | Offer human |
| "I don't want to deal with a robot" | Explicit AI rejection | Transfer |
| Legal or regulatory threats | Situation requires human judgment | Escalate |
| Mentions of media or public action | Reputation risk | Escalate |
| Repeated "you don't understand" | Trust in AI comprehension broken | Offer human |
| Expressions of desperation | Wellbeing concern | Handle with care; consider escalation |

---

## 5. Ethical Considerations in Emotion Detection

### 5.1 Core Ethical Principles

| Principle | Application |
|-----------|-------------|
| **Respect** | Emotion detection serves the customer, not surveillance |
| **Fairness** | Detection must not discriminate based on customer characteristics |
| **Transparency** | Customers should know emotion affects how we respond |
| **Privacy** | Emotional data is sensitive and protected |
| **Beneficence** | Emotion detection should improve, not manipulate, experience |

### 5.2 What Emotion Detection Is FOR

| Appropriate Use | Description |
|-----------------|-------------|
| **Improving empathy** | Responding appropriately to customer feelings |
| **Appropriate escalation** | Getting humans involved when needed |
| **Adapting communication** | Adjusting tone and pace to customer state |
| **Quality assurance** | Understanding customer experience patterns |

### 5.3 What Emotion Detection Is NOT FOR

| Prohibited Use | Why It's Wrong |
|----------------|----------------|
| **Manipulation** | Using emotional state to pressure decisions |
| **Discrimination** | Treating customers differently based on demographics |
| **Profiling** | Building emotional profiles across interactions |
| **Retention pressure** | Using detected frustration to apply pressure |
| **Scoring customers** | Rating customers based on emotional patterns |
| **Punitive treatment** | Providing worse service to "difficult" customers |

### 5.4 Bias Risks and Mitigations

| Bias Risk | Description | Mitigation |
|-----------|-------------|------------|
| **Cultural expression variation** | Emotions are expressed differently across cultures | Conservative detection; don't over-interpret |
| **Language and accent** | Non-native speakers may be misclassified | Focus on explicit signals, not subtle cues |
| **Gender bias** | Same behavior may be labeled differently by gender | No demographic factors in detection |
| **Age assumptions** | Older/younger customers stereotyped | Detection based on content, not assumptions |
| **Disability impact** | Speech patterns may be misinterpreted | Accommodate variation; err toward neutral |

### 5.5 Safeguards

| Safeguard | Implementation |
|-----------|----------------|
| **Content-based only** | Detect from what customer says/writes, not how they sound |
| **Conservative thresholds** | When uncertain, assume neutral or slightly negative |
| **No demographic inputs** | Customer age, gender, location not used in emotion detection |
| **Human oversight** | Patterns reviewed for bias regularly |
| **Customer benefit focus** | Every detection should lead to better service |

### 5.6 Transparency Commitments

| Commitment | Description |
|------------|-------------|
| **No hidden emotion scoring** | Customers are not secretly rated |
| **Emotion affects response, not access** | All customers get service regardless of emotion |
| **Data minimization** | Emotion assessments not retained beyond session |
| **Audit capability** | Emotion-based decisions can be reviewed |

### 5.7 Customer Rights Regarding Emotion Detection

| Right | Implementation |
|-------|----------------|
| **Right to human service** | Can opt out of AI and emotion detection by requesting human |
| **Right to fair treatment** | Emotional state does not reduce service quality |
| **Right to not be manipulated** | Detected emotion used to help, not exploit |
| **Right to be wrong** | Customer can express frustration without penalty |

---

## 6. Classification Governance

### 6.1 Taxonomy Ownership

| Role | Responsibility |
|------|----------------|
| **Product** | Defines business intent categories |
| **Operations** | Validates categories match real customer needs |
| **Compliance** | Reviews ethical considerations and bias risks |
| **AI Team** | Implements detection; monitors accuracy |
| **Quality Assurance** | Audits classification accuracy |

### 6.2 Review Cycle

| Activity | Frequency |
|----------|-----------|
| Intent category review | Quarterly |
| Emotion detection bias audit | Monthly |
| Edge case pattern analysis | Monthly |
| Ethics compliance review | Quarterly |
| Taxonomy update (if needed) | As needed with change control |

### 6.3 Adding New Categories

New intent or emotion categories require:

1. Business justification
2. Clear definition with observable signals
3. Response guidelines
4. Ethical review
5. Testing before deployment

---

## Appendix A: Quick Reference — Intent Categories

| Intent | Customer Says | AI Does |
|--------|---------------|---------|
| Status Inquiry | "Where is my...?" | Look up and inform |
| Transaction Request | "I want to..." | Execute transaction |
| Problem Report | "It's not working" | Troubleshoot |
| Information Request | "How do I...?" | Provide information |
| Complaint | "This is unacceptable" | Acknowledge; resolve |
| Change Request | "I need to change..." | Process update |
| Cancellation Request | "Cancel my..." | Process cancellation |
| Billing Inquiry | "Why was I charged...?" | Explain; resolve |
| Technical Support | "Help me set up..." | Guide through steps |
| Account Access | "I can't log in" | Verify; restore access |
| Feedback | "I wanted to suggest..." | Document; thank |
| Human Request | "Let me talk to someone" | Transfer immediately |

---

## Appendix B: Quick Reference — Emotion Categories

| Emotion | Observable Signals | AI Response Priority |
|---------|-------------------|---------------------|
| Positive | Thanks, compliments | Match warmth |
| Neutral | Direct, factual | Be efficient |
| Impatient | "Quickly," short responses | Skip pleasantries |
| Frustrated | "Frustrating," complaints | Acknowledge first |
| Anxious | "Worried," "concerned" | Reassure first |
| Angry | Demands, hostility | De-escalate; offer human |
| Distressed | Overwhelmed, desperate | Show care; prioritize |

---

## Appendix C: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-17 | Product & AI Design | Initial taxonomy |

---

*This taxonomy provides the foundation for understanding and appropriately responding to customers. All classifications should serve the goal of better customer experiences, applied fairly and ethically.*
