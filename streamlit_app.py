import streamlit as st
import sqlite3
import json
from langchain import PromptTemplate
from langchain.llms import OpenAI

api_key = st.secrets["api_key"]

template = """
    You are a tutor for a 4th grade student. Take the following topic of interest from the student and the common core learning standard and create {count} free response question(FRQ) for the student. 
    
    Each FRQ should meet the following criteria:
        1. FRQ should assess the student’s knowledge of the Common Core learning standard
        2. FRQ should have the context required to answer the FRQ. 
        3. Assume that the student will be viewing the question and the student is not familiar with the details of the learning standard. So provide any additional context to the question.
        
    Also include a Rubric that will be used by the teacher for evaluating the student's responses. Do not provide rubric in a tabular format. Do not provide any feedback.

    TOPIC: {topic}
    STANDARD: {standard}
"""

QA_template = """
    You are a reviewer of the questions generated by a Question Generator. The Question Generator takes the Common core learning standard and a student's interest as input and generates questions to assess the student's knowledge of that standard. The Question generator tool also provides a rubrik for evaluating each question generated by the tool. The question generator can generate upto 5 quesions at a time. 
    
    Your job is to evaluate the output of the question generator (Questions and the corresponding rubriks) and ensure that they meet or exceed quality standards using the following rubrik.
    
    Rubrik for evaluation


    1. Relevance to CCSS Writing Standard:
        5: Directly aligns with the specified CCSS standard, demonstrating a clear understanding of the standard's requirements.
        4: Mostly aligns with the specified CCSS standard, with minor deviations.
        3: Somewhat aligns with the specified CCSS standard but lacks depth or specificity.
        2: Limited alignment with the specified CCSS standard; significant deviations present.
        1: Does not align with the specified CCSS standard.
    2. Relevance to Topic of Interest:
        5: Highly relevant to the specified topic, demonstrating deep engagement and understanding.
        4: Mostly relevant to the specified topic, with minor unrelated elements.
        3: Moderately relevant to the specified topic but lacks focus.
        2: Limited relevance to the specified topic; significant unrelated elements.
        1: Not relevant to the specified topic.
    3. Question Clarity and Complexity:
        5: Question is clear, concise, and appropriately complex for the intended audience.
        4: Question is mostly clear and appropriately complex, with minor ambiguities.
        3: Question is somewhat clear but may be too simple or too complex.
        2: Question is unclear or poorly structured, leading to confusion.
        1: Question is incomprehensible or entirely inappropriate in complexity.
    4. Rubric Quality:
        5: Provided rubric is clear, comprehensive, and directly aligned with the question.
        4: Provided rubric is mostly clear and aligned with the question, with minor issues.
        3: Provided rubric is somewhat clear but lacks depth or alignment with the question.
        2: Provided rubric is unclear or poorly structured.
        1: Provided rubric is missing or entirely inappropriate.
    5. Creativity and Engagement:
        5: Question is highly engaging and encourages creative thinking.
        4: Question is engaging and somewhat encourages creative thinking.
        3: Question is moderately engaging but lacks creativity.
        2: Question is unengaging or does not encourage creative thinking.
        1: Question is dull and does not engage the student at all.
    6. Bias and Sensitivity:
        5: Question is free from bias and is culturally sensitive.
        4: Question has minor biases or insensitivities but is mostly appropriate.
        3: Question has noticeable biases or insensitivities.
        2: Question has significant biases or insensitivities.
        1: Question is highly biased or culturally insensitive.

    Provide your response in the following JSON format where each X represents the score of 1 to 5 of each element of the rubrik above. Do not output any other information. Sample JSON response format:
        
        "question_topic": "France",
        "CCSS_standard" : "CCSS.ELA-LITERACY.W.4.1"
        "question_text": "What is the capital of France?",
        "relevance_to_CCSS_standard": 5,
        "relevance_to_topic_of_interest": 4,
        "question_clarity_and_complexity": 3,
        "rubric_quality": 4,
        "creativity_and_engagement": 5,
        "bias_and_sensitivity": 4,
        "overall_quality": 3
        "evaluated_at": "2023-08-07T12:34:56"
        


    Here below are the inputs that were provided to the Question Generator Tool:
     TOPIC: {topic}
     STANDARD: {standard}
     QUESTIONS TO BE GENERATED: {count}

    Here below is the output of the question generator tool for your evaluation:
    
    OUTPUT: {output}
"""

    



prompt = PromptTemplate(
    input_variables=["topic", "standard", "count"],
    template=template,
)


QA_prompt = PromptTemplate(
    input_variables=["topic", "standard", "count", "output"],
    template=QA_template,
)



