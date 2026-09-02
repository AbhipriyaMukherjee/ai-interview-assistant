import pdfplumber


pdf_path = "tests/fixtures/portfolios/Persona_2_Over_Achiever.pdf"


with pdfplumber.open(pdf_path) as pdf:

    print("Number of pages:", len(pdf.pages))

    for page_number, page in enumerate(pdf.pages):

        print("\n====================")
        print(f"PAGE {page_number + 1}")
        print("====================")


        # 1. Extract normal text
        text = page.extract_text()

        print("\nRAW TEXT:")
        print(text)


        # 2. Extract detailed character information
        print("\nCHARACTER METADATA SAMPLE:")

        chars = page.chars

        print("Total characters:", len(chars))

        for char in chars[:20]:
            print(char)


        # 3. Group by lines
        print("\nLINES WITH FONT SIZE:")

        words = page.extract_words(
            extra_attrs=[
                "fontname",
                "size"
            ]
        )


        for word in words:
            print(
                f"""
Text: {word['text']}
Font: {word['fontname']}
Size: {word['size']}
Position: x={word['x0']} y={word['top']}
"""
            )