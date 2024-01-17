import openai
import os
import json
import subprocess

tool_request = "Please use the netstat and ps commands to determine what processes are running on the system, and what ports they are listening on, then write a script to handle the outputs given the results of the tool use. You have access to two functions, run_netstat and run_ps, which will run the netstat and ps commands respectively, and return the output. Please use the tools provided with the run before you begin working on any code. You do definately have access to tools, please do not say that you do not have the ability to run tools, or that there has been a misunderstanding, there has not been any misunderstanding, you have been configured with the tools for sure."

client = openai.Client()

## I have a triangle of agents
python_tool_developer_agent_id = "asst_6wETukcfY4rQCYx8Mr44SUMh"
critical_agent_id = "asst_CknX6IzcAX4khLQTevuBd3iV"
alignment_agent_id = "asst_CgSpumbHrbALNaW8PZ0HzatQ"

tool_developer = client.beta.assistants.retrieve(python_tool_developer_agent_id)
critical_agent = client.beta.assistants.retrieve(critical_agent_id)
alignment_agent = client.beta.assistants.retrieve(alignment_agent_id)

thread = client.beta.threads.create()


def run_netstat(arguments):
    print(arguments)
    ## run the netstat command locally, and return the output
    completed_process = subprocess.run(["netstat", arguments], capture_output=True, text=True)
    ## get the output 
    output = completed_process.stdout
    
    return output

def run_ps(arguments):
    print(arguments)
    ## run the ps command locally, and return the output
    completed_process = subprocess.run(["ps", arguments], capture_output=True, text=True)
    ## get the output 
    output = completed_process.stdout
    
    return output

tools = {
    "run_netstat": run_netstat,
    "run_ps": run_ps
}

def send_message_and_wait_for_response(message_text, thread, assistant):
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        tools=[{
            "name": "run_netstat",
            "description": "Run the netstat command locally, and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "-f": {
                        "type": "string",
                        "description": "IP address family"
                    },
                    "-p": {
                        "type": "string",
                        "description": "protocol"
                    },
                    "-I": {
                        "type": "string",
                        "description": "network interface"
                    },
                    "-w": {
                        "type": "string",
                        "description": "wait time"
                    },
                    "-a": {
                        "type": "boolean",
                        "description": "Show all sockets (listening and non-listening)"
                    }
                },
                "required": []
                }
            },
            {
            "name": "run_ps",
            "description": "Run the ps command locally, and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "-a": {
                        "type": "boolean",
                        "description": "Show processes for all users"
                    },
                    "-x": {
                        "type": "boolean",
                        "description": "Show processes without a controlling terminal"
                    },
                    "-u": {
                        "type": "string",
                        "description": "Show processes for the specified user"
                    },
                    "-p": {
                        "type": "string",
                        "description": "Show processes for the specified PID"
                    }
                },
                "required": []
                }
            }
        ]
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
        
        if run.status == "requires_action":
            
            tool_outputs = []

            tool_calls = run.required_action.submit_tool_outputs.tool_calls

            ## for each tool call, run the tool and collect the output

            for tool_call in tool_calls:
                print(tool_call)
                print(tool_call.function.name)
                results = tools[tool_call.function.name](tool_call.function.arguments)

                print(tool_call.function.arguments)

                

                tool_outputs.append({

                    "tool_call_id": tool_call.id,

                    "output": results

                })
                
            ## submit the tool outputs to the run

            run = client.beta.threads.runs.submit_tool_outputs(

                thread_id=thread.id,

                run_id=run.id,

                tool_outputs=tool_outputs

            )

        
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    print(messages)
    return messages

## first, ask the first agent for the python tool
send_message_and_wait_for_response(tool_request, thread, tool_developer)

## next, ask the critical agent to review and iterate on the tool
send_message_and_wait_for_response("Ensure any relevant tools have been run properly. Please critique the script written above, and iterate on that script. If the tools have not been run, please run the tools.", thread, critical_agent)


## finally, ask the alignment agent to review the output
send_message_and_wait_for_response("Please review and iterate on the script written above, and ensure it's aligned with our values.", thread, alignment_agent)

## do that whole thing 3 more times 
for i in range(1):
    ## first, ask the first agent for the python tool
    send_message_and_wait_for_response("Please apply any remaining feedback, complete any todos left in the code, and iterate on any remaining items left uncompleted.", thread, tool_developer)
    

    ## next, ask the critical agent to review and iterate on the tool
    send_message_and_wait_for_response("Please critique the script written above, and iterate on that script.", thread, critical_agent)

    ## finally, ask the alignment agent to review the output
    send_message_and_wait_for_response("Please review and iterate on the script written above, and ensure it's aligned with our values.", thread, alignment_agent)

## finally, extract the output of the final script
messages = send_message_and_wait_for_response("Please return only the script written above, and nothing else, this output will be written directly to a file so please do not provide any other text, or the fencing (eg: ```python) on the code block.", thread, alignment_agent)

## write all messages to a file
for message in messages:
    with open("output.txt", "a") as f:
        f.write(message.content[0].text + "\n")