def load_LLM(openai_api_key):
    """Logic for loading the chain"""
    llm = OpenAI(model_name="gpt-3.5-turbo",temperature=0.6, openai_api_key=openai_api_key)
    return llm
    


st.set_page_config(page_title="AI Questions Generator", page_icon=":robot:")
st.header("AI Questions Generator")


st.markdown("I am an AI Question Generator Tool for 4th grade students. I take a student's topic of interest and Common Core Learning Standard as inputs and generate up to 5 open ended questions for the student to answer. I am powered by [LangChain](https://langchain.com/) and [OpenAI](https://openai.com) ")


st.markdown("## Enter your preferences")


col1, col2 = st.columns(2)

with col1:
    option_standard = st.selectbox('Which [learning standard](http://www.thecorestandards.org/ELA-Literacy/W/4/) would you like to test?',
    ('CCSS.ELA-LITERACY.W.4.1', 'CCSS.ELA-LITERACY.W.4.2', 'CCSS.ELA-LITERACY.W.4.3', 'CCSS.ELA-LITERACY.W.4.4','CCSS.ELA-LITERACY.W.4.5','CCSS.ELA-LITERACY.W.4.6','CCSS.ELA-LITERACY.W.4.7', 'CCSS.ELA-LITERACY.W.4.8','CCSS.ELA-LITERACY.W.4.9', 'CCSS.ELA-LITERACY.W.4.10'))

with col2:
    option_count = st.selectbox('How many questions would you like to generate?',('1','2','3','4','5'))

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


    
def generate_question():
    global counter
    global output_questions
    global QA_result
    counter += 1
    llm = load_LLM(openai_api_key=api_key)
    prompt_with_inputs = prompt.format(topic=topic_input,standard=option_standard,count=option_count)
    output_questions = llm(prompt_with_inputs)
    QA_prompt_with_inputs = QA_prompt.format(topic=topic_input,standard=option_standard,count=option_count,output=output_questions)
    QA_Response = llm(QA_prompt_with_inputs)
    QA_check(QA_Response=QA_Response)


def QA_check(QA_Response):
    global QA_result
    # Parse the JSON string into a dictionary
    data = json.loads(QA_Response)
    
    if ( data['relevance_to_CCSS_standard'] < 3 or 
        data['relevance_to_topic_of_interest'] < 3 or
        data['question_clarity_and_complexity'] < 3 or 
        data['rubric_quality'] < 3 or 
        data['creativity_and_engagement'] < 3 or 
        data['bias_and_sensitivity'] < 3 or 
        data['overall_quality'] < 3 ):
        QA_result="Fail"
    else:
        QA_result="Pass"
    data['QA_result'] = QA_result
    st.write(QA_result)
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('QA_Response.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()

    # Create a table to store the AI tool's output
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        question_topic TEXT,
        CCSS_standard TEXT,
        question_text TEXT,
        relevance_to_CCSS_standard INTEGER,
        relevance_to_topic_of_interest INTEGER,
        question_clarity_and_complexity INTEGER,
        rubric_quality INTEGER,
        creativity_and_engagement INTEGER,
        bias_and_sensitivity INTEGER,
        overall_quality INTEGER,
        QA_result TEXT,
        evaluated_at TIMESTAMP
    )
    ''')

    # Insert the JSON data into the table
    cursor.execute('''
    INSERT INTO questions (
        question_topic,
        CCSS_standard,
        question_text,
        relevance_to_CCSS_standard,
        relevance_to_topic_of_interest,
        question_clarity_and_complexity,
        rubric_quality,
        creativity_and_engagement,
        bias_and_sensitivity,
        overall_quality,
        QA_result,
        evaluated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    ''', (
        data['question_topic'],
        data['CCSS_standard'],
        data['question_text'],
        data['relevance_to_CCSS_standard'],
        data['relevance_to_topic_of_interest'],
        data['question_clarity_and_complexity'],
        data['rubric_quality'],
        data['creativity_and_engagement'],
        data['bias_and_sensitivity'],
        data['overall_quality'],
        data['QA_result'],
        data['evaluated_at']
    ))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    If (data['QA_result']=="Fail" and counter<3)
        generate_question()



if topic_input:
    if not option_standard:
        st.warning('Please select a writing standard. Instructions [here](http://www.thecorestandards.org/ELA-Literacy/W/4/)', icon="⚠️")
        st.stop()
    counter=0
    output_questions=""
    QA_result=""            
    generate_question()
    st.markdown("### Your Question(s):")
    st.write(QA_Response)
    st.write (counter)
    st.write(output_questions)
 
