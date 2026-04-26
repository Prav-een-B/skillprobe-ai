"""
Prompt templates for all AI interactions.
"""

EXTRACT_SKILLS_PROMPT = """You are an expert technical recruiter and skill analyst.

Given the following Job Description and Candidate Resume, extract and analyse the skills.

## Job Description:
{jd_text}

## Candidate Resume:
{resume_text}

## Your Task:
Analyse both documents and return a JSON object with exactly this structure:

{{
  "required_skills": [
    {{
      "name": "Skill Name",
      "importance": "critical" | "important" | "nice-to-have",
      "category": "category like frontend, backend, devops, database, soft-skill, etc."
    }}
  ],
  "candidate_skills": [
    {{
      "name": "Skill Name",
      "claimed_experience": "e.g. 3 years",
      "context": "Brief context from resume about how they used this skill"
    }}
  ],
  "initial_gaps": [
    {{
      "skill": "Skill Name",
      "status": "missing" | "weak" | "partial",
      "adjacent_to": ["Related skills the candidate already has"]
    }}
  ]
}}

Rules:
- Extract 5-12 required skills from the JD, prioritised by importance
- Match candidate skills against required skills (case-insensitive, consider synonyms)
- A skill is "missing" if not mentioned in resume at all
- A skill is "weak" if mentioned but with very little experience/context
- A skill is "partial" if mentioned but at a lower level than required
- Include adjacent_to for gap skills — these are related skills the candidate already knows
- Return ONLY valid JSON, no markdown, no explanation
"""

GENERATE_QUESTION_PROMPT = """You are a friendly but thorough technical interviewer.

You are assessing a candidate's proficiency in **{skill_name}**.

Context from their resume:
{resume_context}

Job requirement context:
{jd_context}

Difficulty level: **{difficulty}**
This is question {question_number} of {total_questions} for this skill.

{previous_qa}

Generate ONE assessment question that:
1. Tests PRACTICAL understanding, not just textbook knowledge
2. Is appropriate for the {difficulty} difficulty level:
   - easy: fundamental concepts, basic usage
   - medium: real-world scenarios, problem-solving
   - hard: architecture decisions, edge cases, trade-offs
3. Is conversational and encouraging in tone
4. If this is a follow-up question, build on the previous answer
5. Can be answered in 2-4 sentences (not a coding test)
6. DO NOT use generic greetings like "Hi there", "Welcome", or "Hello" unless this is literally the very first question of the entire assessment. Jump straight into the conversation naturally.

Return a JSON object:
{{
  "question": "Your question here",
  "what_good_answer_covers": "Key points a strong answer would include (for your evaluation reference)"
}}

Return ONLY valid JSON.
"""

EVALUATE_ANSWER_PROMPT = """You are a fair, expert technical evaluator.

Skill being assessed: **{skill_name}**
Difficulty: **{difficulty}**

Question asked:
"{question}"

Candidate's answer:
"{answer}"

What a good answer covers:
"{good_answer_covers}"

Evaluate the answer and return a JSON object:
{{
  "score": <1-5 integer>,
  "level": "novice" | "beginner" | "intermediate" | "advanced" | "expert",
  "feedback": "Brief, encouraging feedback explaining the score. Be specific about what was good and what was missing.",
  "strengths": ["specific strength 1", "specific strength 2"],
  "weaknesses": ["specific gap 1", "specific gap 2"]
}}

Scoring rubric:
- 1 (Novice): Cannot explain the concept, completely wrong or no answer
- 2 (Beginner): Basic awareness but significant gaps, mostly textbook
- 3 (Intermediate): Decent understanding, can apply with some guidance
- 4 (Advanced): Strong understanding, handles nuances well
- 5 (Expert): Exceptional depth, could teach this topic

Be fair but honest. Do NOT inflate scores. Return ONLY valid JSON.
"""

