import streamlit as st
import sqlite3
import json
from langchain import PromptTemplate
from langchain.llms import OpenAI
import pandas as pd
from datetime import datetime
import re

api_key = st.secrets["api_key"]
st.set_page_config(page_title="AI Questions Generator", page_icon=":robot:")


question_template = """
    You are a great tutor. Take the following topic of interest from the student and the common core learning standard and create one free response question for the student. The Question should meet the following criteria:
        1. Question should assess the student’s knowledge of the Common Core learning standard given.
        2. Question should have the context required to answer it. 
        3. Assume that the student will be viewing the question and the student is not familiar with the details of the learning standard. So provide any additional context required for answering the question effectively.
        
    Also include a Rubric that will be used by the teacher for evaluating the student's responses. Do not provide rubric in a tabular format. Do not provide any feedback. Title the rubric as "How you will be evaluated". Keep rubric limited to 100 words.

    TOPIC: {topic}
    CCSS_standard: {CCSS_standard}
"""

question_QA_template = """
    You are a reviewer of the questions generated by a Question Generator. The Question Generator takes the Common core learning standard and a student's interest as input and generates questions to assess the student's knowledge of that standard. The Question generator tool also provides a rubric for evaluating each question generated by the tool. The question generator can generate upto 5 quesions at a time. 
    
    Your job is to evaluate the output of the question generator (Question and the corresponding rubric).
    
    Rubric for evaluation:

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

    Provide your response in the following JSON format. Do not output any other information. Sample JSON response format:
        
        "topic": "France",
        "CCSS_standard" : "CCSS.ELA-LITERACY.W.4.1"
        "question": "What is the capital of France?",
        "rubric": " How you will be evaluated:
        Use of at least three different types of figurative language (similes, metaphors, personification)
        Accurate explanation of each type of figurative language used
        Clear and effective description of the player's skills and abilities
        Coherent organization and logical flow in the paragraph
        Correct grammar, punctuation, and spelling",
        "relevance_to_CCSS_standard": 5,
        "relevance_to_topic_of_interest": 4,
        "question_clarity_and_complexity": 3,
        "rubric_quality": 4,
        "creativity_and_engagement": 5,
        "bias_and_sensitivity": 4,
        "overall_quality": 3
        


    Here below are the inputs that were provided to the Question Generator Tool:
     TOPIC: {topic}
     CCSS_standard: {CCSS_standard}

    Here below is the output of the question generator tool for your evaluation:
    
    OUTPUT: {question}
"""


CCSS_standard_template = """Is {CCSS_standard} a valid CCSS standard? Answer only YES or NO."""


feedback_template = """You are the world best writing grader who is evaluating the writing of a student. Here below is the question and the rubrik that the student answered to:


Question Topic: {topic}
CCSS Standard: {CCSS_standard}
*******question and rubric starts here *************
{question}
*******question and rubric ends here *************
Review the following writing by the student  and provide feedback to the student that is easily understandable by the student, and that gives them steps to improve on areas they need to work on. Also, rewrite the student's writing as part of the feedback to show what a great writing would look like. If the student did a great job, no need to rewrite and just give the feedback to the student. If you feel that the student needs to resubmit the writing, suggest the student do so. After that, evaluate your feedback for clarity, constructiveness, Actionability and Supportiveness on a scale of 0-10 for quality assurance purposes. If you score your feedback less than 9, then re-write your feedback. Here below is a sample feedback for reference. Only provide the final feedback in your response/completion as it will be sent to the student directly. Don't include any other information in your response. 

***********Sample feedback starts here *************
“Hello,

Excellent job on expressing your enthusiasm for "Belly Up" by Stuart Gibbs. I can see that you've shared your opinion and gave us a summary of the story. Let's find ways to make your writing even better!

1. **Introduction:** You've done a nice job introducing your favorite book and why you like it. Try to introduce your topic in a more engaging way by combining the first few sentences. For instance, "My favorite book ever is 'Belly Up' by Stuart Gibbs, a suspenseful tale that starts with a mystery: the death of a hippo named Henry."

2. **Supporting Reasons:** You've shared that the interesting topic, suspense, and humor are why you enjoy the book. Well done! Let's give specific examples to support these points and help the reader understand what makes these elements so good.

3. **Linking Words:** You started off strong with the linking word 'Because'. Incorporate more of these into your writing to seamlessly connect your opinion and reasons.

4. **Conclusion:** Your concluding statement encourages others to read the book, which is excellent! In your conclusion, try to summarize why you think the book is worth reading.

5. **Other Feedback:** Remember to check your spelling and grammar. For example, 'Their' should be 'there', and 'breathe' should be 'breath'. Also, always capitalize names such as 'FunJungle'.

Let's see how your revised writing could look:

"My all-time favorite book is 'Belly Up' by Stuart Gibbs, a suspenseful tale that begins with a mysterious event: the death of a hippo named Henry. The book becomes even more exciting when Teddy, a kid living in FunJungle, steps up to investigate. He is not alone in this thrilling journey; his friend Summer assists him, and together they encounter numerous suspects and dangers. The suspense is so well-crafted that I found myself holding my breath towards the end! Apart from suspense, the book is filled with humor. For instance, the line 'He genuinely enjoyed shooting poop at people' had me laughing out loud! To conclude, with its captivating plot, well-crafted suspense, and sprinkles of humor, 'Belly Up' is a must-read. I highly recommend it!"

Good work! I am seeing great improvement in your writing day-by-day. Keep writing and improving.

Regards,
Your AI Writing Coach”

***********Sample feedback ends here *************

***********Student's answer begins here **********
{answer}
"""

