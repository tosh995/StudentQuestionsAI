import os
import streamlit as st
import OpenAI

openai.api_key = os.getenv("API_KEY")

def main():
    st.title('GPT-4 Question Generator')

    # Inputs for writing standard name and topic of interest
    standard_name = st.text_input("Enter the writing standard name:")
    topic_interest = st.text_input("Enter a topic of personal interest:")

    # Button to trigger the question generation
    if st.button('Generate Question'):
        if standard_name and topic_interest:
            # Create a prompt for GPT-4
            prompt = f"Generate a question about {topic_interest} that tests the {standard_name} writing standard."

            # Make a request to the OpenAI API
            response = openai.Completion.create(
                engine="text-davinci-003",  # as of my knowledge cutoff, this was the latest engine
                prompt=prompt,
                temperature=0.6,
                max_tokens=60
            )

            # Extract the question
            question = response.choices[0].text.strip()

            # Output the question
            st.text_area("Generated Question:", question, height=200)
        else:
            st.write('Please enter both the writing standard name and topic of interest.')

if __name__ == "__main__":
    main()
