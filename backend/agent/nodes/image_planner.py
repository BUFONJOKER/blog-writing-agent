from agent.state import BlogAgentState
from pydantic import BaseModel, Field
from typing_extensions import List
from langchain_core.prompts import ChatPromptTemplate


class ImagePlacement(BaseModel):
    prompt: str = Field(
        description="Highly detailed visual description for the image generator."
    )
    after_section: str = Field(
        description="The exact header text of the blog post after which the image should be placed."
    )


class ImagePlannerInput(BaseModel):
    image_plan: List[ImagePlacement]


def image_planner_node(state: BlogAgentState, model) -> dict:

    # model = load_model()

    structured_model = model.with_structured_output(
        schema=ImagePlannerInput, method="function_calling"
    )

    system_prompt = """
    You are a senior visual content strategist and image planner for high-quality blog posts.

    Your task is to analyze the given blog post and generate a precise, structured image placement plan.

    ## Objectives
    - Improve reader engagement
    - Enhance clarity of complex ideas
    - Break long text sections visually
    - Align visuals with section meaning (not random decoration)

    ## Rules for Image Placement
    1. Place images ONLY after meaningful sections (not after every section).
    2. Prefer sections that:
    - Introduce new concepts
    - Contain technical explanations
    - Include comparisons, workflows, or step-by-step processes
    3. Avoid placing images after:
    - Conclusion sections
    - Very short sections
    4. Use the EXACT section header text as written in the blog.

    ## Image Prompt Requirements
    Each image prompt MUST:
    - Be highly detailed and descriptive (minimum 30-60 words)
    - Be written for AI image generation (like Midjourney / DALL·E)
    - Include:
    - Main subject
    - Scene/environment
    - Style (e.g., realistic, 3D render, isometric, illustration)
    - Lighting and mood
    - Camera angle or composition (if relevant)
    - Be specific to the section content (no generic images)

    ## Do NOT:
    - Do NOT repeat similar prompts
    - Do NOT generate vague descriptions like "an image showing technology"
    - Do NOT invent section names (must match exactly)

    ## Output Format
    Return ONLY structured data following the schema:
    - prompt: detailed image generation prompt
    - after_section: exact section header

    ## Example
    Input Section:
    "## How Neural Networks Work"

    Output:
    {{
    "prompt": "A detailed 3D visualization of a neural network with multiple interconnected layers, glowing nodes and flowing data connections, futuristic digital environment, soft blue lighting, isometric perspective, high detail, modern AI concept art",
    "after_section": "## How Neural Networks Work"
    }}

    Generate 3-6 high-quality image placements depending on blog length.
    """

    user_prompt = """
    Analyze the following blog post and create a high-quality image placement plan.

    ## Blog Post:
    {blog_post}

    ## Instructions:
    - Carefully read the full blog
    - Identify the most important sections where visuals will add value
    - Generate 3-6 image placements (not too many, not too few)
    - Ensure each image is unique and tailored to its section

    Return only structured output.
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )

    chain = prompt | structured_model

    input_variables = {"blog_post": state.final_post}

    response = chain.invoke(input_variables)

    return {"image_plan": [item.model_dump() for item in response.image_plan]}


if __name__ == "__main__":
    state = BlogAgentState(
        prompt="Write a blog post about the benefits of using MCP servers for Minecraft.",
        final_post="""# Modern Minecraft Server Modding: Why \"MCP Servers\" Are Obsolete in 2026\n\n**A Technical Guide to Fabric, Forge, and Paper Frameworks for High-Performance Server Deployment**\n\nIn the landscape of **Minecraft server modding in 2026**, terminology often lags behind technical reality. A persistent misconception regarding \"MCP servers\" continues to confuse administrators, yet current infrastructure relies on distinct loader frameworks. For those deploying stable environments, distinguishing between historical development toolsets and modern server binaries is critical. \n\nThis guide details the correct deployment architectures for Forge, Fabric, and Paper, ensuring high-performance infrastructure without relying on deprecated concepts.\n\n## The End of an Era: Clarifying MCP's Historical Role\n\nThe term \"Mod Coder Pack\" (MCP) is frequently misunderstood as a server solution. Technically, MCP was a **client-side** decompilation and deobfuscation toolset used by mod developers to read obfuscated Minecraft code. It was never intended for server deployment. Understanding **MCP history** is vital to avoid configuring obsolete infrastructure.\n\n### Why MCP Is Irrelevant to Server Administration\n\nThe deprecation of **MCP** was solidified years prior to 2026, following Mojang's release of official mapping names. Continuing to reference MCP in an administrative context indicates a misunderstanding of the modern toolchain.\n\n*   **Historical Context:** MCP allowed developers to mod the client by renaming obfuscated methods.\n*   **Modern Reality:** Server administrators interact with compiled server jars (e.g., `forge-installer.jar`), not deobfuscation tools.\n*   **Administrative Impact:** No configuration or deployment step in 2026 requires MCP. Focus instead on loader compatibility and JVM arguments.\n\n### Toolchain Evolution: MCP vs. Modern Build Tools\n\nWhile MCP handled obfuscation historically, modern development relies on specialized build plugins. Administrators should recognize these terms when reviewing mod source requirements, though they are not installed on the server itself.\n\n| Feature | Mod Coder Pack (MCP) | Modern Toolchain (ForgeGradle/Fabric Loom) |\n| :--- | :--- | :--- |\n| **Primary Role** | Client-side deobfuscation | Build automation & dependency management |\n| **Server Usage** | None | None (Used for compiling mods) |\n| **Status** | **Deprecated** | **Active Standard** |\n| **Integration** | Manual patching | Gradle/Kotlin DSL pipelines |\n\n## Modern Server Frameworks Compared\n\nEffective **server framework selection** dictates infrastructure requirements and mod compatibility. In 2026, the ecosystem is divided primarily between Forge, Fabric, and Paper. It is crucial to distinguish between the server loader (runtime) and the build tools (development), such as **ForgeGradle** and **Fabric Loom**. These tools replace MCP's development role but do not run on production servers.\n\n### Forge: Stability for Large Modpacks\n\nForge remains the standard for extensive modpacks requiring deep game mechanics changes. Deployment relies on the official **Forge Installer**, not development tools.\n\n*   **Deployment Binary:** `forge-installer.jar` (generates the server jar).\n*   **Use Case:** Large-scale modpacks (100+ mods) requiring complex interoperability.\n*   **Performance:** Higher memory overhead; requires careful JVM tuning.\n\n### Fabric: Lightweight and Modular\n\nFabric utilizes a **Fabric Server Loader** designed for minimal overhead. It is preferred for performance-critical deployments where vanilla mechanics are largely preserved. Development for this ecosystem utilizes **Fabric Loom** to manage mappings.\n\n*   **Deployment Binary:** `fabric-server-launch.jar`.\n*   **Use Case:** Lightweight modding, performance enhancements, and snapshot support.\n*   **Performance:** Lower memory footprint and faster startup times compared to Forge.\n\n### Paper: Vanilla-Plus Performance\n\nPaper is not a mod loader but a high-performance server implementation. It is suitable for administrators seeking **Minecraft server performance improvements** without the complexity of mod loaders.\n\n*   **Deployment Binary:** `paperclip.jar`.\n*   **Use Case:** Vanilla servers requiring plugins, anti-grief tools, and optimization.\n*   **Compatibility:** Runs Bukkit/Spigot plugins; incompatible with Forge/Fabric mods unless using hybrid solutions (e.g., Magma/Folia), which are generally discouraged for stability.\n\n## Mod Compatibility in 2026\n\nCompatibility challenges have shifted from simple version mismatches to complex dependency conflicts within the loader ecosystem.\n\n1.  **Mixin Conflicts:** Fabric mods often use Mixins to inject code. Multiple mods attempting to modify the same class will cause startup crashes. Review crash logs for `MixinConflict` errors.\n2.  **API Version Locking:** Ensure all mods match the specific loader API version (e.g., Fabric API 0.90.0+ for MC 1.20.4). Mismatched API versions are a primary cause of initialization failures.\n3.  **Dependency Trees:** Use tools to visualize dependency trees. Hidden dependencies often break during updates if not explicitly tracked.\n4.  **NeoForge Transition:** The distinction between Forge and NeoForge is critical for 2026 accuracy. NeoForge became the primary continuation for versions **1.20.4 and higher**. Legacy Forge mods built for 1.20.1 or below are generally incompatible with NeoForge servers. Administrators must verify which framework their modpack targets, as binaries are not interchangeable across this version threshold.\n\n## Server Optimization and Performance Tuning\n\nAchieving stable tick rates requires precise infrastructure configuration. Generic advice often fails to address the specific demands of modded environments.\n\n### Memory Allocation Strategies\n\nJVM arguments must align with the loader's garbage collection needs. For 2026 versions, the following baselines are recommended:\n\n*   **Forge:** 6–8GB minimum for large packs. Use `-XX:+UseG1GC`.\n*   **Fabric:** 4–6GB typically suffices due to modular architecture.\n*   **Paper:** 2–4GB for vanilla-plus configurations.\n\nOver-allocation can cause long garbage collection pauses, leading to tick lag.\n\n### World Pre-Generation\n\nChunk generation is CPU-intensive. Pre-generating worlds mitigates lag spikes during player exploration. Tools like `Chunky` (for Paper) or loader-specific pre-gen mods should be executed before opening the server to the public.\n\n### Network and Tick Rate Management\n\nMaintain 20 TPS (ticks per second). Use monitoring tools to track entity counts and tile entity loads. High entity density in specific chunks often indicates mod compatibility issues or inefficient redstone contraptions.\n\n## Server Deployment Guide: Step-by-Step\n\nFollow this technical workflow for a successful **modded server setup**. Precision in this phase prevents runtime errors and security vulnerabilities.\n\n### Phase 1: Environment Preparation\n\n1.  Provision a VPS or dedicated machine with Linux (Ubuntu 22.04+ recommended).\n2.  Install **Java 21**. Older versions (Java 17) may lack optimizations required for recent Minecraft releases.\n3.  Configure `ufw` to allow only necessary ports (25565, SSH).\n4.  Create a dedicated non-root user for server processes.\n\n### Phase 2: Framework Installation\n\n1.  **Forge:** Download `forge-installer.jar`. Run `java -jar forge-installer.jar --installServer`.\n2.  **Fabric:** Download `fabric-server-launch.jar` and the corresponding `fabric-loader` JSON.\n3.  **Paper:** Download `paperclip.jar` directly from the build server.\n4.  Accept the EULA and configure `server.properties` before the first run.\n\n### Phase 3: Optimization and Testing\n\n1.  Configure JVM arguments in the start script (e.g., `start.sh`).\n2.  Install performance mods (e.g., Spark, Lithium) compatible with your loader.\n3.  Run stress tests using bot clients to simulate player load.\n4.  Record baseline TPS and memory usage metrics.\n\n### Phase 4: Go-Live and Monitoring\n\n1.  Schedule a maintenance window for the final cutover.\n2.  Enable remote monitoring (e.g., Prometheus/Grafana) for resource tracking.\n3.  Configure log rotation to prevent disk space exhaustion.\n4.  Communicate update schedules to the player base.\n\n## Hosting Considerations for Modded Servers\n\nResource allocation must account for the specific overhead of the chosen loader.\n\n### Resource Requirements\n\n| Server Type | RAM | CPU Cores | Storage |\n| :--- | :--- | :--- | :--- |\n| Fabric Server | 4GB | 2 (High Clock Speed) | 20GB NVMe |\n| Forge Server | 8GB | 4 (High Clock Speed) | 40GB NVMe |\n| Paper Server | 2GB | 2 | 15GB NVMe |\n\n### Managed vs. Self-Hosted\n\nManaged hosting provides automated backups and one-click installer support, reducing administrative overhead. Self-hosting offers full control over JVM flags and hardware but requires deep knowledge of Linux networking and security hardening.\n\n## Minecraft Server Migration Best Practices\n\nMigrating legacy worlds to modern frameworks requires data integrity checks.\n\n### Pre-Migration Checklist\n\n*   Create full backups of world data, configs, and operator lists.\n*   Audit mod lists for abandoned projects lacking 2026 updates.\n*   Validate world region files for corruption using region fixer tools.\n*   Establish a rollback snapshot before executing migration scripts.\n\n### Migration Execution\n\n1.  Deploy the new framework in a staging environment.\n2.  Copy world data and run a dry-run startup to check for missing blocks/items.\n3.  Update `server.properties` and `eula.txt`.\n4.  Swap DNS records only after staging validation passes.\n5.  Monitor logs for `WARN` entries regarding missing IDs during the first 24 hours.\n\n## Modding Best Practices 2026\n\nAdopt these engineering standards to maintain server health:\n\n*   **Version Control:** Store configuration files in Git repositories to track changes over time.\n*   **Documentation:** Maintain a public changelog detailing mod additions and removals.\n*   **Automated Testing:** Use CI/CD pipelines to test modpacks against clean server instances before deployment.\n*   **Security Audits:** Regularly scan mod files for known vulnerabilities or malicious code.\n*   **Backup Strategy:** Implement off-site backups with at least 7-day retention.\n\n## Troubleshooting Common Issues\n\n### Server Crashes on Startup\nAnalyze the `latest.log` or `crash-reports` folder. Look for `ModResolutionException` or `NoSuchMethodError`. These indicate incompatible mod versions or missing dependencies.\n\n### Performance Degradation Over Time\nInspect heap dumps using tools like VisualVM. Identify memory leaks caused by specific mods. Schedule automated restarts during low-traffic periods to clear memory.\n\n### Player Connection Issues\nVerify `server-ip` settings in `server.properties`. Ensure no ISP-level port blocking is occurring. Use `tcpdump` to analyze incoming connection packets if issues persist.\n\n## Conclusion\n\nThe modern Minecraft server landscape requires precise tool selection and accurate terminology. \"MCP servers\" are a historical misnomer; successful deployment relies on understanding the distinct roles of Forge, Fabric, and Paper. By utilizing Java 21, correct server installers, and rigorous compatibility testing, administrators can build resilient environments.\n\nFocus on loader-specific binaries rather than development toolsets. Prioritize stability through version locking and proactive monitoring. With the correct infrastructure, your server will remain performant and stable throughout 2026 and beyond.""",
    )

    output = image_planner_node(state)
    print(output)