feedback_QA_template = """
You are the reviewer of the feedback generated by an AI tool for the answer submitted by a student to a question. The question was generated based on a CCSS standard and a topic of interest given by the student. The Question given to the student also had a rubric for evaluating the student's answer. Your job is to evaluate the feedback generated on student's answer using the following rubric.

********Rubric to Assess Feedback Generated by the Tool******
1. **Relevance to Student's Response (0-5 points)**
    5: Feedback directly addresses all aspects of the student's response, providing specific insights and guidance.
    4: Feedback addresses most aspects of the student's response, with some areas lacking detail.
    3: Feedback addresses some aspects of the student's response but misses significant areas.
    2: Feedback is somewhat relevant but lacks depth and misses key aspects of the student's response.
    1: Feedback has minimal relevance to the student's response.
    0: Feedback is not relevant to the student's response.
2. **Alignment with CCSS Standard (0-5 points)**
    5: Feedback is fully aligned with the CCSS standard, reflecting specific learning objectives.
    4: Feedback is mostly aligned with the CCSS standard, with minor deviations.
    3: Feedback is somewhat aligned with the CCSS standard but lacks consistency.
    2: Feedback shows limited alignment with the CCSS standard.
    1: Feedback has minimal alignment with the CCSS standard.
    0: Feedback does not align with the CCSS standard.
3. **Clarity and Understandability (0-5 points)**
    5: Feedback is clear, concise, and easily understood by the student.
    4: Feedback is mostly clear with minor ambiguities.
    3: Feedback is somewhat clear but may be confusing in parts.
    2: Feedback is unclear in significant areas, leading to potential misunderstandings.
    1: Feedback is largely unclear and difficult to understand.
    0: Feedback is not understandable.
4. **Constructiveness and Encouragement (0-5 points)**
    5: Feedback is highly constructive, offering specific suggestions for improvement and encouraging growth.
    4: Feedback is constructive with some areas of encouragement.
    3: Feedback offers some constructive comments but lacks encouragement.
    2: Feedback has limited constructiveness and may be discouraging.
    1: Feedback is not constructive and lacks encouragement.
    0: Feedback is negative and discouraging.
5. **Accuracy and Fairness (0-5 points)**
    5: Feedback accurately assesses the student's response and is fair in its evaluation.
    4: Feedback is mostly accurate with minor inconsistencies.
    3: Feedback is somewhat accurate but may be biased or unfair in parts.
    2: Feedback has significant inaccuracies or biases.
    1: Feedback is largely inaccurate and unfair.
    0: Feedback is completely inaccurate and biased.
***********rubric ends here********

Question Topic: {topic}
CCSS Standard: {CCSS_standard}

***The question and the rubric that was given to the student starts here***
{question}
***The question and the rubric that was given to the student ends here***

***Answer provided by the student starts here ***
{answer}
***Answer provided by the student ends here ***

***The feedback to be evaluated starts here***
{feedback} 

Provide your response in the following JSON format. Do not output any other information. Sample JSON response format:

        
        "feedback_text": " Excellent job on expressing your enthusiasm for "Belly Up" by Stuart Gibbs. I can see that you've shared your opinion and gave us a summary of the story. Let's find ways to make your writing even better!
        1. **Introduction:** You've done a nice job introducing your favorite book and why you like it. Try to introduce your topic in a more engaging way by combining the first few sentences. For instance, "My favorite book ever is 'Belly Up' by Stuart Gibbs, a suspenseful tale that starts with a mystery: the death of a hippo named Henry."
        2. **Supporting Reasons:** You've shared that the interesting topic, suspense, and humor are why you enjoy the book. Well done! Let's give specific examples to support these points and help the reader understand what makes these elements so good.
        3. **Linking Words:** You started off strong with the linking word 'Because'. Incorporate more of these into your writing to seamlessly connect your opinion and reasons.
        4. **Conclusion:** Your concluding statement encourages others to read the book, which is excellent! In your conclusion, try to summarize why you think the book is worth reading.
        5. **Other Feedback:** Remember to check your spelling and grammar. For example, 'Their' should be 'there', and 'breathe' should be 'breath'. Also, always capitalize names such as 'FunJungle'.",
        "relevance_to_students_response": 4,
        "alignment_with_CCSS_standard": 5,
        "clarity_and_understadability": 3,
        "constructiveness_and_encouragement": 4,
        "accuracy_and_fairness": 5,
        "overall_quality": 3
"""

