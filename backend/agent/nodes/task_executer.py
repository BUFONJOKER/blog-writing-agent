from agent.state import BlogAgentState
from agent.model import load_model
from langchain_core.prompts import ChatPromptTemplate


def task_executer_node(state: BlogAgentState) -> dict:
    """
    This function write blog content
    """
    model = load_model()

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
                "suggestions": (
                    state.critic_feedback["suggestions"]
                ),
                "confidence_score": state.quality_score,
                "quality_score": state.quality_score,
                'edited_draft': state.edited_draft,
            }

        revision_cycles += 1

        response = chain.invoke(input_variables)

        edited_draft = response.content

        return {
            'edited_draft': edited_draft,
            'revision_cycles': revision_cycles,
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
                "research_summary": research_summary
            }

        response = chain.invoke(input_variables)

        tasks_output_dict[section_name] = response.content

    # print(f"Length of tasks_output: {len(tasks_output)}")

    return {
        "tasks_output": tasks_output_dict,
        "revision_cycles": revision_cycles if needs_revision else 0,
    }


# --------------- code to test the file -------------------------

# Mock data based on your specific planner output


def test_task_executer_with_exact_plan():
    # 1. This is the EXACT blog_plan you provided
    exact_blog_plan = {
        "title": 'ICC T20 Cricket World Cup 2026: Why "Worst Team" Predictions Are Premature',
        "subtitle": "Understanding Data Limitations and What We Actually Know About the Upcoming Tournament",
        "tone": "analytical, transparent, informative",
        "audience": "cricket enthusiasts, sports analysts, fantasy cricket players",
        "tasks": [
            "Draft an introduction explaining the data availability challenge for ICC T20 World Cup 2026",
            "Write a section on historical context of T20 World Cup team performances",
            "Create a technical analysis section on prediction methodologies and their limitations",
            "Develop a section on what official data we're waiting for from ICC",
            "Conclude with actionable guidance for readers following the tournament",
        ],
        "sections": [
            {
                "name": "Introduction",
                "description": "Hook readers with the common question about worst teams while immediately addressing the data availability issue. Set expectations for what the article will and won't cover.",
                "word_count": "150-200",
                "key_points": [
                    "Acknowledge the popular search query about worst T20 World Cup 2026 teams",
                    "Transparently state that official ICC data is not yet released",
                    "Explain why premature predictions compromise accuracy",
                    "Position the article as an educational resource on tournament analysis",
                ],
                "seo_keywords": [
                    "ICC T20 World Cup 2026",
                    "cricket world cup predictions",
                    "T20 team analysis",
                ],
                "estimated_total_words": 175,
            },
            {
                "name": "Historical Context",
                "description": "Provide historical context by examining past T20 World Cup performances to give readers valuable information while 2026 data is unavailable.",
                "word_count": "250-300",
                "key_points": [
                    "Review underperforming teams from 2021 and 2024 T20 World Cups",
                    "Identify patterns in team performance across tournaments",
                    "Discuss factors that contribute to poor tournament performance",
                    "Reference verifiable historical data from previous editions",
                ],
                "seo_keywords": [
                    "T20 World Cup history",
                    "cricket team performance",
                    "world cup statistics",
                ],
                "estimated_total_words": 275,
            },
            {
                "name": "Technical Analysis",
                "description": "Deep-dive into the methodology of team performance prediction and why it requires official data before making claims.",
                "word_count": "300-350",
                "key_points": [
                    "Explain key performance indicators for T20 cricket teams",
                    "Discuss squad announcement timelines and their importance",
                    "Outline venue and schedule impact on team performance",
                    "Address why speculation without data harms content credibility",
                ],
                "seo_keywords": [
                    "cricket analytics",
                    "team performance metrics",
                    "T20 prediction models",
                ],
                "estimated_total_words": 325,
            },
            {
                "name": "Official Data Timeline",
                "description": "Inform readers about what official information to expect from ICC and when it typically gets released.",
                "word_count": "200-250",
                "key_points": [
                    "List the types of official data ICC typically publishes",
                    "Provide timeline expectations based on previous World Cup cycles",
                    "Direct readers to official ICC channels for updates",
                    "Explain how venues and schedules affect team preparation",
                ],
                "seo_keywords": [
                    "ICC official announcements",
                    "cricket world cup schedule",
                    "ICC tournament data",
                ],
                "estimated_total_words": 225,
            },
            {
                "name": "Conclusion & Guidance",
                "description": "Provide actionable takeaways for readers interested in following the tournament responsibly.",
                "word_count": "150-200",
                "key_points": [
                    "Recommend waiting for official squad announcements",
                    "Suggest following verified cricket analysts and sources",
                    "Encourage historical data analysis over speculation",
                    "Offer guidance on responsible sports content consumption",
                ],
                "seo_keywords": [
                    "cricket betting tips",
                    "fantasy cricket preparation",
                    "sports analysis best practices",
                ],
                "estimated_total_words": 175,
            },
        ],
    }

    # 2. Setup the state for the test
    state = BlogAgentState(
        prompt="Write a blog post about T20 World Cup 2026 teams and data limitations.",
        research_summary="The ICC T20 World Cup 2026 will be hosted by India and Sri Lanka. Official squads and the full match schedule have not been released yet. Historical analysis of the 2024 cup shows that conditions in the subcontinent heavily favor spin and tactical batting over pure pace.",
        blog_plan=exact_blog_plan,
        tasks=exact_blog_plan["tasks"],  # All 5 tasks
    )

    print("---  TESTING TASK EXECUTER NODE ---")
    print(f"Post Title: {exact_blog_plan['title']}")
    print(f"Number of Tasks to Execute: {len(state.tasks)}")

    # 3. Invoke the node
    try:
        result = task_executer_node(state)

        print("Task executer output which will be store in tasks_output field", result)

        # 4. Print the output
        # NOTE: Using 'tasks_output' because that is what is in your task_executer.py return statement
        if "tasks_output" in result:
            print("\n SUCCESS: All sections generated.")
            for i, section_content in enumerate(result["tasks_output"]):
                print(f"\n{'='*20} SECTION {i+1} {'='*20}")
                print(section_content)
        else:
            print(
                "\n FAILED: The node did not return 'tasks_output'. Check your return statement."
            )

    except Exception as e:
        print(f"\n ERROR during execution: {str(e)}")


if __name__ == "__main__":
    test_task_executer_with_exact_plan()
