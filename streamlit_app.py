import streamlit as st
import sqlite3
import json
from langchain import PromptTemplate
from langchain.llms import OpenAI
import pandas as pd

api_key = st.secrets["api_key"]
st.set_page_config(page_title="AI Questions Generator", page_icon=":robot:")


template = """
    You are a great tutor. Take the following topic of interest from the student and the common core learning standard and create one free response question for the student. The Question should meet the following criteria:
        1. Question should assess the student’s knowledge of the Common Core learning standard given.
        2. Question should have the context required to answer it. 
        3. Assume that the student will be viewing the question and the student is not familiar with the details of the learning standard. So provide any additional context required for answering the question effectively.
        
    Also include a Rubric that will be used by the teacher for evaluating the student's responses. Do not provide rubric in a tabular format. Do not provide any feedback. Title the rubric as "How you will be evaluated". Keep rubric limited to 100 words.

    TOPIC: {topic}
    STANDARD: {standard}
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

    Provide your response in the following JSON format where each X represents the score of 1 to 5 of each element of the rubric above. Do not output any other information. Sample JSON response format:
        
        "question_topic": "France",
        "CCSS_standard" : "CCSS.ELA-LITERACY.W.4.1"
        "question_text": "What is the capital of France?",
        "rubric_text": " How you will be evaluated:
        Use of at least three different types of figurative language (similes, metaphors, personification)
        Accurate explanation of each type of figurative language used
        Clear and effective description of the player's skills and abilities
        Coherent organization and logical flow in the paragraph
        Correct grammar, punctuation, and spelling"
        "relevance_to_CCSS_standard": 5,
        "relevance_to_topic_of_interest": 4,
        "question_clarity_and_complexity": 3,
        "rubric_quality": 4,
        "creativity_and_engagement": 5,
        "bias_and_sensitivity": 4,
        "overall_quality": 3
        


    Here below are the inputs that were provided to the Question Generator Tool:
     TOPIC: {topic}
     STANDARD: {standard}

    Here below is the output of the question generator tool for your evaluation:
    
    OUTPUT: {output}
"""


standard_template = """Is {standard} a valid CCSS standard? Answer only YES or NO."""


answer_template = """You are the world best writing grader who is evaluating the writing of a student. Here below is the question and the rubrik that the student answered to:

{question}

Review the following writing by the student  and provide feedback to the student that is easily understandable by the student, and that gives them steps to improve on areas they need to work on. Also, rewrite the student's writing as part of the feedback to show what a great writing would look like. If the student did a great job, no need to rewrite and just give the feedback to the student. If you feel that the student needs to resubmit the writing, suggest the student do so. After that, separately, evaluate your feedback for clarity, constructiveness, Actionability and Supportiveness on a scale of 0-10 for quality assurance purposes. If you score your feedback less than 9, then re-write your feedback. Here below is a sample feedback for reference. Only provide the feedback in your response/completion as it will be sent to the student directly. Don't include any other information in your response. 


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

Student's answer begins: 
{answer}
"""


def load_LLM(openai_api_key):
    """Logic for loading the chain"""
    llm = OpenAI(model_name="gpt-3.5-turbo",temperature=0.6, openai_api_key=openai_api_key)
    return llm
    
counter=0
output_question=""
question_QA_result=""       
question_QA_response=""
llm = load_LLM(openai_api_key=api_key)

question_prompt = PromptTemplate(
    input_variables=["topic", "standard"],
    template=template
)


question_QA_prompt = PromptTemplate(
    input_variables=["topic", "standard", "output"],
    template=question_QA_template
)


standard_prompt = PromptTemplate(
    input_variables=["standard"],
    template=standard_template
)


answer_feedback_prompt = PromptTemplate(
    input_variables=["question","answer"],
    template=answer_template
)

def reset_question_input_page():
    st.session_state.topic_input = ""
    st.session_state.standard_input = ""
    

def default_question_input_page():
    st.session_state.topic_input = "Baseball"
    st.session_state.standard_input = "CCSS.ELA-LITERACY.W.4.9"    

def get_topic():
    input_topic = st.text_input(label="Topic of Interest", placeholder="Example: vacation, basketball, dog etc....", key="topic_input")
    if len(input_topic.split(" ")) > 6:
        st.write("Please enter a shorter topic. The maximum length is 6 words.")
        st.stop()
    return input_topic    

def get_standard():
    input_standard = st.text_input(label="Which [learning standard](http://www.thecorestandards.org/ELA-Literacy/W) would you like to test?", placeholder="Example: CCSS.ELA-LITERACY.W.4.1 etc....", key="standard_input")     
    return input_standard

def get_answer():
    input_answer = st.text_area(label=" ", placeholder="Type your response here...2000 words max", key="answer_input", height=500)
    if len(input_answer.split(" ")) > 2000:
        st.write("Please enter a shorter answer. The maximum length is 2000 words.")
        st.stop()
    return input_answer 