def load_LLM(openai_api_key):
    """Logic for loading the chain"""
    llm = OpenAI(model_name="gpt-3.5-turbo",temperature=0.6, openai_api_key=openai_api_key)
    return llm

#counters for how many QA attempts has been made

if 'question_QA_counter' not in st.session_state:
    st.session_state.question_QA_counter = 0
if 'feedback_QA_counter' not in st.session_state:
    st.session_state.feedback_QA_counter = 0

#counters for how many max QA attempts to make before showing the last results
if 'max_question_QA_counter' not in st.session_state:
    st.session_state.max_question_QA_counter=3
if 'max_feedback_QA_counter' not in st.session_state:    
    st.session_state.max_feedback_QA_counter=3

#if 'topic' not in st.session_state:
#    st.session_state.topic = ""
#if 'CCSS_standard' not in st.session_state:
#    st.session_state.CCSS_standard = ""
if 'question' not in st.session_state:
    st.session_state.question = ""
if 'question_QA_result' not in st.session_state:
    st.session_state.question_QA_result = ""
if 'answer' not in st.session_state:
    st.session_state.answer = ""
if 'feedback' not in st.session_state:
    st.session_state.feedback = ""
if 'feedback_QA_result' not in st.session_state:
    st.session_state.feedback_QA_result = ""
if 'feedback_QA_response' not in st.session_state:
    st.session_state.feedback_QA_response = ""
#variables to store the ID values for foreign key references in various tables
if 'question_last_id' not in st.session_state:
    st.session_state.question_last_id = ""
if 'answer_last_id' not in st.session_state:
    st.session_state.answer_last_id = ""    

if "session_status" not in st.session_state:
    st.session_state.session_status='Topic Input'


llm = load_LLM(openai_api_key=api_key)

#langchain prompt templates below

CCSS_standard_prompt = PromptTemplate(
    input_variables=["CCSS_standard"],
    template=CCSS_standard_template
)

question_prompt = PromptTemplate(
    input_variables=["topic", "CCSS_standard"],
    template=question_template
)

question_QA_prompt = PromptTemplate(
    input_variables=["topic", "CCSS_standard", "question"],
    template=question_QA_template
)

feedback_prompt = PromptTemplate(
    input_variables=["topic","CCSS_standard","question","answer"],
    template=feedback_template
)

feedback_QA_prompt = PromptTemplate(
    input_variables=["topic","CCSS_standard","question","answer","feedback"],
    template=feedback_QA_template
)

#function to reset the input screen
def reset_question_input_page():
    st.session_state.topic1 = ""
    st.session_state.CCSS_standard1 = ""
    
#function to apply default values to input screen, facilitates testing and development
def default_question_input_page():
    st.session_state.topic1 = "Baseball"
    st.session_state.CCSS_standard1 = "CCSS.ELA-LITERACY.W.4.9"   
    #st.write("Default Updated")

#function to get topic from the input screen
def get_topic():
    input_topic = st.text_input(label="Topic of Interest", placeholder="Example: vacation, basketball, dog etc....", key="topic1")
    if len(input_topic.split(" ")) > 6:
        st.write("Please enter a shorter topic. The maximum length is 6 words.")
        st.stop()
    return input_topic    

