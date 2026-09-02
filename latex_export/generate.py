import os 

def generate_latex(resume):
    """
    Converts the structured resume JSON into a LaTeX document.
    """

    contact = resume.get("contact", "")
    summary = resume.get("summary", "")
    skills = resume.get("skills", [])
    experience = resume.get("experience", [])
    projects = resume.get("projects", [])

    latex = r"""\documentclass[11pt]{article}

\usepackage[margin=0.7in]{geometry}
\usepackage{enumitem}


\setlength{\parindent}{0pt}
\setlist[itemize]{noitemsep, topsep=2pt}

\begin{document}

\begin{center}
    {\Large \textbf{Resume}}\\
    """ + contact + r"""
\end{center}

\vspace{5pt}

\section*{Summary}
""" + summary + r"""

\section*{Skills}
""" + ", ".join(skills) + r"""

\section*{Experience}
\begin{itemize}
"""

    for item in experience:
        latex += r"\item " + item + "\n"

    latex += r"""
\end{itemize}

\section*{Projects}
\begin{itemize}
"""

    for project in projects:
        latex += r"\item " + project + "\n"

    latex += r"""
\end{itemize}

\end{document}
"""

    output_path = os.path.join(os.path.dirname(__file__), "resume.tex")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(latex)

    return output_path

def compile_pdf(tex_path):
    """
    Converts the LaTeX .tex file into a PDF using pdflatex.
    """

    pdflatex_path = r"C:\Users\KIIT0001\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"

    output_dir = os.path.dirname(tex_path)

    os.system(
        f'"{pdflatex_path}" -interaction=nonstopmode '
        f'-output-directory="{output_dir}" "{tex_path}"'
    )

    pdf_path = os.path.splitext(tex_path)[0] + ".pdf"

    return pdf_path

if __name__ == "__main__":
    resume_data = {
        "contact": "john@example.com | (555) 123-4567",
        "summary": "Experienced software developer who builds highly efficient REST endpoints in Flask.",
        "skills": ["Python", "Flask", "SQL"],
        "experience": [
            "Built core REST APIs handling 10k daily users.",
            "Optimized query execution time by 30%."
        ],
        "projects": [
            "Created AI Mock Interview Tool with real-time feedback."
        ]
    }

    tex_path = generate_latex(resume_data)
    pdf_path = compile_pdf(tex_path)

    print("LaTeX resume generated successfully!")
    print("PDF generated at:", pdf_path)
