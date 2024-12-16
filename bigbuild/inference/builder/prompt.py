"""prompt templates"""

lazy_prompt = """You are diligent and tireless!
You always COMPLETELY edit all the build file!
"""

instruction = """\
Edit the build files to include all necessary dependency-related configurations \
to ensure the project builds and runs successfully. Output a copy of each build file.

You will receive four sections of information to configure dependencies in build files:
1. **Project Structure**: A tree structure representing the project's layout.
2. **Environment Specifications**: Details about the operating system and language SDK where the project will run.
3. **Source Code**: The full source code of the project.
4. **Build Files**: Build files missing dependency configurations, which you will need to update.

!Important Notes:
1. The project may include multiple build files. Ensure you update all of them with the necessary dependency configurations.
2. Only edit the files listed in the "Build Files" section.
3. Limit your edits strictly to dependency configurations within the build files.

To suggest changes to a file you MUST return the entire content of the updated file.
You MUST use this *file listing* format:

path/to/filename.js
```
// entire file content ...
// ... goes in between
```

Every *file listing* MUST use this format:
- First line: the filename with any originally provided path; no extra markup, punctuation, comments, etc. **JUST** the filename with path.
- Second line: opening ```
- ... entire content of the file ...
- Final line: closing ```

To suggest changes to a file you MUST return a *file listing* that contains the entire content of the file.
*NEVER* skip, omit or elide content from a *file listing* using "..." or by adding comments like "... rest of code..."!
Create a new file you MUST return a *file listing* which includes an appropriate filename, including any appropriate path.
"""

task_information_template = """\
--- Begin of Project Structure ---
{project_structure}
--- End of Project Structure ---

--- Begin of Environment Specifications ---
{env_specs}
--- End of Environment Specifications ---

--- Begin of Source Code ---
{src_section}
--- End of Source Code ---

--- Begin of Build Files ---
{build_section}
--- End of Build Files ---"""


file_template = """\
{path}
```
{content}
```"""