#function to get the CCSS Standard from the input screen
def get_CCSS_standard():
    input_CCSS_standard = st.text_input(label="Which [learning standard](http://www.thecorestandards.org/ELA-Literacy/W) would you like to test?", placeholder="Example: CCSS.ELA-LITERACY.W.4.1 etc....", key="CCSS_standard1")     
    return input_CCSS_standard


#function to get the student's answer from the input screen
def get_answer():
    input_answer = st.text_area(label=" ", placeholder="Type your response here...2000 words max", key="answer_input", height=500)
    st.session_state.session_status='Answer Ready'
    if len(input_answer.split(" ")) > 2000:
        st.write("Please enter a shorter answer. The maximum length is 2000 words.")
        return
    return input_answer 


#function to insert the Question and its QA information into Question table
def db_insert_question(question_QA_response,question_QA_result):
    data = json.loads(question_QA_response)

    #global question
    # st.write("Attempt Number " + str(counter) + " " + question_QA_result)
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('studentquestionsai.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()
    
    
    # Read the contents of the 'questions' table into a Pandas DataFrame
    #query = "SELECT * FROM questions"
    #df = pd.read_sql(query, conn)

    # Display the DataFrame using Streamlit
    #st.write("Contents of the 'questions' table:")
    #st.dataframe(df)
    # Drop the table named 'questions'
    #cursor.execute('DROP TABLE IF EXISTS questions')

    # Create a table to store the AI tool's output
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        CCSS_standard TEXT,
        question TEXT,
        rubric TEXT,
        relevance_to_CCSS_standard INTEGER,
        relevance_to_topic_of_interest INTEGER,
        question_clarity_and_complexity INTEGER,
        rubric_quality INTEGER,
        creativity_and_engagement INTEGER,
        bias_and_sensitivity INTEGER,
        overall_quality INTEGER,
        question_QA_result TEXT,
        load_date_time TIMESTAMP
    )
    ''')
    # Insert the JSON data into the table
    cursor.execute('''
    INSERT INTO question (
        topic,
        CCSS_standard,
        question,
        rubric,
        relevance_to_CCSS_standard,
        relevance_to_topic_of_interest,
        question_clarity_and_complexity,
        rubric_quality,
        creativity_and_engagement,
        bias_and_sensitivity,
        overall_quality,
        question_QA_result,
        load_date_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?)
    ''', (
        data['topic'],
        data['CCSS_standard'],
        data['question'],
        data['rubric'],
        data['relevance_to_CCSS_standard'],
        data['relevance_to_topic_of_interest'],
        data['question_clarity_and_complexity'],
        data['rubric_quality'],
        data['creativity_and_engagement'],
        data['bias_and_sensitivity'],
        data['overall_quality'],
        question_QA_result,
        datetime.now()
    ))
    
    st.session_state.question_last_id = cursor.lastrowid  #capture lastrowid to store as foreign key reference in other tables

    # Commit the changes and close the connection
    conn.commit()
    conn.close()



#function to insert the answer into answer table
def db_insert_answer():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('studentquestionsai.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()
    
    
    
    # Create a table to store the answer
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS answer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER,
        answer TEXT,
        load_date_time TIMESTAMP
    )
    ''')
    # Insert the answer into the table
    cursor.execute('''
    INSERT INTO answer (
        question_id,
        answer,
        load_date_time
    ) VALUES (?, ?, ?)
    ''', (
    st.session_state.question_last_id,
    st.session_state.answer,
    datetime.now()
    ))
    
    st.session_state.answer_last_id = cursor.lastrowid  #capture lastrowid to store as foreign key reference in other tables

    # Commit the changes and close the connection
    conn.commit()
    conn.close()



