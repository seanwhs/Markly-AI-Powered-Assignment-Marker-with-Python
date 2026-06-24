# rubrics.py
# This module defines the scoring criteria for different academic domains.
# These rubrics are used by the AI to ensure consistent and transparent 
# evaluation of student assignments.

# A dictionary mapping subject names to their respective scoring rubrics.
# Each rubric item includes its weight in points and a brief definition 
# of what the evaluator should assess.
RUBRICS = {
    # Math rubric prioritizes the accuracy of steps and results.
    "Mathematics": """
1. Calculation Accuracy (5 points)
   - Correctness of numerical computation and results

2. Correct Methodology (3 points)
   - Use of appropriate formulas, steps, and logical approach

3. Final Answer Correctness (2 points)
   - Accuracy of final stated result with proper form
""",

    # English rubric focuses on communication quality and argumentative depth.
    "English": """
1. Grammar & Syntax (4 points)
   - Sentence structure, spelling, and grammatical correctness

2. Clarity & Flow (3 points)
   - Logical progression of ideas and readability

3. Argument Strength (3 points)
   - Quality of reasoning, evidence, and coherence of argument
""",

    # Science rubric emphasizes scientific literacy and logical interpretation.
    "Science": """
1. Conceptual Understanding (4 points)
   - Correctness of scientific principles and explanations

2. Application of Knowledge (3 points)
   - Ability to apply concepts to given scenarios or experiments

3. Scientific Reasoning (3 points)
   - Logical interpretation of results and cause-effect relationships
""",

    # Programming rubric balances functional correctness with software design standards.
    "Programming": """
1. Correctness (4 points)
   - Code produces correct output and meets requirements

2. Code Quality & Readability (3 points)
   - Clean structure, naming conventions, and maintainability

3. Efficiency & Optimization (2 points)
   - Appropriate use of algorithms and performance considerations

4. Design & Structure (1 point)
   - Use of functions, modularity, and good software design principles
"""
}