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

    return latex


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

    latex_code = generate_latex(resume_data)

    with open("latex_export/resume.tex", "w", encoding="utf-8") as file:
     file.write(latex_code)

    print("LaTeX resume generated successfully!")