#function to load the feedback into the feedback table
def db_insert_feedback(feedback_QA_response,feedback_QA_result):
    data = json.loads(feedback_QA_response)

    conn = sqlite3.connect('studentquestionsai.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()
    
    
    # Drop the table named 'feedback'
    #cursor.execute('DROP TABLE IF EXISTS feedback')

    # Create a table to store the feedback and its QA information
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER 
        answer_id INTEGER,
        feedback TEXT,
        relevance_to_students_response INTEGER,
        alignment_with_CCSS_standard INTEGER,
        clarity_and_understadability INTEGER,
        constructiveness_and_encouragement INTEGER,
        accuracy_and_fairness INTEGER,
        overall_quality INTEGER,
        feedback_QA_result TEXT,
        load_date_time TIMESTAMP
    )
    ''')


    # Insert the JSON data into the table
    cursor.execute('''
    INSERT INTO feedback (
        question_id, 
        answer_id,
        feedback,
        relevance_to_students_response,
        alignment_with_CCSS_standard,
        clarity_and_understadability,
        constructiveness_and_encouragement,
        accuracy_and_fairness,
        overall_quality,
        feedback_QA_result,
        load_date_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        st.session_state.question_last_id,
        st.session_state.answer_last_id,
        data['feedback'],
        data['relevance_to_students_response'],
        data['alignment_with_CCSS_standard'],
        data['clarity_and_understadability'], 
        data['constructiveness_and_encouragement'], 
        data['accuracy_and_fairness'],
        data['overall_quality'],
        feedback_QA_result,
        datetime.now()
    ))
    # Commit the changes and close the connection
    conn.commit()
    conn.close()




#function to generate question 
def generate_question():
    prompt_with_inputs = question_prompt.format(topic=st.session_state.topic,CCSS_standard=st.session_state.CCSS_standard)
    #call LLM to generate question
    st.session_state.question = llm(prompt_with_inputs)
    #starting Question QA process
    question_QA_prompt_with_inputs = question_QA_prompt.format(topic=st.session_state.topic,CCSS_standard=st.session_state.CCSS_standard,question=st.session_state.question)
    #call LLM to generate QA for question
    st.session_state.question_QA_response = llm(question_QA_prompt_with_inputs)
    question_QA_check(question_QA_response=st.session_state.question_QA_response)

def question_QA_check(question_QA_response):
    st.session_state.question_QA_counter += 1
    # Parse the JSON string into a dictionary
    cleaned_string = re.sub(r'[\x00-\x1F]+', '', question_QA_response)
    data = json.loads(cleaned_string)
    #data = json.loads(question_QA_response)
    if ( data['relevance_to_CCSS_standard'] < 4 or 
        data['relevance_to_topic_of_interest'] < 4 or
        data['question_clarity_and_complexity'] < 4 or 
        data['rubric_quality'] < 4 or 
        data['creativity_and_engagement'] < 4 or 
        data['bias_and_sensitivity'] < 4 or 
        data['overall_quality'] < 4 ):
        st.session_state.question_QA_result="Fail"
    else:
        st.session_state.question_QA_result="Pass"
    db_insert_question(question_QA_response,st.session_state.question_QA_result) #load the question with its QA information to Question table
   
   #continue generating question if the QA fails until we reach the max limit 
    if (st.session_state.question_QA_result=="Fail" and st.session_state.question_QA_counter<st.session_state.max_question_QA_counter):
        generate_question()

#process to generate question starts on clining the generate question button 
def generate_question_button_click():
    if st.session_state.topic:
        if not st.session_state.CCSS_standard:
            st.warning('Please enter a writing CCSS standard. Instructions [here](http://www.thecorestandards.org/ELA-Literacy/W/4/)', icon="⚠️")
            return
        CCSS_standard_prompt_with_inputs = CCSS_standard_prompt.format(CCSS_standard=st.session_state.CCSS_standard)
        st.session_state.CCSS_standard_response = llm(CCSS_standard_prompt_with_inputs)
        if st.session_state.CCSS_standard_response == "No" or st.session_state.CCSS_standard_response == "NO" or st.session_state.CCSS_standard_response == "No." or st.session_state.CCSS_standard_response == "NO." :
            st.warning("It seems this learning standard isn't correct. Please re-enter. Reference [this link](http://www.thecorestandards.org/ELA-Literacy/W) if needed.",icon="⚠️")
            st.write(st.session_state.CCSS_standard)
            return
        st.session_state.question_QA_counter=0
        st.session_state.question=""
        st.session_state.question_QA_result=""       
        st.session_state.question_QA_response=""
        generate_question()
        st.session_state.session_status='Answer Input'
        load_question_display()
        
        
def load_question_display():        
        st.header("AI Questions Generator")
        st.markdown("### Your Question:")
        #st.write(question_QA_response)
        #st.write (counter)
        st.write(st.session_state.question)
        #st.session_state.answer=get_answer()
        #load_question_display()
        st.session_state.answer = st.text_area(label=" ",on_change=False, placeholder="Type your response here...2000 words max", key="answer_input", height=500)
        #if len(input_answer.split(" ")) > 2000:
            #st.write("Please enter a shorter answer. The maximum length is 2000 words.") 
        st.button("Submit Answer", help="Click to submit your answer", on_click=generate_feedback_button_click)


