import os
import re
from huggingface_hub import InferenceClient
from langchain_core.runnables import RunnableLambda, RunnableConfig
from agent.state import BlogAgentState
from agent.config import HUGGINGFACEHUB_API_TOKEN


def _image_generation_logic(state: BlogAgentState, config: RunnableConfig) -> dict:
    """
    Internal logic for image generation. Including config in args allows
    LangSmith to track this as a proper node execution.
    """
    # 1. Initialize the Client
    client = InferenceClient(
        provider="nscale",
        api_key=HUGGINGFACEHUB_API_TOKEN,
    )

    # Setup directories
    IMAGE_DIR = "agent/generated_images"
    os.makedirs(IMAGE_DIR, exist_ok=True)

    current_post = state.final_post

    for i, entry in enumerate(state.image_plan):
        try:
            print(f"Generating image {i} for: {entry['after_section']}...")

            # 2. Generate the Image
            image = client.text_to_image(
                entry["prompt"],
                model="stabilityai/stable-diffusion-xl-base-1.0",
                width=1280,
                height=720,
            )

            # 3. Save the image locally
            file_name = f"blog_img_{i}.png"
            file_path = os.path.join(IMAGE_DIR, file_name)
            image.save(file_path)

            # 4. Integrate into Markdown with size control
            image_tag = f'\n\n<div align="center"><img src="generated_images/{file_name}" alt="Blog Image" width="800" /></div>\n\n'

            current_post = current_post.replace(
                entry["after_section"], f"{entry['after_section']}{image_tag}"
            )

        except Exception as e:
            print(f"Error generating image {i}: {e}")

    # 5. Save the final .md file
    safe_name = (
        re.sub(r"[^\w\s-]", "", state.prompt).strip().lower().replace(" ", "_")[:30]
    )
    output_path = f"agent/final_blog_post_{safe_name}.md"

    with open(output_path, "w", encoding="utf-8") as md_file:
        md_file.write(current_post)

    print(f"--- Final blog post saved to: {output_path} ---")

    # We return the updated state keys
    return {"final_post": current_post}


# 6. Create the Traceable Runnable
# This name 'image_generation_node' is what will appear in LangSmith

image_generation_node = RunnableLambda(_image_generation_logic).with_config(
    run_name="image_generation_node"
)