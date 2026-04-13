from agent.state import BlogAgentState
from langchain_core.prompts import ChatPromptTemplate


def task_executer_node(state: BlogAgentState, model) -> dict:
    """Draft one blog section from the current task and workflow state.

    Args:
        state: Current workflow state containing the blog plan and task data.
        model: Language model used to generate the section draft.

    Returns:
        dict: Draft content, metadata, and/or revision output for downstream nodes.
    """
    # model = load_model()

    system_prompt = """
    You are a SENIOR technical blog writer, SEO strategist, and content editor with 15+ years of experience.

    Your job is to write a HIGH-IMPACT, HUMAN-LIKE blog section that is:
    - Deeply informative
    - SEO-optimized
    - Engaging and easy to read
    - Strategically structured for retention and clarity

    You must follow ALL instructions strictly.

    --------------------------------------------------
    ### 1. BLOG CONTEXT (GLOBAL)
    --------------------------------------------------
    - Title: {title}
    - Subtitle: {subtitle}
    - Tone: {tone}
    - Target Audience: {audience}

    Use this to:
    - Maintain consistent tone and voice
    - Match technical depth to audience level
    - Align with the blog’s core goal

    --------------------------------------------------
    ### 2. TASK (STRICT SCOPE CONTROL)
    --------------------------------------------------
    Task: {task}

    Rules:
    - Write ONLY the assigned section
    - Do NOT introduce unrelated topics
    - Do NOT repeat content from other sections
    - Ensure smooth logical progression within this section

    --------------------------------------------------
    ### 3. SECTION REQUIREMENTS (NON-NEGOTIABLE)
    --------------------------------------------------
    - Section Name: {section_name}
    - Description: {section_description}
    - Target Word Count: {section_word_count}
    - Key Points: {section_key_points}
    - SEO Keywords: {section_seo_keywords}
    - Estimated Words: {estimated_total_words}

    You MUST:
    - Cover ALL key points explicitly and in depth
    - Stay within ±10% of word count
    - Avoid redundancy
    - Ensure each paragraph delivers NEW value

    --------------------------------------------------
    ### 4. SEO OPTIMIZATION (CRITICAL)
    --------------------------------------------------
    - Naturally integrate ALL provided keywords
    - Maintain readability (no keyword stuffing)
    - Use keywords in:
    - Headings (where natural)
    - First 100 words (if possible)
    - Throughout content contextually

    - Optimize for:
    - Search intent (informational / transactional / comparison)
    - Featured snippets (clear explanations, bullet lists)
    - Scannability

    --------------------------------------------------
    ### 5. RESEARCH USAGE (STRICT ACCURACY)
    --------------------------------------------------
    Research Summary:
    {research_summary}

    Rules:
    - Base content on provided research
    - Do NOT hallucinate facts
    - Expand logically using domain knowledge
    - Prefer precise, technical, and verifiable explanations

    --------------------------------------------------
    ### 6. WRITING STYLE (VERY IMPORTANT)
    --------------------------------------------------
    - Match tone: {tone}
    - Adapt to audience: {audience}

    Write like a HUMAN expert:
    - Avoid robotic phrasing
    - Avoid generic filler (e.g., "in today's world", "it is important to note")
    - Use varied sentence structure
    - Use subtle transitions between ideas

    Enhance engagement:
    - Use micro-hooks at paragraph starts
    - Use examples, comparisons, or mini-explanations
    - Make complex ideas feel simple

    --------------------------------------------------
    ### 7. STRUCTURE & READABILITY
    --------------------------------------------------
    - Start with a strong opening (hook + context)
    - Maintain logical flow between paragraphs
    - Break down complex ideas into digestible parts

    Use:
    - Short paragraphs (2–4 lines max)
    - Bullet points for clarity
    - Numbered steps (if procedural)

    --------------------------------------------------
    ### 8. FORMATTING (MANDATORY MARKDOWN)
    --------------------------------------------------
    - Use ## for section title
    - Use ### for subsections
    - Use bullet points and lists where useful
    - Use **bold** for key insights
    - Use code blocks for technical content
    - Avoid overly dense text

    --------------------------------------------------
    ### 9. OUTPUT RULES (STRICT)
    --------------------------------------------------
    - Output ONLY the final section in MARKDOWN
    - Do NOT explain your reasoning
    - Do NOT mention instructions
    - Do NOT include placeholders
    - Do NOT repeat the section title unnecessarily

    --------------------------------------------------
    ### 10. QUALITY BAR (FINAL CHECK)
    --------------------------------------------------
    Before finishing, ensure:
    - Content is NOT generic
    - Content feels like expert-written, publish-ready material
    - Clear, useful, and actionable insights are present
    - SEO + readability + clarity are all optimized

    ### 11. HUMAN EDGE & ENGAGEMENT (CRITICAL)

    You MUST:
    - Introduce at least 1 strong insight, misconception, or “hard truth” per section
    - Occasionally challenge common assumptions
    - Add micro-tension (problem → solution flow)

    Avoid sounding like documentation.
    Write like a real expert explaining what most people get wrong.

    This must feel like a top-ranking blog section.
    """
    user_prompt = """
    Write the blog section following ALL system instructions.

    Before generating, internally verify:

    ✔ All key points are fully covered
    ✔ Content is insightful, not generic
    ✔ SEO keywords are used naturally
    ✔ Structure is clean and scannable
    ✔ Tone matches the audience
    ✔ Content stays within the word count

    Execution rules:
    - Start strong (no weak or generic opening)
    - Maintain flow and clarity throughout
    - Avoid repetition and filler
    - Deliver value in every paragraph

    Now generate the final section.
    """

    needs_revision = state.needs_revision
    blog_plan = state.blog_plan
    research_summary = state.research_summary

    title = blog_plan["title"]
    subtitle = blog_plan["subtitle"]
    tone = blog_plan["tone"]
    audience = blog_plan["audience"]

    if needs_revision:
        revision_cycles = state.revision_cycles
        edited_draft = state.edited_draft
        system_prompt = """
        You are an expert Senior Technical Content Strategist. Your task is to refine and rewrite a blog based on detailed feedback.

        ### CONTEXT
        - **Title:** {title}
        - **Subtitle:** {subtitle}
        - **Tone:** {tone}
        - **Target Audience:** {audience}

        ### RESEARCH DATA
        {research_summary}

        ### CRITIC FEEDBACK (ACTION REQUIRED)
        The previous draft was flagged for improvement. You must address the following:
        - **Quality Score:** {quality_score}/10
        - **Confidence Score:** {confidence_score}
        - **Identified Issues:** {issues}
        - **Suggested Improvements:** {suggestions}

        ### WRITING CONSTRAINTS
        1. **Precision:** No fluff or "corporate speak." Use technical examples where relevant.
        2. **Integration:** Naturally weave in SEO keywords; avoid keyword stuffing.
        3. **Accuracy:** Use provided research only. Do not hallucinate external facts.
        4. **Scope:** Write ONLY this section. Do not include intros or outros for the full blog.
        5. **Formatting:** Use Markdown (##, ###), **bold** for emphasis, and code blocks for technical snippets.

        ### OUTPUT RULES
        - Return ONLY the final Markdown content.
        - No conversational filler (e.g., "Sure, here is the revised section...").
        - No meta-commentary on the instructions.
        """

        user_prompt = """
        Draft the revised version of the "{edited_draft} draft of blog.

        Ensure that you specifically solve the issues identified by the critic: {issues}.
        The content must remain aligned with the tone for a {audience} audience.

        Checklist before generating:
        - Does the content fully cover all key points?
        - Is the tone aligned with the audience?
        - Are SEO keywords used naturally?
        - Is the structure clean and readable in markdown?
        - Is the content within the word count range?

        Generate the revised Markdown now.
        """

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", user_prompt)]
        )

        chain = prompt_template | model

        input_variables = {
            "title": title,
            "subtitle": subtitle,
            "tone": tone,
            "audience": audience,
            "research_summary": research_summary,
            "issues": state.critic_feedback["issues"],
            "suggestions": (state.critic_feedback["suggestions"]),
            "confidence_score": state.quality_score,
            "quality_score": state.quality_score,
            "edited_draft": state.edited_draft,
        }

        revision_cycles += 1

        response = chain.invoke(input_variables)

        edited_draft = response.content

        return {
            "edited_draft": edited_draft,
            "revision_cycles": revision_cycles,
        }

    tasks = state.tasks

    sections = blog_plan["sections"]

    tasks_output_dict = {}

    for i in range(len(tasks)):

        task = tasks[i]
        section = sections[i]
        section_name = section["name"]
        section_description = section["description"]
        section_word_count = section["word_count"]
        section_key_points = section["key_points"]
        section_seo_keywords = section["seo_keywords"]
        estimated_total_words = section["estimated_total_words"]

        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", user_prompt)]
        )

        chain = prompt_template | model

        input_variables = {
            "title": title,
            "subtitle": subtitle,
            "tone": tone,
            "audience": audience,
            "task": task,
            "section_name": section_name,
            "section_description": section_description,
            "section_word_count": section_word_count,
            "section_key_points": section_key_points,
            "section_seo_keywords": section_seo_keywords,
            "estimated_total_words": estimated_total_words,
            "research_summary": research_summary,
        }

        response = chain.invoke(input_variables)

        tasks_output_dict[section_name] = response.content

    # print(f"Length of tasks_output: {len(tasks_output)}")

    return {
        "tasks_output": tasks_output_dict,
        "revision_cycles": revision_cycles if needs_revision else 0,
    }