EVALUATE_AND_GENERATE_PROMPT = """You are an expert technical interviewer evaluating a candidate's answer and then immediately asking the NEXT question in a seamless conversation.

## Step 1: Evaluate the Answer
Skill being assessed: **{eval_skill_name}**
Difficulty: **{eval_difficulty}**
Question asked: "{eval_question}"
Candidate's answer: "{eval_answer}"
What a good answer covers: "{eval_good_answer_covers}"

Evaluate the answer based on this rubric:
- 1 (Novice): Cannot explain the concept, completely wrong or no answer
- 2 (Beginner): Basic awareness but significant gaps, mostly textbook
- 3 (Intermediate): Decent understanding, can apply with some guidance
- 4 (Advanced): Strong understanding, handles nuances well
- 5 (Expert): Exceptional depth, could teach this topic

## Step 2: Generate the Next Question
We are now moving to the next part of the assessment.
Next Skill to assess: **{next_skill_name}** (Note: this might be the same skill as above, or a new one)
Difficulty for next question: **{next_difficulty}**
This is question {next_question_number} of {next_total_questions} for the next skill.

Context from resume: {resume_context}
Job requirement context: {jd_context}

Generate ONE assessment question that:
1. Tests PRACTICAL understanding, not just textbook knowledge.
2. Is appropriate for the {next_difficulty} difficulty level.
3. Is conversational and encouraging. It should seamlessly follow the feedback from Step 1.
4. DO NOT say "Hello" or "Welcome". Acknowledge their previous answer and naturally transition to this new question.
5. If {next_skill_name} is different from {eval_skill_name}, briefly mention we are moving to a new topic.

Return a JSON object with BOTH the evaluation and the next question:
{{
  "evaluation": {{
    "score": <1-5 integer>,
    "level": "novice" | "beginner" | "intermediate" | "advanced" | "expert",
    "feedback": "Brief, encouraging feedback explaining the score.",
    "strengths": ["specific strength 1"],
    "weaknesses": ["specific gap 1"]
  }},
  "next_question": {{
    "question": "The conversational text containing feedback on their previous answer AND the new question. Make it flow naturally as a single response.",
    "what_good_answer_covers": "Key points a strong answer would include"
  }}
}}

Return ONLY valid JSON.
"""

GENERATE_PLAN_PROMPT = """You are an expert learning coach and career advisor.

## Candidate Assessment Results:

### Skills Assessed:
{skill_results}

### Job Description Summary:
{jd_summary}

### Candidate Background:
{resume_summary}

## Your Task:
Create a personalised learning plan that focuses on ADJACENT SKILLS — skills the candidate can realistically acquire based on what they already know.

Return a JSON object:
{{
  "overall_readiness_score": <0-100 number representing how ready the candidate is for this role>,
  "summary": "A 2-3 sentence personalised summary of the candidate's readiness and key areas to focus on",
  "strengths": ["Skill areas where the candidate is strong"],
  "critical_gaps": ["The most important gaps to address first"],
  "learning_items": [
    {{
      "skill_name": "Skill to learn/improve",
      "current_level": "Current proficiency level",
      "target_level": "Target proficiency level for this role",
      "priority": "high" | "medium" | "low",
      "why_important": "Why this skill matters for the target role",
      "resources": [
        {{
          "title": "Resource name",
          "url": "https://actual-url-to-resource",
          "type": "course" | "documentation" | "tutorial" | "video" | "book",
          "estimated_hours": <number>
        }}
      ],
      "estimated_weeks": <number of weeks to reach target level>,
      "prerequisites_you_have": ["Skills the candidate already has that will help"],
      "milestones": ["Week 1: ...", "Week 2: ...", "Week 3: ..."]
    }}
  ],
  "total_estimated_weeks": <total weeks for the full plan>
}}

Rules:
- Focus on gaps first (skills scored 1-3), prioritise critical skills
- Include 3-5 REAL, WORKING resource URLs per skill (popular platforms like Coursera, Udemy, YouTube, official docs, freeCodeCamp, etc.)
- Time estimates should be realistic for someone studying part-time (10-15 hrs/week)
- Connect each learning item to the candidate's existing skills (adjacent learning)
- Milestones should be specific and measurable
- Order learning items by priority (high → medium → low)
- Return ONLY valid JSON
"""
