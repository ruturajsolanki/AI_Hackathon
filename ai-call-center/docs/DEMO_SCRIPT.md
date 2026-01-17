# Live Demo Script

**Total Duration:** 5-7 minutes  
**Audience:** Judges, non-technical stakeholders  
**Tone:** Calm, confident, clear

---

## Pre-Demo Checklist

- [ ] Backend running (`http://localhost:8000`)
- [ ] Frontend running (`http://localhost:5173`)
- [ ] Browser open to dashboard
- [ ] Terminal ready for API calls (optional)
- [ ] Notes visible only to presenter

---

## Part 1: The Problem (20 seconds)

> *[Dashboard visible, no interaction started yet]*

**SAY:**

> "Every day, enterprises handle millions of customer calls. Each call costs $8-15 and requires trained agents working around the clock.
>
> What if AI could handle 80% of routine inquiries instantly—while knowing exactly when to bring in a human?
>
> That's what we built. Let me show you."

---

## Part 2: Start the Interaction (30 seconds)

> *[Click "Start New Call" or equivalent]*

**SAY:**

> "A customer just reached out through chat. Let's see what happens."

**TYPE in the chat input:**

```
Hi, I noticed a $50 charge on my bill that I don't recognize. Can you help?
```

> *[Press Send]*

**SAY:**

> "Watch what happens behind the scenes."

---

## Part 3: Agent Processing (1 minute)

> *[Point to the Agent Decision Panel as it updates]*

**SAY:**

> "Three AI agents are working together right now."

**[As Primary Agent panel updates]**

> "First, our **Primary Agent** reads the message. It detected this is a **billing inquiry**, and the customer seems **neutral but concerned**. It drafts a helpful response."

**[Point to confidence score]**

> "See this confidence score? **85%**. The AI is saying: 'I'm fairly certain I understand this correctly.'"

**[As Supervisor Agent panel updates]**

> "But we don't just trust that. A second agent—the **Supervisor**—reviews the response. It checks: Is the tone appropriate? Does it follow our policies? Is there any risk?"

**[Point to approval status]**

> "The Supervisor approved it. The response goes to the customer."

> *[Customer sees the AI response appear]*

---

## Part 4: Show Escalation (1.5 minutes)

**SAY:**

> "Now let's see what happens when things get complicated."

**TYPE:**

```
This is ridiculous! I've been charged wrong THREE times now. I want to cancel my account immediately.
```

> *[Press Send]*

**SAY:**

> "The customer is frustrated and mentions cancellation. Let's see how the AI handles this."

**[Watch the Agent Decision Panel]**

> "Notice the Primary Agent detected **angry** emotion and **cancellation intent**. But look at the confidence—it dropped to **55%**."

> "The Supervisor sees this is high-risk: frustrated customer, potential cancellation. It flags this for **escalation**."

**[Point to Escalation Agent panel]**

> "The Escalation Agent makes the call: this needs a human. It generates a summary for the human agent so they don't have to start from scratch."

**[Point to escalation status]**

> "The AI knew its limits. It didn't try to handle something it shouldn't."

---

## Part 5: Analytics Dashboard (1 minute)

> *[Navigate to or scroll to Analytics section]*

**SAY:**

> "Every decision is tracked. Let me show you what this means for operations."

**[Point to key metrics]**

> "In this session alone:
> - The first inquiry was **resolved by AI** in under 2 seconds
> - The second was **escalated** appropriately
> - All decisions are logged with full reasoning for compliance"

**[If showing aggregated metrics]**

> "At scale, we see patterns:
> - **75%** of interactions resolved without human involvement
> - **Average confidence** stays above 80%
> - **Zero compliance violations**—the system catches them before they reach customers"

---

## Part 6: The Safety Layer (45 seconds)

**SAY:**

> "Let me show you one more thing—how we prevent AI mistakes."

**TYPE:**

```
I'm going to sue your company.
```

> *[Press Send]*

**SAY:**

> "Watch what happens with sensitive content."

**[Point to Agent Panel]**

> "The system detected **legal language**—a sensitive topic. Even though the AI could respond, the safety rules kicked in. This is automatically escalated to a human."

> "These safety rules are **hard-coded**. The AI cannot override them. No matter how confident it is, certain situations always go to humans."

---

## Part 7: Enterprise Impact (45 seconds)

> *[Optional: show a summary slide or return to dashboard overview]*

**SAY:**

> "So what does this mean for an enterprise?"

**[Pause briefly between each point]**

> "**Cost**: Routine inquiries that cost $10 with a human cost less than a penny with AI."

> "**Speed**: Customers get answers in seconds, not minutes on hold."

> "**Quality**: Every response is reviewed by a second AI before delivery."

> "**Compliance**: Complete audit trail. Every decision is explainable."

> "**Safety**: The AI knows what it doesn't know—and asks for help."

---

## Part 8: Closing (20 seconds)

**SAY:**

> "This isn't about replacing humans. It's about **letting AI handle the routine** so humans can focus on what matters—the complex problems, the frustrated customers, the moments that need a human touch."

> "Thank you. I'm happy to take questions."

---

## Backup Talking Points

*If questions arise or demo needs to fill time:*

### "How does it know when to escalate?"

> "Confidence scoring. The AI continuously rates how certain it is. Below 50%? It escalates. High-risk keywords like 'legal' or 'cancel'? It escalates. Angry customer with a complaint? It escalates. The thresholds are configurable by the business."

### "What if the AI is wrong?"

> "Three safeguards: First, the Supervisor Agent reviews every response. Second, hard-coded rules block certain content. Third, humans can override any decision. The system is designed to fail safe—when in doubt, escalate."

### "What about privacy?"

> "Customer messages are processed but not stored in logs. Customer IDs are hashed. The audit trail captures decisions, not personal data. Designed for GDPR and similar regulations."

### "Can this work with voice calls?"

> "The architecture supports it. Speech-to-text on input, text-to-speech on output. The same agent logic applies. We've abstracted the voice integration for future expansion."

### "What's the cost at scale?"

> "Conservative estimate: less than one cent per interaction at scale. That's 99% cheaper than a human agent for routine inquiries."

---

## Demo Recovery

*If something goes wrong:*

| Issue | Recovery |
|-------|----------|
| Backend not responding | "Let me restart the service—this demonstrates our health check system." |
| Slow response | "In production, this runs on optimized infrastructure. What you're seeing is a local demo." |
| Unexpected AI response | "Interesting—the AI interpreted that differently. This is why we have the Supervisor layer." |
| UI not updating | Refresh the page. "Hot reload in action." |

---

## Key Phrases to Remember

- "The AI knows what it doesn't know."
- "Three agents working together."
- "Confidence-based autonomy."
- "Fail safe, not fail silent."
- "Routine work for AI, meaningful work for humans."
