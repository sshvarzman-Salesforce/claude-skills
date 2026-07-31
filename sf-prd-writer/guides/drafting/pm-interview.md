# PM Interview ("Grill Me" Mode)

Run this guide when the user says *"grill me"*, *"interview me first"*, *"ask me questions before drafting"*, or *"I want to fill in the gaps before you start"*. Also offer it proactively when the user's input is thin (< 3 sentences, no customer names, no scope signal) — add a 4th question to the Phase 1 confirmation message in SKILL.md:

> *4. Want me to interview you first to pull out customer signal, scope edges, and success criteria before I draft? (Saves a lot of TBDs)*

**What this phase does:** Before running Slack research or drafting anything, the skill interviews you with targeted PM questions to extract the context the PRD needs. Your answers become the primary grounding for the draft — Slack research then fills in supporting evidence around what you've already told it.

**This is not a blocker.** If the user says no or doesn't answer the interview offer, skip straight to research.

---

## Step 1: Run Slack research first (lightweight)

Before asking questions, do a quick targeted Slack search (2–3 searches max) on the feature topic to understand what's already known. This prevents asking questions the skill can answer itself from Slack.

- Search for the feature name / core concept
- Search for any named customer or channel mentioned in the user's prompt
- Note what's already answered vs. what's genuinely unknown

## Step 2: Generate the interview questions

Based on the user's input and what the lightweight Slack research did/didn't surface, generate **8–12 sharp, specific questions** that would fill the biggest gaps in the PRD. Do not ask generic boilerplate — tailor every question to this specific feature.

**Question categories to draw from (pick the most relevant, don't ask all of them):**

**The Customer Pain**
- Who specifically is experiencing this problem? (role, industry, workflow context)
- What do they do today as a workaround? How much does the workaround cost them?
- Have you heard this directly from a customer — if so, who, and what did they say?
- Is this a blocker for a specific customer's GA or renewal decision?

**The Scope Edge**
- What's the minimum version of this that would be valuable? What would you cut if you had to ship in 2 weeks?
- What channels / objects / plan types does this apply to? Any explicit exclusions?
- What does "done" look like for v1 vs. post-GA?
- Is there a related feature that could overlap with this? (I found [X] in Slack — is that the same thing?)

**The Success Signal**
- How will a rep/admin know this is working? What do they see or do differently?
- What metric would you track to prove this moved the needle?
- What would make this a failure even if shipped on time?

**The Constraints**
- Are there known technical constraints or dependencies engineering has flagged?
- Is there a timeline driver — customer commitment, release gate, exec ask?
- What's the confidence level on the scope — locked, likely, or still fuzzy?

**The Stakeholders**
- Who needs to sign off on this before it goes to scrum teams?
- Is UX already involved? Do mocks exist?
- Any adjacent teams (Platform, Einstein, Industries) who need to be aware or aligned?

## Step 3: Ask all questions in a single message

Format as a numbered list. Keep questions concise — one sentence each. Lead with the highest-value questions (customer pain, scope edge). End with:

> *Answer as many or as few as you'd like — partial answers are fine. I'll draft from whatever you give me plus what I find in Slack.*

## Step 4: Receive answers, then proceed to research

Once the user replies (even partially), treat their answers as the primary grounding layer. Proceed to full Slack research with the feature topic now sharply defined by their answers. When drafting, pull from their answers first — Slack evidence supplements, it doesn't override.

**TBD reduction goal:** After a completed interview, the draft should have no more than 2–3 TBD/placeholder fields (typically Figma links and engineering lead). Every section the user answered should be fully written.
