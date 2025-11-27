"""
Canvas Color Updater & Re-Brander
A Streamlit app for automating Canvas LMS course re-branding across LACCD colleges.
"""

import streamlit as st
import time
import re
from typing import Optional
from canvasapi import Canvas
from openai import OpenAI
from auth import render_login_form, is_authenticated, init_session_state

# Page config
st.set_page_config(
    page_title="Canvas Color Updater",
    page_icon="🎨",
    layout="wide"
)

# Initialize auth session state
init_session_state()

# LACCD Color Mapping - All 9 colleges + District
COLOR_MAP = {
    "LACCD (District)": {
        "primary": "#005a95",
        "secondary": "#00345f",
        "accent": "#bb9e6d",
        "full_name": "Los Angeles Community College District"
    },
    "ELAC (East LA)": {
        "primary": "#447D29",
        "secondary": "#33511D",
        "accent": "#FDB913",
        "full_name": "East Los Angeles College"
    },
    "LACC (LA City)": {
        "primary": "#C13C40",
        "secondary": "#305589",
        "accent": "#112844",
        "full_name": "Los Angeles City College"
    },
    "LAHC (LA Harbor)": {
        "primary": "#5F7FE2",
        "secondary": "#002663",
        "accent": "#FFC72C",
        "full_name": "Los Angeles Harbor College"
    },
    "LAMC (LA Mission)": {
        "primary": "#004590",
        "secondary": "#FF611A",
        "accent": "#718089",
        "full_name": "Los Angeles Mission College"
    },
    "LAPC (LA Pierce)": {
        "primary": "#BF2116",
        "secondary": "#1F1F1F",
        "accent": "#FFFFFF",
        "full_name": "Los Angeles Pierce College"
    },
    "LASC (LA Southwest)": {
        "primary": "#C5B358",
        "secondary": "#000000",
        "accent": "#FFFFFF",
        "full_name": "Los Angeles Southwest College"
    },
    "LATTC (LA Trade-Tech)": {
        "primary": "#562c82",
        "secondary": "#1c1c1c",
        "accent": "#aea4eb",
        "full_name": "Los Angeles Trade-Technical College"
    },
    "LAVC (LA Valley)": {
        "primary": "#00593F",
        "secondary": "#FFC72C",
        "accent": "#FFFFFF",
        "full_name": "Los Angeles Valley College"
    },
    "WLAC (West LA)": {
        "primary": "#4169E1",
        "secondary": "#003594",
        "accent": "#FFD700",
        "full_name": "West Los Angeles College"
    },
}

# Build color replacement maps
def build_color_maps():
    """Build mappings for primary->primary, secondary->secondary, accent->accent replacements."""
    all_primaries = {v["primary"].lower(): k for k, v in COLOR_MAP.items()}
    all_secondaries = {v["secondary"].lower(): k for k, v in COLOR_MAP.items()}
    all_accents = {v["accent"].lower(): k for k, v in COLOR_MAP.items()}
    return all_primaries, all_secondaries, all_accents

ALL_PRIMARIES, ALL_SECONDARIES, ALL_ACCENTS = build_color_maps()

def get_all_source_colors():
    """Get all known LACCD colors for detection."""
    colors = set()
    for college_data in COLOR_MAP.values():
        colors.add(college_data["primary"].lower())
        colors.add(college_data["secondary"].lower())
        colors.add(college_data["accent"].lower())
    return colors

ALL_SOURCE_COLORS = get_all_source_colors()


