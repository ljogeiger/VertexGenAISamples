from google import genai
from google.genai import types
import base64

def generate():
  client = genai.Client(
      vertexai=True,
      project="sandbox-aiml",
      location="global",
  )


  model = "gemini-2.5-flash-preview-04-17"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text="""solve x^2 + 4x + 4 = 0""")
      ]
    ),
  ]
  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    seed = 0,
    max_output_tokens = 8192,
    response_modalities = ["TEXT"],
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
    system_instruction=[types.Part.from_text(text="""Provide step by step guidance on your thought process""")],
    thinking_config=types.ThinkingConfig(
        include_thoughts=True,
    )
  )

  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    print(chunk.text, end="")
    print(chunk)

generate()

""" EXAMPLE RESPONSE
Okay, let's solve the quadratic equation x² + 4x + 4 = 0 step by step.

**Goal:** Find the value(s) of x that make this equation true.

**Method 1: Factoring (Recognizing a Perfect Square Trinomial)**

1.  **Analyze the equation:**
    *   We have a quadratic equation in the form ax² + bx + c = 0.
    *   Here, a = 1, b = 4, and c = 4.

2.  **Look for patterns:**
    *   Notice that the first term, x², is a perfect square (x)².
    *   Notice that the last term, 4, is a perfect square (2)².
    *   Now, check if the middle term, 4x, is twice the product of the square roots of the first and last terms: 2 * (x) * (2) = 4x.
    *   Yes, it matches! This means the expression x² + 4x + 4 is a perfect square trinomial.
    *   Specifically, it's in the form (A + B)² = A² + 2AB + B², where A = x and B = 2.

3.  **Factor the perfect square trinomial:**
    *   So, x² + 4x + 4 can be factored as (x + 2)².
    *   Our equation becomes: (x + 2)² = 0

4.  **Solve for x:**
    *   Take the square root of both sides:
        √(x + 2)² = √0
        x + 2 = 0
    *   Subtract 2 from both sides:
        x = -2

    This means x = -2 is a repeated root (or a root with multiplicity 2).

**Method 2: Using the Quadratic Formula**

1.  **Identify a, b, and c:**
    *   From x² + 4x + 4 = 0:
        *   a = 1 (coefficient of x²)
        *   b = 4 (coefficient of x)
        *   c = 4 (constant term)

2.  **Write down the quadratic formula:**
    *   x = [-b ± √(b² - 4ac)] / 2a

3.  **Substitute the values of a, b, and c into the formula:**
    *   x = [-4 ± √(4² - 4 * 1 * 4)] / (2 * 1)

4.  **Simplify the expression under the square root (the discriminant):**
    *   x = [-4 ± √(16 - 16)] / 2
    *   x = [-4 ± √0] / 2

5.  **Simplify further:**
    *   x = [-4 ± 0] / 2

6.  **Calculate the two possible values for x (which will be the same in this case because the discriminant is 0):**
    *   x = (-4 + 0) / 2 = -4 / 2 = -2
    *   x = (-4 - 0) / 2 = -4 / 2 = -2

    Both paths lead to the same solution.

**Conclusion:**
The solution to the equation x² + 4x + 4 = 0 is **x = -2**.
This is a single, repeated real root.
"""