def generate_question():
    global counter
    global output_question
    global question_QA_response
    global option_count
    global standard_input
    global topic_input
    counter += 1
    prompt_with_inputs = question_prompt.format(topic=topic_input,standard=standard_input)
    output_question = llm(prompt_with_inputs)
    question_QA_prompt_with_inputs = question_QA_prompt.format(topic=topic_input,standard=standard_input,output=output_question)
    question_QA_response = llm(question_QA_prompt_with_inputs)
    question_QA_check(question_QA_response=question_QA_response)

def question_QA_check(question_QA_response):
    global question_QA_result
    global counter
    # Parse the JSON string into a dictionary
    data = json.loads(question_QA_response)
    
    if ( data['relevance_to_CCSS_standard'] < 4 or 
        data['relevance_to_topic_of_interest'] < 4 or
        data['question_clarity_and_complexity'] < 4 or 
        data['rubric_quality'] < 4 or 
        data['creativity_and_engagement'] < 4 or 
        data['bias_and_sensitivity'] < 4 or 
        data['overall_quality'] < 4 ):
        question_QA_result="Fail"
    else:
        question_QA_result="Pass"
    data['question_QA_result'] = question_QA_result
   # st.write("Attempt Number " + str(counter) + " " + question_QA_result)
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('question_QA_response.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()
    
    
    # Read the contents of the 'questions' table into a Pandas DataFrame
    query = "SELECT * FROM questions"
    df = pd.read_sql(query, conn)

    # Display the DataFrame using Streamlit
    st.write("Contents of the 'questions' table:")
    st.dataframe(df)
    # Drop the table named 'questions'
    #cursor.execute('DROP TABLE IF EXISTS questions')

    # Create a table to store the AI tool's output
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        question_topic TEXT,
        CCSS_standard TEXT,
        question_text TEXT,
        rubric_text TEXT,
        relevance_to_CCSS_standard INTEGER,
        relevance_to_topic_of_interest INTEGER,
        question_clarity_and_complexity INTEGER,
        rubric_quality INTEGER,
        creativity_and_engagement INTEGER,
        bias_and_sensitivity INTEGER,
        overall_quality INTEGER,
        question_QA_result TEXT,
        evaluated_at TIMESTAMP
    )
    ''')

    # Insert the JSON data into the table
    cursor.execute('''
    INSERT INTO questions (
        question_topic,
        CCSS_standard,
        question_text,
        rubric_text,
        relevance_to_CCSS_standard,
        relevance_to_topic_of_interest,
        question_clarity_and_complexity,
        rubric_quality,
        creativity_and_engagement,
        bias_and_sensitivity,
        overall_quality,
        question_QA_result,
        evaluated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
    ''', (
        data['question_topic'],
        data['CCSS_standard'],
        data['question_text'],
        data['rubric_text'],
        data['relevance_to_CCSS_standard'],
        data['relevance_to_topic_of_interest'],
        data['question_clarity_and_complexity'],
        data['rubric_quality'],
        data['creativity_and_engagement'],
        data['bias_and_sensitivity'],
        data['overall_quality'],
        data['question_QA_result'],
        datetime.now()
    ))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    if (data['question_QA_result']=="Fail" and counter<3):
        generate_question()

def start_generate():
    global topic_input
    global standard_input
    global counter
    global output_question
    global question_QA_result   
    global question_QA_response
    if topic_input:
        if not standard_input:
            st.warning('Please enter a writing standard. Instructions [here](http://www.thecorestandards.org/ELA-Literacy/W/4/)', icon="⚠️")
            return
        standard_prompt_with_inputs = standard_prompt.format(standard=standard_input)
        standard_response = llm(standard_prompt_with_inputs)
        if standard_response == "No" or standard_response == "NO" or standard_response == "No." or standard_response == "NO." :
            st.warning("It seems this learning standard isn't correct. Please re-enter. Reference [this link](http://www.thecorestandards.org/ELA-Literacy/W) if needed.",icon="⚠️")
            return
        counter=0
        output_question=""
        question_QA_result=""       
        question_QA_response=""
        generate_question()
        st.header("AI Questions Generator")
        st.markdown("### Your Question:")
        #st.write(question_QA_response)
        #st.write (counter)
        st.write(output_question)
        input_answer=get_answer()
        
        #return
        st.stop()

def load_first_input_page():
    global topic_input 
    global counter
    global output_question
    global question_QA_response
    global option_count
    global standard_input
    global topic_input
    st.header("AI Questions Generator")
    st.markdown("I am an AI Question Generator Tool. I take a student's topic of interest and Common Core Learning Standard as inputs and generate open ended questions for the student to answer. I am powered by [LangChain](https://langchain.com/) and [OpenAI](https://openai.com) ")
    st.markdown("## Enter your preferences")
    standard_input = get_standard()
    topic_input = get_topic()
    col3, col4, col5 = st.columns(3)    
    with col3:
        st.button("Generate Question",type='secondary', help="Click to generate a question", on_click=start_generate)
    with col4:
        st.button("Reset", type='secondary', help="Click to reset the page", on_click=reset_question_input_page)
    with col5:
        st.button("Default", type='secondary', help="Click to use default values", on_click=default_question_input_page)
        
if counter == 0: 
    load_first_input_page()