def replace_colors(html_content: str, target_college: str, replace_all: bool = False) -> tuple[str, list[str]]:
    """
    Replace colors with target college colors.

    If replace_all=False: Only replace known LACCD colors (primary->primary, etc.)
    If replace_all=True: Replace ALL hex colors with target primary color

    Returns: (updated_html, list of changes made)
    """
    if not html_content:
        return html_content, []

    changes = []
    target_colors = COLOR_MAP[target_college]

    # Find all hex colors in the content (case-insensitive)
    hex_pattern = r'#[0-9a-fA-F]{6}'

    def replace_color(match):
        color = match.group(0).lower()

        # Skip if it's already the target color
        if color == target_colors["primary"].lower():
            return match.group(0)
        if color == target_colors["secondary"].lower():
            return match.group(0)
        if color == target_colors["accent"].lower():
            return match.group(0)

        # Replace ALL colors mode
        if replace_all:
            changes.append(f"Color: {color} -> {target_colors['primary']}")
            return target_colors["primary"]

        # Check if it's a known LACCD color and map appropriately
        if color in ALL_PRIMARIES:
            source_college = ALL_PRIMARIES[color]
            if source_college != target_college:
                changes.append(f"Primary: {color} ({source_college}) -> {target_colors['primary']}")
                return target_colors["primary"]
        elif color in ALL_SECONDARIES:
            source_college = ALL_SECONDARIES[color]
            if source_college != target_college:
                changes.append(f"Secondary: {color} ({source_college}) -> {target_colors['secondary']}")
                return target_colors["secondary"]
        elif color in ALL_ACCENTS:
            source_college = ALL_ACCENTS[color]
            if source_college != target_college:
                changes.append(f"Accent: {color} ({source_college}) -> {target_colors['accent']}")
                return target_colors["accent"]

        return match.group(0)  # Return unchanged if not a known LACCD color

    updated_html = re.sub(hex_pattern, replace_color, html_content, flags=re.IGNORECASE)
    return updated_html, changes