#first function that loads the welcome screen for the tool
def load_welcome_page():
    st.session_state.session_status='Topic Input'
    st.header("AI Questions Generator1")
    st.markdown("I am an AI Question Generator Tool. I take a student's topic of interest and Common Core Learning Standard as inputs and generate open ended questions for the student to answer. I am powered by [LangChain](https://langchain.com/) and [OpenAI](https://openai.com) ")
    st.markdown("## Enter your preferences")
    st.session_state.CCSS_standard = get_CCSS_standard()
    st.session_state.topic = get_topic()
    col3, col4, col5 = st.columns(3)    
    with col3:
        st.button("Generate Question",type='secondary', help="Click to generate a question", on_click=generate_question_button_click)
    with col4:
        st.button("Reset", type='secondary', help="Click to reset the page", on_click=reset_question_input_page)
    with col5:
        st.button("Default", type='secondary', help="Click to use default values", on_click=default_question_input_page)


#function to respond to submission of the feedback_QA_counter Answer by the student on clicking the submit button 
def generate_feedback_button_click():
    st.session_state.session_status='Show Feedback'
    st.write(st.session_state.session_status)
    st.write(st.session_state.answer)
    if st.session_state.answer:
        #st.write(st.session_state.answer)
        #load the answer into the answer table
        db_insert_answer()  
        st.write("db insert complete")
        #start the feedback process
        st.session_state.feedback_QA_counter =0
        generate_feedback()
        
        
        
        
def generate_feedback():
    feedback_prompt_with_inputs = feedback_prompt.format(topic=st.session_state.topic,CCSS_standard=st.session_state.CCSS_standard,question=st.session_state.question,answer=st.session_state.answer)
    st.write("now calling LLM")
    #call LLM to generate feedback
    feedback = llm(feedback_prompt_with_inputs)
    feedback_QA_prompt_with_inputs = feedback_QA_prompt.format(topic=st.session_state.topic,CCSS_standard=st.session_state.CCSS_standard,question=st.session_state.question,answer=st.session_state.answer,feedback=st.session_state.feedback)
    #Call LLM to generate QA on Feedback 
    st.session_state.feedback_QA_response = llm(feedback_QA_prompt_with_inputs)
    st.write("showing feedback QA response")
    st.write("st.session_state.feedback_QA_response is " + st.session_state.feedback_QA_response)
    feedback_QA_check(feedback_QA_response=st.session_state.feedback_QA_response)


def feedback_QA_check(feedback_QA_response):
    st.session_state.feedback_QA_counter +=1
    # Parse the JSON string into a dictionary
    cleaned_string = re.sub(r'[\x00-\x1F]+', '', feedback_QA_response)
    data = json.loads(cleaned_string)
    #data = json.loads(feedback_QA_response) 
    if ( data['relevance_to_students_response'] < 4 or 
        data['alignment_with_CCSS_standard'] < 4 or
        data['clarity_and_understadability'] < 4 or 
        data['constructiveness_and_encouragement'] < 4 or 
        data['accuracy_and_fairness'] < 4 or 
        data['overall_quality'] < 4 ): 
        st.session_state.feedback_QA_result="Fail"
    else:
        st.session_state.feedback_QA_result="Pass"
    db_insert_feedback(feedback_QA_response,st.session_state.feedback_QA_result)
    st.write(" feedback DB insert complete ")
    st.write(" feedback status " + st.session_state.feedback_QA_result)

    if (st.session_state.feedback_QA_result=="Fail" and st.session_state.feedback_QA_counter<st.session_state.max_feedback_QA_counter):
        st.write(" regenerating feedback ")
        generate_feedback()
    st.session_state.session_status='Show Feedback'    
    st.write(" feedback ready to show ")
    load_feedback_display()
    
def load_feedback_display():    
    st.header("AI Questions Generator")
    st.markdown("### Your Question:")
    #st.write(question_QA_response)
    st.write (st.session_state.feedback_QA_counter)
    st.write(st.session_state.question)
    st.write(st.session_state.feedback)
    st.button("Get Another Question", help="Click to get another question", on_click=load_welcome_page)
    #return
    #st.stop()
    
   

        
if st.session_state.session_status == 'Topic Input': 
    load_welcome_page()
elif st.session_state.answer:
    load_question_display()
elif st.session_state.session_status=='Show Feedback':    
    load_feedback_display()