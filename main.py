import openai

tool_request = "Please write a python tool that will help me analyze a spreadsheet of data that has 3 columns, email, name, and funnel phase."

client = openai.Client()

## I have a triangle of agents
python_tool_developer_agent_id = "asst_6wETukcfY4rQCYx8Mr44SUMh"
critical_agent_id = "asst_CknX6IzcAX4khLQTevuBd3iV"
alignment_agent_id = "asst_CgSpumbHrbALNaW8PZ0HzatQ"

tool_developer = client.beta.assistants.retrieve(python_tool_developer_agent_id)
critical_agent = client.beta.assistants.retrieve(critical_agent_id)
alignment_agent = client.beta.assistants.retrieve(alignment_agent_id)

thread = client.beta.threads.create()

def send_message_and_wait_for_response(message_text, thread, assistant):
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )

    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print(messages)
    return messages

## first, ask the first agent for the python tool
send_message_and_wait_for_response(tool_request, thread, tool_developer)

## next, ask the critical agent to review and iterate on the tool
send_message_and_wait_for_response("Please critique the script written above, and iterate on that script.", thread, critical_agent)


## finally, ask the alignment agent to review the output
send_message_and_wait_for_response("Please review and iterate on the script written above, and ensure it's aligned with our values.", thread, alignment_agent)

## do that whole thing 3 more times 
for i in range(3):
    ## first, ask the first agent for the python tool
    send_message_and_wait_for_response("Please apply any remaining feedback, complete any todos left in the code, and iterate on any remaining items left uncompleted.", thread, tool_developer)
    

    ## next, ask the critical agent to review and iterate on the tool
    send_message_and_wait_for_response("Please critique the script written above, and iterate on that script.", thread, critical_agent)

    ## finally, ask the alignment agent to review the output
    send_message_and_wait_for_response("Please review and iterate on the script written above, and ensure it's aligned with our values.", thread, alignment_agent)

## finally, extract the output of the final script
send_message_and_wait_for_response("Please return only the script written above, and nothing else, this output will be written directly to a file so please do not provide any other text, or the fencing (eg: ```python) on the code block.", thread, alignment_agent)
