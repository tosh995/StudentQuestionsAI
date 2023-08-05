import streamlit as st
from langchain import PromptTemplate
from langchain.llms import OpenAI

template = """

    You are a tutor for a 4th grade student. Take the following topic of interest from the student and the common core learning standard and create 5 questions. Each question should be in the following format:

    
    - Introduction
    - Context about the question
    - Open ended question
    - A rubrik to help the student understand how their answer to the question will be evaluated
    
  
    
    
    TOPIC: {topic}
    STANDARD: {standard}

    
    Your Questions Response:
"""

prompt = PromptTemplate(
    input_variables=["topic", "standard"],
    template=template,
)

def load_LLM(openai_api_key):
    """Logic for loading the chain you want to use should go here."""
    # Make sure your openai_api_key is set as an environment variable
    llm = OpenAI(temperature=.7, openai_api_key=openai_api_key)
    return llm

st.set_page_config(page_title="AI Questions Generator", page_icon=":robot:")
st.header("Questions Generator")

col1, col2 = st.columns(2)

with col1:
    st.markdown("This is an AI Question Generator Tool. \n\n It takes a students topic of interest and Common core learning standard as an input and generates 5 open ended questions for the student to answer. This toolis powered by [LangChain](https://langchain.com/) and [OpenAI](https://openai.com) ")

with col2:
    st.image(image='AIGenerator.jpg', width=500, caption='AI Tutor')

st.markdown("## Enter your topic of interest")

def get_api_key():
    input_text = st.text_input(label="OpenAI API Key ",  placeholder="Ex: sk-2twmA8tfCb8un4...", key="openai_api_key_input")
    return input_text

openai_api_key = get_api_key()


    

option_standard = st.selectbox('Which learning standard would you like to test?',
    ('CCSS.ELA-LITERACY.W.4.1', 'CCSS.ELA-LITERACY.W.4.2', 'CCSS.ELA-LITERACY.W.4.3', 'CCSS.ELA-LITERACY.W.4.4','CCSS.ELA-LITERACY.W.4.5','CCSS.ELA-LITERACY.W.4.6','CCSS.ELA-LITERACY.W.4.7', 'CCSS.ELA-LITERACY.W.4.8','CCSS.ELA-LITERACY.W.4.9', 'CCSS.ELA-LITERACY.W.4.10'))

def get_topic():
    input_topic = st.text_input(label="Topic of Interest", placeholder="Example: vacation, basketball, dog etc....", key="topic_input")
    return input_topic

topic_input = get_topic()

if len(topic_input.split(" ")) > 6:
    st.write("Please enter a shorter topic. The maximum length is 6 words.")
    st.stop()

def update_text_with_example():
    print ("in updated")
    st.session_state.topic_input = "basketball"

st.button("*See An Example*", type='secondary', help="Click to see an example of the email you will be converting.", on_click=update_text_with_example)

st.markdown("### Your Converted Email:")

if email_input:
    if not openai_api_key:
        st.warning('Please insert OpenAI API Key. Instructions [here](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key)', icon="⚠️")
        st.stop()

    llm = load_LLM(openai_api_key=openai_api_key)

    prompt_with_email = prompt.format(tone=option_tone, dialect=option_dialect, email=email_input)

    formatted_email = llm(prompt_with_email)

    st.write(formatted_email)