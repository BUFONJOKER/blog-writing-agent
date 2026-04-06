from agent.state import BlogAgentState
from agent.model import load_model
from langchain_core.prompts import ChatPromptTemplate


def task_executer_node(state: BlogAgentState) -> dict:
    """
    This function write blog content
    """
    model = load_model()

    system_prompt = """
        You are a senior technical blog writer and content strategist.

        Your responsibility is to generate a HIGH-QUALITY, WELL-STRUCTURED section of a blog post based strictly on the provided plan, section details, and research.

        You MUST follow all instructions carefully and DO NOT skip any requirement.

        -------------------------------------
        ### 1. BLOG METADATA (GLOBAL CONTEXT)
        -------------------------------------
        - Title: {title}
        - Subtitle: {subtitle}
        - Tone: {tone}
        - Target Audience: {audience}

        Use this information to maintain consistency in writing style, tone, and complexity.

        -------------------------------------
        ### 2. YOUR TASK
        -------------------------------------
        You are given a specific section writing task:

        Task: {task}

        You must:
        - Write ONLY the assigned section (NOT the full blog)
        - Stay focused on the section scope
        - Ensure smooth logical flow and clarity
        - Avoid repetition of ideas from other sections

        -------------------------------------
        ### 3. SECTION DETAILS (STRICTLY FOLLOW)
        -------------------------------------
        - Section Name: {section_name}
        - Description: {section_description}
        - Target Word Count: {section_word_count}
        - Key Points to Cover: {section_key_points}
        - SEO Keywords: {section_seo_keywords}
        - Estimated Total Words for Section: {estimated_total_words}

        REQUIREMENTS:
        - Cover ALL key points explicitly
        - Respect the word count (±10% tolerance)
        - Naturally incorporate SEO keywords (NO keyword stuffing)
        - Ensure each paragraph adds value

        -------------------------------------
        ### 4. RESEARCH INTEGRATION
        -------------------------------------
        Research Summary:\n
        {research_summary}\n

        You MUST:
        - Use the research to improve accuracy and depth
        - Do NOT hallucinate facts outside the research
        - Prefer factual, precise, and verifiable explanations
        - If research is limited, still produce a complete section using general knowledge

        -------------------------------------
        ### 5. WRITING STYLE GUIDELINES
        -------------------------------------
        - Match the tone exactly: {tone}
        - Adapt complexity to audience: {audience}
        - Use clear, concise, and professional language
        - Avoid fluff, filler, or generic statements
        - Use examples where helpful (especially for technical topics)

        -------------------------------------
        ### 6. FORMATTING REQUIREMENTS (MANDATORY)
        -------------------------------------
        Generate output in MARKDOWN:

        - Use proper headings (## for section title, ### for subsections)
        - Use bullet points or numbered lists where helpful
        - Use **bold** for emphasis on key ideas
        - Use code blocks for technical explanations (if applicable)
        - Keep paragraphs short and readable

        -------------------------------------
        ### 7. OUTPUT CONSTRAINTS
        -------------------------------------
        - DO NOT include explanations about what you are doing
        - DO NOT mention instructions or metadata
        - DO NOT repeat the section name unnecessarily
        - ONLY output the final section content in markdown
        """
    user_prompt = """
        Write the requested blog section based on the system instructions.

        Checklist before generating:
        - Does the content fully cover all key points?
        - Is the tone aligned with the audience?
        - Are SEO keywords used naturally?
        - Is the structure clean and readable in markdown?
        - Is the content within the word count range?

        Now generate the section.
        """

    needs_revision = state.needs_revision

    if needs_revision:
        revision_cycles = state.revision_cycles
        critic_feedback = state.critic_feedback
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
        Draft the revised version of the "{edited_draft} draft of blog

        Ensure that you specifically solve the issues identified by the critic: {issues}.
        The content must remain aligned with the tone for a {audience} audience and must fully integrate the SEO keywords: {seo_keywords}.

        Checklist before generating:
        - Does the content fully cover all key points?
        - Is the tone aligned with the audience?
        - Are SEO keywords used naturally?
        - Is the structure clean and readable in markdown?
        - Is the content within the word count range?

        Generate the revised Markdown now.
        """

        revision_cycles += 1

        return {
            'edited_draft': edited_draft,
            'revision_cycles': revision_cycles,
        }

    tasks = state.tasks
    blog_plan = state.blog_plan
    research_summary = state.research_summary

    title = blog_plan["title"]
    subtitle = blog_plan["subtitle"]
    tone = blog_plan["tone"]
    audience = blog_plan["audience"]
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

        response = chain.invoke(
            {
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
                "issues": state.critic_feedback["issues"] if needs_revision else None,
                "suggestions": (
                    state.critic_feedback["suggestions"] if needs_revision else None
                ),
                "confidence_score": state.quality_score if needs_revision else None,
                "quality_score": state.quality_score if needs_revision else None,
                "revision_cycles": state.revision_cycles if needs_revision else None,
                'edited_draft': state.edited_draft if needs_revision else None,
            }
        )

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