def ai_polish_content(html_content: str, target_college: str, openrouter_key: str, model: str) -> str:
    """Use AI to replace college name references and fix any HTML issues."""
    if not html_content or not openrouter_key:
        return html_content

    target_full_name = COLOR_MAP[target_college]["full_name"]
    target_short = target_college.split(" ")[0]  # e.g., "LAPC"

    # Build list of other college names to replace
    other_colleges = []
    for key, data in COLOR_MAP.items():
        if key != target_college:
            other_colleges.append(key.split(" ")[0])  # Short name like "ELAC"
            other_colleges.append(data["full_name"])

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_key
    )

    system_prompt = f"""You are a Canvas LMS HTML expert. Your task is to:
1. Replace any references to other LACCD colleges with {target_full_name} (or {target_short} for short references)
2. Ensure the HTML structure remains valid
3. Preserve all existing formatting, styles, and structure
4. Only change college name references, nothing else

Other college names to look for and replace: {', '.join(other_colleges[:10])}

Return ONLY the updated HTML, no explanations or markdown code blocks."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": html_content}
            ],
            max_tokens=16000
        )
        result = response.choices[0].message.content

        # Clean up if AI wrapped in code blocks
        if result.startswith("```html"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]

        return result.strip()
    except Exception as e:
        st.warning(f"AI processing failed: {e}")
        return html_content


def process_course(canvas_url: str, api_token: str, course_id: int, target_college: str,
                   dry_run: bool = True, use_ai: bool = False, openrouter_key: str = None,
                   ai_model: str = None, replace_all: bool = False):
    """Process all content in a Canvas course."""

    try:
        canvas = Canvas(canvas_url, api_token)
        course = canvas.get_course(course_id)
        st.success(f"Connected to course: **{course.name}**")
    except Exception as e:
        st.error(f"Failed to connect to Canvas: {e}")
        return

    # Track statistics and updated item names
    stats = {
        "pages": {"total": 0, "updated": 0, "items": []},
        "assignments": {"total": 0, "updated": 0, "items": []},
        "discussions": {"total": 0, "updated": 0, "items": []},
        "announcements": {"total": 0, "updated": 0, "items": []},
        "quizzes": {"total": 0, "updated": 0, "items": []},
        "new_quizzes": {"total": 0, "updated": 0, "items": []},
        "syllabus": {"updated": False}
    }

    progress_bar = st.progress(0, text="Starting...")
    status_text = st.empty()

    # Process Pages (0-15%)
    try:
        status_text.text("📄 Scanning pages...")
        pages = list(course.get_pages())
        stats["pages"]["total"] = len(pages)

        for i, page in enumerate(pages):
            progress_bar.progress(int((i + 1) / max(len(pages), 1) * 15), text=f"📄 Processing page {i + 1}/{len(pages)}...")
            try:
                page_detail = course.get_page(page.url)
                if page_detail.body:
                    new_body, changes = replace_colors(page_detail.body, target_college, replace_all)
                    if use_ai and openrouter_key:
                        new_body = ai_polish_content(new_body, target_college, openrouter_key, ai_model)
                    if new_body != page_detail.body:
                        if not dry_run:
                            page_detail.edit(wiki_page={'body': new_body})
                            time.sleep(0.5)
                        stats["pages"]["updated"] += 1
                        stats["pages"]["items"].append(page.title)
            except:
                pass
    except:
        pass

    # Process Assignments (15-30%)
    try:
        status_text.text("📝 Scanning assignments...")
        assignments = list(course.get_assignments())
        stats["assignments"]["total"] = len(assignments)

        for i, assignment in enumerate(assignments):
            progress_bar.progress(15 + int((i + 1) / max(len(assignments), 1) * 15), text=f"📝 Processing assignment {i + 1}/{len(assignments)}...")
            try:
                if assignment.description:
                    new_desc, changes = replace_colors(assignment.description, target_college, replace_all)
                    if use_ai and openrouter_key:
                        new_desc = ai_polish_content(new_desc, target_college, openrouter_key, ai_model)
                    if new_desc != assignment.description:
                        if not dry_run:
                            assignment.edit(assignment={'description': new_desc})
                            time.sleep(0.5)
                        stats["assignments"]["updated"] += 1
                        stats["assignments"]["items"].append(assignment.name)
            except:
                pass
    except:
        pass

    # Process Discussions (30-45%)
    try:
        status_text.text("💬 Scanning discussions...")
        discussions = list(course.get_discussion_topics())
        stats["discussions"]["total"] = len(discussions)

        for i, discussion in enumerate(discussions):
            progress_bar.progress(30 + int((i + 1) / max(len(discussions), 1) * 15), text=f"💬 Processing discussion {i + 1}/{len(discussions)}...")
            try:
                if discussion.message:
                    new_msg, changes = replace_colors(discussion.message, target_college, replace_all)
                    if use_ai and openrouter_key:
                        new_msg = ai_polish_content(new_msg, target_college, openrouter_key, ai_model)
                    if new_msg != discussion.message:
                        if not dry_run:
                            discussion.update(message=new_msg)
                            time.sleep(0.5)
                        stats["discussions"]["updated"] += 1
                        stats["discussions"]["items"].append(discussion.title)
            except:
                pass
    except:
        pass

    # Process Announcements (45-60%)
    try:
        status_text.text("📢 Scanning announcements...")
        announcements = list(course.get_discussion_topics(only_announcements=True))
        stats["announcements"]["total"] = len(announcements)

        for i, announcement in enumerate(announcements):
            progress_bar.progress(45 + int((i + 1) / max(len(announcements), 1) * 15), text=f"📢 Processing announcement {i + 1}/{len(announcements)}...")
            try:
                if announcement.message:
                    new_msg, changes = replace_colors(announcement.message, target_college, replace_all)
                    if use_ai and openrouter_key:
                        new_msg = ai_polish_content(new_msg, target_college, openrouter_key, ai_model)
                    if new_msg != announcement.message:
                        if not dry_run:
                            announcement.update(message=new_msg)
                            time.sleep(0.5)
                        stats["announcements"]["updated"] += 1
                        stats["announcements"]["items"].append(announcement.title)
            except:
                pass
    except:
        pass

    # Process Syllabus (60-65%)
    try:
        status_text.text("📋 Scanning syllabus...")
        progress_bar.progress(60, text="📋 Processing syllabus...")
        syllabus_body = getattr(course, 'syllabus_body', None)
        if syllabus_body:
            new_syllabus, changes = replace_colors(course.syllabus_body, target_college, replace_all)
            if use_ai and openrouter_key:
                new_syllabus = ai_polish_content(new_syllabus, target_college, openrouter_key, ai_model)
            if new_syllabus != course.syllabus_body:
                if not dry_run:
                    course.edit(course={'syllabus_body': new_syllabus})
                    time.sleep(0.5)
                stats["syllabus"]["updated"] = True
    except:
        pass

    # Process Classic Quizzes (65-80%)
    try:
        status_text.text("❓ Scanning quizzes...")
        quizzes = list(course.get_quizzes())
        stats["quizzes"]["total"] = len(quizzes)

        for i, quiz in enumerate(quizzes):
            progress_bar.progress(65 + int((i + 1) / max(len(quizzes), 1) * 15), text=f"❓ Processing quiz {i + 1}/{len(quizzes)}...")
            try:
                if quiz.description:
                    new_desc, changes = replace_colors(quiz.description, target_college, replace_all)
                    if use_ai and openrouter_key:
                        new_desc = ai_polish_content(new_desc, target_college, openrouter_key, ai_model)
                    if new_desc != quiz.description:
                        if not dry_run:
                            quiz.edit(quiz={'description': new_desc})
                            time.sleep(0.5)
                        stats["quizzes"]["updated"] += 1
                        stats["quizzes"]["items"].append(quiz.title)
            except:
                pass
    except:
        pass

    # Process New Quizzes (80-95%)
    try:
        status_text.text("❓ Scanning new quizzes...")
        progress_bar.progress(80, text="❓ Processing new quizzes...")
        import requests
        new_quizzes_url = f"{canvas_url}/api/quiz/v1/courses/{course_id}/quizzes"
        headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.get(new_quizzes_url, headers=headers)

        if response.status_code == 200:
            new_quizzes = response.json()
            stats["new_quizzes"]["total"] = len(new_quizzes)

            for i, nq in enumerate(new_quizzes):
                progress_bar.progress(80 + int((i + 1) / max(len(new_quizzes), 1) * 15), text=f"❓ Processing new quiz {i + 1}/{len(new_quizzes)}...")
                if 'instructions' in nq and nq['instructions']:
                    new_instructions, changes = replace_colors(nq['instructions'], target_college, replace_all)
                    if use_ai and openrouter_key:
                        new_instructions = ai_polish_content(new_instructions, target_college, openrouter_key, ai_model)
                    if new_instructions != nq['instructions']:
                        if not dry_run:
                            update_url = f"{canvas_url}/api/quiz/v1/courses/{course_id}/quizzes/{nq['id']}"
                            requests.patch(update_url, headers=headers, json={"instructions": new_instructions})
                            time.sleep(0.5)
                        stats["new_quizzes"]["updated"] += 1
                        stats["new_quizzes"]["items"].append(nq.get('title', 'Untitled'))
    except:
        pass

    # Complete
    progress_bar.progress(100, text="Complete!")
    status_text.empty()

    # Show summary
    st.write("---")
    mode_label = "DRY RUN" if dry_run else "LIVE"

    # Helper function to render a category with expander
    def render_category(icon, name, data):
        label = f"{icon} {name}: {data['updated']}/{data['total']} updated"
        if data['items']:
            with st.expander(label):
                for item in data['items']:
                    st.write(f"• {item}")
        else:
            st.write(label)

    col1, col2 = st.columns(2)
    with col1:
        render_category("📄", "Pages", stats['pages'])
        render_category("📝", "Assignments", stats['assignments'])
        render_category("💬", "Discussions", stats['discussions'])
    with col2:
        render_category("📢", "Announcements", stats['announcements'])
        render_category("❓", "Quizzes", stats['quizzes'])
        render_category("❓", "New Quizzes", stats['new_quizzes'])
        if stats["syllabus"]["updated"]:
            st.write("📋 Syllabus: Updated")

    if dry_run:
        st.info(f"**{mode_label} complete!** No changes were written to Canvas.")
    else:
        st.success(f"**{mode_label} complete!** All changes have been saved.")


def render_color_preview(college: str):
    """Render a color preview for the selected college."""
    colors = COLOR_MAP[college]
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin: 10px 0;">
        <div style="background-color: {colors['primary']}; width: 60px; height: 40px; border-radius: 4px; border: 1px solid #ccc;" title="Primary"></div>
        <div style="background-color: {colors['secondary']}; width: 60px; height: 40px; border-radius: 4px; border: 1px solid #ccc;" title="Secondary"></div>
        <div style="background-color: {colors['accent']}; width: 60px; height: 40px; border-radius: 4px; border: 1px solid #ccc;" title="Accent"></div>
    </div>
    <div style="display: flex; gap: 10px; font-size: 12px; color: #666;">
        <div style="width: 60px; text-align: center;">Primary</div>
        <div style="width: 60px; text-align: center;">Secondary</div>
        <div style="width: 60px; text-align: center;">Accent</div>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.title("🎨 Canvas Color Updater")
    st.markdown("*Automate re-branding of Canvas LMS courses across LACCD colleges*")

    # Sidebar for configuration
    with st.sidebar:
        # Check authentication first (renders login form if needed)
        if not render_login_form():
            st.stop()  # Stop execution if not authenticated

        st.write("---")
        st.header("Canvas Connection")

        canvas_url = st.text_input(
            "Canvas base URL",
            value="https://ilearn.laccd.edu",
            help="Your Canvas instance URL"
        )

        api_token = st.text_input(
            "Canvas API Token",
            type="password",
            help="Generate this in Canvas: Account > Settings > New Access Token"
        )

        course_id = st.text_input(
            "Course ID",
            help="The numeric ID from your course URL"
        )

        st.write("---")
        st.header("Target Color Scheme")

        target_college = st.selectbox(
            "Normalize course colors TO:",
            options=list(COLOR_MAP.keys()),
            index=5,  # Default to LAPC
            help="All LACCD colors will be replaced with this college's colors"
        )

        render_color_preview(target_college)

        replace_all_colors = st.checkbox(
            "Replace ALL colors (not just LACCD colors)",
            value=False,
            help="When checked, replaces every hex color with the target primary color. Use this if the course has custom colors."
        )

        st.write("---")

        dry_run = st.checkbox(
            "Dry run (log changes but don't write to Canvas)",
            value=True,
            help="Preview changes before applying them"
        )

        st.write("---")
        st.header("AI Features (Optional)")

        use_ai = st.checkbox(
            "Enable AI text replacement",
            value=False,
            help="Use AI to replace college name references in text"
        )

        openrouter_key = None
        ai_model = None

        if use_ai:
            openrouter_key = st.text_input(
                "OpenRouter API Key",
                type="password",
                help="Get your key at openrouter.ai"
            )

            ai_model = st.selectbox(
                "AI Model",
                options=[
                    "openai/gpt-4o",
                    "openai/gpt-4o-mini",
                    "anthropic/claude-3.5-sonnet",
                    "anthropic/claude-3-haiku",
                    "google/gemini-pro-1.5"
                ],
                help="Select the AI model to use"
            )

        st.write("---")

        # Theme toggle
        theme_mode = st.selectbox(
            "Theme",
            options=["Light", "Dark"],
            index=0,
            help="Switch between light and dark mode"
        )

        # Apply theme via custom CSS
        if theme_mode == "Dark":
            st.markdown("""
            <style>
                .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                    background-color: #1a1a2e;
                    color: #eaeaea;
                }
                header[data-testid="stHeader"] {
                    background-color: #1a1a2e !important;
                }
                .stSidebar, section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
                    background-color: #16213e !important;
                }
                .stTextInput > div > div > input,
                .stSelectbox > div > div > div {
                    background-color: #1f4068;
                    color: #eaeaea;
                }
                .stMarkdown, .stText, p, span, label, .stSubheader {
                    color: #eaeaea !important;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #eaeaea !important;
                }
            </style>
            """, unsafe_allow_html=True)

        st.write("---")

        run_button = st.button(
            "🚀 Run color update",
            type="primary",
            use_container_width=True
        )

    # Main content area
    if run_button:
        if not api_token:
            st.error("Please enter your Canvas API Token")
            return
        if not course_id:
            st.error("Please enter a Course ID")
            return

        try:
            course_id_int = int(course_id)
        except ValueError:
            st.error("Course ID must be a number")
            return

        if use_ai and not openrouter_key:
            st.error("Please enter your OpenRouter API Key to use AI features")
            return

        mode = "DRY RUN" if dry_run else "LIVE"
        color_mode = "ALL colors" if replace_all_colors else "LACCD colors only"
        st.info(f"Running update on course {course_id}, replacing {color_mode} to **{target_college}** ({mode})...")

        process_course(
            canvas_url=canvas_url,
            api_token=api_token,
            course_id=course_id_int,
            target_college=target_college,
            dry_run=dry_run,
            use_ai=use_ai,
            openrouter_key=openrouter_key,
            ai_model=ai_model,
            replace_all=replace_all_colors
        )

        if dry_run:
            st.info("👆 Review the changes above, then uncheck 'Dry run' and run again to apply.")
        else:
            st.success("Color update completed.")
    else:
        # Show instructions when not running
        st.markdown("""
        ## How to Use

        1. **Enter your Canvas credentials** in the sidebar
           - Your Canvas base URL (default is LACCD's iLearn)
           - Your API token (generate in Canvas: Account → Settings → New Access Token)
           - The Course ID you want to update

        2. **Select the target college** whose colors you want to apply

        3. **Run a dry run first** to preview changes without modifying anything

        4. **Uncheck dry run** and run again to apply the changes

        ---

        ### What This Tool Does

        - Scans all Pages, Assignments, Discussions, Announcements, Syllabus, and Quizzes
        - Finds hex color codes belonging to any LACCD college
        - Replaces them with the equivalent color from your target college:
          - Primary colors → Target Primary
          - Secondary colors → Target Secondary
          - Accent colors → Target Accent

        ### AI Features (Optional)

        Enable AI to also replace text references to college names (e.g., "Welcome to ELAC" → "Welcome to Pierce College").

        ---

        ### Color Reference
        """)

        # Show all college colors
        cols = st.columns(2)
        for i, (college, colors) in enumerate(COLOR_MAP.items()):
            with cols[i % 2]:
                st.markdown(f"**{college}**")
                st.markdown(f"""
                <div style="display: flex; gap: 5px; margin-bottom: 15px;">
                    <div style="background-color: {colors['primary']}; width: 40px; height: 25px; border-radius: 3px; border: 1px solid #ccc;" title="{colors['primary']}"></div>
                    <div style="background-color: {colors['secondary']}; width: 40px; height: 25px; border-radius: 3px; border: 1px solid #ccc;" title="{colors['secondary']}"></div>
                    <div style="background-color: {colors['accent']}; width: 40px; height: 25px; border-radius: 3px; border: 1px solid #ccc;" title="{colors['accent']}"></div>
                    <span style="font-size: 11px; color: #888;">{colors['primary']} | {colors['secondary']} | {colors['accent']}</span>
                </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
